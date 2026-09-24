# -*- coding: utf-8 -*-
"""Оценки ∂P/∂s по квартальной панели центров субъектов."""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np, sys, json
from linearmodels.panel import PanelOLS
import statsmodels.formula.api as smf
from build_panel import build

def fe(d, y, xs, trend=False, weights=None):
    x = d.set_index(["region", "t"])
    exog = x[xs].copy()
    if trend:
        # регион-специфические линейные тренды
        for r in x.index.get_level_values(0).unique():
            exog["tr_" + r] = (x.index.get_level_values(0) == r) * (x.index.get_level_values(1) - 8084)
    m = PanelOLS(x[y], exog, entity_effects=True, time_effects=True, drop_absorbed=True,
                 weights=None if weights is None else x[weights])
    r = m.fit(cov_type="clustered", cluster_entity=True)
    return r

def row(r, v):
    return dict(b=float(r.params[v]), se=float(r.std_errors[v]),
                lo=float(r.conf_int().loc[v, "lower"]), hi=float(r.conf_int().loc[v, "upper"]),
                n=int(r.nobs))

def main(spread=3.5, lag=1, H=None, verbose=True):
    d = build(spread=spread, lag=lag, H=H)
    d = d.sort_values(["region", "t"])
    d["pv_l1"] = d.groupby("region").pv.shift(1)
    out = {}
    for y in ["lp1", "lp2", "lgap"]:
        out[(y, "pv")] = row(fe(d, y, ["pv"]), "pv")
        dd = d.dropna(subset=["pv_l1"])
        out[(y, "pv_l1")] = row(fe(dd, y, ["pv_l1"]), "pv_l1")
        out[(y, "pv+trend")] = row(fe(d, y, ["pv"], trend=True), "pv")
    if verbose:
        for k, v in out.items():
            print("%-5s %-9s b=%7.3f se=%6.3f [%6.3f, %6.3f] n=%d" % (k[0], k[1], v["b"], v["se"], v["lo"], v["hi"], v["n"]))
    return d, out

if __name__ == "__main__":
    main()
