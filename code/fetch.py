# -*- coding: utf-8 -*-
"""Сбор первоисточников RPGI: таблицы ИЖК Банка России и книги цен Росстата.

Что делает:
  1. Скачивает шесть таблиц ЦБ (02_10, 02_11, 02_13, 02_15, 02_16, 02_17) — они лежат
     под постоянными именами и перезаписываются ЦБ при каждом обновлении.
  2. Ищет книги Росстата за текущий и прошлый год по шаблону имени
     (sred_cen_{perv|vtor}_{1..4}kv-{год}.xlsx): новые издания и пересмотры уже лежащих.
  3. Каждый файл проверяет (это книга xlsx, а не страница ошибки, и открывается openpyxl),
     считает sha256 и сравнивает с хеш-файлом. Совпало — файл не трогается.
  4. Изменившиеся и новые файлы кладёт на место и сам обновляет hashes_cbr.json
     и hashes_rosstat.json. Ручной записи хешей больше нет.

Результат печатается и пишется в JSON-отчёт (--report). Код возврата: 0 — всё скачано или
ничего не изменилось, 2 — хотя бы один обязательный файл ЦБ не скачался. Недоступность
Росстата не валит запуск (обновление ЦБ идёт отдельно), а попадает в отчёт как предупреждение.
При --github-output в $GITHUB_OUTPUT пишется changed=true|false.

Запуск:
  python code/fetch.py                     # скачать и обновить
  python code/fetch.py --dry-run           # только сравнить, ничего не записывать
  python code/fetch.py --only cbr          # только ЦБ (или --only rosstat)
  python code/fetch.py --mirror URL        # брать файлы с зеркала: URL/<хост>/<путь>

Зависимости: Python 3.9+, openpyxl.
"""
import argparse, datetime as dt, hashlib, io, json, os, sys, time, urllib.error, urllib.request, zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(BASE, "code", "sources.json")
UA = "RPGI-fetch/1.0 (+https://github.com/rav11l/rpgi)"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def remap(url, mirror):
    """https://www.cbr.ru/a/b.xlsx → <mirror>/www.cbr.ru/a/b.xlsx"""
    if not mirror:
        return url
    rest = url.split("://", 1)[1]
    return mirror.rstrip("/") + "/" + rest


def download(url, tries=3, timeout=60):
    """Возвращает (байты, None) или (None, причина). 404 — не ошибка сети, а отсутствие файла."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(), None
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):
                return None, "HTTP %d" % e.code
            last = "HTTP %d" % e.code
        except Exception as e:  # сеть, таймаут, TLS
            last = "%s: %s" % (type(e).__name__, e)
        time.sleep(2 * (i + 1))
    return None, last


def valid_xlsx(data):
    """Книга xlsx — это zip с xl/workbook.xml, которую открывает openpyxl.
    Защищает от страниц-заглушек, которые сайты отдают с кодом 200."""
    if not data or data[:2] != b"PK":
        return False, "не zip (вероятно, HTML-страница вместо файла)"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if "xl/workbook.xml" not in z.namelist():
                return False, "zip без xl/workbook.xml"
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
        n = len(wb.sheetnames)
        wb.close()
        if n == 0:
            return False, "в книге нет листов"
    except Exception as e:
        return False, "не открывается: %s" % e
    return True, ""


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_atomic(path, data):
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def check_one(name, url, local_path, known_sha, required, args, log):
    data, err = download(remap(url, args.mirror))
    rec = {"file": name, "url": url, "required": required}
    if data is None:
        rec["status"] = "failed" if required or not err.startswith("HTTP 404") else "absent"
        rec["reason"] = err
        log.append(rec)
        return None
    ok, why = valid_xlsx(data)
    if not ok:
        # у ЦБ это ошибка; у Росстата — «не книга»: либо файла нет и сайт отдал заглушку
        # с кодом 200, либо адрес сменился. В отчёт идёт отдельной строкой, запуск не валит.
        rec["status"] = "failed" if required else "not_xlsx"
        rec["reason"] = why
        log.append(rec)
        return None
    h = sha256(data)
    rec.update(sha256=h, bytes=len(data))
    if known_sha == h:
        rec["status"] = "unchanged"
    else:
        rec["status"] = "new" if known_sha is None else "changed"
        rec["previous_sha256"] = known_sha
        if not args.dry_run:
            write_atomic(local_path, data)
    log.append(rec)
    return rec


def fetch_cbr(cfg, args, log, today):
    c = cfg["cbr"]
    hpath = os.path.join(BASE, c["hashes"])
    hashes = load_json(hpath)
    known = hashes.get("sha256", {})
    changed = False
    for name in c["files"]:
        rec = check_one(name, c["base_url"] + name, os.path.join(BASE, c["dir"], name),
                        known.get(name), True, args, log)
        if rec and rec["status"] in ("new", "changed"):
            known[name] = rec["sha256"]
            changed = True
    if changed and not args.dry_run:
        hashes["sha256"] = known
        hashes["обновлено"] = today
        save_json(hpath, hashes)


def fetch_rosstat(cfg, args, log, today):
    c = cfg["rosstat"]
    hpath = os.path.join(BASE, c["hashes"])
    hashes = load_json(hpath)
    entries = hashes.setdefault("файлы", [])
    paths_fixed = any(not e["file"].startswith(c["dir"] + "/") for e in entries)
    # пути в хеш-файле — относительно корня репозитория (раньше указывали на локальную папку)
    for e in entries:
        e["file"] = c["dir"] + "/" + os.path.basename(e["file"])
    by_name = {os.path.basename(e["file"]): e for e in entries}
    year_now = int(args.year or dt.date.today().year)
    changed = False
    for year in range(year_now - c.get("years_back", 1), year_now + 1):
        for market in c["markets"]:
            for q in c["quarters"]:
                name = c["name_template"].format(market=market, q=q, year=year)
                prev = by_name.get(name)
                rec = check_one(name, c["base_url"] + name, os.path.join(BASE, c["dir"], name),
                                prev["sha256"] if prev else None, False, args, log)
                if rec and rec["status"] in ("new", "changed"):
                    entry = {"file": c["dir"] + "/" + name, "bytes": rec["bytes"], "sha256": rec["sha256"]}
                    if prev:
                        prev.update(entry)
                    else:
                        entries.append(entry)
                        by_name[name] = entry
                    changed = True
    if (changed or paths_fixed) and not args.dry_run:
        entries.sort(key=lambda e: e["file"])
        if changed:
            hashes["обновлено"] = today
        save_json(hpath, hashes)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", choices=["cbr", "rosstat"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--mirror", help="зеркало вида http://host:port; файл ищется по <mirror>/<хост>/<путь>")
    ap.add_argument("--year", help="текущий год для поиска книг Росстата (по умолчанию — по часам)")
    ap.add_argument("--report", help="куда записать JSON-отчёт")
    ap.add_argument("--github-output", action="store_true", help="записать changed=... в $GITHUB_OUTPUT")
    args = ap.parse_args()

    cfg = load_json(CONFIG)
    today = dt.date.today().isoformat()
    log = []
    if args.only in (None, "cbr"):
        fetch_cbr(cfg, args, log, today)
    if args.only in (None, "rosstat"):
        fetch_rosstat(cfg, args, log, today)

    changed = [r for r in log if r["status"] in ("new", "changed")]
    failed = [r for r in log if r["status"] == "failed" and r["required"]]
    warned = [r for r in log if r["status"] == "failed" and not r["required"]]
    for r in log:
        if r["status"] == "absent":
            continue
        extra = r.get("reason") or r.get("sha256", "")[:12]
        print("%-9s %-40s %s" % (r["status"], r["file"], extra))
    absent = sum(r["status"] == "absent" for r in log)
    not_xlsx = [r for r in log if r["status"] == "not_xlsx"]
    print("\nизменилось: %d, ошибок ЦБ: %d, недоступно у Росстата: %d, не книга по адресу Росстата: %d, "
          "не опубликовано (Росстат): %d%s"
          % (len(changed), len(failed), len(warned), len(not_xlsx), absent, "  [dry-run: ничего не записано]" if args.dry_run else ""))

    if args.report:
        save_json(args.report, {"date": today, "dry_run": args.dry_run, "files": log})
    if args.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("changed=%s\n" % ("true" if changed else "false"))
            f.write("failed=%s\n" % ("true" if failed else "false"))
            f.write("rosstat_unreachable=%s\n" % ("true" if warned else "false"))
    sys.exit(2 if failed else 0)


if __name__ == "__main__":
    main()
