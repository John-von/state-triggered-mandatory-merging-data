# Data Dictionary

## Codes

| Field | Value | Meaning |
|---|---:|---|
| `mode` | 1 | COOP: continuous safety-priority cooperative gap creation |
| `mode` | 2 | PASSIVE: passive merging without active target-lane regulation |
| `mode` | 3 | ECO: state-triggered cooperative gap creation |
| `variant` | 1 | Full ECO safeguards |
| `variant` | 2 | Relative-speed prediction disabled |
| `variant` | 3 | Barrier-based safety filter disabled |
| `variant` | 4 | All three tested safety layers disabled |

## Raw experiment fields

These fields occur in `joint_raw.csv` and `eco_joint_raw.csv`.

| Field | Unit | Description |
|---|---|---|
| `k1` | veh/km | Initial target-lane density |
| `sp1` | m | Initial target-lane vehicle spacing |
| `penetration` | proportion | Nominal CAV penetration setting, from 0 to 1 |
| `mode` | code | Strategy code defined above |
| `seed` | integer | Paired random seed, from 0 to 19 |
| `comp` | % | Mandatory-merge completion rate |
| `fuelL` | L | Total simulated fuel consumption |
| `perveh_mL` | mL/vehicle | Fuel consumption per vehicle |
| `perkm_L100` | L/100 km | Distance-normalized fuel consumption |
| `co2_gkm` | g/km | Carbon dioxide equivalent calculated with the fixed factor used in the study |
| `sigma_v` | m/s | Speed standard deviation |
| `a_rms` | m/s^2 | Acceleration root mean square |
| `stop_veh_s` | vehicle-s | Aggregate stopped-vehicle time |
| `min_gap` | m | Minimum observed net longitudinal gap |
| `n_hard` | count | Hard-braking event count |
| `n_abort` | count | Aborted maneuver count |
| `final_gap_violation` | samples | Spacing-violation samples after state advancement and protection |
| `pre_gap_violation` | samples | Spacing-violation samples before the final protection stage |
| `n_gap_correction` | count | Minimum-gap correction count |
| `n_safety` | count | Barrier-filter intervention count |
| `v_mean` | m/s | Mean network speed |
| `n_merged` | vehicles | Number of completed mandatory merges |

`eco_safety_ablation_raw.csv` uses the same performance and safety measures, with `variant` replacing density and strategy fields.

## Summary fields

Suffixes have the following meanings:

| Suffix | Meaning |
|---|---|
| `_mean` | Arithmetic mean across the indicated runs |
| `_min` | Minimum across the indicated runs |
| `_sum` | Sum across the indicated runs |
| `_ci95` | Half-width of the two-sided 95% confidence interval |
| `_pct` | Relative difference expressed as a percentage |
| `_pp` | Absolute difference in percentage points |

In `eco_vs_coop_paired_summary.csv` and `eco_vs_passive_paired_summary.csv`, positive saving, reduction, and gain values indicate a favorable ECO effect. `stop_reduction_veh_s` is an absolute paired reduction in vehicle-seconds. `speed_gain_pct` is a relative gain in mean speed.

## Representative trajectories

`eco_typical_trajectory.mat` contains the structures `coopTypical`, `ecoTypical`, and `passiveTypical`, together with the parameter structure `P` and the nominal penetration setting. Each strategy structure contains 900 time steps for 38 vehicles. The main matrices are:

| Matrix | Description |
|---|---|
| `recX` | Absolute longitudinal coordinates |
| `recV` | Longitudinal speeds |
| `recA` | Longitudinal accelerations |
| `recLane` | Lane-state records |

`representative_trajectories.csv` provides the principal trajectory matrices in long format. Its fields are `strategy`, `time_s`, `vehicle_id`, `position_m`, `speed_mps`, `acceleration_mps2`, and `lane_state`.
