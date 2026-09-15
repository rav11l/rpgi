# -*- coding: utf-8 -*-
"""Рисунки к статье. Печать чёрно-белая: различение линий — начертанием и подписями, не цветом."""
import csv, io, os, statistics as st
import openpyxl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "data") + os.sep
OUT = os.path.join(BASE, "figs") + os.sep
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Serif", "font.size": 9,
    "axes.edgecolor": "#444444", "axes.linewidth": 0.8,
    "axes.grid": True, "grid.color": "#DDDDDD", "grid.linewidth": 0.5,
    "xtick.color": "#333333", "ytick.color": "#333333",
    "axes.labelcolor": "#111111", "text.color": "#111111",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})
INK, MID, SOFT = "#111111", "#666666", "#C8C8C8"

# ——— данные ———
gaps_by_year, gaps_by_reg = {}, {}
for r in csv.DictReader(io.open(D+"rosstat_centres_gap_2021_2026.csv", encoding="utf-8"), delimiter=";"):
    y, c, g = int(r["year"]), r["centre"], float(r["gap_pct"])
    gaps_by_year.setdefault(y, {})[c] = g
    gaps_by_reg.setdefault(c, {})[y] = g

MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
def load(fn):
    ws = openpyxl.load_workbook(D+"sources/cbr/"+fn, read_only=True, data_only=True)["в рублях"]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(rows) if r and isinstance(r[1], str) and "Январь 2019" in str(r[1]))
    return [str(x).strip() if x else "" for x in rows[h]], {str(r[0]).strip(): r for r in rows[h+1:] if r and r[0]}
mt, dt = load("02_11_New_loans_mortgage.xlsx")
md, dd = load("02_16_New_loans_scpa_mortgage.xlsx")

def share_year(reg, year):
    tot = ddu = 0
    for i, mm in enumerate(mt):
        if not mm or not mm.endswith(str(year)) or mm not in md: continue
        j = md.index(mm)
        try: t, d = float(dt[reg][i]), float(dd[reg][j])
        except: continue
        tot += t; ddu += d
    return 100*ddu/tot if tot else None

def corr(a, b):
    n = len(a); ma, mb = sum(a)/n, sum(b)/n
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / ((sum((x-ma)**2 for x in a)**.5)*(sum((y-mb)**2 for y in b)**.5))

# ——— Рисунок 1: разрыв по центрам субъектов ———
years = sorted(gaps_by_year)
p25 = [st.quantiles(list(gaps_by_year[y].values()), n=4)[0] for y in years]
p50 = [st.median(list(gaps_by_year[y].values())) for y in years]
p75 = [st.quantiles(list(gaps_by_year[y].values()), n=4)[2] for y in years]
kaz = [gaps_by_reg["Республика Татарстан (Татарстан)"][y] for y in years]

fig, ax = plt.subplots(figsize=(6.3, 3.3))
ax.fill_between(years, p25, p75, color=SOFT, linewidth=0, zorder=1)
ax.plot(years, p50, color=MID, linewidth=1.6, linestyle="--", zorder=3)
ax.plot(years, kaz, color=INK, linewidth=2.0, marker="o", markersize=4.5,
        markerfacecolor="white", markeredgewidth=1.4, zorder=4)
ax.annotate("Казань", (years[-3], kaz[-3]), xytext=(-6, 10), textcoords="offset points",
            fontsize=9, fontweight="bold", ha="right")
ax.annotate("медиана центров", (years[2], p50[2]), xytext=(4, -16), textcoords="offset points", fontsize=8.5, color=MID)
ax.annotate("межквартильный размах", (years[0], p75[0]), xytext=(2, 8), textcoords="offset points", fontsize=8, color="#8A8A8A")
for x, v in ((2024, kaz[3]), (2025, kaz[4]), (2026, kaz[5])):
    ax.annotate(f"{v:.0f}".replace(".", ","), (x, v), xytext=(0, 8), textcoords="offset points",
                ha="center", fontsize=8.5)
ax.set_ylabel("Разрыв цен, %"); ax.set_xlabel("")
ax.yaxis.set_major_locator(MultipleLocator(10)); ax.set_ylim(-10, 60)
ax.set_xticks(years); ax.spines[["top", "right"]].set_visible(False)
fig.savefig(OUT+"fig1_gap_centres.png"); plt.close(fig)

# ——— Рисунок 2: межрегиональная проверка ———
lvl = [(c, g, share_year(c, 2025)) for c, g in gaps_by_year[2025].items() if c in dt and c in dd]
lvl = [(c, g, s) for c, g, s in lvl if s]
dg, ds = [], []
for reg, d in gaps_by_reg.items():
    if reg not in dt or reg not in dd: continue
    for y in range(2022, 2027):
        if y in d and (y-1) in d:
            s1, s0 = share_year(reg, y), share_year(reg, y-1)
            if s1 and s0: dg.append(d[y]-d[y-1]); ds.append(s1-s0)
r_lvl, r_d = corr([x[2] for x in lvl], [x[1] for x in lvl]), corr(ds, dg)

fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.1))
a = axes[0]
a.scatter([x[2] for x in lvl], [x[1] for x in lvl], s=16, facecolor="none", edgecolor=MID, linewidth=0.9)
kz = [x for x in lvl if "Татарстан" in x[0]][0]
a.scatter([kz[2]], [kz[1]], s=42, color=INK, zorder=5)
a.annotate("Татарстан", (kz[2], kz[1]), xytext=(-8, 8), textcoords="offset points", fontsize=8.5, ha="right", fontweight="bold")
a.set_xlabel("Доля выдач под ДДУ, %"); a.set_ylabel("Разрыв цен, %")
a.set_title(f"а) уровни, 2025 год: r = {r_lvl:+.2f}".replace(".", ","), fontsize=9, loc="left", pad=8)

b = axes[1]
b.axhline(0, color="#AAAAAA", linewidth=0.7); b.axvline(0, color="#AAAAAA", linewidth=0.7)
b.scatter(ds, dg, s=12, facecolor="none", edgecolor=MID, linewidth=0.7, alpha=0.85)
b.set_xlabel("Изменение доли, п. п."); b.set_ylabel("Изменение разрыва, п. п.")
b.set_title(f"б) первые разности, 351 наблюдение: r = {r_d:+.2f}".replace(".", ","), fontsize=9, loc="left", pad=8)
for ax_ in axes: ax_.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(OUT+"fig2_panel_check.png"); plt.close(fig)

# ——— Рисунок 3: помесячная доля выдач под ДДУ ———
labels, rf, rt, med, lo, hi = [], [], [], [], [], []
regs = [k for k in dt if k in dd and "ФЕДЕРАЛЬНЫЙ ОКРУГ" not in k and "РОССИЙСКАЯ" not in k]
for i, mm in enumerate(mt):
    if not mm or mm not in md: continue
    j = md.index(mm)
    try: t, d = float(dt["РОССИЙСКАЯ ФЕДЕРАЦИЯ"][i]), float(dd["РОССИЙСКАЯ ФЕДЕРАЦИЯ"][j])
    except: continue
    vals = []
    for reg in regs:
        try:
            tt, ddv = float(dt[reg][i]), float(dd[reg][j])
            if tt >= 300: vals.append(100*ddv/tt)
        except: pass
    if len(vals) < 40: continue
    labels.append(mm); rf.append(100*d/t)
    try: rt.append(100*float(dd["Республика Татарстан (Татарстан)"][j])/float(dt["Республика Татарстан (Татарстан)"][i]))
    except: rt.append(None)
    vals.sort(); med.append(st.median(vals))
    lo.append(vals[int(0.1*len(vals))]); hi.append(vals[int(0.9*len(vals))])
x = list(range(len(labels)))
fig, ax = plt.subplots(figsize=(6.5, 3.2))
ax.fill_between(x, lo, hi, color=SOFT, linewidth=0, zorder=1)
ax.plot(x, med, color="#999999", linewidth=1.1, linestyle=":", zorder=2)
ax.plot(x, rf, color=INK, linewidth=1.8, zorder=4)
ax.plot(x, rt, color=MID, linewidth=1.4, linestyle="--", zorder=3)
def mark(month, text, dy):
    if month in labels:
        i = labels.index(month)
        ax.axvline(i, color="#555555", linewidth=0.8, linestyle=(0, (2, 2)), zorder=2)
        ax.annotate(text, (i, 88+dy), xytext=(4, 0), textcoords="offset points", fontsize=8, color="#333333")
mark("Июль 2024", "июль 2024", 0); mark("Февраль 2026", "февраль 2026", -8)
ax.annotate("Россия", (x[-1], rf[-1]), xytext=(6, -2), textcoords="offset points", fontsize=8.5, fontweight="bold")
ax.annotate("Татарстан", (x[-1], rt[-1]), xytext=(6, -10), textcoords="offset points", fontsize=8.5, color=MID)
ax.annotate("медиана регионов", (x[len(x)//4], med[len(x)//4]), xytext=(0, -22), textcoords="offset points", fontsize=8, color="#8A8A8A")
ticks = [i for i, l in enumerate(labels) if l.startswith("Январь")]
ax.set_xticks(ticks); ax.set_xticklabels([labels[i].split()[1] for i in ticks])
ax.set_ylabel("Доля выдач под ДДУ, %"); ax.set_ylim(0, 100)
ax.set_xlim(0, len(x)+3); ax.spines[["top", "right"]].set_visible(False)
fig.savefig(OUT+"fig3_ddu_monthly.png"); plt.close(fig)

print("r уровни 2025:", round(r_lvl, 3), "| r разности панель:", round(r_d, 3), "| n панели:", len(dg))
print("месяцев в ряду:", len(labels), "| февраль 2026 РФ:", round(rf[labels.index("Февраль 2026")], 1))
print("готово:", os.listdir(OUT))
