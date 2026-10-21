# State-triggered cooperative mandatory merging

Source code and data for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow*, by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

Download [S1 File, version 3.0.1](https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v3.0.1). The release asset `S1_Source_Code_and_Data.zip` is identical to the manuscript's S1 File. `S1_SHA256SUMS.txt` verifies the archive.

Version 3.0.1 aligns the figure script with Figures 1–10 in the consolidated manuscript. It removes redundant figure exports without changing simulation code, experimental records, statistical analyses or numerical results from version 3.0.0. Necessary methodological details are now included in the main article.

The archive contains 3874 simulation records, two deterministic hold-recovery tests, representative trajectories, timing measurements, statistical analyses and scripts for Figures 1–10. All seed-level outcomes and diagnostics are retained. See the [reproduction guide](revision_v3_0_1/README.md) and [data dictionary](revision_v3_0_1/DATA_DICTIONARY.md). Browse the [MATLAB implementation](revision_v3_0_1/code/), [processed data](revision_v3_0_1/processed/), [analysis script](revision_v3_0_1/analyze_corrected.py) and [figure script](revision_v3_0_1/plot_corrected.py). Binary MAT records are included in the release archive.

The corrected simulator first released in version 3.0.0 uses bounded closure stopping without resetting vehicle positions or speeds, a missing-neighbor speed reference, current-state-matched lateral restart, solver feasibility checks and fallback, and full-horizon distance normalization. Its rerun numerical results supersede earlier versions.

The principal simulations permit safety intervention over every vehicle, including nominal human-driven vehicles. The records retain CAV-only filtering failures, incomplete queue service, communication disturbances and infeasible constraints. The experiments do not establish continuous-time safety or guaranteed merge completion.

Earlier releases, `revision_v3/`, `revision_v2/`, and the original top-level data and scripts remain available for version history. Use version 3.0.1 for the consolidated revised manuscript.

Code is MIT-licensed. Data, figures and documentation are CC BY 4.0. See [LICENSE.md](LICENSE.md) and [CITATION.cff](CITATION.cff).
