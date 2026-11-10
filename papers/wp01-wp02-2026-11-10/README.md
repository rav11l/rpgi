# WP-2026-01 and WP-2026-02 — RPGI v0.9.0

Original manuscript and journal-submission date: **11 September 2026**.
Website revision: **10 November 2026**. Repository archive: **RPGI v0.9.0**, DOI [10.5281/zenodo.24115487](https://doi.org/10.5281/zenodo.24115487).
This dataset DOI identifies the replication archive, not a journal article or journal acceptance.

Published RU/EN pages: https://digitaleconomylab.ru/wp-2026-01 and https://digitaleconomylab.ru/wp-2026-02.

The ZIP contains frozen source workbooks, the original land-audit log/matrix, revised matrix,
and the verification program. Extract it, install `openpyxl`, `numpy` and `scipy`, and run
`python verify_numbers.py research-sources`. No network access is needed for the calculation.
WP-01 is fixed to the August 2026 lending snapshot; the root repository contains a different
September snapshot. The original workbooks are preserved byte for byte.
The WP-04 model was checked against its stored output, not re-estimated.

Joint region/year fixed effects with region-clustered CR1 inference replace one-pass demeaning.
For WP-01: b = -0.027978, SE = 0.184637, 95% CI [-0.396046, 0.340090].
This interval does not establish a zero causal effect. Index ratios are not price-premium levels.

The revised land matrix recodes September observations: 22 full, 16 partial, 29 not found,
3 unchecked (70 cells). It is not a new November census of city records. Three Saint Petersburg
cells were corrected. Original evidence is preserved.

Text and derived data: CC BY 4.0; source data retain their original terms. Code: MIT.
