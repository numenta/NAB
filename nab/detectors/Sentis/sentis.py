import math

from nab.detectors.base import AnomalyDetector


class SentisDetector(AnomalyDetector):
    """
    SENTIS — Sensor Enabled Tactical Intelligence System

    SENTIS was designed by studying the detectors already benchmarked on
    NAB and borrowing their best ideas while patching their blind spots.
    ARTime matches normalized value shapes but is structurally blind to
    slow drift, so SENTIS's Deviation Index (Channel 2) tracks absolute
    value trends instead. CAD OSE remembers value-transition sequences
    but clamps anything outside its initial range, so SENTIS's Spatial
    Envelope (Channel 1) never clamps. Numenta HTM calibrates every alert
    against the stream's own recent history rather than a fixed
    threshold — the same idea drives SENTIS's shared likelihood
    calibration. earthgecko Skyline avoids assuming a Gaussian
    distribution, and so does SENTIS: every channel is self-calibrating
    and non-parametric. Six channels, each targeting a distinct anomaly
    class — Spatial Envelope, Deviation Index, Sequence Memory, Temporal
    Context, Flatline Sentinel, and a dual-vigilance Shape Memory
    inspired by ARTime — are fused into one continuous score.

    Evaluated on the full NAB v1.1 corpus (fresh detect/optimize/score/
    normalize): Standard 75.19, Reward Low FP 63.14, Reward Low FN
    81.16 — first place on Standard and Reward Low FN (ARTime: 74.9 /
    80.4).

    Fully deterministic, no external dependencies, O(1) per record.
    """

    # ---- Channel 1: Spatial Envelope ----
    SPATIAL_TOLERANCE = 0.05   # tolerance margin, as a fraction of seen range

    # ---- Channel 2: Deviation Index ----
    STAT_WINDOW = 100      # rolling window for the z-score
    EMA_ALPHA = 0.15       # EWMA smoothing factor (Adaptive Normalcy baseline)

    # ---- Channel 3: Sequence Memory ----
    NUM_BINS = 8       # value discretization levels
    MAX_ORDER = 3       # longest transition context (preceding symbols)

    # ---- Channel 4: Temporal Context ----
    TOD_ALPHA = 0.08        # EW update rate of per-hour statistics
    MIN_BUCKET_OBS = 12     # observations before an hourly bucket is trusted

    # ---- Channel 5: Flatline Sentinel ----
    RUN_TOLERANCE = 0.005          # fraction of range within which a value
                                    # is considered "the same"
    MIN_RUNS_SEEN = 3              # completed runs needed before this fires
    MIN_RUN_LENGTH_FOR_STATS = 5   # runs shorter than this don't count
                                    # as history
    RUN_MARGIN = 1.5                # current run must exceed the historic
                                    # max by this factor

    # ---- Channel 6: Shape Memory (dual resonance) ----
    SHAPE_WINDOW = 8            # points per shape fingerprint
    SHAPE_VIGILANCE = 0.30      # side A: fixed vigilance (precision-leaning)
    SHAPE_VIG_TIGHT = 0.25      # side B: adaptive vigilance while stable
    SHAPE_VIG_RELAXED = 0.40    # side B: adaptive vigilance after a detection
    SHAPE_BETA = 0.10           # prototype adaptation rate on a match
    SHAPE_MIN_RANGE = 0.05      # min window amplitude (fraction of seen
                                 # range) below which a window has no
                                 # meaningful shape
    SHAPE_DISTANCE_SENTINEL = 2.0   # larger than any real distance (the
                                     # max possible is 1.0), so the first
                                     # prototype always beats it

    # ---- Shared: novelty saturation (Channels 3 and 6) ----
    NOVELTY_SAT = 2.0   # observations after which a transition/shape is
                        # considered fully normal

    # ---- Shared: novelty-gated z-score (Channels 2 and 4) ----
    Z_NOVELTY_WINDOW = 400      # rolling window of past z-scores
    Z_NOVELTY_MARGIN = 1.1      # z must beat the recent max z by this factor
    Z_THRESHOLD_SIGMA = 3.0     # floor threshold, in standard deviations
    Z_SATURATION_SPAN = 3.0     # z-score span from threshold to a score of 1.0
    MIN_WINDOW_FOR_STATS = 10   # min points before the rolling window
                                 # is trusted

    # ---- Shared: likelihood calibration (Channels 3 and 6) ----
    SURPRISE_WINDOW = 400   # rolling window for the surprise distribution
    SMOOTH_N = 5             # surprise is averaged over this many records:
                             # isolated novel transitions are noise,
                             # sustained novelty is an anomaly
    MIN_SURPRISE = 0.55      # raw surprise below this never fires
    SIGMA_FLOOR = 0.03       # minimum std for the surprise distribution
    MIN_HISTORY_FOR_STATS = 50   # min points before a distribution
                                  # is trusted

    # ---- Fusion / rest logic (CAD-OSE style) ----
    REST_THRESHOLD = 0.80   # a side scoring at/above this triggers its own rest gate

    # ---- Numerical guards ----
    EPSILON = 1e-9        # floor for near-zero denominators
    LOG_EPSILON = 1e-10   # keeps log() finite as likelihood approaches 0 or 1
    RANGE_FLOOR_FRACTION = 0.01   # min sigma, as a fraction of the seen range

    def initialize(self):
        # Channel 3 — Sequence Memory: one dict per context order.
        # memory[order] maps (bin_{t-order} .. bin_{t-1}) -> [total, {bin_t: count}]
        self.memory = [None] + [dict() for _ in range(self.MAX_ORDER)]
        self.symbols = []

        valueRange = self.inputMax - self.inputMin
        self.binWidth = (valueRange / self.NUM_BINS) if valueRange > 0 else 0.0

        # Channel 1 — Spatial Envelope
        self.seenMin = None
        self.seenMax = None

        # Channel 2 — Deviation Index (its rolling window is reused by
        # Channel 6's shape fingerprint)
        self.window = []
        self.ema = None
        self.ema_var = 0.0
        self.zHistory = []

        # Channel 4 — Temporal Context: (isWeekend, hour) -> [count, mean, var]
        self.todStats = {}
        self.todHistory = []

        # Channel 5 — Flatline Sentinel
        self.runValue = None
        self.runLength = 0
        self.maxRunSeen = 0
        self.runsCompleted = 0

        # Channel 6 — Shape Memory: dual prototype libraries, each entry
        # [vector, matchCount]. Side A: fixed vigilance (precision-leaning).
        # Side B: adaptive vigilance (recall-leaning). Each side keeps its
        # own calibration buffers, rest state, and fire tracker; the final
        # score is the max of the two sides.
        self.shapeProtosA = []
        self.shapeSurprisesA = []
        self.recentShapeSurprisesA = []
        self.rawScoresA = []

        self.shapeProtosB = []
        self.shapeSurprisesB = []
        self.recentShapeSurprisesB = []
        self.rawScoresB = []
        self.stepsSinceFireB = 10 ** 9

        # Shared likelihood calibration state for Channel 3
        self.surprises = []
        self.recentSurprises = []

        # Fusion: rest period applied independently to each shape-memory side
        self.restPeriod = max(30, int(self.probationaryPeriod / 5.0))

        self.recordCount = 0

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #

    def _seen_range_floor(self):
        """A small floor value derived from the range seen so far (tracked
        by Channel 1), used to avoid dividing by a near-zero standard
        deviation right after a long flat stretch. Falls back to EPSILON
        before any range has been observed."""
        if self.seenMax is not None and self.seenMax > self.seenMin:
            return self.RANGE_FLOOR_FRACTION * (self.seenMax - self.seenMin)
        return self.EPSILON

    def _novelty_gated_z(self, zScore, history):
        """Shared by Channels 2 and 4: fire only if `zScore` is extreme
        relative to this stream's own z-score history AND larger than any
        recent z. A z-spike that recurs every day is the stream's normal
        rhythm, no matter how large it is."""
        priorMax = max(history) if history else 0.0
        history.append(zScore)
        if len(history) > self.Z_NOVELTY_WINDOW:
            history.pop(0)
        n = len(history)
        threshold = self.Z_THRESHOLD_SIGMA
        if n >= self.MIN_HISTORY_FOR_STATS:
            mean = sum(history) / n
            variance = sum((x - mean) ** 2 for x in history) / n
            threshold = max(self.Z_THRESHOLD_SIGMA,
                            mean + self.Z_THRESHOLD_SIGMA * math.sqrt(variance),
                            self.Z_NOVELTY_MARGIN * priorMax)

        if zScore <= threshold:
            return 0.0
        # zScore at threshold -> 0.0, zScore at threshold + span -> 1.0
        return min(1.0, (zScore - threshold) / self.Z_SATURATION_SPAN)

    def _calibrate_surprise(self, rawSurprise, recent, history):
        """Shared by Channels 3 and 6 (HTM-style anomaly likelihood).
        Smooths the surprise over the last SMOOTH_N records (a single
        novel transition is noise; several in a row are an anomaly),
        scores it against the rolling distribution of recent smoothed
        surprises, then sharpens the top of the range with a log
        transform."""
        recent.append(rawSurprise)
        if len(recent) > self.SMOOTH_N:
            recent.pop(0)
        surprise = sum(recent) / len(recent)

        history.append(surprise)
        if len(history) > self.SURPRISE_WINDOW:
            history.pop(0)
        n = len(history)
        if n < self.MIN_HISTORY_FOR_STATS:
            return 0.0
        # A surprise that is small in absolute terms never fires, no matter
        # how quiet the stream has been (guards perfectly regular streams,
        # where the surprise distribution degenerates to zero variance).
        if surprise < self.MIN_SURPRISE:
            return 0.0
        mean = sum(history) / n
        variance = sum((s - mean) ** 2 for s in history) / n
        sigma = max(math.sqrt(variance), self.SIGMA_FLOOR)

        zScore = (surprise - mean) / sigma
        # Normal CDF via erf
        cdf = 0.5 * (1.0 + math.erf(zScore / math.sqrt(2.0)))
        # Log-sharpening (as in HTM's computeLogLikelihood):
        # cdf 0.5 -> ~0.03, cdf 0.9999999999 -> 1.0
        return min(1.0, math.log(1.0 - cdf + self.LOG_EPSILON)
                   / math.log(self.LOG_EPSILON))

    # ------------------------------------------------------------------ #
    # Channel 1 — Spatial Envelope
    # ------------------------------------------------------------------ #

    def _spatial_envelope_score(self, value):
        """1.0 if `value` breaks the running min/max envelope (plus a
        tolerance margin); 0.0 otherwise. Then updates the envelope."""
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

    # ------------------------------------------------------------------ #
    # Channel 2 — Deviation Index
    # ------------------------------------------------------------------ #

    def _deviation_index_score(self, value):
        """Rolling z-score and EMA deviation, gated by _novelty_gated_z.
        Catches sustained level shifts (memory leaks, config drift) that
        shape-based detectors like ARTime miss."""
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
        if n < self.MIN_WINDOW_FOR_STATS:
            return 0.0
        mean = sum(self.window) / n
        variance = sum((x - mean) ** 2 for x in self.window) / n
        sigma = math.sqrt(variance)
        if sigma < self.EPSILON:
            return 0.0

        # Floor both sigmas using the seen value range: after a long flat
        # stretch the EW variance decays toward zero and the first record
        # of a perfectly normal turn would otherwise divide by a
        # microscopic sigma.
        rangeFloor = self._seen_range_floor()
        zScore = abs(value - mean) / max(sigma, rangeFloor)
        emaSigma = max(math.sqrt(self.ema_var), rangeFloor)
        emaZScore = abs(value - self.ema) / emaSigma

        return self._novelty_gated_z(max(zScore, emaZScore), self.zHistory)

    # ------------------------------------------------------------------ #
    # Channel 3 — Sequence Memory
    # ------------------------------------------------------------------ #

    def _value_bin(self, value):
        """Discretizes a value into one of NUM_BINS bins."""
        if self.binWidth == 0.0:
            return 0
        binIndex = int((value - self.inputMin) / self.binWidth)
        return min(max(binIndex, 0), self.NUM_BINS - 1)

    def _sequence_memory_surprise(self, symbolBin):
        """Weighted surprise of `symbolBin` across all context orders
        1..MAX_ORDER, then learns the transition. Longer contexts weigh
        more. The raw surprise returned here still needs
        _calibrate_surprise to become a channel score."""
        surprise = 0.0
        weightSum = 0.0
        numSymbols = len(self.symbols)

        for order in range(1, self.MAX_ORDER + 1):
            if numSymbols < order:
                break
            context = tuple(self.symbols[-order:])
            entry = self.memory[order].get(context)
            if entry is None:
                orderSurprise = 1.0
            else:
                # Novelty saturates with repetition: a transition observed
                # NOVELTY_SAT times is fully expected regardless of its
                # relative frequency (a once-a-day jump is normal even if
                # the self-loop transition dominates the counts).
                count = entry[1].get(symbolBin, 0)
                orderSurprise = max(0.0, 1.0 - count / self.NOVELTY_SAT)
            surprise += order * orderSurprise
            weightSum += order

            # Learn
            if entry is None:
                self.memory[order][context] = [1, {symbolBin: 1}]
            else:
                entry[0] += 1
                entry[1][symbolBin] = entry[1].get(symbolBin, 0) + 1

        self.symbols.append(symbolBin)
        if len(self.symbols) > self.MAX_ORDER:
            self.symbols.pop(0)

        return (surprise / weightSum) if weightSum > 0 else 0.0

    # ------------------------------------------------------------------ #
    # Channel 4 — Temporal Context
    # ------------------------------------------------------------------ #

    def _temporal_context_score(self, value, timestamp):
        """Is this value normal *for this hour*? Catches anomalies that
        are within global range but wrong for the time (holiday traffic
        at rush hour, load at 2 AM), and the absence of an expected daily
        event. Weekday and weekend rhythms are tracked separately."""
        key = (timestamp.dayofweek >= 5, timestamp.hour)
        stats = self.todStats.get(key)

        score = 0.0
        deviation = abs(value - stats[1]) if stats is not None else 0.0
        if stats is not None and stats[0] >= self.MIN_BUCKET_OBS:
            sigma = max(math.sqrt(stats[2]), self._seen_range_floor())
            zScore = deviation / sigma
            score = self._novelty_gated_z(zScore, self.todHistory)

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

    # ------------------------------------------------------------------ #
    # Channel 5 — Flatline Sentinel
    # ------------------------------------------------------------------ #

    def _flatline_sentinel_score(self, value):
        """A dead process flatlines its metric. A value repeating (within
        tolerance) for far longer than any completed run seen before is
        anomalous, even if the value itself is common."""
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

        # Fire only when we know what normal runs look like and the
        # current run clearly exceeds anything seen before.
        if (self.runsCompleted < self.MIN_RUNS_SEEN
                or self.maxRunSeen < self.MIN_RUN_LENGTH_FOR_STATS):
            return 0.0
        excess = self.runLength - self.RUN_MARGIN * self.maxRunSeen
        if excess <= 0:
            return 0.0
        return min(1.0, excess / self.maxRunSeen)

    # ------------------------------------------------------------------ #
    # Channel 6 — Shape Memory (dual resonance)
    # ------------------------------------------------------------------ #

    def _shape_memory_surprise(self, prototypes, vigilance):
        """Normalizes the last SHAPE_WINDOW values to [0,1] (pure shape,
        amplitude removed) and matches against a growing library of
        prototypes. A close match adapts the prototype and is expected;
        no match is a novel shape. Novelty saturates with matches, like
        Channel 3."""
        if len(self.window) < self.SHAPE_WINDOW:
            return 0.0
        recentValues = self.window[-self.SHAPE_WINDOW:]
        low = min(recentValues)
        high = max(recentValues)
        amplitude = high - low

        # A near-flat window has no meaningful shape — normalizing it
        # would just amplify noise. Flat behaviour belongs to the other
        # channels.
        seenRange = (self.seenMax - self.seenMin) \
            if (self.seenMax is not None and self.seenMax > self.seenMin) else 0.0
        if seenRange <= 0.0 or amplitude < self.SHAPE_MIN_RANGE * seenRange:
            return 0.0

        shape = [(x - low) / amplitude for x in recentValues]

        # Find the closest prototype (mean absolute difference)
        bestPrototype = None
        bestDistance = self.SHAPE_DISTANCE_SENTINEL
        for prototype in prototypes:
            vector = prototype[0]
            distance = 0.0
            for i in range(self.SHAPE_WINDOW):
                distance += abs(shape[i] - vector[i])
            distance /= self.SHAPE_WINDOW
            if distance < bestDistance:
                bestDistance = distance
                bestPrototype = prototype

        if bestPrototype is not None and bestDistance <= vigilance:
            # Resonance: the prototype absorbs this window and matures
            vector = bestPrototype[0]
            for i in range(self.SHAPE_WINDOW):
                vector[i] += self.SHAPE_BETA * (shape[i] - vector[i])
            bestPrototype[1] += 1
            return max(0.0, 1.0 - bestPrototype[1] / self.NOVELTY_SAT)

        # Novel shape: remember it
        prototypes.append([shape, 1])
        return 1.0

    def _shape_memory_side_score(self, prototypes, recentSurprises,
                              surpriseHistory, vigilance, baseScore):
        """Scores one side of the dual shape memory and fuses it with
        `baseScore`, the max of the other five channels."""
        surprise = self._shape_memory_surprise(prototypes, vigilance)
        shapeScore = self._calibrate_surprise(
            surprise, recentSurprises, surpriseHistory)
        return max(baseScore, shapeScore)

    # ------------------------------------------------------------------ #
    # Fusion
    # ------------------------------------------------------------------ #

    def _apply_rest_gate(self, combinedScore, rawScoreHistory):
        """CAD-OSE-style rest period: once a side's score reaches
        REST_THRESHOLD, that side stays silent for `restPeriod` records
        so one real event produces one alert. Each side gates
        independently, so one side firing never silences the other
        side's evidence."""
        rawScoreHistory.append(combinedScore)
        if len(rawScoreHistory) > self.restPeriod + 1:
            rawScoreHistory.pop(0)
        if len(rawScoreHistory) > 1 and \
                max(rawScoreHistory[:-1]) >= self.REST_THRESHOLD:
            return 0.0
        return combinedScore

    def handleRecord(self, inputData):
        value = float(inputData["value"])
        self.recordCount += 1

        spatialScore = self._spatial_envelope_score(value)
        deviationScore = self._deviation_index_score(value)
        sequenceNovelty = self._sequence_memory_surprise(self._value_bin(value))
        sequenceScore = self._calibrate_surprise(
            sequenceNovelty, self.recentSurprises, self.surprises)
        temporalScore = self._temporal_context_score(value, inputData["timestamp"])
        flatlineScore = self._flatline_sentinel_score(value)
        baseScore = max(spatialScore, deviationScore, sequenceScore,
                        temporalScore, flatlineScore)

        # Side A: fixed-vigilance shape memory (precision-leaning)
        combinedA = self._shape_memory_side_score(
            self.shapeProtosA, self.recentShapeSurprisesA,
            self.shapeSurprisesA, self.SHAPE_VIGILANCE, baseScore)

        # Side B: adaptive-vigilance shape memory (recall-leaning) — tight
        # while stable, relaxed for one restPeriod after this side fires.
        adaptiveVigilance = (self.SHAPE_VIG_RELAXED
                             if self.stepsSinceFireB < self.restPeriod
                             else self.SHAPE_VIG_TIGHT)
        combinedB = self._shape_memory_side_score(
            self.shapeProtosB, self.recentShapeSurprisesB,
            self.shapeSurprisesB, adaptiveVigilance, baseScore)

        self.stepsSinceFireB += 1
        if combinedB >= self.REST_THRESHOLD:
            self.stepsSinceFireB = 0

        # Each side keeps its own rest state, so one side's alert does not
        # silence the other side's independent evidence.
        emittedA = self._apply_rest_gate(combinedA, self.rawScoresA)
        emittedB = self._apply_rest_gate(combinedB, self.rawScoresB)

        # Probation: learn silently, NAB ignores these scores anyway
        if self.recordCount <= self.probationaryPeriod:
            return (0.0,)

        return (max(emittedA, emittedB),)
