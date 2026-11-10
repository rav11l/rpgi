"""Independent FE/CR1 check. Run: pip install statsmodels; python validation/check_panel.py"""
from pathlib import Path
import sys, io, contextlib, runpy
import numpy as np
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
from panel_utils import fit_twfe


def check(panel):
    regions = sorted({r[0] for r in panel})
    years = sorted({r[1] for r in panel})
    x = np.array([[s, 1] + [int(r == rr) for rr in regions[1:]]
                  + [int(y == yy) for yy in years[1:]] for r, y, g, s in panel], float)
    y = np.array([r[2] for r in panel])
    groups = np.array([regions.index(r[0]) for r in panel])
    reference = sm.OLS(y, x).fit(cov_type='cluster',
        cov_kwds={'groups': groups, 'use_correction': True}, use_t=True)
    actual = fit_twfe(panel)
    np.testing.assert_allclose(actual['slope'], reference.params[0], atol=1e-10)
    np.testing.assert_allclose(actual['cluster_se'], reference.bse[0], rtol=1e-8)
    np.testing.assert_allclose(actual['ci95'], reference.conf_int()[0], rtol=1e-8)


rng = np.random.default_rng(716)
panel = []
for r in range(12):
    for y in range(7):
        if (r * 3 + y) % 11 == 0:
            continue
        x = rng.normal() + r * .15 + y * .2
        panel.append((str(r), y, .7 * x + r * .5 - y * .2 + rng.normal(scale=.3), x))
check(panel)
for script in ['fe_panel.py', 'counts_check.py']:
    with contextlib.redirect_stdout(io.StringIO()):
        result = runpy.run_path(str(ROOT / 'code' / script))
    check(result['panel'])
print('PASS: synthetic unbalanced panel and both actual panels match statsmodels OLS/cluster CR1')
