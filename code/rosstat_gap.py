# -*- coding: utf-8 -*-
"""Сборка data/rosstat_centres_gap_2021_2026.csv из книг Росстата (добавлено в v0.3.0).

Для каждого года берётся книга с наиболее полной редакцией (edition_rank: 4kv, затем 2kv),
лист «по центру субъекта РФ», графа «Все типы квартир», I и II кварталы. В круг года входят
центры, для которых опубликованы оба рынка за оба квартала. Разрыв = (перв/втор − 1) × 100
по средним I–II кварталов.

Запуск: python code/rosstat_gap.py
"""
import csv, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rosstat_parse import parse, edition_rank

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "data", "sources", "rosstat")
OUT = os.path.join(BASE, "data", "rosstat_centres_gap_2021_2026.csv")

def qv(vals, n):
    for q, v in vals.items():
        if re.match(r"^%s\s*квартал" % n, q.strip()):
            return v
    return None

def main():
    books = {}
    for p in glob.glob(os.path.join(SRC, "*.xlsx")):
        d = parse(p)
        if not d or not d["market"]:
            continue
        k = (d["year"], d["market"])
        if k not in books or edition_rank(d["path"]) < edition_rank(books[k]["path"]):
            books[k] = d
    rows = []
    for year in sorted({y for y, _ in books}):
        P, V = books.get((year, "perv")), books.get((year, "vtor"))
        if not P or not V:
            continue
        for c in sorted(set(P["data"]) & set(V["data"])):
            p1, p2 = qv(P["data"][c], "I"), qv(P["data"][c], "II")
            v1, v2 = qv(V["data"][c], "I"), qv(V["data"][c], "II")
            if None in (p1, p2, v1, v2) or 0 in (v1, v2):
                continue
            pm, vm = (p1 + p2) / 2, (v1 + v2) / 2
            rows.append([year, c, p1, p2, v1, v2, round(pm, 2), round(vm, 2),
                         round((pm / vm - 1) * 100, 4), P["path"], V["path"]])
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["year", "centre", "perv_q1", "perv_q2", "vtor_q1", "vtor_q2",
                    "perv_mean", "vtor_mean", "gap_pct", "src_perv", "src_vtor"])
        w.writerows(rows)
    print("записано %d строк" % len(rows))

if __name__ == "__main__":
    main()
