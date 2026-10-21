# Experiment and data dictionary

The eight job columns are family, queue scale, mode ID, random seed, target-lane center spacing (m), nominal target-lane CAV penetration, variant and gate. Modes 1/2/3 are COOP/ECO/PASSIVE. Queue scales 1/2/3 contain 38/57/76 vehicles, of which 12/18/24 begin in the closing lane. All closing-lane vehicles are controlled.

Families:

1. Main density–penetration grid, 1500 runs.
2. Additional 57/76-vehicle queue runs, 120. The 38-vehicle comparison reuses main records.
3. Equal-budget training, 120 runs using seeds 100–104. Gate 0 is continuously enabled, gate 1 is state-triggered.
4. Matched continuous-ECO configuration, 500 runs. Gated counterparts reuse main ECO records.
5. Robustness/transfer conditions 2–17, 960 runs. Condition 1 reuses the main ideal condition.
6. Safety ablations 2–4, 60 runs. Variant 1 reuses the full main ECO condition. Variant 2 disables relative-speed admission, 3 disables barrier filtering, 4 disables prediction, hold and barrier filtering. The closure guard remains active.
7. Six grouped component reversions, 120 runs: ramp/clock, scheduling, weights/gains, acceleration limits, admission and gap buffer.
8. Threshold sensitivity, 260 runs. Values 130/140/145 encode density thresholds 30/40/45 veh/km. Values 1250/1550 encode activation distances 250/550 m. Values 2015/2040 encode critical distances 15/40 m.
9. COOP settings with gating, 60 runs. Other factorial cells reuse the main and matched records.
10. Refined dynamic integration, 54 runs. Variant 10/20 denotes substeps per 0.1 s control interval.
11. Independent evaluation of selected tuning candidates, 120 runs using seeds 0–19.

Robustness conditions 2/3/4 use broadcast delays 0.1/0.3/0.5 s; 5/6/7 use independent packet loss 5%/10%/20%; 8 is control-only noise; 9 is all-layer noise; 10 combines 0.3 s delay, 10% loss and control noise; 11/12 use ±20%/±40% IDM variation; 13 disables HDV filtering at ±20%; 14/15 move the closure to 650/850 m; 16/17 scale speeds to 80%/120%.

`processed/seed_metrics.csv` contains one row per simulation run. `comp_rate` is completion in percent. `fuel_L` is whole-fleet fuel in litres and `fuel_L100` is litres per 100 vehicle-km. `sigma_v` is pooled speed SD. `a_rms` uses the acceleration command, whereas `actual_acceleration_rms` uses finite differences of body longitudinal speed. Main-paper acceleration and jerk figures use realized values. `stopped_vehicle_s` counts vehicle samples below 1 m/s times 0.1 s. `delay_vehicle_s` integrates positive fractional loss from each vehicle's initial desired speed.

`min_gap` is the minimum relevant net gap over sampled states. `final_gap_violation_steps` counts vehicle–time overlap samples, not distinct collisions. `standstill_violations` counts gaps below 2 m, while `headway_violations` uses the operational 1.0 s speed-dependent headway. The barrier uses 1.3 s and a strategy buffer. `filter_infeasible` counts vehicle–time requests below emergency braking authority; `filter_infeasible_steps` counts control steps containing any such request. Closure diagnostics are separate. Legacy field `closure_clamps` now counts preparation-stage crossing observations; it performs no state reset.

`qp_*` fields record calls, FISTA iterations/limits, raw residual failures, successful repair and zero-increment fallback. The maximum returned residual includes fallback vectors, which are not certified feasible. `dense_*` fields apply only to runs with intermediate sampling; infinity for an unmeasured minimum means not evaluated, not infinite clearance.

`completion_time` in MAT records is NaN for an unfinished vehicle. `censored_completion_s` assigns the 90 s horizon to unfinished vehicles for descriptive restricted-time accounting. `common_service.csv` evaluates each policy at its own time of reaching the smallest final completion count across policies for a seed. At zero common service, time/fuel/delay are undefined (NaN).

`paired_contrasts.csv` reports ECO minus the comparator. Absolute means and pointwise t intervals retain physical units. Relative improvements reverse signs for cost outcomes, while mean-speed gains are positive increases. Holm correction is separate for each family, outcome and baseline. `dz` is the paired mean difference divided by its sample SD. The exact signed-rank calculation retains tied ranks. Matched-grid contrasts have their own 25-condition correction family.

Full trajectories store state samples after each 0.1 s step. Initial state is stored separately in `R.initial`. `restart_records` columns are time, vehicle ID, current lateral position/velocity/acceleration and regenerated reference position/velocity/acceleration. Kinematic lateral motion is prescribed, not a validation of steering/yaw dynamics. Outside the queue/service subset, `residual_queue` stores its final value and unused long time curves are omitted. All completion times, scalar outcomes and diagnostics remain available.
