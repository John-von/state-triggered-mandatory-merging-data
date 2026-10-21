# State-triggered cooperative mandatory merging

Source code and data for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow*, by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

Version 3.0.2 accompanies Figures 1–14 in the revised manuscript. All figure groups are retained with two, four or six panels. Redundant panels have been removed, and Figure 1 includes the completion curve from the same representative records. The corrected simulator, experimental records and statistical results remain unchanged from version 3.0.0. Earlier releases remain available for version history.

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

## Model revision

The closure position/velocity reset was replaced with bounded braking and an upstream maneuver reserve. A missing-neighbor execution reference now uses desired speed. Hold release regenerates a current-state-matched quintic. QP residuals are checked, with interior-point repair and zero-increment fallback when repair fails. The distance denominator includes the full interval from the initial state. All dependent experiments were rerun.

The principal results assume that a final safety layer can override nominal HDV acceleration. CAV-only filtering, delayed/noisy information, infeasible barriers and incomplete queue service are retained in the records. No continuous-time safety or finite-time completion guarantee is claimed. The stopping rule, dynamics, sensing, solver and timing definitions are described in the manuscript.

The journal S1 File and the release archive are identical. Code is MIT-licensed. Data, figures and documentation are CC BY 4.0.

The archive retains every seed-level outcome and diagnostic. Time curves are retained for the queue/service comparisons, and full trajectories for the three representative main runs and both hold tests. Unused trajectory arrays and duplicate final images are omitted to keep the submission file compact. The runner regenerates the complete records when rerun.
