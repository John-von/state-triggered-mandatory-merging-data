# Source code and data for cooperative mandatory merging

Version 2.0.1, 7 October 2026. S1 File for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow*.

The identical archive is available at https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v2.0.1.

## Contents

| Folder | Contents |
| --- | --- |
| `PLOS_ONE_Mixed_Traffic_Merging_Data/data/` | 1500 main runs, 80 safety-ablation runs, summaries and trajectories |
| `analysis_scripts/` | Core MATLAB simulator, 380 activation/threshold runs, 300 paired comparisons and 27 timing runs |
| `round2_analysis/` | Extended simulator, 1020 robustness/transfer runs, 120 component reversions and 306 paired contrasts |
| `figure_reproduction/` | Scripts for the final figures and the original Figure 2 |

The 3100 experiment records exclude timing and verification reruns. Seeds 0-19 are paired across strategies. Timing records cover 24300 measured steps after warm-up. Variable definitions are in `PLOS_ONE_Mixed_Traffic_Merging_Data/DATA_DICTIONARY.md` and the CSV headers.

## Requirements

MATLAB R2023b was used for simulation. Sweep scripts require Parallel Computing Toolbox; statistical scripts require Statistics and Machine Learning Toolbox. The projected-FISTA solver does not require Optimization Toolbox. Python plotting and analysis require the packages in `requirements.txt`.

## Reproduce figures and summaries

Run from the extracted archive root:

```text
python figure_reproduction/reproduce_figures.py
python analysis_scripts/summarize_revision.py
python round2_analysis/analyze_round2.py
```

Figures are written to `figure_reproduction/figures/`. The analysis scripts rebuild summaries from saved records. For the main-grid statistical tests, run in MATLAB:

```matlab
run('analysis_scripts/statistics_revision.m')
```

## Rerun simulations

Set the MATLAB current folder to the archive root. Use a working copy and separate MATLAB sessions for the two simulator folders, which contain functions with shared names.

| Experiment | MATLAB command |
| --- | --- |
| Three-strategy verification | `run('analysis_scripts/quick_reproduction_check.m')` |
| Main grid | `run('analysis_scripts/reproduce_original_grid.m')` |
| Safety ablation and representative trajectories | `addpath('analysis_scripts/code'); run('analysis_scripts/code/run_eco_safety_and_typical.m')` |
| Activation, thresholds and timing | `run('analysis_scripts/run_revision.m')` |
| Robustness and transfer | `run('round2_analysis/run_robustness.m')` |
| Component reversions | `run('round2_analysis/run_components.m')` |

Sweeps resume saved checkpoints. To recompute a sweep, move its `job_*.mat`, `robust_*.mat` or `component_*.mat` files out of the working copy. Timing varies with hardware and workload. The verification script records a known one-count difference in the original COOP intervention counter, which uses a strict floating-point comparison. Performance metrics agree within the archived CSV precision.

## Record conventions

Original main-grid codes are 1=COOP, 2=PASSIVE and 3=ECO. Robustness and timing codes are 1=COOP, 2=ECO and 3=PASSIVE. Use the file-specific mapping. Experiment settings and checkpoint indices are listed in `round2_analysis/analysis/experiment_settings.csv`, `registered_jobs.csv` and `component_registered_jobs.csv`.

Negative net gaps represent simulated overlap; negative-gap samples are not distinct crashes. Communication tests preserve exact discrete lane/role labels and distinguish control-only noise from noise affecting the safety layer. Raw records include unsuccessful runs. The fuel model uses a common simplified powertrain.

## License

Author-generated code is MIT-licensed. Data, figures and documentation are CC BY 4.0. See `LICENSE.md` and `CITATION.cff`. `SHA256SUMS.txt` contains file checksums.
