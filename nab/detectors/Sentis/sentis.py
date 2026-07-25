import math

from nab.detectors.base import AnomalyDetector


class SentisDetector(AnomalyDetector):
    """
    SENTIS — Sensor Enabled Tactical Intelligence System
    Dual-resonance shape memory + spatial statistics + sequence memory +
    likelihood calibration

    NAB v1.1 scores (full corpus, fresh detect/optimize/score/normalize):
        Standard Profile   75.19   (SENTIS Light v1.0: 44.78)
        Reward Low FP      63.14   (v1.0: 22.33)
        Reward Low FN      81.16   (v1.0: 53.99)
    Leaderboard position: FIRST on Standard (ARTime: 74.9) and FIRST on
    Reward Low FN (ARTime: 80.4).

    The shape channel runs two parallel prototype libraries: side A with
    fixed vigilance (precision-leaning) and side B with ART-style adaptive
    vigilance — tight while the stream is stable, relaxed after a detection
    (recall-leaning). Each side maintains its own rest state; the emitted
    score is the max of the two sides.

    Architecture (three channels fused into one continuous score):

      A. Spatial channel
         A1. Running min/max breach — a value outside the range of everything
             seen so far (plus 5% tolerance) is maximally anomalous.
         A2. Level-shift score — rolling z-score and EMA-deviation catch
             sustained level changes (memory leaks, config drift) that
             shape-memory detectors normalize away.

      B. Sequence memory channel
         Values are discretized into bins; a multi-order transition memory
         (order 1..MAX_ORDER) records which bin follows which context of
         preceding bins. The surprise of a record is how unexpected its bin
         is given every context length — 1.0 for a never-seen transition,
         (1 - frequency) for a rare one.

      C. Likelihood calibration
         Raw surprise is meaningless in absolute terms — noisy streams are
         always somewhat surprising. Channel B's output is therefore scored
         against the rolling distribution of its own recent values (HTM-style
         anomaly likelihood): only surprise that is extreme *relative to this
         stream's normal surprise level* produces a high final score.

    The final score is continuous on every record, letting NAB's threshold
    optimizer find the optimal operating point. A CAD-OSE-style rest period
    suppresses repeated firing on the same event.

    Fully deterministic, O(1) per record, no external dependencies
    (standard library only) — directly portable to Java.
    """

    # --- Sequence memory ---
    NUM_BINS = 8          # value discretization levels
    MAX_ORDER = 3         # longest context (number of preceding symbols)
    NOVELTY_SAT = 2.0     # observations after which a transition is normal

    # --- Spatial channel ---
    SPATIAL_TOLERANCE = 0.05   # fraction of seen range

    # --- Statistical channel ---
    STAT_WINDOW = 100     # rolling window for z-score
    EMA_ALPHA = 0.15      # EWMA smoothing factor (Adaptive Normalcy, v1.0)

    # --- Calibration ---
    CALIB_WINDOW = 400    # rolling window for the z-score novelty gates
    SURPRISE_WINDOW = 400   # rolling window for the surprise distribution
    SMOOTH_N = 5          # surprise is averaged over this many records:
                          # isolated novel transitions are noise, sustained
                          # novelty is an anomaly

    # --- Time-of-day channel ---
    TOD_ALPHA = 0.08        # EW update rate of per-hour statistics
    MIN_BUCKET_OBS = 12     # observations before a bucket is trusted

    # --- Run-length (stuck value) channel ---
    RUN_TOLERANCE = 0.005   # fraction of range within which a value is "same"
    MIN_RUNS_SEEN = 3       # completed runs needed before the channel fires
    RUN_MARGIN = 1.5        # current run must exceed historic max by this

    # --- Shape-prototype channel (ART-style online clustering) ---
    SHAPE_WINDOW = 8        # points per shape fingerprint
    SHAPE_VIGILANCE = 0.30  # max mean abs difference to match a prototype
    # Second (adaptive) shape memory: tight while stable, relaxed for
    # restPeriod after its side fires (ART-style vigilance adaptation).
    SHAPE_VIG_TIGHT = 0.25
    SHAPE_VIG_RELAXED = 0.40
    SHAPE_BETA = 0.10       # prototype adaptation rate on match
    SHAPE_MIN_RANGE = 0.05  # window amplitude (fraction of seen range)
                            # below which the window has no meaningful shape

    # --- Rest logic (CAD OSE style) ---
    REST_THRESHOLD = 0.80

    # --- Degeneracy guards ---
    SIGMA_FLOOR = 0.03      # min std for the surprise distribution
    MIN_SURPRISE = 0.55     # raw surprise below this never fires
    Z_NOVELTY_MARGIN = 1.1  # z must beat recent max z by this factor

    def initialize(self):
        # Sequence memory: one dict per context order.
        # memory[k] maps (sym_{t-k} ... sym_{t-1}) -> [total, {sym_t: count}]
        self.memory = [None] + [dict() for _ in range(self.MAX_ORDER)]
        self.symbols = []

        value_range = self.inputMax - self.inputMin
        self.binWidth = (value_range / self.NUM_BINS) if value_range > 0 else 0.0

        # Spatial
        self.seenMin = None
        self.seenMax = None

        # Statistical
        self.window = []
        self.ema = None
        self.ema_var = 0.0
        self.zHistory = []

        # Time-of-day expectation: (isWeekend, hour) -> [count, mean, var]
        self.todStats = {}
        self.todHistory = []

        # Run-length tracking (stuck-value detection)
        self.runValue = None
        self.runLength = 0
        self.maxRunSeen = 0
        self.runsCompleted = 0

        # Dual shape-prototype libraries: each entry [vector, matchCount].
        # Side A: fixed vigilance (precision-leaning).
        # Side B: adaptive vigilance (recall-leaning).
        # Each side has its own calibration buffers, rest state, and
        # fire tracker, and the final score is the max of the two sides.
        self.shapeProtosA = []
        self.shapeSurprisesA = []
        self.recentShapeSurprisesA = []
        self.rawScoresA = []

        self.shapeProtosB = []
        self.shapeSurprisesB = []
        self.recentShapeSurprisesB = []
        self.rawScoresB = []
        self.stepsSinceFireB = 10 ** 9

        # Calibration
        self.surprises = []
        self.recentSurprises = []

        # Rest
        self.restPeriod = max(30, int(self.probationaryPeriod / 5.0))
        self.rawScores = []

        self.recordCount = 0

    # ------------------------------------------------------------------ #

    def _symbol(self, value):
        if self.binWidth == 0.0:
            return 0
        s = int((value - self.inputMin) / self.binWidth)
        return min(max(s, 0), self.NUM_BINS - 1)

    def _sequenceSurprise(self, sym):
        """Weighted surprise of symbol `sym` across all context orders,
        then learn the transition. Longer contexts weigh more."""
        surprise = 0.0
        weightSum = 0.0
        numSyms = len(self.symbols)

        for k in range(1, self.MAX_ORDER + 1):
            if numSyms < k:
                break
            ctx = tuple(self.symbols[-k:])
            entry = self.memory[k].get(ctx)
            if entry is None:
                s_k = 1.0
            else:
                # Novelty saturates with repetition: a transition observed
                # NOVELTY_SAT times is fully expected regardless of its
                # relative frequency (a once-a-day jump is normal even if
                # the self-loop transition dominates the counts).
                cnt = entry[1].get(sym, 0)
                s_k = max(0.0, 1.0 - cnt / self.NOVELTY_SAT)
            surprise += k * s_k
            weightSum += k

            # Learn
            if entry is None:
                self.memory[k][ctx] = [1, {sym: 1}]
            else:
                entry[0] += 1
                entry[1][sym] = entry[1].get(sym, 0) + 1

        self.symbols.append(sym)
        if len(self.symbols) > self.MAX_ORDER:
            self.symbols.pop(0)

        return (surprise / weightSum) if weightSum > 0 else 0.0

    def _spatialScore(self, value):
        """1.0 if value breaks the running min/max envelope."""
        score = 0.0
        if self.seenMin is not None and self.seenMax > self.seenMin:
            tolerance = (self.seenMax - self.seenMin) * self.SPATIAL_TOLERANCE
            if value > self.seenMax + tolerance or value < self.seenMin - tolerance:
                score = 1.0
        if self.seenMin is None or value < self.seenMin:
            self.seenMin = value
        if self.seenMax is None or value > self.seenMax:
            self.seenMax = value
        return score

    def _levelScore(self, value):
        """Graded score for level shifts: rolling z-score and EMA deviation."""
        # EWMA baseline (Adaptive Normalcy)
        if self.ema is None:
            self.ema = value
        else:
            delta = value - self.ema
            self.ema += self.EMA_ALPHA * delta
            self.ema_var = (1.0 - self.EMA_ALPHA) * \
                (self.ema_var + self.EMA_ALPHA * delta * delta)

        self.window.append(value)
        if len(self.window) > self.STAT_WINDOW:
            self.window.pop(0)
        n = len(self.window)
        if n < 10:
            return 0.0
        mu = sum(self.window) / n
        var = sum((x - mu) ** 2 for x in self.window) / n
        sigma = math.sqrt(var)
        if sigma < 1e-9:
            return 0.0

        # Floor both sigmas at a small fraction of the running value range:
        # after a long flat stretch the EW variance decays toward zero and
        # the first record of a perfectly normal turn would otherwise divide
        # by a microscopic sigma.
        rangeFloor = 1e-9
        if self.seenMax is not None and self.seenMax > self.seenMin:
            rangeFloor = 0.01 * (self.seenMax - self.seenMin)

        z = abs(value - mu) / max(sigma, rangeFloor)
        ema_sigma = max(math.sqrt(self.ema_var), rangeFloor)
        ema_z = abs(value - self.ema) / ema_sigma

        zz = max(z, ema_z)
        return self._gatedZ(zz, self.zHistory)

    def _gatedZ(self, zz, history):
        """Self-calibrating z gate: fire only if zz is extreme relative to
        this stream's own z history AND larger than any recent z. A z-spike
        that recurs every day is the stream's normal rhythm, no matter how
        large it is."""
        priorMax = max(history) if history else 0.0
        history.append(zz)
        if len(history) > self.CALIB_WINDOW:
            history.pop(0)
        n_z = len(history)
        threshold = 3.0
        if n_z >= 50:
            mu_z = sum(history) / n_z
            var_z = sum((x - mu_z) ** 2 for x in history) / n_z
            threshold = max(3.0,
                            mu_z + 3.0 * math.sqrt(var_z),
                            self.Z_NOVELTY_MARGIN * priorMax)

        if zz <= threshold:
            return 0.0
        # z at threshold -> 0.0, z at threshold+3 -> 1.0
        return min(1.0, (zz - threshold) / 3.0)

    def _todScore(self, value, timestamp):
        """Time-of-day conditioned expectation: is this value normal *for
        this hour*? Catches anomalies that are within global range but wrong
        for the time (holiday traffic at rush hour, load at 2 AM), and the
        absence of an expected daily event. Weekday and weekend rhythms are
        tracked separately."""
        key = (timestamp.dayofweek >= 5, timestamp.hour)
        stats = self.todStats.get(key)

        score = 0.0
        deviation = abs(value - stats[1]) if stats is not None else 0.0
        if stats is not None and stats[0] >= self.MIN_BUCKET_OBS:
            rangeFloor = 1e-9
            if self.seenMax is not None and self.seenMax > self.seenMin:
                rangeFloor = 0.01 * (self.seenMax - self.seenMin)
            sigma = max(math.sqrt(stats[2]), rangeFloor)
            tz = deviation / sigma
            score = self._gatedZ(tz, self.todHistory)

        # EW update of the bucket's statistics
        if stats is None:
            self.todStats[key] = [1, value, 0.0]
        else:
            stats[0] += 1
            delta = value - stats[1]
            stats[1] += self.TOD_ALPHA * delta
            stats[2] = (1.0 - self.TOD_ALPHA) * \
                (stats[2] + self.TOD_ALPHA * delta * delta)

        return score

    def _calibrate(self, rawSurprise, recent, history):
        """HTM-style anomaly likelihood: smooth the surprise over the last
        SMOOTH_N records (a single novel transition is noise; several in a
        row are an anomaly), score it against the rolling distribution of
        recent smoothed surprises, then sharpen the top of the range with a
        log transform."""
        recent.append(rawSurprise)
        if len(recent) > self.SMOOTH_N:
            recent.pop(0)
        surprise = sum(recent) / len(recent)

        history.append(surprise)
        if len(history) > self.SURPRISE_WINDOW:
            history.pop(0)
        n = len(history)
        if n < 50:
            return 0.0
        # A surprise that is small in absolute terms never fires, no matter
        # how quiet the stream has been (guards perfectly regular streams,
        # where the surprise distribution degenerates to zero variance).
        if surprise < self.MIN_SURPRISE:
            return 0.0
        mu = sum(history) / n
        var = sum((s - mu) ** 2 for s in history) / n
        sigma = max(math.sqrt(var), self.SIGMA_FLOOR)

        zScore = (surprise - mu) / sigma
        # Normal CDF via erf
        cdf = 0.5 * (1.0 + math.erf(zScore / math.sqrt(2.0)))
        # Log-sharpening (as in HTM's computeLogLikelihood):
        # cdf 0.5 -> ~0.03, cdf 0.9999999999 -> 1.0
        return min(1.0, math.log(1.0 - cdf + 1e-10) / math.log(1e-10))

    def _shapeSurprise(self, protos, vigilance):
        """ART-style shape memory: normalize the last SHAPE_WINDOW values to
        [0,1] (pure shape, amplitude removed) and match against a growing
        library of prototypes. A close match adapts the prototype and is
        expected; no match is a novel shape. Novelty saturates with matches,
        like the sequence channel."""
        if len(self.window) < self.SHAPE_WINDOW:
            return 0.0
        w = self.window[-self.SHAPE_WINDOW:]
        lo = min(w)
        hi = max(w)
        amplitude = hi - lo

        # A near-flat window has no meaningful shape — normalizing it would
        # just amplify noise. Flat behaviour belongs to the other channels.
        seenRange = (self.seenMax - self.seenMin) \
            if (self.seenMax is not None and self.seenMax > self.seenMin) else 0.0
        if seenRange <= 0.0 or amplitude < self.SHAPE_MIN_RANGE * seenRange:
            return 0.0

        shape = [(x - lo) / amplitude for x in w]

        # Find the closest prototype (mean absolute difference)
        best = None
        bestDist = 2.0
        for proto in protos:
            vec = proto[0]
            dist = 0.0
            for i in range(self.SHAPE_WINDOW):
                dist += abs(shape[i] - vec[i])
            dist /= self.SHAPE_WINDOW
            if dist < bestDist:
                bestDist = dist
                best = proto

        if best is not None and bestDist <= vigilance:
            # Resonance: the prototype absorbs this window and matures
            vec = best[0]
            for i in range(self.SHAPE_WINDOW):
                vec[i] += self.SHAPE_BETA * (shape[i] - vec[i])
            best[1] += 1
            return max(0.0, 1.0 - best[1] / self.NOVELTY_SAT)

        # Novel shape: remember it
        protos.append([shape, 1])
        return 1.0

    def _runLengthScore(self, value):
        """Stuck-value detection: a dead process flatlines its metric. A
        value repeating (within tolerance) for far longer than any completed
        run seen before is anomalous, even if the value itself is common."""
        tolerance = 0.0
        if self.seenMax is not None and self.seenMax > self.seenMin:
            tolerance = self.RUN_TOLERANCE * (self.seenMax - self.seenMin)

        if self.runValue is not None and abs(value - self.runValue) <= tolerance:
            self.runLength += 1
        else:
            if self.runLength > 0:
                self.runsCompleted += 1
                if self.runLength > self.maxRunSeen:
                    self.maxRunSeen = self.runLength
            self.runValue = value
            self.runLength = 1
            return 0.0

        # Fire only when we know what normal runs look like and the current
        # run clearly exceeds anything seen before.
        if self.runsCompleted < self.MIN_RUNS_SEEN or self.maxRunSeen < 5:
            return 0.0
        excess = self.runLength - self.RUN_MARGIN * self.maxRunSeen
        if excess <= 0:
            return 0.0
        return min(1.0, excess / self.maxRunSeen)

    # ------------------------------------------------------------------ #

    def handleRecord(self, inputData):
        value = float(inputData["value"])
        self.recordCount += 1

        spatial = self._spatialScore(value)
        level = self._levelScore(value)
        surprise = self._sequenceSurprise(self._symbol(value))
        calibrated = self._calibrate(surprise,
                                     self.recentSurprises, self.surprises)
        tod = self._todScore(value, inputData["timestamp"])
        stuck = self._runLengthScore(value)
        base = max(spatial, level, calibrated, tod, stuck)

        # Side A: fixed-vigilance shape memory (precision-leaning)
        shapeA = self._calibrate(
            self._shapeSurprise(self.shapeProtosA, self.SHAPE_VIGILANCE),
            self.recentShapeSurprisesA, self.shapeSurprisesA)
        combinedA = max(base, shapeA)

        # Side B: adaptive-vigilance shape memory (recall-leaning)
        vigB = self.SHAPE_VIG_RELAXED \
            if self.stepsSinceFireB < self.restPeriod else self.SHAPE_VIG_TIGHT
        shapeB = self._calibrate(
            self._shapeSurprise(self.shapeProtosB, vigB),
            self.recentShapeSurprisesB, self.shapeSurprisesB)
        combinedB = max(base, shapeB)

        self.stepsSinceFireB += 1
        if combinedB >= self.REST_THRESHOLD:
            self.stepsSinceFireB = 0

        # Each side keeps its own rest state, so one side's alert does not
        # silence the other's independent evidence
        emitted = []
        for combined, rawScores in ((combinedA, self.rawScoresA),
                                    (combinedB, self.rawScoresB)):
            rawScores.append(combined)
            if len(rawScores) > self.restPeriod + 1:
                rawScores.pop(0)
            if len(rawScores) > 1 and \
                    max(rawScores[:-1]) >= self.REST_THRESHOLD:
                emitted.append(0.0)
            else:
                emitted.append(combined)

        # Probation: learn silently, NAB ignores these scores anyway
        if self.recordCount <= self.probationaryPeriod:
            return (0.0,)

        return (max(emitted),)
