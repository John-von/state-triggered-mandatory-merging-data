# Original data component

This folder preserves the original v1.0.0 data, metadata and plotting script. For the complete code, revision experiments and final figure layout, use the parent archive README.

# Data for State-Triggered Cooperative Mandatory Merging

This repository contains the data underlying the findings reported in the manuscript:

> State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow

The study compares continuous safety-priority cooperation (COOP), state-triggered cooperation (ECO), and passive merging (PASSIVE). The main experiment covers five target-lane densities, five nominal connected and automated vehicle (CAV) penetration settings, three strategies, and 20 paired random seeds. It therefore contains 1,500 simulation runs. A separate safety ablation contains 80 runs.

Repository: https://github.com/John-von/state-triggered-mandatory-merging-data

## Repository contents

- `data/raw/joint_raw.csv`: 1,000 COOP and PASSIVE records.
- `data/raw/eco_joint_raw.csv`: 500 ECO records.
- `data/raw/eco_safety_ablation_raw.csv`: 80 safety-ablation records.
- `data/summary/`: cell-level summaries and paired effects with 95% confidence intervals.
- `data/trajectories/eco_typical_trajectory.mat`: MATLAB structures for the representative trajectories used in Figures 1 and 2.
- `data/trajectories/representative_trajectories.csv`: the same longitudinal position, speed, acceleration, and lane-state records in an open tabular format.
- `figures/`: the eight figure files used in the manuscript.
- `scripts/reproduce_figures.m`: MATLAB script that rebuilds the eight analysis figures from the archived data.
- `DATA_DICTIONARY.md`: definitions, units, strategy codes, and ablation codes.

The repository is a data release. It does not include the core traffic-simulation and control-algorithm implementation. The shared raw and summary data are sufficient to verify the numerical findings, tables, confidence intervals, and figures reported in the manuscript.

## Experimental design

Target-lane densities are 25.0, 29.4, 35.7, 41.7, and 50.0 veh/km. Nominal CAV penetration settings are 0%, 25%, 50%, 75%, and 100%. Random seeds are fixed at 0-19 and are paired across strategies.

The target lane contains 26 vehicles. Because the number of controllable vehicles is an integer, the nominal penetration settings correspond to realized rates of 0/26, 7/26, 13/26, 20/26, and 26/26.

## Reproducing the figures

MATLAB R2021a or later is recommended. The archived results were produced and checked with MATLAB R2023b. The Statistics and Machine Learning Toolbox is required for the Student-t confidence intervals.

From the repository root, run:

```matlab
run('scripts/reproduce_figures.m')
```

The script writes eight files to `reproduced_figures/`. It reads only the archived files in `data/` and does not rerun the traffic simulation.

## Numerical checks

- All 500 ECO runs complete every mandatory merge without maneuver-stage spacing violations. The minimum observed net gap is 2.091 m.
- Across the 20 nonzero-penetration operating cells, ECO reduces fuel consumption per 100 km by 0.96%-6.91% relative to COOP and increases mean speed by 0.39%-5.39%.
- Relative to PASSIVE, ECO uses 0.04%-4.99% more fuel per 100 km in those cells.
- Removing relative-speed prediction, removing the barrier-based filter, and disabling all three tested safety layers produce 24, 1,789, and 3,447 vehicle-time-step spacing-violation samples, respectively.

## Authors

- Jie Yu, School of Civil Engineering, Hunan City University, Yiyang, China
- Tao Chen, School of Management, Guilin University of Aerospace Technology, Guilin, China
- Qiang Wen, School of Business, Wuyi University, Wuyishan, China

Correspondence: Tao Chen, `ct2025069@guat.edu.cn`.

## License

The data and figures are released under the Creative Commons Attribution 4.0 International License. The figure-reproduction script is released under the MIT License. See `LICENSE.md`.
