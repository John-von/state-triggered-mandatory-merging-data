# State-triggered cooperative mandatory merging

Source code and data for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow*, by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

Download [S1 File, version 3.0.0](https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v3.0.0). The release asset `S1_Source_Code_and_Data.zip` is identical to the manuscript's S1 File. `S1_SHA256SUMS.txt` verifies the archive.

Version 3.0.0 contains the corrected simulator and rerun results. Closure stopping now uses bounded braking without resetting vehicle positions or speeds. Other corrections cover the missing-neighbor speed reference, current-state-matched lateral restart, solver feasibility checks and fallback, and full-horizon distance normalization. These corrected numerical results supersede earlier releases.

The archive contains 3874 simulation records, two deterministic hold-recovery tests, representative trajectories, timing measurements, statistical analyses and scripts for Figures 1–14. All seed-level outcomes and diagnostics are retained. See the [reproduction guide](revision_v3/README.md) and [data dictionary](revision_v3/DATA_DICTIONARY.md). Browse the [MATLAB implementation](revision_v3/code/), [processed data](revision_v3/processed/), [analysis script](revision_v3/analyze_corrected.py) and [figure script](revision_v3/plot_corrected.py). Binary MAT records are included in the release archive.

The principal simulations permit safety intervention over every vehicle, including nominal human-driven vehicles. The records also retain CAV-only filtering failures, incomplete queue service, communication disturbances and infeasible constraints. The experiments do not establish continuous-time safety or guaranteed merge completion.

Earlier releases, `revision_v2/`, and the original top-level data and scripts remain available for version history. Use version 3.0.0 for the current revised manuscript.

Code is MIT-licensed. Data, figures and documentation are CC BY 4.0. See [LICENSE.md](LICENSE.md) and [CITATION.cff](CITATION.cff).
