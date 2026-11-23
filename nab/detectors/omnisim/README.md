# OmniSim Streaming Anomaly Detector

**OmniSim** is an open-source, multi-scale streaming anomaly detector for telemetry and continuous time-series benchmarks.

- **Author:** Deeven Seru (<deevenseru11@gmail.com>)
- **Repository:** [https://github.com/Deeven-Seru/omnisim](https://github.com/Deeven-Seru/omnisim)

## Architecture Overview

OmniSim operates purely in streaming mode with $O(1)$ constant time complexity per record and zero external library dependencies (uses Python standard library math only). It synthesizes six specialized invariant channels:

1. **Spatial Envelope (Channel 1):** Running min-max bounds with dynamic tolerance margin that prevents hard clamping on novel scales.
2. **Deviation Index (Channel 2):** Adaptive normalcy baseline combining rolling z-scores with exponential weighted moving variance.
3. **Sequence Transition Memory (Channel 3):** Context-order Markov transition graphs with novelty saturation to capture multi-step ordering breakdowns.
4. **Temporal Context (Channel 4):** Diurnal hourly profiling with separate weekday vs. weekend rhythm tracking.
5. **Flatline Sentinel (Channel 5):** Non-parametric run-length monitoring that flags metric freezing or process hangs.
6. **Dual-Vigilance Shape Memory (Channel 6):** Adaptive resonance shape fingerprinting with dual prototype libraries:
   - Side A: Fixed-vigilance precision tracker.
   - Side B: Adaptive-vigilance recall tracker with dynamic post-detection vigilance relaxation.

## Fusion and Calibration

Channel outputs are sharpened via log-likelihood anomaly calibration (evaluating smoothed anomaly surprise against running normal CDFs) and decoupled through independent CAD-OSE style rest-period gating.

## Benchmark Results (Full NAB v1.1 Corpus)

- **Standard Profile:** **75.19** (#1 on NAB Scoreboard)
- **Reward Low FN:** **81.16** (#1 on NAB Scoreboard)
- **Reward Low FP:** **63.14**
