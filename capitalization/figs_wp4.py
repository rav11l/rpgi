# -*- coding: utf-8 -*-
"""Рисунки WP-2026-04."""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build_panel import build

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white"})

d = build()
m = d.groupby(["t", "tq"])[["pv", "lgap", "r_ddu", "r_b"]].median().reset_index()
lab = [x if x.endswith("Q1") else "" for x in m.tq]
lab = [x[:4] if x else "" for x in lab]

# Рис. 1: две панели, одна шкала на панель
fig, ax = plt.subplots(2, 1, figsize=(6.4, 4.6), sharex=True)
ax[0].plot(m.t, m.r_b, color=ORANGE, lw=2, label=r"Рыночный ориентир $r_b$")
ax[0].plot(m.t, m.r_ddu, color=BLUE, lw=2, label="Ставка по ИЖК под ДДУ")
ax[0].set_ylabel("% годовых"); ax[0].legend(frameon=False, loc="upper left")
ax[0].text(m.t.iloc[-1] + 0.3, m.r_b.iloc[-1], "%.1f" % m.r_b.iloc[-1], color=INK2, va="center", fontsize=8)
ax[0].text(m.t.iloc[-1] + 0.3, m.r_ddu.iloc[-1], "%.1f" % m.r_ddu.iloc[-1], color=INK2, va="center", fontsize=8)
ax[1].plot(m.t, m.pv, color=BLUE, lw=2, label="pv — льгота на 1 ₽ кредита")
ax[1].plot(m.t, np.exp(m.lgap) - 1, color=AQUA, lw=2, label="Сырой разрыв P₁/P₂ − 1")
ax[1].set_ylabel("доля"); ax[1].legend(frameon=False, loc="upper left")
ax[1].set_xticks(m.t); ax[1].set_xticklabels(lab)
ax[1].set_ylim(0, 0.8)
fig.savefig("fig1_series.png"); plt.close(fig)

# Рис. 2: θ по спецификациям
R = pd.read_csv("results_capitalization.csv")
specs = list(dict.fromkeys(R.spec))
short = {"база: до погашения, спред 3,5, лаг 1": "База", "веса — объём выдач": "Веса — объём выдач",
         "региональные тренды": "Региональные тренды", "без ДФО": "Без ДФО",
         "горизонт 84 мес.": "Горизонт 84 мес.", "спред 2,0": "Спред 2,0 п. п.", "спред 5,0": "Спред 5,0 п. п.",
         "срок 240 мес.": "Срок 240 мес.", "ориентир — среднее за 12 мес.": "Ориентир: среднее за 12 мес."}
fig, ax = plt.subplots(figsize=(6.4, 4.6))
off = {"lp1": -0.22, "lp2": 0.0, "lgap": 0.22}
col = {"lp1": BLUE, "lp2": ORANGE, "lgap": AQUA}
name = {"lp1": "Первичная цена", "lp2": "Вторичная цена", "lgap": "Разрыв"}
for y in ["lp1", "lp2", "lgap"]:
    r = R[R.outcome == y].set_index("spec").loc[specs]
    yy = np.arange(len(specs))[::-1] + off[y]
    ax.hlines(yy, r.theta_lo, r.theta_hi, color=col[y], lw=2)
    ax.plot(r.theta, yy, "o", ms=6, color=col[y], mec="white", mew=1.2, label=name[y])
ax.set_xlim(-1.3, 2.15); ax.axvline(0, color=INK2, lw=0.8); ax.axvline(1, color=INK2, lw=0.8, ls=(0, (3, 3)))
ax.text(1.02, len(specs) - 0.45, "полная\nкапитализация", color=INK2, fontsize=7.5, va="top")
ax.set_yticks(np.arange(len(specs))[::-1]); ax.set_yticklabels([short[s] for s in specs])
ax.grid(axis="y", visible=False)
ax.set_xlabel("θ — доля субсидии, перешедшая в цену (точка и 95 % интервал, φ = 0,6)")
ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
fig.savefig("fig2_theta.png"); plt.close(fig)

# Рис. 3: первая стадия февраля 2026 при двух экспозициях
X = pd.read_csv("feb2026_cross_section.csv", index_col=0)
c = pd.read_csv("cbr_monthly.csv"); s25 = c[c.year == 2025].groupby("region")[["vol_ddu", "vol_all"]].sum()
X = X.join((s25.vol_ddu / s25.vol_all).rename("S25"), how="inner")
fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
for ax, xv, xl, tt in [(axs[0], X.E * 100, "Падение доли ДДУ январь → февраль 2026\nсверх обычного, п. п.", "t = −0,5"),
                       (axs[1], X.S25 * 100, "Доля ДДУ в выдачах 2025 года, %", "t = −2,6")]:
    ax.scatter(xv, X.dshare * 100, s=18, color=BLUE, edgecolor="white", linewidth=0.7)
    b = np.polyfit(xv, X.dshare * 100, 1); xs = np.linspace(xv.min(), xv.max(), 50)
    ax.plot(xs, np.polyval(b, xs), color=INK2, lw=1.5)
    ax.set_xlabel(xl, fontsize=8)
    ax.text(0.97, 0.95, ("наклон %.2f, " % b[0]).replace(".", ",").replace("-", "−") + tt, transform=ax.transAxes,
            ha="right", va="top", color=INK2, fontsize=7.5)
axs[0].set_ylabel("Δ доли ДДУ, п. п.")
axs[0].set_title("Месячная экспозиция", fontsize=8.5, color=INK, loc="left")
axs[1].set_title("Предопределённая экспозиция", fontsize=8.5, color=INK, loc="left")
fig.savefig("fig3_feb2026.png"); plt.close(fig)
print("ok")
