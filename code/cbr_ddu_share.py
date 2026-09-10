# -*- coding: utf-8 -*-
"""Доля ипотечных выдач под ДДУ по России, Татарстану и регионам.
Источник: таблицы Банка России 02_11 (объём ИЖК) и 02_16 (объём ИЖК под ДДУ),
лист «в рублях», помесячно с января 2019 года.
Выход: Данные/cbr_rf_rt_ddu_share_2019_2026.csv и Данные/cbr_ddu_share_regions_2026_02.csv
"""
import csv, os, openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "Данные", "Первоисточники")
OUT = os.path.join(BASE, "Данные")

def load(fn):
    ws = openpyxl.load_workbook(os.path.join(SRC, fn), read_only=True, data_only=True)["в рублях"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    hdr = next(i for i, r in enumerate(rows) if r and isinstance(r[1], str) and "Январь 2019" in str(r[1]))
    months = [str(x).strip() if x else "" for x in rows[hdr]]
    data = {str(r[0]).strip(): r for r in rows[hdr + 1:] if r and r[0]}
    return months, data

m_tot, d_tot = load("02_11_New_loans_mortgage.xlsx")
m_ddu, d_ddu = load("02_16_New_loans_scpa_mortgage.xlsx")
RF, RT = "РОССИЙСКАЯ ФЕДЕРАЦИЯ", "Республика Татарстан (Татарстан)"

def val(d, key, months, month):
    try:
        return float(d[key][months.index(month)])
    except Exception:
        return None

# 1. помесячный ряд РФ и РТ
with open(os.path.join(OUT, "cbr_rf_rt_ddu_share_2019_2026.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["месяц", "РФ_всего_млн_руб", "РФ_ДДУ_млн_руб", "РФ_доля_ДДУ_проц",
                "РТ_всего_млн_руб", "РТ_ДДУ_млн_руб", "РТ_доля_ДДУ_проц"])
    for mm in m_tot[1:]:
        if not mm or mm not in m_ddu:
            continue
        row = [mm]
        ok = False
        for key in (RF, RT):
            t, d = val(d_tot, key, m_tot, mm), val(d_ddu, key, m_ddu, mm)
            if t and d:
                row += [round(t), round(d), round(100 * d / t, 1)]; ok = True
            else:
                row += ["", "", ""]
        if ok:
            w.writerow(row)

# 2. срез по регионам: январь → февраль 2026
rows = []
for k, r in d_tot.items():
    if "ФЕДЕРАЛЬНЫЙ ОКРУГ" in k or "РОССИЙСКАЯ" in k or k not in d_ddu:
        continue
    tj, tf = val(d_tot, k, m_tot, "Январь 2026"), val(d_tot, k, m_tot, "Февраль 2026")
    dj, df = val(d_ddu, k, m_ddu, "Январь 2026"), val(d_ddu, k, m_ddu, "Февраль 2026")
    if not all([tj, tf, dj, df]) or tj < 300 or tf < 300:  # отсечены регионы с выдачами < 300 млн ₽
        continue
    sj, sf = 100 * dj / tj, 100 * df / tf
    rows.append([k, round(tj), round(dj), round(sj, 1), round(tf), round(df), round(sf, 1), round(sf - sj, 1), sf - sj])
rows.sort(key=lambda x: x[8])  # сортировка по неокруглённому изменению
with open(os.path.join(OUT, "cbr_ddu_share_regions_2026_02.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["место_по_глубине_падения", "регион", "январь_всего_млн", "январь_ДДУ_млн", "январь_доля_проц",
                "февраль_всего_млн", "февраль_ДДУ_млн", "февраль_доля_проц", "изменение_п_п"])
    for i, r in enumerate(rows, 1):
        w.writerow([i] + r[:8])
print("регионов:", len(rows))
print("Татарстан:", [ [i]+r for i, r in enumerate(rows, 1) if "Татарстан" in r[0] ])
