# -*- coding: utf-8 -*-
"""RPGI v0.1.0 — сводные метрики индикатора.

Вход:  data/rosstat_centres_gap_2021_2026.csv, data/cbr_rf_rt_ddu_share_2019_2026.csv
Выход: data/rpgi_v0.1.0.csv (по центрам субъектов: разрыв, медиана, место)
       data/rpgi_v0.1.0_summary.csv (по годам для выбранного центра)
Печатает корреляции разрыва с долей выдач под ДДУ в уровнях и первых разностях.
"""
import csv, os, statistics as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "data")
CENTRE = "Республика Татарстан (Татарстан)"   # строки названы по субъекту,
# значения — по его административному центру (лист «по центру субъекта РФ»)
REGION_SHARE_COL = "РТ_доля_ДДУ_проц"
MONTHS = {"Январь":1,"Февраль":2,"Март":3,"Апрель":4,"Май":5,"Июнь":6,
          "Июль":7,"Август":8,"Сентябрь":9,"Октябрь":10,"Ноябрь":11,"Декабрь":12}

def read_gaps():
    rows = []
    with open(os.path.join(D, "rosstat_centres_gap_2021_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            rows.append((int(r["year"]), r["centre"], float(r["gap_pct"])))
    return rows

def read_share(window="year"):
    """Доля выдач под ДДУ по объёму в рублях.

    window="year"  — за весь доступный год (определение по умолчанию: так считаны
                     опубликованные значения 0,89 и 0,66; 2026 год неполный, январь–июль);
    window="h1"    — за I–II кварталы, то есть в том же окне, что и ценовой ряд.
    """
    tot, ddu = {}, {}
    with open(os.path.join(D, "cbr_rf_rt_ddu_share_2019_2026.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name, year = r["месяц"].rsplit(" ", 1)
            m = MONTHS.get(name)
            if not m or not r["РТ_всего_млн_руб"]:
                continue
            if window == "h1" and m > 6:
                continue
            y = int(year)
            tot[y] = tot.get(y, 0) + float(r["РТ_всего_млн_руб"])
            ddu[y] = ddu.get(y, 0) + float(r["РТ_ДДУ_млн_руб"])
    return {y: 100 * ddu[y] / tot[y] for y in tot}

def corr(a, b):
    n = len(a)
    ma, mb = sum(a)/n, sum(b)/n
    cov = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    va = sum((x-ma)**2 for x in a) ** 0.5
    vb = sum((y-mb)**2 for y in b) ** 0.5
    return cov / (va*vb)

def main():
    rows = read_gaps()
    years = sorted({y for y, _, _ in rows})
    out, summary = [], []
    for y in years:
        cut = sorted([(c, g) for yy, c, g in rows if yy == y], key=lambda x: -x[1])
        med = st.median([g for _, g in cut])
        for rank, (c, g) in enumerate(cut, 1):
            out.append({"year": y, "centre": c, "gap_pct": round(g, 2),
                        "median_centres_pct": round(med, 2), "rank": rank, "centres_n": len(cut),
                        "gap_to_median": round(g / med, 2) if med else ""})
        me = [r for r in out if r["year"] == y and r["centre"] == CENTRE]
        if me:
            summary.append(me[0])
    with open(os.path.join(D, "rpgi_v0.1.0.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(out)
    with open(os.path.join(D, "rpgi_v0.1.0_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(summary)

    print(f"{CENTRE} — центр субъекта: годы {[r['year'] for r in summary]}")
    print("разрыв, %:", [r["gap_pct"] for r in summary])
    print("медиана центров, %:", [r["median_centres_pct"] for r in summary])
    print("место:", [f'{r["rank"]}/{r["centres_n"]}' for r in summary])

    lines = []
    for window, label in (("year", "год целиком (по умолчанию)"), ("h1", "I–II кварталы, окно ценового ряда")):
        share = read_share(window)
        ys = [r["year"] for r in summary if r["year"] in share]
        gap = [r["gap_pct"] for r in summary if r["year"] in share]
        sh = [share[y] for y in ys]
        dg = [gap[i+1]-gap[i] for i in range(len(gap)-1)]
        ds = [sh[i+1]-sh[i] for i in range(len(sh)-1)]
        cl, cd = corr(gap, sh), corr(dg, ds)
        print(f"\nдоля выдач под ДДУ, {label}: {[round(x, 1) for x in sh]}")
        print(f"  корреляция в уровнях:          {cl:+.3f}  (n = {len(gap)})")
        print(f"  корреляция в первых разностях: {cd:+.3f}  (n = {len(dg)})")
        lines.append({"window": window, "window_label": label,
                      "corr_levels": round(cl, 3), "n_levels": len(gap),
                      "corr_first_diff": round(cd, 3), "n_first_diff": len(dg),
                      "share_series": " ".join(f"{x:.1f}" for x in sh)})
    with open(os.path.join(D, "rpgi_v0.1.0_correlations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lines[0].keys()), delimiter=";")
        w.writeheader(); w.writerows(lines)

    print("\nСвязь разрыва с разницей ставок по ДДУ и прочим кредитам в этот расчёт не входит:")
    print("нужна таблица средневзвешенных ставок Банка России, в депозит не включена (см. README, «Границы»).")

if __name__ == "__main__":
    main()
