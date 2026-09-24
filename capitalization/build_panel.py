# -*- coding: utf-8 -*-
"""Квартальная панель «цена — субсидия» по центрам субъектов РФ, 2021Q1–2026Q2.

Цены: книги Росстата (лист «по центру субъекта РФ», «Все типы квартир»), все кварталы.
Кредит: таблицы Банка России 02_10/11/13 (все ИЖК) и 02_15/16/17 (ИЖК под ДДУ), помесячно.
Ключевая ставка: cbr.ru/hd_base/KeyRate (ступенчатая функция по датам решений).

Мера субсидии pv — приведённая стоимость процентной льготы на 1 ₽ кредита под ДДУ:
    pv = 1 − [pmt(r_s,T)·a(r_b,H) + B_s(H)·(1+r_b)^−H] / 1,
где r_s — средневзвешенная ставка по ИЖК под ДДУ в регионе, T — средневзвешенный срок,
r_b — рыночный ориентир (ключевая ставка с лагом + спред), H — горизонт жизни кредита
(досрочное погашение/рефинансирование). Кредит дисконтируется по рыночной ставке.
"""
import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np, datetime as dt

# --- ключевая ставка: (дата начала действия, значение) -----------------------------
KEY = [("2018-12-17", 7.75), ("2019-06-17", 7.5), ("2019-07-29", 7.25), ("2019-09-09", 7.0),
       ("2019-10-28", 6.5), ("2019-12-16", 6.25), ("2020-02-10", 6.0), ("2020-04-27", 5.5),
       ("2020-06-22", 4.5), ("2020-07-27", 4.25), ("2021-03-22", 4.5), ("2021-04-26", 5.0), ("2021-06-15", 5.5),
       ("2021-07-26", 6.5), ("2021-09-13", 6.75), ("2021-10-25", 7.5), ("2021-12-20", 8.5),
       ("2022-02-14", 9.5), ("2022-02-28", 20.0), ("2022-04-11", 17.0), ("2022-05-04", 14.0),
       ("2022-05-27", 11.0), ("2022-06-14", 9.5), ("2022-07-25", 8.0), ("2022-09-19", 7.5),
       ("2023-07-24", 8.5), ("2023-08-15", 12.0), ("2023-09-18", 13.0), ("2023-10-30", 15.0),
       ("2023-12-18", 16.0), ("2024-07-29", 18.0), ("2024-09-16", 19.0), ("2024-10-28", 21.0),
       ("2025-06-09", 20.0), ("2025-07-28", 18.0), ("2025-09-15", 17.0), ("2025-10-27", 16.5),
       ("2025-12-22", 16.0), ("2026-02-16", 15.5), ("2026-03-23", 15.0), ("2026-04-27", 14.5),
       ("2026-06-22", 14.25), ("2026-07-27", 14.0)]

def key_monthly():
    days = pd.date_range("2019-01-01", "2026-07-31", freq="D")
    s = pd.Series(np.nan, index=days)
    for d, v in KEY:
        s[s.index >= d] = v
    m = s.resample("MS").mean()
    return m

# --- сопоставление названий субъектов --------------------------------------------
ALIAS = {
    "Архангельская область (кроме Ненецкого автономного округа)":
        "Архангельская область без данных по Ненецкому автономному округу",
    "Ненецкий автономный округ (Архангельская область)": "в том числе Ненецкий автономный округ",
    "Республика Северная Осетия-Алания": "Республика Северная Осетия - Алания",
    "Тюменская область (кроме Ханты-Мансийского автономного округа-Югры и Ямало-Ненецкого автономного округа)":
        "Тюменская область без данных по Ханты-Мансийскому автономному округу - Югре и Ямало-Ненецкому автономному округу",
    "Ханты-Мансийский автономный округ - Югра (Тюменская область)": "в том числе Ханты-Мансийский автономный округ - Югра",
    "Ямало-Ненецкий автономный округ (Тюменская область)": "в том числе Ямало-Ненецкий автономный округ",
}

def annuity(r_m, n):
    r_m = np.asarray(r_m, float); n = np.asarray(n, float)
    return np.where(r_m > 0, (1 - (1 + r_m) ** (-n)) / np.where(r_m > 0, r_m, 1), n)

def pv_subsidy(r_s, r_b, T, H):
    """Приведённая стоимость льготы на 1 ₽ кредита (ставки в % годовых, сроки в месяцах)."""
    rs, rb = np.asarray(r_s) / 1200, np.asarray(r_b) / 1200
    T = np.asarray(T, float); h = np.minimum(H, T) if H is not None else T
    pmt = 1 / annuity(rs, T)
    bal = pmt * annuity(rs, T - h)                    # остаток долга к моменту h
    return 1 - (pmt * annuity(rb, h) + bal * (1 + rb) ** (-h))

def build(spread=3.5, lag=1, H=None, T_fixed=None, bench="key"):
    c = pd.read_csv("cbr_monthly.csv")
    km = key_monthly()
    c["date"] = pd.to_datetime(dict(year=c.year, month=c.month, day=1))
    c["key"] = c.date.map(km.shift(lag))
    if bench == "ma12":   # ожидания: среднее ключевой ставки за 12 мес.
        c["key"] = c.date.map(km.rolling(12, min_periods=1).mean().shift(lag))
    c["r_b"] = c.key + spread
    # ставка по прочим (не ДДУ) выдачам из тождества объёмов
    c["vol_non"] = c.vol_all - c.vol_ddu
    c["r_non"] = (c.r_all * c.vol_all - c.r_ddu * c.vol_ddu) / c.vol_non
    c["pv"] = pv_subsidy(c.r_ddu, c.r_b, c.t_ddu if T_fixed is None else T_fixed, H)
    c["pv_non"] = pv_subsidy(c.r_non, c.r_b, c.t_all, H)
    c["q"] = (c.month - 1) // 3 + 1
    w = c.vol_ddu
    g = c.assign(pv_w=c.pv * w, rddu_w=c.r_ddu * w, pvnon_w=c.pv_non * c.vol_non,
                 rnon_w=c.r_non * c.vol_non).groupby(["region", "year", "q"])
    Q = g.agg(vol_all=("vol_all", "sum"), vol_ddu=("vol_ddu", "sum"), vol_non=("vol_non", "sum"),
              n_all=("n_all", "sum"), n_ddu=("n_ddu", "sum"), pv_w=("pv_w", "sum"),
              rddu_w=("rddu_w", "sum"), pvnon_w=("pvnon_w", "sum"), rnon_w=("rnon_w", "sum"),
              r_b=("r_b", "mean"), key=("key", "mean"), months=("month", "count")).reset_index()
    Q["pv"] = Q.pv_w / Q.vol_ddu
    Q["pv_non"] = Q.pvnon_w / Q.vol_non
    Q["r_ddu"] = Q.rddu_w / Q.vol_ddu
    Q["r_non"] = Q.rnon_w / Q.vol_non
    Q["share_ddu"] = Q.vol_ddu / Q.vol_all
    Q["share_ddu_n"] = Q.n_ddu / Q.n_all
    Q["loan_ddu"] = Q.vol_ddu / Q.n_ddu            # млн ₽ на договор
    Q = Q.drop(columns=["pv_w", "rddu_w", "pvnon_w", "rnon_w"])

    p = pd.read_csv("prices_q.csv")
    p["region"] = p.centre.map(lambda x: ALIAS.get(x, x))
    d = p.merge(Q, on=["region", "year", "q"], how="left")
    d["t"] = d.year * 4 + d.q - 1
    d["tq"] = d.year.astype(str) + "Q" + d.q.astype(str)
    d["lp1"] = np.log(d.perv); d["lp2"] = np.log(d.vtor); d["lgap"] = d.lp1 - d.lp2
    return d

if __name__ == "__main__":
    d = build()
    d.to_csv("panel_q.csv", index=False)
    print(d.shape, d.pv.isna().sum(), "без данных ЦБ")
    print(d.groupby("tq")[["pv", "r_ddu", "r_b", "share_ddu", "lgap"]].median().round(3).to_string())
