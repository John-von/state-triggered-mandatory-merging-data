# State-triggered cooperative mandatory merging

Data and source code for *State-triggered cooperative mandatory merging at temporary lane closures in mixed traffic flow* by Jie Yu, Tao Chen, Qiang Wen and Mingyuan Bai.

## Complete reproducibility release

Download [S1 Source Code and Data, version 2.0.0](https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v2.0.0). The release asset `S1_Source_Code_and_Data.zip` is identical to the manuscript's S1 File. Its companion `S1_SHA256SUMS.txt` verifies the archive, and the archive contains file-level checksums.

The package includes the MATLAB simulation and control implementation, 1500 original main runs, 80 safety-ablation runs, 1520 revision runs, paired statistical analyses, per-step computational profiling, representative trajectories and the final figure-reproduction scripts. It preserves adverse outcomes and the limitations of the modeled control and sensing assumptions.

The [reproduction guide](revision_v2/README.md) explains requirements, scripts, strategy-code mappings, run counts and interpretation. Browse the [original/instrumented simulator](revision_v2/analysis_scripts/code/), [robustness and component extensions](revision_v2/round2_analysis/code/) and [final plotting code](revision_v2/figure_reproduction/). Download the full release for MAT trajectories and other binary records. The browsable `revision_v2/` tree contains the source code, tabular records, summaries and documentation.

Version 2.0.0 was checked with a three-strategy MATLAB reproduction run, complete record/seed checks and verification that all final figure PNGs match the manuscript figure archive. A one-count difference in the legacy COOP safety-intervention counter is documented in the guide; the checked performance and violation results agree.

## Earlier release

The [original v1.0.0 data release](https://github.com/John-von/state-triggered-mandatory-merging-data/releases/tag/v1.0.0) and original top-level `data/`, `figures/` and `scripts/` remain available for provenance. They do not contain the complete revised simulator or final figure layout. Use version 2.0.0 for the revised manuscript.

## License and citation

Author-generated source code: MIT License. Data, figures and documentation: CC BY 4.0. See [LICENSE.md](LICENSE.md) and [CITATION.cff](CITATION.cff). Existing notices for the original data release are retained in that release and in the S1 archive. Mingyuan Bai contributed manuscript review and editing.
