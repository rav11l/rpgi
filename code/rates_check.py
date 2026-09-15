# -*- coding: utf-8 -*-
"""Связь ценового разрыва с разницей ставок по ИЖК под ДДУ и по прочим ИЖК.
Татарстан, 2021-2026. Закрывает пункт 8 README депозита RPGI.

Источники:
  rpgi/data/cbr_rates_rt_2021_2026.csv      - средневзвешенные ставки, Татарстан.
                                              Пересобирается из первоисточника:
                                              python code/cbr_rates.py
                                              (02_13_Rates_mortgage.xlsx - все ИЖК,
                                               02_17_Rates_scpa_mortgage.xlsx - под ДДУ;
                                               лист "ставка в рублях", строка "Республика
                                               Татарстан (Татарстан)"). Оба файла лежат в
                                              rpgi/data/sources/cbr/, sha256 - в
                                              hashes_cbr.json.
  rpgi/data/cbr_tatarstan_izhk_ddu_2019_2026.csv - объёмы выдач (02_11 и 02_16)
  rpgi/data/rosstat_kazan_gap_summary.csv        - ценовой разрыв

Ставка по ПРОЧИМ ИЖК не публикуется и разворачивается из тождества
    r_all * V_all = r_ddu * V_ddu + r_other * V_other
Это важно: r_all содержит ДДУ внутри себя, поэтому разность (r_ddu - r_all)
тождественно равна (1 - s) * (r_ddu - r_other), где s - доля выдач под ДДУ.
Она механически связана с долей, а доля коррелирует с разрывом на 0,89.
Сравнивать надо с ПРОЧИМИ, а не со ВСЕМИ.
"""
import csv, math, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(BASE, "data")

def rd(f):
    with open(os.path.join(B, f), encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=";"))

rate = {(int(r["year"]), int(r["month"])): (float(r["rate_izhk_all_pct"]), float(r["rate_izhk_ddu_pct"]))
        for r in rd("cbr_rates_rt_2021_2026.csv")}
vol  = {(int(r["year"]), int(r["month"])): (float(r["izhk_total_mln_rub"]), float(r["izhk_ddu_mln_rub"]))
        for r in rd("cbr_tatarstan_izhk_ddu_2019_2026.csv")}
gap  = {int(r["year"]): float(r["kazan_gap_pct"]) for r in rd("rosstat_kazan_gap_summary.csv")}

def pearson(x, y):
    n = len(x); mx = sum(x)/n; my = sum(y)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(x, y))
    sxx = sum((a-mx)**2 for a in x); syy = sum((b-my)**2 for b in y)
    return sxy / math.sqrt(sxx*syy)

def annual(months):
    out = {}
    for y in sorted(gap):
        Vt = Vd = Wt = Wd = no = do = 0.0
        for m in months:
            if (y, m) not in rate or (y, m) not in vol:
                continue
            ra, rdd = rate[(y, m)]; vt, vd = vol[(y, m)]; vo = vt - vd
            Vt += vt; Vd += vd; Wt += ra*vt; Wd += rdd*vd
            if vo > 0:
                ro = (ra*vt - rdd*vd)/vo
                no += ro*vo; do += vo
        if Vt:
            out[y] = (Wt/Vt, Wd/Vd, no/do, Vd/Vt*100)
    return out

for label, months in (("год целиком", list(range(1, 13))), ("I-II кварталы", [1, 2, 3, 4, 5, 6])):
    A = annual(months); ys = sorted(A)
    print("\n===== окно: %s =====" % label)
    print("%5s %11s %11s %12s %10s %9s %8s %11s" % (
        "год", "ставка ИЖК", "ставка ДДУ", "ставка проч", "проч-ДДУ", "ДДУ-все", "доля %", "разрыв цен"))
    for y in ys:
        ra, rdd, ro, s = A[y]
        print("%5d %11.2f %11.2f %12.2f %10.2f %9.2f %8.2f %11.2f" % (y, ra, rdd, ro, ro-rdd, rdd-ra, s, gap[y]))
    G = [gap[y] for y in ys]
    for nm, ser in (("прочие - ДДУ (верно)", [A[y][2]-A[y][1] for y in ys]),
                    ("ДДУ - все ИЖК (арт.)", [A[y][1]-A[y][0] for y in ys])):
        d1 = [ser[i+1]-ser[i] for i in range(len(ser)-1)]
        d2 = [G[i+1]-G[i] for i in range(len(G)-1)]
        print("  corr(разрыв, %-21s) уровни = %+.3f | разности = %+.3f" % (nm, pearson(ser, G), pearson(d1, d2)))
    # проверка тождества (r_ddu - r_all) = (1 - s) * (r_ddu - r_other)
    err = max(abs((A[y][1]-A[y][0]) - (1-A[y][3]/100)*(A[y][1]-A[y][2])) for y in ys)
    print("  проверка тождества (r_ддy-r_все) = (1-s)(r_ддy-r_проч): макс. расхождение %.4f п. п." % err)
