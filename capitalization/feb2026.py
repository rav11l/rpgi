# -*- coding: utf-8 -*-
"""Февраль 2026: дозовый разностный анализ по экспозиции региона (Проверка 1 записки WP-2026-03).

Экспозиция E_j — падение доли выдач под ДДУ январь→февраль 2026 за вычетом обычного для региона
январско-февральского шага 2019–2025 (сезонность). Отклики — изменения цен II кв. 2026 к IV кв. 2025
за вычетом того же изменения годом раньше (II кв. 2025 к IV кв. 2024): так снимаются сезонность
и общий фон. Первая стадия — то же самое для объёма выдач под ДДУ и для меры субсидии.
"""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
import statsmodels.formula.api as smf
from build_panel import build, ALIAS

c = pd.read_csv("cbr_monthly.csv")
c["share"] = c.vol_ddu / c.vol_all
jf = c[c.month.isin([1, 2])].pivot_table(index=["region", "year"], columns="month", values="share").reset_index()
jf["step"] = jf[2] - jf[1]
base = jf[jf.year.between(2019, 2025)].groupby("region").step.mean()
E = -(jf[jf.year == 2026].set_index("region").step - base)       # >0: сильнее обычного падение
E.name = "E"

d = build()
k = d.set_index(["region", "tq"])

def dd(v, a1="2026Q2", a0="2025Q4", b1="2025Q2", b0="2024Q4"):
    x = k[v].unstack()
    return (x[a1] - x[a0]) - (x[b1] - x[b0])

def dd_log(v, **kw):
    x = np.log(k[v]).unstack()
    return (x["2026Q2"] - x["2025Q4"]) - (x["2025Q2"] - x["2024Q4"])

# «субсидия на рубль ипотечного спроса»: pv × объём ДДУ (дозовая форма, не доля)
k = k.assign(sub_rub=k.pv * k.vol_ddu)
X = pd.DataFrame({"dlp1": dd("lp1"), "dlp2": dd("lp2"), "dlgap": dd("lgap"),
                  "dshare": dd("share_ddu"), "dlvol_ddu": dd_log("vol_ddu"),
                  "dlvol_non": dd_log("vol_non"), "dpv": dd("pv"),
                  "dlsub": dd_log("sub_rub")}).join(E, how="inner").dropna()
X["w"] = k.vol_all.unstack()["2025Q4"].reindex(X.index)
print("регионов:", len(X))
print(X.describe().loc[["mean", "50%", "std"]].round(3).to_string())

res = {}
for y in ["dshare", "dlvol_ddu", "dlvol_non", "dpv", "dlsub", "dlp1", "dlp2", "dlgap"]:
    m = smf.ols(f"{y} ~ E", X).fit(cov_type="HC1")
    res[y] = m
    print("%-10s b=%8.3f se=%7.3f t=%6.2f  R2=%.3f" % (y, m.params.E, m.bse.E, m.tvalues.E, m.rsquared))

# плацебо: та же экспозиция на изменения годом раньше (II кв. 2025 к IV кв. 2024 минус II кв. 2024 к IV кв. 2023)
def dd_pl(v):
    x = k[v].unstack()
    return (x["2025Q2"] - x["2024Q4"]) - (x["2024Q2"] - x["2023Q4"])
P = pd.DataFrame({"dlp1": dd_pl("lp1"), "dlp2": dd_pl("lp2"), "dshare": dd_pl("share_ddu")}).join(E, how="inner").dropna()
for y in ["dshare", "dlp1", "dlp2"]:
    m = smf.ols(f"{y} ~ E", P).fit(cov_type="HC1")
    print("ПЛАЦЕБО %-7s b=%8.3f se=%7.3f t=%6.2f" % (y, m.params.E, m.bse.E, m.tvalues.E))
X.to_csv("feb2026_cross_section.csv")
