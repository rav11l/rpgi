# -*- coding: utf-8 -*-
"""Все числа WP-2026-04, которых нет в results_capitalization.csv и feb2026_output.txt.
Выход: numbers.json и печать. Таблица 1 — table1.csv."""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import warnings; warnings.filterwarnings("ignore")
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf
from build_panel import build, key_monthly, pv_subsidy
from estimate import fe, row

N = {}
DFO = ["Еврейская автономная область", "Приморский край", "Республика Саха (Якутия)", "Хабаровский край",
       "Республика Бурятия", "Сахалинская область", "Забайкальский край", "Амурская область",
       "Камчатский край", "Магаданская область", "Чукотский автономный округ"]
d = build().sort_values(["region", "t"])
d["dfo"] = d.region.isin(DFO)
N["obs"] = len(d); N["centres_total"] = d.centre.nunique()
cq = d.groupby("tq").centre.nunique(); N["centres_q_min"], N["centres_q_max"] = int(cq.min()), int(cq.max())

# Таблица 1
t1 = d.groupby("year").agg(centres=("centre", "nunique"), r_ddu=("r_ddu", "median"), r_b=("r_b", "median"),
                           pv=("pv", "median"), share=("share_ddu", "median"),
                           gap=("lgap", lambda x: float(np.median(np.exp(x) - 1))))
t1.to_csv("table1.csv", float_format="%.4f"); print(t1.round(3))

# медианы pv и ставки по кварталам
m = d.groupby("tq")[["pv", "r_ddu", "r_b"]].median()
for q in ["2021Q1", "2025Q1", "2026Q2"]:
    N["pv_" + q] = round(float(m.loc[q, "pv"]), 3); N["rddu_" + q] = round(float(m.loc[q, "r_ddu"]), 2)

# остаточная вариация pv: настоящая двусторонняя FE-регрессия
def resid(df, v):
    r = smf.ols(f"{v} ~ C(region) + C(t)", df).fit(); return r.resid
e = resid(d, "pv"); N["pv_sd_raw"] = float(d.pv.std()); N["pv_sd_resid"] = float(e.std())
N["dfo_share_obs"] = float(d.dfo.mean()); N["dfo_share_resid_var"] = float((e[d.dfo] ** 2).sum() / (e ** 2).sum())
nd = d[~d.dfo]; N["pv_sd_resid_noDFO"] = float(resid(nd, "pv").std())

# ставка ДДУ в ДФО относительно общероссийской медианы, по годам
x = d.r_ddu - d.groupby("t").r_ddu.transform("median")
N["dfo_rddu_gap_by_year"] = {int(k): round(float(v), 2) for k, v in x[d.dfo].groupby(d.year[d.dfo]).mean().items()}
N["dfo_rddu_gap_mean"] = round(float(x[d.dfo].mean()), 2)
# относительная цена ДФО (медианы) 2021 и 2026
rel = d.groupby(["year", "dfo"]).lp1.median().unstack(); rp = rel[True] - rel[False]
N["dfo_rel_lp1"] = {int(k): round(float(v), 3) for k, v in rp.items()}
relpv = d.groupby(["year", "dfo"]).pv.median().unstack(); N["dfo_rel_pv"] = {int(k): round(float(v), 3) for k, v in (relpv[True] - relpv[False]).items()}
# оценка только на ДФО
rd = d[d.dfo]
N["b_lp1_DFOonly"] = row(fe(rd, "lp1", ["pv"]), "pv")

# дополнительные спецификации
for lab, kw in [("T240", dict(T_fixed=240)), ("ma12", dict(bench="ma12"))]:
    dd = build(**kw).sort_values(["region", "t"])
    N["spec_" + lab] = {y: row(fe(dd, y, ["pv"]), "pv") for y in ["lp1", "lp2", "lgap"]}
    N["spec_" + lab]["pv_2022Q2"] = float(dd.groupby("tq").pv.median()["2022Q2"])

# опережающие значения
g = d.groupby("region").pv
d["pv_f1"], d["pv_f2"], d["pv_l1"] = g.shift(-1), g.shift(-2), g.shift(1)
dl = d.dropna(subset=["pv_f1", "pv_f2", "pv_l1"])
r = fe(dl, "lp1", ["pv_f2", "pv_f1", "pv", "pv_l1"])
N["leads"] = {v: [float(r.params[v]), float(r.std_errors[v])] for v in ["pv_f2", "pv_f1", "pv", "pv_l1"]}
N["leads_n"] = int(r.nobs)
wt = r.wald_test(formula="pv_f2 = 0, pv_f1 = 0"); N["leads_joint_p"] = float(wt.pval)
N["base_on_leads_sample"] = row(fe(dl, "lp1", ["pv"]), "pv")

# дикий кластерный бутстреп (Webb, 6 точек), нулевая гипотеза b = 0
def wcb(df, y, B=1999, seed=1):
    rng = np.random.default_rng(seed)
    Xd = pd.get_dummies(df[["region"]].astype(str), drop_first=True).join(pd.get_dummies(df.t.astype(str), prefix="t", drop_first=True)).astype(float)
    Xd.insert(0, "c", 1.0); F = Xd.values
    Q, _ = np.linalg.qr(F)
    def res(v): return v - Q @ (Q.T @ v)
    yr, xr = res(df[y].values), res(df.pv.values)
    cl = pd.factorize(df.region)[0]; G = cl.max() + 1
    def tstat(yv):
        b = (xr @ yv) / (xr @ xr); u = yv - b * xr
        s = np.bincount(cl, weights=xr * u, minlength=G)
        v = (s ** 2).sum() / (xr @ xr) ** 2 * G / (G - 1)
        return b / np.sqrt(v)
    t0 = tstat(yr)
    w6 = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    ts = np.array([tstat(yr * w6[rng.integers(0, 6, G)][cl]) for _ in range(B)])
    return float(t0), float((np.abs(ts) >= abs(t0)).mean())
N["wcb"] = {y: wcb(d, y) for y in ["lp1", "lp2", "lgap"]}
N["wcb_trend_note"] = "только база"

# национальный ряд pv (строка РФ, взвешено по объёму), 2020 и 2025
c = pd.read_csv("cbr_monthly.csv"); rf = c[c.region == "РОССИЙСКАЯ ФЕДЕРАЦИЯ"].copy()
km = key_monthly(); rf["date"] = pd.to_datetime(dict(year=rf.year, month=rf.month, day=1))
rf["r_b"] = rf.date.map(km.shift(1)) + 3.5
rf["pv"] = pv_subsidy(rf.r_ddu, rf.r_b, rf.t_ddu, None)
rf = rf.dropna(subset=["pv"])
npv = rf.groupby("year").apply(lambda g: np.average(g.pv, weights=g.vol_ddu))
N["nat_pv"] = {int(k): round(float(v), 3) for k, v in npv.items()}
dpv = npv[2025] - npv[2020]; N["nat_dpv"] = float(dpv); N["cbr_theta"] = 0.11 / (0.6 * dpv)
# наклон медианного разрыва на медианную pv по кварталам
mq = d.groupby("t").agg(pv=("pv", "median"), lgap=("lgap", "median"), rgap=("lgap", lambda s: float(np.median(np.exp(s) - 1))))
N["slope_lgap"] = float(np.polyfit(mq.pv, mq.lgap, 1)[0]); N["slope_rgap"] = float(np.polyfit(mq.pv, mq.rgap, 1)[0])

# φ: кредит под ДДУ / стоимость 50 м²
d["ltv50"] = d.loan_ddu * 1e6 / (d.perv * 50)
N["ltv50_by_year"] = {int(k): round(float(v), 3) for k, v in d.groupby("year").ltv50.median().items()}

# февраль: общий шок (сезонная разность), альтернативная экспозиция — доля ДДУ в 2025 году
X = pd.read_csv("feb2026_cross_section.csv", index_col=0)
N["feb_dlvol_ddu_mean"], N["feb_dlvol_ddu_median"] = float(X.dlvol_ddu.mean()), float(X.dlvol_ddu.median())
N["feb_dpv_median"] = float(X.dpv.median()); N["feb_dlp1_mean"] = float(X.dlp1.mean()); N["feb_dlgap_mean"] = float(X.dlgap.mean())
N["feb_n"] = len(X)
sh25 = c[c.year == 2025].groupby("region")[["vol_ddu", "vol_all"]].sum(); sh25 = (sh25.vol_ddu / sh25.vol_all).rename("S25")
X2 = X.join(sh25, how="inner")
N["feb_alt"] = {}
for y in ["dshare", "dpv", "dlp1", "dlp2"]:
    mm = smf.ols(f"{y} ~ S25", X2).fit(cov_type="HC1"); N["feb_alt"][y] = [float(mm.params.S25), float(mm.bse.S25), float(mm.tvalues.S25)]
N["feb_E_units"] = "доля (0,17 = 17 п. п.)"
# 2МНК: Δ ln цены на Δ доли ДДУ, инструмент — доля ДДУ в 2025 году (74 региона)
from linearmodels.iv import IV2SLS
X2["const"] = 1.0
N["feb_2sls"] = {}
for y in ["dlp1", "dlp2", "dlgap"]:
    r2 = IV2SLS(X2[y], X2[["const"]], X2[["dshare"]], X2[["S25"]]).fit(cov_type="robust")
    ci = r2.conf_int().loc["dshare"]
    N["feb_2sls"][y] = [float(r2.params.dshare), float(r2.std_errors.dshare), float(ci.iloc[0]), float(ci.iloc[1])]
N["feb_first_stage_F_HC1"] = N["feb_alt"]["dshare"][2] ** 2
N["b_lp1_DFOonly"]["theta"] = N["b_lp1_DFOonly"]["b"] / 0.6
json.dump(N, open("numbers.json", "w"), ensure_ascii=False, indent=1, default=float)
print(json.dumps(N, ensure_ascii=False, indent=1, default=float))
