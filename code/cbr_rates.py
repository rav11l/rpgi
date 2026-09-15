# -*- coding: utf-8 -*-
"""Извлечение средневзвешенных ставок по ИЖК для Республики Татарстан.

Источники (лежат в data/sources/cbr/, контрольные суммы в hashes_cbr.json):
    02_13_Rates_mortgage.xlsx       - средневзвешенная ставка по всем ИЖК
    02_17_Rates_scpa_mortgage.xlsx  - средневзвешенная ставка по ИЖК под ДДУ
Лист «ставка в рублях», строка «Республика Татарстан (Татарстан)».

Результат: data/cbr_rates_rt_2021_2026.csv (year;month;rate_izhk_all_pct;rate_izhk_ddu_pct).

Запуск:  python code/cbr_rates.py
Требует openpyxl.
"""
import csv, os, sys

MONTHS = {"Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4, "Май": 5, "Июнь": 6,
          "Июль": 7, "Август": 8, "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "sources", "cbr")
OUT = os.path.join(ROOT, "data", "cbr_rates_rt_2021_2026.csv")
REGION = "Татарстан"
FIRST_YEAR = 2021


def series(filename):
    """Помесячный ряд ставки по региону: {(год, месяц): ставка}."""
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(SRC, filename), data_only=True, read_only=True)
    ws = wb["ставка в рублях"]
    rows = list(ws.iter_rows(values_only=True))

    header = None
    for r in rows:
        if r and any(isinstance(c, str) and c.strip().split(" ")[0] in MONTHS for c in r if c):
            header = r
            break
    region = None
    for r in rows:
        if r and isinstance(r[0], str) and REGION in r[0]:
            region = r
            break
    if header is None or region is None:
        raise RuntimeError("не найдена шапка с месяцами или строка региона в " + filename)

    out, month_cols = {}, []
    for i, h in enumerate(header):
        if isinstance(h, str):
            p = h.strip().split()
            if p and p[0] in MONTHS and len(p) > 1 and p[1].isdigit():
                out[(int(p[1]), MONTHS[p[0]])] = region[i]
                month_cols.append(i)
    # у первого столбца с данными шапка пуста: это январь года, с которого начинается ряд
    if month_cols:
        y0, m0 = min(out)
        prev = (y0, m0 - 1) if m0 > 1 else (y0 - 1, 12)
        if prev not in out and region[month_cols[0] - 1] is not None:
            out[prev] = region[month_cols[0] - 1]
    return out


def main():
    a = series("02_13_Rates_mortgage.xlsx")
    d = series("02_17_Rates_scpa_mortgage.xlsx")
    keys = sorted(k for k in a if k in d and k[0] >= FIRST_YEAR and a[k] is not None and d[k] is not None)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["year", "month", "rate_izhk_all_pct", "rate_izhk_ddu_pct"])
        for y, m in keys:
            w.writerow([y, m, "%.2f" % float(a[(y, m)]), "%.2f" % float(d[(y, m)])])
    print("записано %d месяцев: %d-%02d .. %d-%02d" % (len(keys), keys[0][0], keys[0][1], keys[-1][0], keys[-1][1]))
    print(OUT)


if __name__ == "__main__":
    sys.exit(main())
