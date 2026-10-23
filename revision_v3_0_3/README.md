# State-triggered cooperative mandatory merging

Source code and data for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow*, by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

Version 3.0.3 accompanies Figures 1–14 in the revised manuscript. Figure labels use at most two decimal places, with milliradians for steering and yaw rate. The simulator, experimental records and statistical results are unchanged from version 3.0.0.

## Reproduce

MATLAB R2023b with Optimization Toolbox is required. The experiment runner uses Parallel Computing Toolbox with five local workers. Python 3.12 with NumPy, pandas, SciPy, Matplotlib and Pillow reproduces the analyses and figures. Install the Python packages listed in `requirements.txt`. Figure scripts use Times New Roman when available.

From this directory:

1. `matlab -singleCompThread -batch "run('run_corrected.m')"` runs missing experiments and resumes from saved records. Existing records are retained. To recompute every simulation, first move the supplied `corrected/` directory to a separate backup location.
2. `python analyze_corrected.py` regenerates the statistical tables from the records.
3. `python plot_corrected.py` regenerates Figures 1–14.
4. `matlab -singleCompThread -batch "run('run_final_timing.m')"` repeats serial timing. Close experiment workers and other computational workloads first. Wall-clock results depend on the machine.

For a single simulation, add `code/` to the MATLAB path, obtain settings from `params_merge`, set the desired fields, and call `simulate_final(mode, penetration, seed, P, false)`. Modes are `COOP`, `ECO` and `PASSIVE`.

## Files

- `code/`: vehicle parameters, simulator, compact record exporter and tuning candidates.
- `corrected/registered_jobs.csv`: the first 3754 experiments in job-list order.
- `corrected/evaluation_jobs.csv`: 120 independent tuning-evaluation jobs, numbered 3755–3874.
- `corrected/run_XXXX.mat`: parameters `P`, job definition and compact result `S` for one run.
- `corrected/trajectory_XXXX.mat`: full trajectory `R` for representative runs.
- `corrected/hold_physical_4.mat` and `hold_physical_16.mat`: deterministic recovery probes, with a deliberately insufficient initial rear gap of 0.20 m.
- `corrected/tuning_training.csv`: equal-budget candidate-selection results.
- `corrected/runtime_*.csv`: serial step measurements and summaries.
- `processed/`: seed metrics, paired contrasts, summaries and common-service accounting.
- `figures/`: output directory populated by the figure-reproduction script.
- `DATA_DICTIONARY.md`: experiment and metric definitions.
- `SHA256SUMS.txt`: checksums of the included files.

## Timing protocol

Timing used MATLAB R2023b with Optimization Toolbox on an Intel Core i5-12500H computer with 16 GB RAM, one computational thread and no parallel pool. Each strategy–queue combination was warmed with seed 999, then measured over seeds 0–2, with 900 steps per run. Each measurement includes sensing, communication, QP repair, filtering, state propagation, diagnostics and trajectory recording. Initialization, final fuel aggregation and file output are excluded. The script `run_final_timing.m` and `corrected/runtime_*.csv` retain the protocol and measurements.

Display rounding does not modify raw records or statistical calculations. Minimum gaps are evaluated over the relevant vehicle pairs and sampled times in each run, then minimized across all 20 seeds for extrema displays. Confidence intervals are pointwise 95% t intervals. Each box spans the 25th–75th percentiles with a median line and whiskers to observations within 1.5 interquartile ranges. Scatter points are individual seeds and diamonds are means.

## Model revision

The closure position/velocity reset was replaced with bounded braking and an upstream maneuver reserve. A missing-neighbor execution reference now uses desired speed. Hold release regenerates a current-state-matched quintic. QP residuals are checked, with interior-point repair and zero-increment fallback when repair fails. The distance denominator includes the full interval from the initial state. All dependent experiments were rerun.

The principal results assume that a final safety layer can override nominal HDV acceleration. CAV-only filtering, delayed/noisy information, infeasible barriers and incomplete queue service are retained in the records. No continuous-time safety or finite-time completion guarantee is claimed. The stopping rule, dynamics, sensing and solver definitions are described in the manuscript.

The journal S1 File and the release archive are identical. Code is MIT-licensed. Data, figures and documentation are CC BY 4.0.

The archive retains every seed-level outcome and diagnostic. Time curves are retained for the queue/service comparisons, and full trajectories for the three representative main runs and both hold tests. Unused trajectory arrays and duplicate final images are omitted to keep the submission file compact. The runner regenerates the complete records when rerun.
