# Source code and data for state-triggered cooperative mandatory merging

Version 2.0.0, 4 October 2026. This archive accompanies *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow* by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

The identical `S1_Source_Code_and_Data.zip` is supplied as S1 File and as an asset of the [versioned public release](https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v2.0.0). File-level checksums are in `SHA256SUMS.txt`. The repository retains the original release history as well as browsable source code. Its entire working tree is not an identical copy of this archive.

## Contents and evidence

| Folder | Contents |
| --- | --- |
| `PLOS_ONE_Mixed_Traffic_Merging_Data/data/` | Original seed-level records (1500 main runs and 80 safety-ablation runs), summaries and representative trajectories |
| `analysis_scripts/code/` | Core simulator, parameter definitions and instrumentation |
| `analysis_scripts/analysis/` | 380 trigger/configuration and threshold runs, 300 original-grid paired statistical comparisons, timing records and the instrumented representative run |
| `round2_analysis/code/` | Simulator extensions for communication, sensing, driver heterogeneity, transfer and component reversions |
| `round2_analysis/analysis/` | 1020 robustness/transfer runs, 120 component reversions, 306 paired ECO-minus-baseline contrasts, per-run MAT records and 51 representative seed-0 trajectories |
| `figure_reproduction/` | Final plotting scripts and inputs for Figs 1 and 3–13, and the retained original Fig 2 |
| `validation/` | Reproduction check and execution logs |

The revision adds 1520 controlled runs (380 + 120 + 1020). Timing is a separate set of 27 measured simulations with 900 steps each, following nine warm-up simulations. The total of 3100 main/ablation/revision records excludes timing and validation reruns. Run counts are not counts of independent traffic observations.

## Requirements

The simulation records were generated with MATLAB R2023b. The full sweep scripts use Parallel Computing Toolbox. Statistical scripts use Statistics and Machine Learning Toolbox. The core projected-FISTA solver does not require Optimization Toolbox. Python analyses and final figures require NumPy, pandas, SciPy and Matplotlib (see `requirements.txt`). Install these in your own Python environment. No bundled third-party packages are included.

## Quick verification

Extract the complete archive and set the MATLAB current folder to its root:

```matlab
run('analysis_scripts/quick_reproduction_check.m')
```

This recomputes one paired seed for COOP, PASSIVE and ECO and checks continuous metrics against the archived CSV precision, with exact completion and violation-count checks. The 4 October 2026 check passed. The legacy COOP intervention counter is 20341 on rerun versus 20340 in the original CSV, because it counts arbitrarily small floating-point corrections. This does not change the checked performance or violation results. The discrepancy is retained in `validation/quick_check_20261004.log` and the diagnostics CSV.

## Reproduce final figures and statistics

Run from the archive root:

```text
python figure_reproduction/replot_legacy.py
python figure_reproduction/replot_fig3.py
python figure_reproduction/replot_original.py
python figure_reproduction/replot.py
```

The scripts write to `figure_reproduction/figures/`. They reproduce Figs 1, 3–13 with the final panel labels and layout. Fig 2 is the retained original illustration, supplied in that output folder. The numerical inputs correspond to the archived experiment records. Historical plotting code in `PLOS_ONE_Mixed_Traffic_Merging_Data/scripts/` and `round2_analysis/analyze_round2.py` retains earlier graphical layouts and should not be used for the final figure appearance.

```matlab
run('analysis_scripts/statistics_revision.m')
```

```text
python analysis_scripts/summarize_revision.py
python round2_analysis/analyze_round2.py
```

These commands rebuild statistical summaries from saved records. They do not rerun the simulation. Run them in a working copy if the deposited results are to remain byte-identical.

## Rerun simulation experiments

Use separate fresh MATLAB sessions for each group to avoid function-name collisions between the two `code/` directories. Work on a copy of the archive.

```matlab
run('analysis_scripts/reproduce_original_grid.m')
```

This writes the original 1500-run grid to `analysis_scripts/reproduced_main/`. To regenerate the 80 safety-ablation runs and original representative trajectories:

```matlab
addpath('analysis_scripts/code')
run('analysis_scripts/code/run_eco_safety_and_typical.m')
```

For the revision sweeps:

```matlab
run('analysis_scripts/run_revision.m')
run('round2_analysis/run_robustness.m')
run('round2_analysis/run_components.m')
```

Run the first line in a separate session from the last two. The scripts resume completed per-run MAT checkpoints. To force a fresh sweep, first move the corresponding `job_*.mat`, `robust_*.mat` or `component_*.mat` checkpoint files out of the working copy's `analysis` folder. Retain the deposited archive unchanged. Representative robustness trajectories are saved for seed 0 in each of 17 conditions and three strategies. CPU timings depend on hardware and workload and are not expected to reproduce exactly.

## Interpreting the records

Seeds 0–19 are paired across strategies. Main runs use five initial target-lane densities and five nominal CAV penetrations. Detailed variable definitions and original strategy codes are in `PLOS_ONE_Mixed_Traffic_Merging_Data/DATA_DICTIONARY.md`. **Strategy codes differ by file:** original `joint_raw.csv` uses 1=COOP and 2=PASSIVE, while ECO is in a separate file; robustness and runtime records use 1=COOP, 2=ECO and 3=PASSIVE. Read the named columns rather than assuming a common numeric mapping.

Robustness settings are in `round2_analysis/analysis/experiment_settings.csv`. `registered_jobs.csv` and `component_registered_jobs.csv` map every checkpoint to its condition and seed. Minimum net gap is a sampled longitudinal measure. A negative value denotes simulated overlap, and a count of negative-gap samples is not a count of distinct crashes. Completed merges alone do not establish safety under arbitrary conditions. The `hdv_unfiltered` condition tests removal of the modeled HDV safety override. Communication tests preserve exact discrete lane/role labels, and all-layer sensing noise is explicitly distinguished from noise restricted to nominal control.

The deposit includes adverse outcomes and the lower original-grid fuel intensity of PASSIVE. It contains no road or hardware-in-the-loop measurements and no reproduced external-method benchmark. The fuel model is a simplified common powertrain model. Test parameters and outcomes should not be interpreted as a deployment certification.

## License and citation

Author-generated code is available under the MIT License. Data, figures and documentation are available under CC BY 4.0. Existing notices in the original data subdirectory are retained. See `LICENSE.md` and `CITATION.cff`. Mingyuan Bai contributed manuscript review and editing; the author list does not attribute software development to him.
