#!/usr/bin/env python3
"""Build the stance cards (PNG), the one-page stance reference sheet (PDF),
the figure-grid HTML snippet used by index.html, and the guide PDF.

Usage (from the repo root):   python3 stances/build/build_stances.py [cards|sheet|grid|all]
Needs: python3, google-chrome (headless) with Source Sans Pro / Oxygen / Noto Sans CJK JP fonts.
"""
import os, sys, subprocess, html, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stance_data import STANCES, SRC
from stance_render import figure, footprint, weight_bar

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "stances")
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or "google-chrome"
FOOTER = ("Names and ranks follow the Katsu Dojo Digital Textbook (katsudojo.com). An unofficial study aid; "
          "your Sensei's instructions always come first.")

CSS = """
*{box-sizing:border-box}body{margin:0;background:#fff;font-family:'Source Sans Pro','Source Sans 3',sans-serif;color:#2b3a4a}
.card{width:1200px;height:860px;position:relative;background:#fefefc;border:2px solid #004a87;overflow:hidden}
.hd{height:104px;background:#004a87;border-bottom:5px solid #FDBF17;color:#fff;display:flex;align-items:center;padding:0 30px;gap:24px}
.hd .nm{font-family:Oxygen,sans-serif;font-weight:700;font-size:46px;letter-spacing:.01em;line-height:1.05}
.hd .sub{font-size:25px;color:#dbe8f4;margin-top:4px}
.hd .kj{margin-left:auto;font-family:'Noto Sans CJK JP','Noto Sans JP',sans-serif;font-weight:700;font-size:50px;color:#FDBF17;text-align:right;line-height:1}
.hd .rk{background:#FDBF17;color:#004985;font-weight:700;font-size:19px;padding:6px 14px;border-radius:20px;white-space:nowrap}
.row{display:flex;gap:22px;padding:18px 30px 0}
.pf{width:540px;height:408px;border:2px solid #cdd8e4;border-radius:10px;background:linear-gradient(#f6f9fc,#eaf1f8);display:flex;align-items:flex-end;justify-content:center;padding:6px 10px 0;position:relative}
.pf .lab{position:absolute;left:12px;top:8px;font-weight:700;font-size:16px;color:#004985;letter-spacing:.04em;text-transform:uppercase}
.pf svg.fig{width:100%;height:100%}
.pp{width:560px;height:408px;border:2px solid #cdd8e4;border-radius:10px;overflow:hidden;position:relative}
.pp .lab{position:absolute;right:12px;top:8px;font-weight:700;font-size:16px;color:#004985;letter-spacing:.04em;text-transform:uppercase;z-index:2;background:#fbfcfeee;padding:0 4px}
.pp svg{display:block;width:560px;height:408px}
.wbar{display:flex;margin:16px 30px 0;height:46px;border-radius:23px;overflow:hidden;border:2px solid #004a87;font-weight:700;font-size:23px;color:#fff}
.wbar div{display:flex;align-items:center;justify-content:center}
.wa{background:#004a87}.wb{background:#FDBF17;color:#004985}
.bt{display:flex;gap:22px;padding:14px 30px 0}
.pts{flex:1}.pts h3,.cf h3{margin:0 0 4px;font-family:Oxygen,sans-serif;color:#004a87;font-size:21px}
.pts ul{margin:0;padding-left:22px;font-size:20px;line-height:1.26}.pts li{margin:2px 0}
.cf{width:440px;background:#fff8e6;border-left:6px solid #a11;border-radius:8px;padding:8px 14px;align-self:flex-start}
.cf h3{color:#a11}.cf ul{margin:0;padding-left:20px;font-size:17.5px;line-height:1.24;color:#4a2f00}
.cf.ok{background:#f1f7ee;border-left-color:#3a7d2a}.cf.ok h3{color:#2f6a22}.cf.ok p{margin:0;font-size:17.5px;color:#27481f}
.ft{position:absolute;left:0;right:0;bottom:0;height:34px;background:#eef3f8;border-top:2px solid #FDBF17;font-size:15.5px;color:#4a5b6c;display:flex;align-items:center;padding:0 30px}
"""

def card_html(st):
    flags = st["flags"]
    if flags:
        cf = '<div class="cf"><h3>Confirm with Sensei</h3><ul>' + "".join(f"<li>{html.escape(f)}</li>" for f in flags) + "</ul></div>"
    else:
        cf = '<div class="cf ok"><h3>Sources agree</h3><p>The Shito-ryu and general sources compared all describe this stance the same way. Your Sensei still has the last word.</p></div>'
    pts = "".join(f"<li>{html.escape(p)}</li>" for p in st["points"])
    view = "Front view" if st["view"] == "front" else "Side view"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="card">
 <div class="hd"><div><div class="nm">{html.escape(st['name'])}</div><div class="sub">{html.escape(st['english'])}</div></div>
  <div class="rk">{html.escape(st['rank'])}</div><div class="kj">{st['kanji']}</div></div>
 <div class="row">
  <div class="pf"><span class="lab">{view}</span>{figure(st)}</div>
  <div class="pp"><span class="lab">Footprints, top view</span>{footprint(st)}</div>
 </div>
 {weight_bar(st)}
 <div class="bt"><div class="pts"><h3>Key points</h3><ul>{pts}</ul></div>{cf}</div>
 <div class="ft">{html.escape(FOOTER)}</div>
</div></body></html>"""

def chrome_shot(html_path, png_path, w=1204, h=864):
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={w},{h}", "--force-device-scale-factor=1",
                    f"--screenshot={png_path}", "file://" + html_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def build_cards(only=None):
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()
    for st in STANCES:
        if only and only not in st["slug"]: continue
        p = os.path.join(tmp, st["slug"] + ".html")
        open(p, "w", encoding="utf-8").write(card_html(st))
        chrome_shot(p, os.path.join(OUT, st["slug"] + ".png"))
        print("card", st["slug"])

SHEET_CSS = """
@page{size:Letter portrait;margin:0.3in}
*{box-sizing:border-box}body{margin:0;font-family:'Source Sans Pro','Source Sans 3',sans-serif;color:#2b3a4a;font-size:9.5pt}
h1{font-family:Oxygen,sans-serif;color:#fff;background:#004a87;border-bottom:4px solid #FDBF17;margin:0;padding:8px 12px;font-size:17pt}
h1 small{font-family:'Source Sans Pro',sans-serif;font-weight:400;font-size:9.5pt;color:#dbe8f4;display:block;margin-top:1px}
.g{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:5px}
.c{border:1.5px solid #cdd8e4;border-radius:6px;padding:4px 6px;display:grid;grid-template-columns:62px 90px 1fr;gap:6px;align-items:center;height:1.24in;overflow:hidden;background:#fff}
.c .f{height:1.1in;display:flex;align-items:flex-end}.c .f svg{width:100%;height:100%}
.c .p svg{width:90px;height:auto;display:block;border:1px solid #dbe4ee}
.c .t b{font-family:Oxygen,sans-serif;color:#004a87;font-size:10pt}.c .t .k{font-family:'Noto Sans CJK JP',sans-serif;color:#7a5800;font-weight:700;font-size:9.5pt}
.c .t .e{font-size:8.5pt;color:#4a5b6c}.c .t .w{margin-top:2px;font-weight:700;color:#004985;font-size:8.5pt}
.c .t .r{margin-top:1px;font-size:7.4pt;line-height:1.13;color:#2b3a4a}.c .t .q{margin-top:1px;font-size:6.8pt;color:#a11;font-weight:600}
.n{font-size:7.2pt;color:#4a5b6c;margin-top:4px;line-height:1.3}
"""
CUE = {
 "01":"Heels touch, toes V out about 45 degrees each. Upright, legs straight.",
 "02":"Feet shoulder width, parallel. Knees soft, fists low in front.",
 "03":"Front knee over toes, back leg straight, heels about 2 shoulder widths apart, hips forward.",
 "04":"Feet about 2 shoulder widths, toes out 45 degrees, knees over toes, hips low.",
 "05":"Short zenkutsu: about 65 cm heel to heel, back leg straight, front knee hides the toes.",
 "06":"Front heel up, ball on floor. Back foot out 30 to 45 degrees, back knee bent, weight mostly back.",
 "07":"Back leg crosses behind the front leg; back knee tucks behind front knee, ball of back foot only.",
 "08":"Feet together, toes and heels touching, pointing forward. Legs straight.",
 "09":"Back knee deeply bent with most weight; front leg straight. Back foot out 90 degrees.",
 "10":"Front foot forward, back foot out 90 degrees. Front heel slides back to the back heel (an L).",
 "11":"Hourglass: shoulder-wide, toes in, knees pulled in; back toes level with front heel.",
 "12":"Front foot forward, back foot out 90 degrees. Front heel slides back to the middle of the back foot (a T).",
 "13":"Stand on one slightly bent leg; raised foot touches the standing knee.",
}
WSHORT = lambda st: f"{st['weight'][1]}% {st['weight'][0].lower()} / {st['weight'][3]}% {st['weight'][2].lower()}"

SHORTFLAG = {"01":"angle between the feet","02":"foot angle","03":"weight split, back foot angle","05":"weight and exact length",
 "06":"weight on the back leg","07":"weight split, back foot position","09":"weight, front leg bend","10":"weight, back foot angle",
 "11":"name and toe-in angle","12":"spelling and weight","13":"where the foot meets the knee","04":"","08":""}
def sheet_html():
    cells = []
    for st in STANCES:
        fl = ("Confirm with Sensei: " + SHORTFLAG[st["slug"][:2]]) if st["flags"] else ""
        cells.append(f"""<div class="c"><div class="f">{figure(st)}</div><div class="p">{footprint(st, 392, 392)}</div>
<div class="t"><b>{html.escape(st['name'])}</b> <span class="k">{st['kanji']}</span><div class="e">{html.escape(st['english'])} &middot; {html.escape(st['rank'])}</div>
<div class="w">{WSHORT(st)}</div><div class="r">{html.escape(CUE[st['slug'][:2]])}</div>{('<div class="q">'+html.escape(fl)+'</div>') if fl else ''}</div></div>""")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{SHEET_CSS}</style></head><body>
<h1>Tachikata stance reference sheet<small>All 13 stances in the Katsu Dojo shodan list. Footprint squares are 10 cm; red lines are measurements. Facing direction is up.</small></h1>
<div class="g">{''.join(cells)}</div>
<div class="n">Stances marked "Confirm with Sensei" are drawn from the Shito-ryu sources first; other sources differ on a number (weight split or foot angle). Full card for each stance: see the study guide. {html.escape(FOOTER)}</div>
</body></html>"""

def build_sheet():
    tmp = tempfile.mkdtemp(); p = os.path.join(tmp, "sheet.html")
    open(p, "w", encoding="utf-8").write(sheet_html())
    pdf = os.path.join(ROOT, "stance-reference-sheet.pdf")
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", "file://" + p], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("sheet", pdf)

def grid_html():
    items = []
    for st in STANCES:
        fl = " (confirm with Sensei)" if st["flags"] else ""
        alt = f"{st['name']} ({st['english']}): side or front figure, footprints on a 10 cm grid, weight split and key points{fl}"
        items.append(f'<figure class="stf"><a href="stances/{st["slug"]}.png"><img src="stances/{st["slug"]}.png" alt="{html.escape(alt)}" loading="lazy"></a>'
                     f'<figcaption><b>{html.escape(st["romaji"])}</b> {st["kanji"]}<br><small>{html.escape(st["english"])}</small></figcaption></figure>')
    return '<div class="stgrid">' + "".join(items) + "</div>"

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[2] if len(sys.argv) > 2 else None
    if what in ("cards", "all"): build_cards(only)
    if what in ("sheet", "all"): build_sheet()
    if what == "grid": print(grid_html())
