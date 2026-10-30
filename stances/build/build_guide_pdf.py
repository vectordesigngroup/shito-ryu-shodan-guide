#!/usr/bin/env python3
"""Rebuild shito-ryu-shodan-study-guide.pdf (repo root) from index.html.

Takes the requirements, kata, kihon (with the stance picture grid), study plan
and the written-test Q&A (the inline JSON array in index.html), applies the
Dojo look, and prints it with headless Chrome. Run from anywhere:
    python3 stances/build/build_guide_pdf.py
"""
import json, os, re, subprocess, tempfile, html, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser") or "google-chrome"
src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

def section(sid):
    m = re.search(r"<section id=['\"]%s['\"]>(.*?)</section>" % sid, src, re.S)
    return m.group(1)

def clean(h):
    h = re.sub(r"<label class=['\"]ck['\"].*?</label>", "", h, flags=re.S)       # "Can perform" boxes
    h = re.sub(r"<input[^>]*>", "", h)
    h = re.sub(r"(src|href)=\"(stances/[^\"]+)\"", lambda m: '%s="file://%s/%s"' % (m.group(1), ROOT, m.group(2)), h)
    h = re.sub(r'<a href="file://[^"]*\.png">(<img[^>]*>)</a>', r"\1", h)       # no links in print
    h = h.replace('loading="lazy"', "")
    h = h.replace(" Tap a card to see it full size. ", " ")
    h = re.sub(r'<a href="stance-reference-sheet.pdf">.*?</a>', "A one-page version is in stance-reference-sheet.pdf on the site.", h)
    return h

i = src.index('[{"c":')
qa, _ = json.JSONDecoder().raw_decode(src[i:])
qa_html = "<ol class='qa'>" + "".join(
    "<li><b>%s</b><br><span>%s</span></li>" % (html.escape(x["q"]), html.escape(x["a"])) for x in qa) + "</ol>"

CSS = """
@page{size:Letter;margin:0.55in 0.6in}
body{font-family:'Source Sans Pro','Source Sans 3','Noto Sans',sans-serif;color:#2b3a4a;font-size:10.5pt;line-height:1.35;margin:0}
h1{font-family:Oxygen,sans-serif;background:#004a87;color:#fff;border-bottom:4px solid #FDBF17;padding:10px 14px;margin:0 0 4px;font-size:19pt}
.sub{font-size:9.5pt;color:#4a5b6c;margin:0 0 8px}
h2{font-family:Oxygen,sans-serif;color:#004a87;border-bottom:2px solid #FDBF17;padding-bottom:2px;margin:16px 0 6px;font-size:14pt;break-after:avoid}
h3{font-family:Oxygen,sans-serif;color:#004a87;font-size:11.5pt;margin:12px 0 4px;break-after:avoid}
h4{font-family:Oxygen,sans-serif;color:#004a87;font-size:11pt;margin:10px 0 2px;break-after:avoid}
.two{columns:2}.kg{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.kc{border:1px solid #cdd8e4;border-radius:6px;padding:5px 7px;font-size:9.5pt;break-inside:avoid}
.kc .n{display:inline-block;background:#FDBF17;color:#004985;border-radius:10px;padding:0 6px;margin-right:4px;font-weight:700}
table{border-collapse:collapse;width:100%;font-size:8.6pt}td,th{border:1px solid #cdd8e4;padding:3px 5px;vertical-align:top}th{background:#e8eff7;color:#004985}tr{break-inside:avoid}
.stgrid{display:grid;grid-template-columns:1fr;gap:10px;margin:6px 0;justify-items:center}.stf{margin:0;border:1px solid #cdd8e4;border-radius:6px;overflow:hidden;break-inside:avoid}
.stf{width:5.7in}.stf img{display:block;width:100%}.stf figcaption{display:none}
.stnote{font-size:9.5pt}ul.cf li{color:#7a1f1f}
.qa{padding-left:22px;columns:1}.qa li{margin:0 0 5px;break-inside:avoid}.qa span{color:#0a5a1f}
.plan{list-style:none;padding-left:0}.plan li{margin:3px 0}
footer{margin-top:14px;font-size:8.5pt;color:#4a5b6c;border-top:2px solid #FDBF17;padding-top:5px}
.pb{break-before:page}
"""
body = ("<h1>Katsu Dojo Shito-Ryu Black Belt (Shodan) Study Guide</h1>"
        "<p class='sub'>Based on the Katsu Dojo Digital Textbook (katsudojo.com). An unofficial study aid; your Sensei's instructions always come first.</p>"
        + "<section>" + clean(section("req")) + "</section>"
        + "<section>" + clean(section("kata")) + "</section>"
        + "<section class='pb'>" + clean(section("kihon")) + "</section>"
        + "<section>" + clean(section("plan")) + "</section>"
        + "<section class='pb'><h2>Written Test Questions &amp; Answers</h2>" + qa_html + "</section>"
        + "<footer>Based on the Katsu Dojo Digital Textbook (katsudojo.com). An unofficial study aid; your Sensei's instructions always come first.</footer>")
doc = "<!doctype html><html><head><meta charset='utf-8'><title>Katsu Dojo Shito-Ryu Black Belt (Shodan) Study Guide</title><style>%s</style></head><body>%s</body></html>" % (CSS, body)
tmp = tempfile.mkdtemp(); p = os.path.join(tmp, "guide.html"); open(p, "w", encoding="utf-8").write(doc)
out = os.path.join(ROOT, "shito-ryu-shodan-study-guide.pdf")
subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                "--print-to-pdf=" + out, "file://" + p], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("guide pdf", out)
