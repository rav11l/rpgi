# -*- coding: utf-8 -*-
"""Сводная таблица оценок капитализации: results_capitalization.csv.

θ = b / φ, где b — отклик логарифма цены на pv (приведённая стоимость льготы на 1 ₽ кредита),
φ — доля цены, профинансированная льготным кредитом (LTV × доля ипотечных сделок), база 0,6.
"""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
from estimate import fe, row
from build_panel import build

PHI = 0.6
DFO = ["Еврейская автономная область", "Приморский край", "Республика Саха (Якутия)", "Хабаровский край",
       "Республика Бурятия", "Сахалинская область", "Забайкальский край", "Амурская область",
       "Камчатский край", "Магаданская область", "Чукотский автономный округ"]
rows = []
def add(label, d, y, **kw):
    r = row(fe(d, y, ["pv"], **kw), "pv")
    rows.append(dict(spec=label, outcome=y, b=r["b"], se=r["se"], lo=r["lo"], hi=r["hi"], n=r["n"],
                     theta=r["b"] / PHI, theta_lo=r["lo"] / PHI, theta_hi=r["hi"] / PHI))

base = build().sort_values(["region", "t"])
for y in ["lp1", "lp2", "lgap"]:
    add("база: до погашения, спред 3,5, лаг 1", base, y)
    add("веса — объём выдач", base, y, weights="vol_all")
    add("региональные тренды", base, y, trend=True)
    add("без ДФО", base[~base.region.isin(DFO)], y)
    add("горизонт 84 мес.", build(H=84).sort_values(["region", "t"]), y)
    add("спред 2,0", build(spread=2.0).sort_values(["region", "t"]), y)
    add("спред 5,0", build(spread=5.0).sort_values(["region", "t"]), y)
    add("срок 240 мес.", build(T_fixed=240).sort_values(["region", "t"]), y)
    add("ориентир — среднее за 12 мес.", build(bench="ma12").sort_values(["region", "t"]), y)
R = pd.DataFrame(rows)
R.to_csv("results_capitalization.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
