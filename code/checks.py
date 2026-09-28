# -*- coding: utf-8 -*-
"""Проверки пересобранного ряда RPGI перед публикацией.

Сравнивает текущие файлы в data/ с последней опубликованной версией (по умолчанию HEAD
в git) и пишет отчёт в Markdown — он становится описанием pull request.

Ошибки (публиковать нельзя, pull request открывается черновиком):
  G1  центр, который был в ряду за год, из него пропал — так в v0.3.0 выпадала Кострома;
  G2  число центров за год вне допустимого диапазона;
  G3  разрыв не число или вне правдоподобных границ;
  G4  значение прошлых лет изменилось, хотя книги Росстата за этот год не менялись, —
      значит, изменился разбор, а не данные;
  S1  из ряда доли выдач пропал месяц, в ряду появилась дыра или доля вне 0–100 %;
  R1  из ряда ставок пропал месяц.
Предупреждения (публиковать можно, но нужно прочитать):
  G5  значение изменилось вместе с книгой Росстата — пересмотр источника, в CHANGELOG
      отдельной строкой;
  G6  скачок разрыва центра за год больше порога;
  S2, R2  пересмотр ЦБ опубликованных месяцев.
Справочно: новые годы, центры и месяцы, изменение корреляций по Татарстану.

Запуск:
  python code/checks.py                          # сравнить с HEAD, отчёт в stdout
  python code/checks.py --baseline-ref v0.4.0 --report report.md
Код возврата: 0 — ошибок нет, 1 — есть ошибки.
"""
import argparse, csv, io, json, math, os, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP = "data/rosstat_centres_gap_2021_2026.csv"
SHARE = "data/cbr_rf_rt_ddu_share_2019_2026.csv"
RATES = "data/cbr_rates_rt_2021_2026.csv"
CORR = "data/rpgi_v0.1.0_correlations.csv"
H_ROSSTAT = "data/sources/rosstat/hashes_rosstat.json"

CENTRES_MIN, CENTRES_MAX = 65, 85      # в опубликованном ряду 72–77
GAP_MIN, GAP_MAX = -60.0, 200.0        # в опубликованном ряду от −19 до +99 %
JUMP_PP = 40.0                         # скачок разрыва центра за год, п. п.
TOL_GAP = 1e-3                         # разрыв хранится с четырьмя знаками
TOL_SHARE = 0.05                       # доля округлена до 0,1 п. п.
TOL_RATE = 0.005
MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
          "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
LIST_LIMIT = 15


def git_show(ref, path):
    try:
        return subprocess.run(["git", "-C", BASE, "show", "%s:%s" % (ref, path)],
                              check=True, capture_output=True).stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        return None


def read_now(path):
    p = os.path.join(BASE, path)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def rows(text, delim):
    return list(csv.DictReader(io.StringIO(text), delimiter=delim)) if text else []


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


class Report:
    def __init__(self):
        self.errors, self.warnings, self.info = [], [], []

    def err(self, code, msg, items=None):
        self.errors.append((code, msg, items or []))

    def warn(self, code, msg, items=None):
        self.warnings.append((code, msg, items or []))

    def note(self, msg):
        self.info.append(msg)

    def markdown(self, ref):
        out = ["## Проверки RPGI", "",
               "Сравнение с опубликованной версией `%s`." % ref, ""]
        if self.errors:
            out.append("**Итог: есть ошибки, публиковать нельзя.** Pull request открыт черновиком.")
        elif self.warnings:
            out.append("**Итог: ошибок нет, есть предупреждения** — прочитать перед merge.")
        else:
            out.append("**Итог: ошибок и предупреждений нет.**")
        for title, block in (("Ошибки", self.errors), ("Предупреждения", self.warnings)):
            if not block:
                continue
            out += ["", "### " + title]
            for code, msg, items in block:
                out.append("- **%s** %s" % (code, msg))
                for it in items[:LIST_LIMIT]:
                    out.append("  - " + it)
                if len(items) > LIST_LIMIT:
                    out.append("  - … и ещё %d" % (len(items) - LIST_LIMIT))
        if self.info:
            out += ["", "### Справочно"] + ["- " + m for m in self.info]
        return "\n".join(out) + "\n"


def changed_rosstat_books(ref):
    """Имена книг Росстата, у которых sha256 отличается от опубликованной версии."""
    def load(text):
        if not text:
            return {}
        return {os.path.basename(e["file"]): e["sha256"] for e in json.loads(text).get("файлы", [])}
    old, new = load(git_show(ref, H_ROSSTAT)), load(read_now(H_ROSSTAT))
    return {n for n in set(old) | set(new) if old.get(n) != new.get(n)}


def check_gap(ref, rep):
    old = rows(git_show(ref, GAP), ";")
    new = rows(read_now(GAP), ";")
    if not new:
        rep.err("G0", "нет файла %s — сборка ряда не отработала" % GAP)
        return
    changed_books = changed_rosstat_books(ref)
    o = {(r["year"], r["centre"]): r for r in old}
    n = {(r["year"], r["centre"]): r for r in new}

    lost = sorted(k for k in o if k not in n)
    if lost:
        rep.err("G1", "из ряда пропали центры (%d) — проверить разбор книги, в том числе сноски в названиях:" % len(lost),
                ["%s · %s" % k for k in lost])

    by_year = {}
    for (y, c) in n:
        by_year.setdefault(y, []).append(c)
    for y in sorted(by_year):
        k = len(by_year[y])
        if not CENTRES_MIN <= k <= CENTRES_MAX:
            rep.err("G2", "%s год: %d центров, допустимо %d–%d" % (y, k, CENTRES_MIN, CENTRES_MAX))

    bad = []
    for k, r in n.items():
        g = num(r["gap_pct"])
        if g is None or not GAP_MIN <= g <= GAP_MAX:
            bad.append("%s · %s: %s" % (k[0], k[1], r["gap_pct"]))
    if bad:
        rep.err("G3", "разрыв не число или вне границ %g…%g %%:" % (GAP_MIN, GAP_MAX), sorted(bad))

    drift, revised = [], []
    for k in sorted(set(o) & set(n)):
        a, b = num(o[k]["gap_pct"]), num(n[k]["gap_pct"])
        if a is None or b is None or abs(a - b) <= TOL_GAP:
            continue
        srcs = {o[k]["src_perv"], o[k]["src_vtor"], n[k]["src_perv"], n[k]["src_vtor"]}
        line = "%s · %s: %.4f → %.4f" % (k[0], k[1], a, b)
        (revised if srcs & changed_books else drift).append(line)
    if drift:
        rep.err("G4", "изменились прошлые значения при неизменных книгах Росстата — изменился разбор:", drift)
    if revised:
        rep.warn("G5", "пересмотр по новой редакции книг Росстата (%d значений) — в CHANGELOG отдельной строкой:" % len(revised), revised)

    jumps = []
    for (y, c), r in n.items():
        prev = n.get((str(int(y) - 1), c))
        a, b = num(prev["gap_pct"]) if prev else None, num(r["gap_pct"])
        if a is not None and b is not None and abs(b - a) > JUMP_PP and (y, c) not in o:
            jumps.append("%s · %s: %.1f → %.1f %%" % (y, c, a, b))
    if jumps:
        rep.warn("G6", "скачок разрыва больше %g п. п. за год в новых значениях:" % JUMP_PP, sorted(jumps))

    new_years = sorted({y for y, _ in n} - {y for y, _ in o})
    if new_years:
        rep.note("новые годы в ценовом ряду: %s" % ", ".join(new_years))
    added = sorted(k for k in n if k not in o and k[0] not in new_years)
    if added:
        rep.note("новые центры в прежних годах: " + "; ".join("%s · %s" % k for k in added[:LIST_LIMIT]))
    if changed_books:
        rep.note("изменившиеся книги Росстата: " + ", ".join(sorted(changed_books)))
    rep.note("ценовой ряд: %d наблюдений (было %d), по годам: %s" % (
        len(n), len(o), ", ".join("%s — %d" % (y, len(by_year[y])) for y in sorted(by_year))))


def month_key(label):
    name, year = label.rsplit(" ", 1)
    return int(year), MONTHS.index(name) + 1


def check_share(ref, rep):
    old = {r["месяц"]: r for r in rows(git_show(ref, SHARE), ",")}
    new = {r["месяц"]: r for r in rows(read_now(SHARE), ",")}
    if not new:
        rep.err("S0", "нет файла %s — сборка доли выдач не отработала" % SHARE)
        return
    lost = [m for m in old if m not in new]
    if lost:
        rep.err("S1", "из ряда доли выдач пропали месяцы:", lost)
    keys = sorted(month_key(m) for m in new)
    holes = []
    for (y1, m1), (y2, m2) in zip(keys, keys[1:]):
        if (y2 * 12 + m2) - (y1 * 12 + m1) != 1:
            holes.append("%02d.%d → %02d.%d" % (m1, y1, m2, y2))
    if holes:
        rep.err("S1", "в ряду доли выдач дыры между месяцами:", holes)
    out = []
    for m, r in new.items():
        for col in ("РФ_доля_ДДУ_проц", "РТ_доля_ДДУ_проц"):
            v = num(r.get(col))
            if r.get(col) and (v is None or not 0 <= v <= 100):
                out.append("%s, %s: %s" % (m, col, r.get(col)))
    if out:
        rep.err("S1", "доля выдач вне 0–100 %:", out)
    rev = []
    for m in old:
        if m not in new:
            continue
        for col in ("РФ_доля_ДДУ_проц", "РТ_доля_ДДУ_проц"):
            a, b = num(old[m].get(col)), num(new[m].get(col))
            if a is not None and b is not None and abs(a - b) > TOL_SHARE:
                rev.append("%s, %s: %.1f → %.1f" % (m, col, a, b))
    if rev:
        rep.warn("S2", "ЦБ пересмотрел опубликованные месяцы (%d значений):" % len(rev), rev)
    added = [m for m in new if m not in old]
    if added:
        last = max(new, key=month_key)
        rep.note("доля выдач под ДДУ: добавлены месяцы %s; последний — %s: РФ %s %%, Татарстан %s %%"
                 % (", ".join(sorted(added, key=month_key)), last,
                    new[last]["РФ_доля_ДДУ_проц"], new[last]["РТ_доля_ДДУ_проц"]))


def check_rates(ref, rep):
    old = {(r["year"], r["month"]): r for r in rows(git_show(ref, RATES), ";")}
    new = {(r["year"], r["month"]): r for r in rows(read_now(RATES), ";")}
    if not new:
        rep.err("R0", "нет файла %s — сборка ставок не отработала" % RATES)
        return
    lost = ["%s.%s" % (m, y) for (y, m) in old if (y, m) not in new]
    if lost:
        rep.err("R1", "из ряда ставок пропали месяцы:", lost)
    rev = []
    for k in set(old) & set(new):
        for col in ("rate_izhk_all_pct", "rate_izhk_ddu_pct"):
            a, b = num(old[k].get(col)), num(new[k].get(col))
            if a is not None and b is not None and abs(a - b) > TOL_RATE:
                rev.append("%s.%s, %s: %.2f → %.2f" % (k[1], k[0], col, a, b))
    if rev:
        rep.warn("R2", "ЦБ пересмотрел опубликованные ставки (%d значений):" % len(rev), sorted(rev))
    if len(new) > len(old):
        rep.note("ставки по Татарстану: добавлено месяцев — %d" % (len(new) - len(old)))


def check_corr(ref, rep):
    old = {r["window"]: r for r in rows(git_show(ref, CORR), ";")}
    new = {r["window"]: r for r in rows(read_now(CORR), ";")}
    for w, r in new.items():
        o = old.get(w)
        if o and (o["corr_levels"], o["corr_first_diff"]) != (r["corr_levels"], r["corr_first_diff"]):
            rep.note("корреляция по Татарстану (%s): уровни %s → %s, разности %s → %s" % (
                r["window_label"], o["corr_levels"], r["corr_levels"], o["corr_first_diff"], r["corr_first_diff"]))


def main():
    ap = argparse.ArgumentParser(description="Проверки ряда RPGI перед публикацией")
    ap.add_argument("--baseline-ref", default="HEAD", help="с какой версией сравнивать (git ref)")
    ap.add_argument("--report", help="записать отчёт в файл Markdown")
    ap.add_argument("--github-output", action="store_true", help="записать ok=true|false в $GITHUB_OUTPUT")
    args = ap.parse_args()

    rep = Report()
    check_gap(args.baseline_ref, rep)
    check_share(args.baseline_ref, rep)
    check_rates(args.baseline_ref, rep)
    check_corr(args.baseline_ref, rep)
    md = rep.markdown(args.baseline_ref)
    print(md)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md)
    if args.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("ok=%s\n" % ("false" if rep.errors else "true"))
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
