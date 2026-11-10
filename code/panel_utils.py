"""Joint region/year OLS with region-clustered CR1 inference.

Rows are (region, year, outcome, regressor). Joint projection is required for
unbalanced panels; one pass of year-then-region demeaning is not equivalent.
"""
import numpy as np
from scipy.stats import t


def fit_twfe(panel):
    regions = sorted({row[0] for row in panel})
    years = sorted({row[1] for row in panel})
    groups = np.array([regions.index(row[0]) for row in panel])
    y = np.array([row[2] for row in panel], dtype=float)
    x = np.array([row[3] for row in panel], dtype=float)
    effects = np.array([[1] + [int(r == rr) for rr in regions[1:]]
                        + [int(year == yy) for yy in years[1:]]
                        for r, year, _, _ in panel], dtype=float)
    design = np.column_stack([x, effects])
    n, k = design.shape
    g = len(regions)
    if g < 2 or n <= k or np.linalg.matrix_rank(design) != k:
        raise ValueError('Insufficient observations or unidentified fixed-effect model')
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ beta
    bread = np.linalg.inv(design.T @ design)
    meat = np.zeros((k, k))
    for group in range(g):
        mask = groups == group
        score = design[mask].T @ residual[mask]
        meat += np.outer(score, score)
    covariance = bread @ meat @ bread * (g / (g - 1)) * ((n - 1) / (n - k))
    se = float(np.sqrt(covariance[0, 0]))
    critical = float(t.ppf(0.975, g - 1))
    xr = x - effects @ np.linalg.lstsq(effects, x, rcond=None)[0]
    yr = y - effects @ np.linalg.lstsq(effects, y, rcond=None)[0]
    return dict(n=n, regions=g, years=years, parameters=k,
                slope=float(beta[0]), cluster_se=se,
                t_stat=float(beta[0] / se), df=g - 1,
                ci95=[float(beta[0] - critical * se), float(beta[0] + critical * se)],
                pooled_r=float(np.corrcoef(x, y)[0, 1]),
                exact_fe_r=float(np.corrcoef(xr, yr)[0, 1]),
                method='Joint OLS with region and year indicators; region-clustered CR1; Student t(G-1)')
