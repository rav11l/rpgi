# Builds Tilda T123 blocks for digitaleconomylab.ru/wp-2026-07
# blockA: CSS + nav + head + short bilingual version with schemes
# blockB: full text RU ; blockC: full text EN + pager + footer + script
import re, json, os
D = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(D)

def body(fn):
    t = open(os.path.join(P, fn), encoding='utf-8').read()
    t = t.replace('<body>', '').replace('</body>', '').replace('</html>', '')
    # drop header parts duplicated by page head
    t = re.sub(r'<div class="top">.*?</div>', '', t, count=1, flags=re.S)
    t = re.sub(r'<h1>.*?</h1>', '', t, count=1, flags=re.S)
    t = re.sub(r'<div class="subtitle">.*?</div>', '', t, count=1, flags=re.S)
    t = re.sub(r'<div class="author">.*?</div>', '', t, count=1, flags=re.S)
    t = re.sub(r'<p class="end">.*?</p>', '', t, flags=re.S)
    t = t.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
    return t.strip().replace("в подготовленный выпуск RPGI v0.8.0", "в опубликованный выпуск RPGI v0.8.0 (DOI 10.5281/zenodo.23975773)").replace("the prepared RPGI v0.8.0 release", "the published RPGI v0.8.0 release (DOI 10.5281/zenodo.23975773)")

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=Inter:wght@400;500;600&display=swap">'

CSS = r"""<style>
.dglwp7{--paper:#FBFAF7;--ink:#15181C;--muted:#5F6873;--line:#E2DED6;--line-soft:#EFEBE3;--accent:#1D3C5C;--accent-soft:#F0F3F7;--amber:#8A5A12;--amber-soft:#FBF4E7;--green:#2C5F44;--green-soft:#EDF4F0;--grey:#B9B4AA;
--serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;--wrap:760px;
background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16.5px;line-height:1.62;display:block;-webkit-font-smoothing:antialiased}
.dglwp7,.dglwp7 *,.dglwp7 *::before,.dglwp7 *::after{box-sizing:border-box}
.dglwp7 h1,.dglwp7 h2,.dglwp7 h3,.dglwp7 p,.dglwp7 ul,.dglwp7 ol,.dglwp7 li,.dglwp7 table,.dglwp7 th,.dglwp7 td,.dglwp7 figure,.dglwp7 figcaption,.dglwp7 button{margin:0;padding:0;border:0;color:inherit;background:none;font:inherit;text-align:left}
.dglwp7 ul,.dglwp7 ol{list-style:none}
.dglwp7 table{border-collapse:collapse;width:100%}
.dglwp7 a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(29,60,92,.3);overflow-wrap:anywhere}
.dglwp7 a:hover{border-bottom-color:var(--accent)}
.dglwp7 b,.dglwp7 strong{font-weight:600}
.dglwp7 i,.dglwp7 em{font-style:italic}
.dglwp7.dglwp7.dglwp7:not([data-lang="en"]) [data-en]{display:none}
.dglwp7.dglwp7.dglwp7[data-lang="en"] [data-ru]{display:none}
.dglwp7 .wrap{max-width:var(--wrap);margin:0 auto;padding-inline:20px}
.dglwp7 .wpnav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding-top:22px;font-size:13.5px;color:var(--muted)}
.dglwp7 .wpnav a{color:var(--muted);border-bottom-color:transparent}
.dglwp7 .wpnav a:hover{color:var(--accent)}
.dglwp7 .top{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;justify-content:space-between;padding-block:14px 16px;border-bottom:1px solid var(--line)}
.dglwp7 .kicker{font-size:11.5px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent)}
.dglwp7 .lang{display:flex;gap:2px;border:1px solid var(--line);border-radius:2px;overflow:hidden}
.dglwp7 .lang button{font-size:11.5px;font-weight:600;letter-spacing:.08em;padding:5px 11px;cursor:pointer;color:var(--muted)}
.dglwp7 .lang button[aria-pressed="true"]{background:var(--accent);color:#fff}
.dglwp7 .head{padding-block:34px 0}
.dglwp7 h1{font-family:var(--serif);font-weight:700;font-size:clamp(28px,5vw,40px);line-height:1.15;letter-spacing:-.015em;margin-bottom:14px;text-wrap:balance}
.dglwp7 .sub{font-family:var(--serif);font-style:italic;font-size:19px;line-height:1.45;color:var(--muted);margin-bottom:22px}
.dglwp7 .byline{font-size:15px}
.dglwp7 .byline .m{color:var(--muted);font-size:14px}
.dglwp7 .stamp{margin-top:16px;padding-top:14px;border-top:1px solid var(--line-soft);font-size:13px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 18px}
.dglwp7 .summary{border:1px solid var(--line);background:#fff;padding:22px 24px 16px;margin-top:30px}
.dglwp7 .lbl{display:block;font-size:11px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-bottom:12px}
.dglwp7 .summary li{position:relative;padding-left:20px;margin-bottom:10px}
.dglwp7 .summary li::before{content:"";position:absolute;left:0;top:.62em;width:8px;height:8px;background:var(--accent)}
.dglwp7 h2{font-family:var(--serif);font-weight:700;font-size:25px;line-height:1.25;margin:44px 0 14px;text-wrap:balance}
.dglwp7 h3{font-family:var(--serif);font-weight:600;font-size:19px;line-height:1.3;margin:26px 0 10px}
.dglwp7 p{margin-bottom:14px}
.dglwp7 .num{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:18px 0 10px}
.dglwp7 .num>div{background:#fff;border:1px solid var(--line);padding:14px 14px 12px}
.dglwp7 .num .v{font-family:var(--serif);font-weight:700;font-size:28px;line-height:1.1;color:var(--accent);margin:0}
.dglwp7 .num .t{font-size:13.5px;color:var(--muted);margin:6px 0 0;line-height:1.4}
.dglwp7 figure{background:#fff;border:1px solid var(--line);padding:18px 18px 12px;margin:20px 0 22px}
.dglwp7 figure .sc{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dglwp7 figure svg{display:block;width:100%;min-width:560px;height:auto}
.dglwp7 figcaption{font-size:13px;color:var(--muted);line-height:1.5;margin-top:10px}
.dglwp7 .ftitle{font-size:14.5px;font-weight:600;margin-bottom:10px}
.dglwp7 svg text{font-family:var(--sans)}
.dglwp7 .tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:14px 0 10px;max-width:100%}
.dglwp7 th,.dglwp7 td{border-bottom:1px solid var(--line);padding:8px 10px 8px 0;font-size:14.5px;vertical-align:top}
.dglwp7 th{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.dglwp7 .note{font-size:13.5px;color:var(--muted);line-height:1.5}
.dglwp7 .hl{background:var(--amber-soft);border-left:3px solid var(--amber);padding:14px 18px;margin:18px 0}
.dglwp7 .hl p:last-child{margin-bottom:0}
.dglwp7 .fullhead{margin-top:60px;padding-top:26px;border-top:2px solid var(--accent)}
.dglwp7 .fullhead h2{margin-top:0}
.dglwp7 .paper .box{background:#fff;border:1px solid var(--line);border-top:2px solid var(--accent);padding:18px 20px 10px;margin:16px 0 20px}
.dglwp7 .paper .label{font-size:11px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin:22px 0 8px}
.dglwp7 .paper .box .label{margin-top:0}
.dglwp7 .paper ol{list-style:decimal;padding-left:22px}
.dglwp7 .paper ol li{margin-bottom:8px}
.dglwp7 .paper .meta{font-size:14px}
.dglwp7 .paper .abstract-en{font-size:15px}
.dglwp7 .paper .cap{font-size:14px;font-weight:600;margin:20px 0 4px}
.dglwp7 .paper table{margin:6px 0 4px;min-width:520px}
.dglwp7 .paper td,.dglwp7 .paper th{padding-right:12px;min-width:70px}
.dglwp7 .paper .note{margin:6px 0 14px}
.dglwp7 .paper .small{font-size:14px}
.dglwp7 .paper ol.refs{font-size:14px;list-style:decimal}
.dglwp7 .paper ol.refs li,.dglwp7 .paper .small,.dglwp7 .paper .note{overflow-wrap:anywhere}
.dglwp7 .paper .v{font-style:italic}
.dglwp7 .wppager{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:50px}
.dglwp7 .wppager a{display:block;border:1px solid var(--line);background:#fff;padding:14px 16px;border-bottom:1px solid var(--line)}
.dglwp7 .wppager a:hover{border-color:var(--accent)}
.dglwp7 .wppager .dir{display:block;font-size:12px;color:var(--muted);letter-spacing:.04em}
.dglwp7 .wppager .t{display:block;font-family:var(--serif);font-weight:600;font-size:16px;color:var(--ink);margin-top:4px}
.dglwp7 .wppager .r{text-align:right}
.dglwp7 .wppager .r .dir,.dglwp7 .wppager .r .t{text-align:right}
.dglwp7 .wphome{margin-top:18px;font-size:14px}
.dglwp7 .foot{margin-top:30px;padding-block:20px 40px;border-top:1px solid var(--line);font-size:13.5px;color:var(--muted)}
@media (max-width:560px){.dglwp7{font-size:16px}.dglwp7 .num{grid-template-columns:1fr}.dglwp7 h2{font-size:22px}.dglwp7 .wppager{grid-template-columns:1fr}}
</style>"""

def svg_rates(lang):
    L = {'ru': ['Застройщик, 2027','Застройщик, с 2028','Дорогие объекты (от 300 млн)','Личный фонд','ГЖФ и его кооперативы','Для сравнения: Башкортостан','0 — освобождены','Ставки налога по категориям владельцев'],
         'en': ['Developer, 2027','Developer, from 2028','Costly objects (over 300 mln)','Personal fund','GZhF and its cooperatives','For comparison: Bashkortostan','0 — exempt','Tax rates by type of owner']}[lang]
    pct = (lambda s: s) if lang=='ru' else (lambda s: s.replace(',', '.'))
    return f'''<svg viewBox="0 0 700 270" role="img" aria-label="{L[7]}">
<g font-size="13" fill="#15181C"><text x="0" y="34">{L[0]}</text><text x="0" y="74">{L[1]}</text><text x="0" y="114">{L[2]}</text><text x="0" y="154">{L[3]}</text><text x="0" y="194">{L[4]}</text><text x="0" y="244" fill="#5F6873">{L[5]}</text></g>
<rect x="230" y="20" width="160" height="22" fill="#1D3C5C"/><rect x="230" y="60" width="320" height="22" fill="#1D3C5C"/><rect x="230" y="100" width="400" height="22" fill="#1D3C5C" opacity=".55"/><rect x="230" y="140" width="48" height="22" fill="#2C5F44"/><rect x="230" y="180" width="2" height="22" fill="#2C5F44"/><rect x="230" y="230" width="48" height="22" fill="#B9B4AA"/>
<g font-size="13" font-weight="600" fill="#15181C"><text x="398" y="36">1 %</text><text x="558" y="76">2 %</text><text x="638" y="116">{pct("2,5 %")}</text><text x="286" y="156">{pct("0,3 %")}</text><text x="240" y="196">{L[6]}</text><text x="286" y="246">{pct("0,3 %")}</text></g>
<line x1="230" y1="10" x2="230" y2="262" stroke="#E2DED6"/><line x1="0" y1="215" x2="700" y2="215" stroke="#EFEBE3"/></svg>'''

def svg_timeline(lang):
    L = {'ru': ['налога нет','налог каждый месяц, пока квартира не продана','Дом сдан и поставлен на учёт','Через 6 месяцев — регистрация права','Квартиры, проданные в эти полгода,','налог не платят вовсе','1 220 ₽ за м² в год в 2027,','2 440 ₽ за м² в год с 2028','Шкала времени непроданной квартиры'],
         'en': ['no tax','tax every month until the flat is sold','Building completed','6 months later: title registered','Flats sold during these six months','pay no tax at all','1,220 roubles/m² a year in 2027,','2,440 roubles/m² a year from 2028','Timeline of an unsold flat']}[lang]
    return f'''<svg viewBox="0 0 700 160" role="img" aria-label="{L[8]}">
<rect x="20" y="58" width="200" height="34" fill="#EDF4F0" stroke="#2C5F44"/><rect x="220" y="58" width="440" height="34" fill="#F0F3F7" stroke="#1D3C5C"/>
<g font-size="13" font-weight="600"><text x="120" y="80" text-anchor="middle" fill="#2C5F44">{L[0]}</text><text x="440" y="80" text-anchor="middle" fill="#1D3C5C">{L[1]}</text></g>
<g stroke="#15181C"><line x1="20" y1="50" x2="20" y2="100"/><line x1="220" y1="50" x2="220" y2="100"/></g>
<g font-size="12.5" fill="#15181C"><text x="20" y="38">{L[2]}</text><text x="220" y="38">{L[3]}</text></g>
<g font-size="12.5" fill="#5F6873"><text x="20" y="122">{L[4]}</text><text x="20" y="139">{L[5]}</text><text x="300" y="122">{L[6]}</text><text x="300" y="139">{L[7]}</text></g>
<path d="M660 75 l12 0 m-6 -6 l6 6 l-6 6" stroke="#1D3C5C" fill="none" stroke-width="1.5"/></svg>'''

def svg_carry(lang):
    L = {'ru': ['Деньги «заморожены»','13 % от 234 тыс. ₽','Налог с 2028 года','2 % от 122 тыс. ₽','30 400','2 440','Альтернативная стоимость денег и налог'],
         'en': ['Capital tied up','13% of 234,000 roubles','Tax from 2028','2% of 122,000 roubles','30,400','2,440','Opportunity cost versus tax']}[lang]
    return f'''<svg viewBox="0 0 700 130" role="img" aria-label="{L[6]}">
<g font-size="13" fill="#15181C"><text x="0" y="36">{L[0]}</text><text x="0" y="96">{L[2]}</text></g><g font-size="12" fill="#5F6873"><text x="0" y="52">{L[1]}</text><text x="0" y="112">{L[3]}</text></g>
<rect x="190" y="24" width="430" height="26" fill="#B9B4AA"/><rect x="190" y="84" width="35" height="26" fill="#1D3C5C"/>
<g font-size="13" font-weight="600" fill="#15181C"><text x="628" y="42">{L[4]}</text><text x="233" y="102">{L[5]}</text></g></svg>'''

def svg_budget(lang):
    L = {'ru': ['Налог на непроданные','квартиры, с 2028','Аренда земли:','разница с аукционом','≈ 0,72 (базовая оценка)','0,4–0,7 (при ставке 1,5–5 % кадастра)','Налог и недобор по аренде земли'],
         'en': ['Tax on unsold','flats, from 2028','Land lease:','gap to auction','≈ 0.72 (central estimate)','0.4–0.7 (at 1.5–5% of cadastral value)','Tax and the land-lease shortfall']}[lang]
    return f'''<svg viewBox="0 0 700 130" role="img" aria-label="{L[6]}">
<g font-size="13" fill="#15181C"><text x="0" y="36">{L[0]}</text><text x="0" y="52">{L[1]}</text><text x="0" y="96">{L[2]}</text><text x="0" y="112">{L[3]}</text></g>
<rect x="190" y="24" width="168" height="26" fill="#1D3C5C"/><rect x="190" y="84" width="93" height="26" fill="#8A5A12"/><rect x="283" y="84" width="70" height="26" fill="#8A5A12" opacity=".45"/>
<g font-size="13" font-weight="600" fill="#15181C"><text x="366" y="42">{L[4]}</text><text x="361" y="102">{L[5]}</text></g></svg>'''

def fig(title_ru, title_en, fn, cap_ru, cap_en):
    return f'''<figure><p class="ftitle" data-ru>{title_ru}</p><p class="ftitle" data-en>{title_en}</p>
<div class="sc" data-ru>{fn('ru')}</div><div class="sc" data-en>{fn('en')}</div>
<figcaption data-ru>{cap_ru}</figcaption><figcaption data-en>{cap_en}</figcaption></figure>'''

def pair(tag, ru, en, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<{tag}{c} data-ru>{ru}</{tag}><{tag}{c} data-en>{en}</{tag}>'

RV = 'https://realnoevremya.ru/articles/406607-pochemu-glavnuyu-cifru-rynka-zhilya-nevozmozhno-proverit'

short = []
S = short.append
S('''<nav class="wpnav"><a href="/"><span data-ru>← Главная</span><span data-en>← Home</span></a><span class="sep">/</span><a href="/wp">Working papers</a><span class="sep">/</span><span>WP-2026-07</span></nav>
<div class="top"><span class="kicker">Digital Economy Lab · Working Paper WP-2026-07</span><div class="lang"><button type="button" id="wp7-ru" aria-pressed="true">RU</button><button type="button" id="wp7-en" aria-pressed="false">EN</button></div></div>
<div class="head">''')
S(pair('h1','Налог на непроданные квартиры в Татарстане','A Tax on Unsold Flats in Tatarstan'))
S(pair('p','Сколько он стоит застройщикам и бюджету, как устроен у соседей и что изменит на рынке','What it costs developers and the budget, how neighbouring regions do it, and what it will change in the market','sub'))
S(pair('p','<b>Равиль Ахтямов</b>, кандидат экономических наук<br><span class="m">Digital Economy Lab, Казань · ORCID 0000-0002-0783-8573</span>','<b>Ravil Akhtyamov</b>, Candidate of Economic Sciences<br><span class="m">Digital Economy Lab, Kazan · ORCID 0000-0002-0783-8573</span>','byline'))
S('<div class="stamp"><span data-ru><b>5 ноября 2026.</b> Версия 1.6</span><span data-en><b>5 November 2026.</b> Version 1.6</span><span>CC BY 4.0</span><span><b>JEL:</b> H25, H71, R31, R38</span><span data-ru><a href="#wp7-full">Полный текст ниже</a></span><span data-en><a href="#wp7-full">Full text below</a></span></div></div>')
S(pair('p','Проект № 229-7 внесён 31.10.2026; на 05.11.2026 — предварительное рассмотрение, закон ещё не принят. Пояснительная записка и ФЭО опубликованы, но численной оценки базы, поступлений и льгот в них нет. Расчёты ниже — условные сценарии.','Bill No. 229-7 was introduced on 31 October 2026; as of 5 November it is under preliminary consideration, not enacted. The explanatory note and financial justification are published but do not quantify the base, revenue or relief costs. Calculations below are conditional scenarios.','hl'))
S('<p class="note"><a href="https://doi.org/10.5281/zenodo.23975773">RPGI v0.8.0 · Zenodo · DOI 10.5281/zenodo.23975773</a> · <a href="https://github.com/rav11l/rpgi/blob/v0.8.0/housing-tax/WP-2026-07/WP-2026-07.pdf">WP7 v1.6 PDF</a></p>')
S('<div class="summary"><span class="lbl" data-ru>Главное</span><span class="lbl" data-en>In brief</span><ul data-ru>'
  '<li>По внесённому проекту с 2027 года организации в Татарстане будут платить налог за квартиры, которыми владеют. Для застройщика это <b>1 % кадастровой стоимости в 2027 году и 2 % с 2028-го</b>.</li>'
  '<li>На метр это <b>1 220 и 2 440 рублей в год</b> — примерно 0,5 и 1 % цены новостройки в Казани. У новых домов кадастровая стоимость немного выше средней — по нашей выборке около 137 тысяч за метр, — и налог с 2028 года на метр около 2 740 рублей.</li>'
  '<li>С непроданных квартир застройщиков бюджет получит, по нашей базовой оценке, <b>около 0,36 млрд рублей в 2027 году и 0,72 млрд с 2028-го</b>. Налог распространяется и на квартиры других компаний — инвестиционные, арендные, служебные. С ними базовая оценка — <b>около 1,1 и 2,2 млрд</b>, но эта часть посчитана по общероссийской доле: данных по Татарстану нет.</li>'
  '<li>Модель предполагает ограниченное влияние на средние цены. Налог может подтолкнуть застройщиков быстрее продавать квартиры, которые долго не уходят. Но для отдельных проектов с большим непроданным остатком и долгими продажами налог вместе с содержанием пустых квартир может забрать <b>7–10 % прибыли в плохой год</b>.</li>'
  '<li>Если налог смягчат, цена для бюджета только по сегменту застройщиков — от <b>0,3 млрд рублей в год</b> (льготный год после сдачи или половина налога за первые 12 месяцев после регистрации права) до <b>0,5 млрд разово</b> (половина налога и в 2028-м). Налог у застройщика по квартирам в рассрочке сохраняется, если право собственности остаётся за застройщиком до полной оплаты.</li>'
  '<li>Главное, что даёт налог помимо денег: при публикации агрегатов станет понятно, сколько готовых квартир не продано. Сейчас этой цифры нет в открытых данных.</li></ul><ul data-en>'
  '<li>Under the submitted bill, from 2027 organisations in Tatarstan would pay tax on the flats they own. For a developer this is <b>1% of cadastral value in 2027 and 2% from 2028</b>.</li>'
  '<li>Per square metre that is <b>1,220 and 2,440 roubles a year</b> — roughly 0.5% and 1% of the price of a new-build flat in Kazan. New buildings have a slightly higher cadastral value — about 137,000 roubles per square metre in our sample — so the tax from 2028 is about 2,740 roubles per square metre.</li>'
  '<li>Our central estimate of budget revenue from developers’ unsold flats is <b>about 0.36 billion roubles in 2027 and 0.72 billion from 2028</b>. The tax also covers flats held by other companies — investment, rental and service housing. Including them, the central estimate is <b>about 1.1 and 2.2 billion</b>, but this part rests on the national share: there are no data for Tatarstan.</li>'
  '<li>The model suggests a limited effect on average prices. It may encourage developers to sell faster the flats that have been sitting unsold. But for individual projects with a large unsold remainder and slow sales, the tax together with the upkeep of empty flats may take <b>7–10% of profit in a bad year</b>.</li>'
  '<li>If the tax is softened, the cost to the budget in the developer segment alone ranges from <b>0.3 billion roubles a year</b> (a grace year after completion, or half the tax for the first 12 months after title registration) to <b>0.5 billion once</b> (half the tax in 2028 as well). Developers remain liable on instalment sales if title stays with the developer until full payment.</li>'
  '<li>Beyond the money, the tax gives something new: publishing aggregates would show how many completed flats remain unsold. That figure is not in open data today.</li></ul></div>')
S(pair('p','Шестимесячный срок подачи заявления — не налоговая льгота. Его полное использование и совпадение ввода с кадастровым учётом — допущения. Рассрочку нельзя прибавлять к остатку без исключения двойного счёта.','The six-month filing deadline is not tax relief. Its full use and coinciding completion and cadastral-registration dates are assumptions. Instalment scenarios cannot be added to inventory without excluding overlap.','note'))
S(pair('h2','Что меняется','What changes'))
S(pair('p','Сейчас квартиры на балансе организаций в Татарстане налогом не облагаются. Застройщик, у которого после сдачи дома остались непроданные квартиры, за них ничего не платит. В Москве, Петербурге, Подмосковье и на Кубани такой налог есть давно.','Today flats on organisations’ balance sheets in Tatarstan are not taxed. A developer left with unsold flats after a building is completed pays nothing on them. Moscow, St Petersburg, the Moscow Region and the Krasnodar Territory have long had such a tax.'))
S(pair('p','Проект закона меняет это с 1 января 2027 года. Налог считается от кадастровой стоимости квартиры — той, что указана в реестре недвижимости. За 2027 год платится половина, с 2028-го — полная ставка, независимо от того, когда сдан дом.','The draft law changes this from 1 January 2027. The tax is based on the flat’s cadastral value — the value recorded in the real estate register. Half is paid for 2027 and the full rate from 2028, whenever the building was completed.'))
S(fig('Кто сколько будет платить, % кадастровой стоимости в год','Who will pay what, % of cadastral value a year',svg_rates,
 'Ставка 0,3 % для личных фондов — максимум, который разрешает Налоговый кодекс; выше регион поставить не может. Освобождение относится к специализированным организациям, созданным или уполномоченным Раисом для непосредственной реализации Закона № 69-ЗРТ, и связанным кооперативам. ГЖФ — пример, не вся правовая категория.',
 'The 0.3% rate for personal funds is the maximum the Tax Code allows; the region cannot set it higher. The exemption covers specialised organisations created or authorised by the Rais for direct implementation of Law No. 69-ZRT and linked cooperatives. GZhF is an example, not the entire legal category.'))
S(pair('h2','Когда квартира начинает «стоить» налог','When a flat starts to cost tax'))
S(pair('p','Налог начисляется не с момента сдачи дома, а с того месяца, когда застройщик зарегистрирует на себя право на непроданные квартиры. На это у него по закону есть шесть месяцев после постановки дома на учёт. Понятно, что срок будет использован полностью.','Tax is charged not from completion but from the month in which the developer registers title to the unsold flats. By law it has six months after the building is entered in the cadastre to do so, and it will naturally use the full period.'))
S(fig('Путь непроданной квартиры после сдачи дома','The path of an unsold flat after completion',svg_timeline,
 'Поэтому налог ложится в основном на квартиры, которые не удаётся продать дольше полугода, — на «зависший» остаток. Что будет, если застройщик пропустит шестимесячный срок, закон, насколько удалось найти, не уточняет.',
 'So the tax falls mainly on flats that stay unsold for more than six months — the stuck remainder. As far as we could find, the law does not say what happens if a developer misses the six-month deadline.'))
S(pair('h2','Сколько это в рублях','What it means in roubles'))
S('<div class="num"><div><p class="v" data-ru>1 220 ₽</p><p class="v" data-en>1,220 ₽</p><p class="t" data-ru>за м² в год в 2027 году</p><p class="t" data-en>per m² a year in 2027</p></div><div><p class="v" data-ru>2 440 ₽</p><p class="v" data-en>2,440 ₽</p><p class="t" data-ru>за м² в год с 2028 года</p><p class="t" data-en>per m² a year from 2028</p></div><div><p class="v" data-ru>122 тыс. ₽</p><p class="v" data-en>122,000 ₽</p><p class="t" data-ru>в год за квартиру 50 м² с 2028 года</p><p class="t" data-en>a year for a 50 m² flat from 2028</p></div></div>')
S(pair('p','Расчёт сделан от средней кадастровой стоимости квартир в Казани — 122 тысячи рублей за метр. Это примерно половина цены новостройки: на первичном рынке метр в среднем стоит 234 тысячи. В новых домах кадастровая стоимость немного выше: по 58 квартирам в 21 доме, сданном в 2024–2026 годах, медиана — 137 тысяч за метр, или 55 % цены. С 2028 года она может вырасти после новой кадастровой оценки.','The calculation uses the average cadastral value of flats in Kazan — 122,000 roubles per square metre. That is about half the price of a new-build flat: on the primary market a square metre costs 234,000 roubles on average. In new buildings the cadastral value is slightly higher: for 58 flats in 21 buildings completed in 2024–2026 the median is 137,000 roubles per square metre, or 55% of the price. From 2028 it may rise after a new cadastral valuation.'))
S(pair('p','Для типового дома на 50 тысяч квадратных метров, у которого к сдаче не продано от 17 до 46 % площади, налог составит 12–32 млн рублей. Это 0,4–1 % прибыли застройщика. В плохой год, когда прибыль вдвое ниже, — до 2–4 %. Но если к сдаче не продана половина площади, а продажи растягиваются на три–четыре года, налог вместе с содержанием непроданных квартир, которое застройщик и так оплачивает, после переоценки обойдётся в 107–154 млн рублей — 3–5 % прибыли, в плохой год 7–10 %. Для таких проектов это ощутимо.','For a typical 50,000 m² building with 17–46% of floor area unsold at completion, the tax comes to 12–32 million roubles. That is 0.4–1% of the developer’s profit; in a bad year, when profit is half as large, up to 2–4%. But if half the floor area is unsold at completion and sales stretch over three to four years, the tax together with the upkeep of unsold flats, which the developer already pays, will cost 107–154 million roubles after revaluation — 3–5% of profit, 7–10% in a bad year. For such projects this is tangible.'))
S(pair('h2','Что модель говорит о ценах','What the model suggests about prices'))
S(pair('p','Деньги, вложенные в непроданную квартиру, и так стоят застройщику около 13 % в год — столько он мог бы получить, положив их на вклад. Налог добавляет к этому 1–2 %. Это ощутимо, но не настолько, чтобы менять цены на весь рынок. Тем более что налог касается только сданных домов, а основная часть предложения — дома, которые ещё строятся.','Money tied up in an unsold flat already costs a developer about 13% a year — what it could earn on deposit. The tax adds 1–2% to that. This is noticeable, but not enough to move prices across the market, especially since the tax applies only to completed buildings, while most of the supply is still under construction.'))
S(pair('p','Скорее всего, изменится другое: застройщики будут чаще предлагать скидки и рассрочки именно на квартиры в сданных домах, особенно там, где остаток большой.','What is more likely to change is that developers will offer discounts and instalment plans more often on flats in completed buildings, especially where the remainder is large.'))
S(fig('Во что обходится застройщику непроданный метр за год, ₽','What an unsold square metre costs a developer per year, roubles',svg_carry,
 'Налог добавляет к издержкам держания квартиры около 8 %. Ценовой шок он не вызывает, но продавать быстрее становится выгоднее.',
 'The tax adds about 8% to the cost of holding a flat. It causes no price shock, but selling sooner becomes more worthwhile.'))
S(pair('h2','Сколько получит бюджет и что недополучает от аренды земли','What the budget gets, and what it forgoes on land leases'))
S(pair('p','Сколько готовых квартир не продано, официально не считает никто. Мы оценили этот остаток по данным единой системы жилищного строительства (наш.дом.рф): в сданных в 2023–2026 годах домах Казани, по которым есть данные, к сдаче оставалось около 22 % площади непроданной. Отсюда базовая оценка поступлений — 0,36 млрд рублей в 2027 году и 0,72 млрд в год с 2028-го. Разброс большой, от 0,3 до 2 млрд, потому что точной цифры остатка нет. Под налог попадают и квартиры других организаций: те, что компании держат как вложение, сдают или дают сотрудникам. Сколько их в Татарстане, не публикуется. По России на юрлиц и нераспределённый фонд приходится 2 % жилья; если взять от этой доли для республики от одной восьмой до половины, это ещё 0,4–1,4 млрд рублей в 2027 году и 0,7–2,9 млрд с 2028-го, в базовом сценарии — 0,7 и 1,4 млрд.','Nobody officially counts how many completed flats remain unsold. We estimated the remainder from the unified housing construction information system (EISZhS): in Kazan buildings completed in 2023–2026 for which data exist, about 22% of floor area was unsold at completion. This gives a central revenue estimate of 0.36 billion roubles in 2027 and 0.72 billion a year from 2028. The range is wide — 0.3 to 2 billion — because the exact size of the remainder is unknown. Flats held by other organisations — as investments, for rent or for staff — are taxed too. How many there are in Tatarstan is not published. In Russia legal entities and the undistributed stock account for 2% of housing; taking one-eighth to one-half of that share for the republic adds 0.4–1.4 billion roubles in 2027 and 0.7–2.9 billion from 2028, 0.7 and 1.4 billion in the central scenario.'))
S(pair('p','Для сравнения — земля. Под строящимися жилыми комплексами Казани около 56 гектаров публичной земли в аренде. Сколько за неё платят застройщики, не публикуется. Если ставка составляет 1,5–5 % кадастровой стоимости, а не столько, сколько дают на городских аукционах, город и республика недополучают 0,4–0,7 млрд рублей в год, или 1,3–2,1 млрд за три года стройки. Это величина того же порядка, что и налог на непроданные квартиры (около 0,7 млрд в год с 2028 года).','Compare land. Housing projects under construction in Kazan stand on about 56 hectares of leased public land. What developers pay for it is not published. If the rent is 1.5–5% of cadastral value rather than what the city’s auctions achieve, the city and the republic forgo 0.4–0.7 billion roubles a year, or 1.3–2.1 billion over a three-year build. That is the same order of magnitude as the tax on unsold flats (about 0.7 billion a year from 2028).'))
S(fig('Налог и недобор по аренде земли, млрд ₽ в год (оценка)','The tax and the land-lease shortfall, billion roubles a year (estimate)',svg_budget,
 'Разница в аренде рассчитана по 56 га публичной земли под строящимися ЖК Казани: ставка 1,5–5 % кадастровой стоимости против медианы итоговой ставки 66 городских арендных аукционов (142,8 тыс. ₽ за сотку в год). На аукционах в основном небольшие участки, включая ИЖС, поэтому медиана — ориентир, а не рыночная ставка для площадок ЖК. Фактические ставки для застройщиков не публикуются; это сценарная оценка. Налог поступает в бюджет республики, аренда — собственнику земли: городу, республике или федерации.',
 'The rent difference is computed for 56 ha of public land under housing projects in Kazan: a rent of 1.5–5% of cadastral value against the median final rate of 66 city lease auctions (142,800 roubles per 100 m² a year). The auctioned plots are mostly small, including individual-housing plots, so the median is a benchmark, not a market rate for housing-project sites. Actual rents paid by developers are not published; this is a scenario estimate. The tax goes to the republic’s budget, the rent to the landowner: the city, the republic or the federal government.'))
S(pair('h2','Как у соседей','How other regions do it'))
S('<div class="tw" data-ru><table><tr><th>Регион</th><th>Ставка</th><th>Льготный период после сдачи</th></tr><tr><td>Москва</td><td>2 %</td><td>был два года, отменён с 2024</td></tr><tr><td>Санкт-Петербург</td><td>2 % с 2025</td><td>не найден</td></tr><tr><td>Московская область</td><td>2 %</td><td>один год</td></tr><tr><td>Свердловская область</td><td>1 % до 2027, затем 2 %</td><td>не найден</td></tr><tr><td>Башкортостан</td><td>0,3 %</td><td>не найден</td></tr><tr><td><b>Татарстан (проект)</b></td><td><b>1 % в 2027, затем 2 %</b></td><td><b>нет; полгода до регистрации</b></td></tr></table></div>'
  '<div class="tw" data-en><table><tr><th>Region</th><th>Rate</th><th>Grace period after completion</th></tr><tr><td>Moscow</td><td>2%</td><td>two years, abolished from 2024</td></tr><tr><td>St Petersburg</td><td>2% from 2025</td><td>not found</td></tr><tr><td>Moscow Region</td><td>2%</td><td>one year</td></tr><tr><td>Sverdlovsk Region</td><td>1% to 2027, then 2%</td><td>not found</td></tr><tr><td>Bashkortostan</td><td>0.3%</td><td>not found</td></tr><tr><td><b>Tatarstan (draft)</b></td><td><b>1% in 2027, then 2%</b></td><td><b>none; six months until registration</b></td></tr></table></div>')
S(pair('p','Для Москвы и Петербурга сверено с текстами законов, для остальных — по справочным системам и СМИ. Перечень неполный.','Moscow and St Petersburg checked against the texts of the laws; the others from legal databases and media. The list is not exhaustive.','note'))
S(pair('h2','Что сделает меру проверяемой','What would make the measure verifiable'))
S(pair('p','Налог превращает непроданный остаток в учётную величину: она появится в реестре недвижимости и в налоговой отчётности. Чтобы ей можно было пользоваться, полезны четыре вещи:','The tax turns the unsold remainder into a recorded quantity: it will appear in the real estate register and in tax returns. Four things would make it usable:'))
S('<div class="hl" data-ru><p><b>Сводные данные о налоговой базе</b> — сколько квартир, какой площади и какой кадастровой стоимости облагается, по городам и районам. Это была бы первая регулярная оценка непроданного жилья.</p><p><b>Сколько жилья на балансе других организаций</b> — площадь и кадастровая стоимость. От этой цифры зависит, получит бюджет 1 или 2–3 млрд рублей в год.</p><p><b>Оценка льготы для ГЖФ</b> — сколько налога не поступает из-за освобождения. Объём жилья на балансе фонда сейчас не публикуется.</p><p><b>Решения по оспариванию кадастровой стоимости новостроек</b> — с этого года кадастр для застройщика становится деньгами, и споров станет больше.</p></div>'
  '<div class="hl" data-en><p><b>Aggregate data on the tax base</b> — how many flats, of what floor area and cadastral value are taxed, by city and district. This would be the first regular estimate of unsold housing.</p><p><b>How much housing other organisations hold</b> — floor area and cadastral value. This figure decides whether the budget gets 1 or 2–3 billion roubles a year.</p><p><b>An estimate of the GZhF exemption</b> — how much tax is forgone because of it. The amount of housing on the fund’s books is not published today.</p><p><b>Decisions on challenges to new-build cadastral values</b> — from now on cadastral value means money for developers, and disputes will multiply.</p></div>')
S(f'<p data-ru>Почему таких данных не хватает в целом — в колонке для «Реального времени»: <a href="{RV}">«Цена вне реестров: почему главную цифру рынка жилья невозможно проверить»</a>.</p><p data-en>Why such data are missing more generally is discussed in a column for Realnoe Vremya (in Russian): <a href="{RV}">“Price outside the registers: why the key number of the housing market cannot be checked”</a>.</p>')
S('<div class="fullhead" id="wp7-full"><h2 data-ru>Полный текст работы</h2><h2 data-en>Full text of the paper</h2><p class="note" data-ru>Расчёты, источники, таблицы и ограничения. Версия 1.6: внесённый 31 октября проект № 229-7, опубликованные документы и уточнения охвата расчётов. Версия 1.5: цена вариантов смягчения налога и рассрочка (раздел 5.6), уточнение о том, что скидка 50 % относится к календарному 2027 году (раздел 2.1), и кто несёт налог (раздел 6). Версия 1.4: кадастровая стоимость новостроек по выборке из НСПД, переоценка с 2028 года, содержание непроданных квартир и сценарий большого остатка (раздел 5.5). Версия 1.3 добавила оценку по жилью прочих организаций (раздел 5.4). Расчётные файлы и выборка входят в депозит RPGI v0.7.0 (DOI 10.5281/zenodo.23598826); блок 1.5 и документы проекта № 229-7 включены в опубликованный выпуск RPGI v0.8.0 (DOI 10.5281/zenodo.23975773).</p><p class="note" data-en>Calculations, sources, tables and limitations. Version 1.6: Bill No. 229-7 introduced on 31 October, its published documents and clarified calculation scope. Version 1.5: the cost of relief options and instalment sales (Section 5.6), a clarification that the 50% reduction applies to calendar year 2027 (Section 2.1), and who bears the tax (Section 6). Version 1.4: the cadastral value of new-build flats from an NSPD sample, revaluation from 2028, upkeep of unsold flats and a large-remainder scenario (Section 5.5). Version 1.3 added an estimate for housing held by other organisations (Section 5.4). The calculation files and the sample are in the RPGI v0.7.0 deposit (DOI 10.5281/zenodo.23598826); the v1.5 block and Bill No. 229-7 documents are included in the published RPGI v0.8.0 release (DOI 10.5281/zenodo.23975773).</p></div>')

blockA = FONTS + CSS + '<div class="dglwp7" data-lang="ru"><div class="wrap">' + ''.join(short) + '</div></div>'
blockB = '<div class="dglwp7" data-lang="ru"><div class="wrap"><div class="paper" data-ru>' + body('body.html') + '</div></div></div>'
pager = ('<nav class="wppager"><a href="/wp-2026-06"><div data-ru><span class="dir">← Предыдущая · WP-2026-06</span><span class="t">Кто первым реагирует на ключевую ставку</span></div><div data-en><span class="dir">← Previous · WP-2026-06</span><span class="t">Who reacts first to the key rate</span></div></a>'
         '<a class="r" href="/wp-2026-08"><div data-ru><span class="dir">Следующая · WP-2026-08 →</span><span class="t">Нейтральны ли валютные операции Минфина</span></div><div data-en><span class="dir">Next · WP-2026-08 →</span><span class="t">Are the Finance Ministry’s FX operations neutral?</span></div></a></nav>'
         '<p class="wphome"><a href="/wp"><span data-ru>Все working papers</span><span data-en>All working papers</span></a> · <a href="/"><span data-ru>На главную Digital Economy Lab</span><span data-en>Back to Digital Economy Lab</span></a></p>'
         '<div class="foot"><span data-ru>© 2026 Digital Economy Lab. Распространяется по лицензии CC BY 4.0.</span><span data-en>© 2026 Digital Economy Lab. Distributed under the CC BY 4.0 licence.</span></div>')
SCRIPT = r"""<script>
(function(){
  function roots(){return document.querySelectorAll('.dglwp7');}
  function set(l){roots().forEach(function(r){r.setAttribute('data-lang',l);});
    var ru=document.getElementById('wp7-ru'),en=document.getElementById('wp7-en');
    if(ru){ru.setAttribute('aria-pressed',String(l==='ru'));en.setAttribute('aria-pressed',String(l==='en'));}}
  function init(){var ru=document.getElementById('wp7-ru'),en=document.getElementById('wp7-en');
    if(!ru||ru.dataset.init) return; ru.dataset.init='1';
    ru.addEventListener('click',function(){set('ru');}); en.addEventListener('click',function(){set('en');});
    function fromHost(){var l=(document.documentElement.getAttribute('lang')||'').toLowerCase();set(l.indexOf('en')===0?'en':'ru');}
    fromHost();
    try{new MutationObserver(fromHost).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});}catch(e){}}
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
</script>"""
blockC = '<div class="dglwp7" data-lang="ru"><div class="wrap"><div class="paper" data-en>' + body('body_en.html') + '</div>' + pager + '</div></div>' + SCRIPT

for n, b in [('A', blockA), ('B', blockB), ('C', blockC)]:
    open(os.path.join(D, f'wp07_block{n}.html'), 'w', encoding='utf-8').write(b)
    j = len(json.dumps([{'name': 'code', 'value': b}], ensure_ascii=False))
    bad = [c for c in b if ord(c) > 0xFFFF]
    print(n, len(b), 'json', j, 'astral', len(bad), 'email', 'yandex.ru' in b)
open(os.path.join(D, 'wp07_preview.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><body style="margin:0;background:#FBFAF7">' + blockA + blockB + blockC + '</body>')
