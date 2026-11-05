
# ---- v1.5: варианты смягчения (цена для бюджета и для проекта) и рассрочка ----
# Когортная модель: поток ввода I млн м²/год, доля остатка share, равномерная распродажа за T=2m лет,
# налог начисляется с регистрации права (ввод + d лет). Ставка r(t) зависит от календарного года и,
# в варианте «первые 12 месяцев после регистрации», от срока с регистрации. Шаг интегрирования — 1/240 года.
# В стационаре базовый вариант совпадает с функцией rt() блока v1.4 (проверка ниже).
import numpy as np
KN15, KR15, MAINT15 = 137000.0, 171000.0, 720.0
def rate(variant, cal, since_reg):
    if variant == 'ext2028':
        return 0.01 if cal < 2029 else 0.02
    if variant == 'firstyear':
        if cal < 2028: return 0.01
        return 0.01 if since_reg < 1.0 else 0.02
    return 0.01 if cal < 2028 else 0.02          # base, window12
def win(variant): return 1.0 if variant == 'window12' else 0.5
def rt_year(variant, year, share=0.22, m=1.8, K=KN15, inflow=1.0, step=1/240):
    T = 2*m; d = win(variant); tot = 0.0
    for tau in np.arange(year - T - 1, year + 1, step):          # момент ввода когорты
        A = inflow*share*step*1e6                                  # м²
        for t in np.arange(max(year, tau+d), min(year+1, tau+T), step):
            rem = A*(1-(t-tau)/T)
            tot += rem*K*rate(variant, int(np.floor(t)), t-tau-d)*step
    return tot/1e9
def proj15(variant, u, T, K=KR15, start=2028.0, step=1/1000):
    A = u*50000; d = win(variant); tax = 0.0
    for t in np.arange(d, T, step):
        tax += A*(1-t/T)*K*rate(variant, int(np.floor(start+t)), t-d)*step
    mnt = A*T/2*MAINT15
    return dict(tax_mln=tax/1e6, total_mln=(tax+mnt)/1e6, pct_crisis=(tax+mnt)/1.48e9, pct_base=(tax+mnt)/3.30e9)
V = ['base', 'ext2028', 'window12', 'firstyear']
R15 = {'check_base_2028_vs_v14': rt_year('base', 2028)}
R15['rt'] = {v: {str(y): {'K137': rt_year(v, y), 'K171_from2028': rt_year(v, y, K=(KN15 if y < 2028 else KR15))}
                 for y in [2027, 2028, 2029]} for v in V}
R15['project'] = {v: {f'u{u}_T{T}': proj15(v, u, T) for u in [0.285, 0.46] for T in [3, 4]} for v in V}
# Рассрочка с сохранением права собственности за застройщиком до полной оплаты (ст. 491 ГК РФ):
# доля q площади ввода, продаваемая так после ввода, средний срок до полной оплаты L лет.
R15['installment'] = {nm: dict(q=q, L=L, stock=1.0*q*L, y2027=1.0*q*L*1e6*KN15*0.01/1e9,
                       y2028=1.0*q*L*1e6*KN15*0.02/1e9, y2028_reval=1.0*q*L*1e6*KR15*0.02/1e9)
                      for nm, q, L in [('низкий', 0.02, 2.0), ('средний', 0.05, 2.5), ('высокий', 0.10, 3.5)]}
# Пример из СМИ: квартира 60 м², кадастровая стоимость по медиане НСПД
R15['flat60'] = {'cad': 60*KN15, 'tax2027': 60*KN15*0.01, 'tax2028': 60*KN15*0.02, 'tax2028_reval': 60*KR15*0.02}

# firstyear retains calendar-2027 relief, then discounts the first 12 months.
# window12 is a proposed tax exemption, not an existing filing deadline.
# Results cover developers only; installment estimates are not additive.
from pathlib import Path
import json
if __name__ == "__main__":
    out = Path(__file__).with_name("calc_results_v1.5.json")
    out.write_text(json.dumps(R15, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Saved", out.name)
