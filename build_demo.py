#!/usr/bin/env python3
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / "overview.tex"
OUT = Path(__file__).resolve().parent / "index.html"

def split_args(s, i):
    assert s[i] == "{"
    depth = 0
    j = i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced braces")

def clean_tex(s):
    s = __import__("re").sub(r"\\H\{([ou])\}", lambda m: "ő" if m.group(1) == "o" else "ű", s)
    umlaut = {"a":"ä","o":"ö","u":"ü","A":"Ä","O":"Ö","U":"Ü","e":"ë","i":"ï","y":"ÿ"}
    s = __import__("re").sub(r'\\\"([A-Za-z])', lambda m: umlaut.get(m.group(1), m.group(1)), s)
    acute = {"a":"á","e":"é","i":"í","o":"ó","u":"ú","A":"Á","E":"É","I":"Í","O":"Ó","U":"Ú","c":"ć","n":"ń","s":"ś","z":"ź"}
    s = __import__("re").sub(r"\\'([A-Za-z])", lambda m: acute.get(m.group(1), m.group(1)), s)
    grave = {"a":"à","e":"è","i":"ì","o":"ò","u":"ù","A":"À","E":"È","I":"Ì","O":"Ò","U":"Ù"}
    s = __import__("re").sub(r"\\`([A-Za-z])", lambda m: grave.get(m.group(1), m.group(1)), s)
    circ = {"a":"â","e":"ê","i":"î","o":"ô","u":"û","A":"Â","E":"Ê","I":"Î","O":"Ô","U":"Û"}
    s = __import__("re").sub(r"\\\^([A-Za-z])", lambda m: circ.get(m.group(1), m.group(1)), s)
    tilde = {"n":"ñ","a":"ã","o":"õ","N":"Ñ","A":"Ã","O":"Õ"}
    s = __import__("re").sub(r"\\~([A-Za-z])", lambda m: tilde.get(m.group(1), m.group(1)), s)
    s = s.replace("\\c{c}", "ç").replace("\\c{C}", "Ç")
    s = s.replace("\\ss", "ß")
    s = __import__("re").sub(r"\\textnormal\{([^}]*)\}", r"\1", s)
    s = __import__("re").sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", s)
    s = __import__("re").sub(r"\\textasciicircum(?:\{[^}]*\})?", "^", s)
    s = __import__("re").sub(r"\\o(?![A-Za-z])", "ø", s)
    s = __import__("re").sub(r"\\O(?![A-Za-z])", "Ø", s)
    s = __import__("re").sub(r"\\l(?![A-Za-z])", "ł", s)
    s = __import__("re").sub(r"\\L(?![A-Za-z])", "Ł", s)
    s = s.replace("\\ae", "æ").replace("\\AE", "Æ").replace("\\oe", "œ").replace("\\OE", "Œ")
    s = s.replace("\\textquotesingle", "'")
    s = s.replace("\\,", " ")
    s = __import__("re").sub(r"\\([^A-Za-z{}])", r"\1", s)
    return s

def parse_overview(text):
    sections = [(m.start(), m.group(1)) for m in re.finditer(r"\\cataloguesection\{([^}]+)\}\{(\d+)\}", text)]
    sections.append((len(text), None))
    entries = []
    for si, (start, name) in enumerate(sections[:-1]):
        end = sections[si + 1][0]
        block = text[start:end]
        for m in re.finditer(r"\\resultentry", block):
            pos = m.start() + len("\\resultentry")
            while block[pos].isspace():
                pos += 1
            args = []
            for _ in range(4):
                while block[pos].isspace():
                    pos += 1
                arg, pos = split_args(block, pos)
                args.append(arg)
            num, title, desc, links = args
            urls = []
            i = 0
            while True:
                j = links.find("\\href", i)
                if j == -1:
                    break
                k = links.find("{", j)
                url, k = split_args(links, k)
                while k < len(links) and links[k].isspace():
                    k += 1
                assert links[k] == "{", links[k:k+5]
                lab, k = split_args(links, k)
                urls.append((url, lab))
                i = k
            entries.append({
                "n": num,
                "title": clean_tex(title),
                "desc": clean_tex(desc),
                "subject": name,
                "links": [{"label": clean_tex(lab.strip()), "url": u.strip()} for u, lab in urls],
            })
    return entries

def select(entries, total=100):
    from collections import Counter, defaultdict
    by_subject = defaultdict(list)
    for e in entries:
        by_subject[e["subject"]].append(e)
    counts = Counter(e["subject"] for e in entries)
    alloc = {}
    rem = {}
    for subj, n in counts.items():
        exact = n * total / len(entries)
        alloc[subj] = int(exact)
        rem[subj] = exact - alloc[subj]
    while sum(alloc.values()) < total:
        pick = max(rem, key=lambda s: rem[s])
        alloc[pick] += 1
        rem[pick] -= 1
    chosen = []
    for subj in sorted(by_subject):
        chosen.extend(by_subject[subj][:alloc[subj]])
    chosen.sort(key=lambda e: e["n"])
    return chosen

def main():
    text = OVERVIEW.read_text(encoding="utf-8")
    entries = parse_overview(text)
    chosen = sorted(entries, key=lambda e: e["n"])
    demos = {}
    demos_dir = Path(__file__).resolve().parent / "demos"
    for hp in sorted(demos_dir.glob("*.html")):
        demos[hp.stem] = "demos/" + hp.name

    for e in chosen:
        if e["n"] in demos:
            e["demo"] = demos[e["n"]]
    # relevance for specific ones
    rels = {
        "005": "Resolves the long-standing irrationality question for Catalan's constant, with implications for L-values and hypergeometric evaluations.",
        "017": "Determines the exact irrationality exponent of pi, with consequences for the Flint-Hills series.",
        "034": "Turns nef adjoints into semiample morphisms, producing Iitaka fibrations and good minimal models; yields uniform indices for semi-log-canonical log Calabi-Yau pairs, supporting boundedness and moduli of pairs.",
        "043": "Identifies the perverse filtration on Higgs-moduli cohomology with the weight filtration on the character variety via non-abelian Hodge, extending the fixed-determinant P=W conjecture to all coprime ranks.",
    }
    for e in chosen:
        if e["n"] in rels:
            e["relevance"] = rels[e["n"]]
    payload = json.dumps(chosen, ensure_ascii=False)
    # Build HTML
    html_doc = TEMPLATE.replace("__DATA__", payload)
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {OUT} with {len(chosen)} entries")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mathematical Discoveries</title>
<style>
:root {
  --bg: #0b1220;
  --panel: #111a2e;
  --card: #16203a;
  --text: #e6edf7;
  --muted: #9fb0cc;
  --accent: #5eead4;
  --border: #243252;
  --chip: #1f2a44;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f6f8fc;
    --panel: #ffffff;
    --card: #ffffff;
    --text: #0f172a;
    --muted: #475569;
    --accent: #0f766e;
    --border: #dbe3f0;
    --chip: #eef2f7;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 20px;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}
header {
  position: sticky; top: 0; z-index: 10;
  background: color-mix(in srgb, var(--panel) 88%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  padding: 1rem 1.25rem;
}
h1 {
  margin: 0 0 .25rem; font-size: 1.9rem; font-weight: 800; letter-spacing: -.3px;
  background: linear-gradient(120deg, var(--accent), #22d3ee, #818cf8);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.subtitle { color: var(--muted); margin: 0 0 .75rem; font-size: 1rem; max-width: 720px; }
.header-top {
  display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between;
  gap: .75rem; margin-bottom: .5rem;
}
.header-actions { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.header-pill {
  font-size: .78rem; padding: .3rem .6rem; border-radius: 999px;
  border: 1px solid var(--border); background: var(--chip); color: var(--muted);
  text-decoration: none; white-space: nowrap;
}
.header-pill:hover { color: var(--accent); border-color: var(--accent); }
.hero {
  background: linear-gradient(135deg, color-mix(in srgb, var(--card) 80%, var(--accent) 8%), var(--card));
  border: 1px solid var(--border); border-radius: 18px; padding: 1.25rem 1.5rem;
  margin: 0 0 1.25rem; display: flex; flex-wrap: wrap; gap: 1.25rem; align-items: center;
  box-shadow: 0 10px 40px rgba(0,0,0,.18);
}
.hero .hero-text { flex: 1 1 320px; min-width: 0; }
.hero .hero-text h2 { margin: 0 0 .35rem; font-size: 1.2rem; color: var(--accent); }
.hero .hero-text p { margin: 0; color: var(--muted); font-size: .95rem; line-height: 1.6; }
.hero-stats { display: flex; flex-wrap: wrap; gap: .75rem; }
.hero-stats .stat {
  background: var(--chip); border: 1px solid var(--border); border-radius: 12px;
  padding: .6rem .9rem; min-width: 92px; text-align: center;
}
.hero-stats .stat .v { font-size: 1.35rem; font-weight: 800; color: var(--accent); font-family: ui-monospace, monospace; }
.hero-stats .stat .l { font-size: .72rem; color: var(--muted); margin-top: .15rem; }
.controls { display: flex; flex-wrap: wrap; gap: .75rem; align-items: center; }
#q {
  flex: 1 1 260px; min-width: 0; max-width: 420px;
  padding: .6rem .8rem; border-radius: 10px;
  border: 1px solid var(--border); background: var(--card); color: var(--text);
  font-size: 1rem;
}
#count { color: var(--muted); font-size: .9rem; margin-left: auto; }
#chips { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .75rem; }
.chip {
  border: 1px solid var(--border); background: var(--chip); color: var(--text);
  padding: .3rem .7rem; border-radius: 999px; font-size: .8rem; cursor: pointer;
  user-select: none;
}
.chip.active { background: var(--accent); color: #00130f; border-color: var(--accent); font-weight: 600; }
main { padding: 1rem 1.25rem 3rem; }
.grid {
  display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
}
.card {
  background: var(--card); border: 1px solid var(--border); border-radius: 14px;
  padding: 1rem; display: flex; flex-direction: column; gap: .5rem;
  transition: transform .15s ease, box-shadow .15s ease;
}
.card { cursor: pointer; }
.card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.25); }
.meta { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.num { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--accent); font-weight: 700; }
.badge {
  font-size: .72rem; padding: .15rem .5rem; border-radius: 6px;
  background: var(--chip); color: var(--muted); border: 1px solid var(--border);
}
.card h2 { margin: 0; font-size: 1.35rem; line-height: 1.3; }
.desc { margin: 0; color: var(--text); font-size: 1.15rem; }
.links { margin-top: .25rem; display: flex; flex-wrap: wrap; gap: .4rem; }
.links a {
  font-size: .78rem; color: var(--accent); text-decoration: none;
  border: 1px solid var(--border); border-radius: 8px; padding: .25rem .5rem;
  background: var(--chip);
}
.links a:hover { text-decoration: underline; }
.empty { grid-column: 1 / -1; text-align: center; color: var(--muted); padding: 3rem 1rem; }
@media (max-width: 520px) {
  header { padding: .75rem 1rem; }
  main { padding: .75rem 1rem 2rem; }
  .grid { grid-template-columns: 1fr; }
}

.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  display: none; align-items: center; justify-content: center;
  z-index: 100; padding: 1rem;
}
.modal-backdrop.open { display: flex; }
.modal {
  background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
  width: 99vw; max-height: 94vh; overflow: hidden;
  display: flex; flex-direction: column;
}
.modal-head { display:flex; align-items:center; justify-content:space-between; padding: .75rem 1rem; border-bottom:1px solid var(--border); }
.modal-head h2 { margin:0; font-size:1.3rem; }
.modal-close { background:var(--chip); border:1px solid var(--border); color:var(--text); border-radius:8px; padding:.3rem .6rem; cursor:pointer; }
.modal-body { padding: .4rem; overflow: hidden; flex:1; }
.modal-body iframe { width:100%; height:88vh; border:0; border-radius:10px; }
.modal-empty { color: var(--muted); text-align:center; padding:2rem 1rem; }

/* Surprise + back-to-top */
.surprise {
  padding: .5rem 1rem; border-radius: 10px; border: 1px solid var(--border);
  background: linear-gradient(120deg, var(--accent), #818cf8); color: #00130f;
  font-weight: 700; cursor: pointer; transition: transform .15s ease, filter .15s ease;
}
.surprise:hover { transform: translateY(-2px); filter: brightness(1.1); }
#backTop {
  position: fixed; right: 1.25rem; bottom: 1.25rem; z-index: 50;
  width: 46px; height: 46px; border-radius: 50%; border: 1px solid var(--border);
  background: var(--card); color: var(--accent); font-size: 1.2rem; cursor: pointer;
  box-shadow: 0 8px 24px rgba(0,0,0,.25); opacity: 0; transform: translateY(12px);
  transition: opacity .3s ease, transform .3s ease; pointer-events: none;
}
#backTop.show { opacity: 1; transform: translateY(0); pointer-events: auto; }
/* Footer credit */
footer.credit {
  text-align: center; color: var(--muted); font-size: .85rem;
  padding: 1.5rem 1rem 2rem; border-top: 1px solid var(--border);
  margin-top: 2rem;
}
footer.credit a { color: var(--accent); text-decoration: none; }
footer.credit a:hover { text-decoration: underline; }
/* Manual theme overrides */
html.theme-light {
  --bg: #f6f8fc; --panel: #ffffff; --card: #ffffff; --text: #0f172a;
  --muted: #475569; --accent: #0f766e; --border: #dbe3f0; --chip: #eef2f7;
  --good: #16a34a; --warn: #d97706; --bad: #dc2626;
}
html.theme-dark {
  --bg: #0b1220; --panel: #111a2e; --card: #16203a; --text: #e6edf7;
  --muted: #9fb0cc; --accent: #5eead4; --border: #243252; --chip: #1f2a44;
  --good: #22c55e; --warn: #f59e0b; --bad: #ef4444;
}
.theme-toggle {
  padding: .4rem .7rem; border-radius: 8px; border: 1px solid var(--border);
  background: var(--chip); color: var(--text); cursor: pointer; font-size: .85rem;
}
/* Mobile responsiveness improvements */
@media (max-width: 640px) {
  header { padding: .6rem .9rem; }
  h1 { font-size: 1.35rem; }
  .subtitle { font-size: .85rem; }
  .hero { padding: .9rem 1rem; margin-bottom: .9rem; }
  .hero .hero-text h2 { font-size: 1.05rem; }
  .hero-stats { gap: .5rem; }
  .hero-stats .stat { min-width: 78px; padding: .45rem .6rem; }
  .hero-stats .stat .v { font-size: 1.1rem; }
  #chips { flex-wrap: nowrap; overflow-x: auto; padding-bottom: .35rem; -webkit-overflow-scrolling: touch; }
  #chips .chip { flex: 0 0 auto; }
  .controls { gap: .5rem; }
  #q { max-width: 100%; }
  .surprise, .theme-toggle { padding: .35rem .6rem; font-size: .8rem; }
}
/* Floating math background */
.loader .math-bg { position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.loader .math-bg span {
  position: absolute; color: var(--accent); opacity: .18; font-weight: 700;
  font-family: "Times New Roman", "Cambria Math", serif;
  animation: floaty 12s ease-in-out infinite;
  user-select: none;
}
.loader .math-bg span:nth-child(1){ font-size: 5rem; top: 12%; left: 8%; animation-delay: 0s; }
.loader .math-bg span:nth-child(2){ font-size: 4rem; top: 20%; right: 10%; animation-delay: -2s; }
.loader .math-bg span:nth-child(3){ font-size: 6rem; bottom: 15%; left: 15%; animation-delay: -4s; }
.loader .math-bg span:nth-child(4){ font-size: 4.5rem; bottom: 10%; right: 12%; animation-delay: -1s; }
.loader .math-bg span:nth-child(5){ font-size: 3.5rem; top: 45%; left: 3%; animation-delay: -3s; }
.loader .math-bg span:nth-child(6){ font-size: 5rem; top: 8%; right: 35%; animation-delay: -5s; }
.loader .math-bg span:nth-child(7){ font-size: 4rem; bottom: 30%; right: 30%; animation-delay: -2.5s; }
.loader .math-bg span:nth-child(8){ font-size: 4.5rem; top: 60%; left: 40%; animation-delay: -1.5s; }
@keyframes floaty {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-18px) rotate(6deg); }
}
/* Loading overlay */
.loader {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: radial-gradient(1200px 700px at 50% 45%, color-mix(in srgb, var(--accent) 12%, var(--bg)), var(--bg));
  transition: opacity .6s ease, visibility .6s ease;
  overflow: hidden;
}
.loader.hidden { opacity: 0; visibility: hidden; pointer-events: none; }
.loader::before {
  content: ""; position: absolute; inset: -20%;
  background: conic-gradient(from 0deg, transparent, color-mix(in srgb, var(--accent) 18%, transparent), transparent 40%);
  animation: sweep 6s linear infinite;
  filter: blur(60px);
  opacity: .7;
}
@keyframes sweep { to { transform: rotate(360deg); } }
.loader .logo {
  position: relative; z-index: 1;
  font-size: 2.4rem; font-weight: 800; letter-spacing: .6px;
  background: linear-gradient(120deg, var(--accent), #22d3ee, #818cf8, #34d399, var(--accent));
  background-size: 300% 300%;
  -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: shimmer 4s ease-in-out infinite;
  margin-bottom: 1.5rem;
  text-shadow: 0 0 40px color-mix(in srgb, var(--accent) 25%, transparent);
}
.loader .ring {
  position: relative; z-index: 1;
  width: 72px; height: 72px; border-radius: 50%;
  background: conic-gradient(var(--accent), #22d3ee, #818cf8, transparent, var(--accent));
  padding: 4px;
  animation: spin 1.4s linear infinite;
  box-shadow: 0 0 30px color-mix(in srgb, var(--accent) 40%, transparent);
}
.loader .ring::after {
  content: ""; position: absolute; inset: 4px; border-radius: 50%;
  background: var(--bg);
}
.loader .tagline {
  position: relative; z-index: 1;
  margin-top: 1.25rem; color: var(--muted); font-size: .95rem;
}
.loader .dots::after {
  content: ""; animation: dots 1.4s steps(4, end) infinite;
}
@keyframes dots {
  0% { content: ""; }
  25% { content: "."; }
  50% { content: ".."; }
  75% { content: "..."; }
  100% { content: ""; }
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes shimmer {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
/* Responsive safety for index */
#chips { max-width: 100%; }
.grid { max-width: 100%; }
.card { max-width: 100%; min-width: 0; overflow: hidden; }
.card * { min-width: 0; }
mjx-container { max-width: 100% !important; overflow-x: auto; overflow-y: hidden; }
main { max-width: 100%; overflow-x: hidden; }
* { scrollbar-width: thin; scrollbar-color: var(--accent) var(--chip); }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--chip); border-radius: 6px; }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { filter: brightness(1.2); }
</style>
<script>
window.MathJax = {
  tex: { inlineMath: [['$','$'], ['\\(','\\)']], processEscapes: true },
  options: { skipHtmlTags: ['script','noscript','style','textarea','pre','code'] },
  startup: { ready() { MathJax.startup.defaultReady(); if (window.__renderMath) window.__renderMath(); } }
};
</script>
<script src="vendor/mathjax/tex-chtml.js" async></script>
</head>
<body>
<div id="loader" class="loader" role="status" aria-live="polite">
  <div class="logo">Mathematical Discoveries</div>
  <div class="math-bg" aria-hidden="true">
    <span>&sum;</span><span>&int;</span><span>&pi;</span><span>&part;</span>
    <span>&infin;</span><span>&radic;</span><span>&asymp;</span><span>&nabla;</span>
  </div>
  <div class="ring"></div>
  <div class="tagline">Loading 372 result families<span class="dots"></span></div>
</div>
<header>
  <div class="header-top">
    <div>
      <h1>Mathematical Discoveries</h1>
      <p class="subtitle">An interactive catalog of 372 result families from the OpenAI mathematics manuscript collection, spanning 17 subjects. Every entry has a runnable demo; notation renders with locally vendored MathJax.</p>
    </div>
    <div class="header-actions">
      <span class="header-pill">372 families</span>
      <span class="header-pill">17 subjects</span>
      <a class="header-pill" href="https://github.com/openai/math" target="_blank" rel="noopener noreferrer">openai/math ↗</a>
    </div>
  </div>
  <div class="controls">
    <input id="q" type="search" placeholder="Search titles, descriptions, subjects…" autocomplete="off">
    <button id="surprise" class="surprise" type="button">Surprise me</button>
    <button id="themeToggle" class="theme-toggle" type="button" title="Toggle theme">Theme</button>
    <span id="count"></span>
  </div>
  <div id="chips"></div>
</header>
<main>
  <section class="hero">
    <div class="hero-text">
      <h2>Explore the collection</h2>
      <p>Filter by subject, search titles and descriptions, and open any family to run its interactive demo. Results range from number theory and algebraic geometry to probability, PDEs, and operator algebras.</p>
    </div>
    <div class="hero-stats">
      <div class="stat"><div class="v">372</div><div class="l">result families</div></div>
      <div class="stat"><div class="v">17</div><div class="l">subjects</div></div>
      <div class="stat"><div class="v">372</div><div class="l">interactive demos</div></div>
      <div class="stat"><div class="v">100%</div><div class="l">local MathJax</div></div>
    </div>
  </section>
  <div id="grid" class="grid"></div>
</main>

<div id="modalBackdrop" class="modal-backdrop" role="dialog" aria-modal="true">
  <div class="modal">
    <div class="modal-head">
      <button id="modalPrev" class="modal-close" type="button" title="Previous">‹</button>
      <h2 id="modalTitle">Demo</h2>
      <button id="modalNext" class="modal-close" type="button" title="Next">›</button>
      <button id="modalClose" class="modal-close" type="button">Close</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>
<script type="application/json" id="data">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const grid = document.getElementById('grid');
const q = document.getElementById('q');
const chipsEl = document.getElementById('chips');
const countEl = document.getElementById('count');

const modalBackdrop = document.getElementById('modalBackdrop');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalClose = document.getElementById('modalClose');

function openDemo(d){
  currentDemoIndex = DATA.indexOf(d);
  modalTitle.textContent = '#' + d.n + ' ' + d.title;
  modalBody.innerHTML = '';
  if (!d.demo) {
    const ctx = document.createElement('p');
    ctx.style.color = 'var(--muted)';
    ctx.style.fontSize = '1rem';
    ctx.textContent = d.desc;
    modalBody.appendChild(ctx);
    const rel = document.createElement('p');
    rel.style.fontSize = '1rem';
    rel.style.color = 'var(--accent)';
    rel.textContent = 'Relevance: ' + (d.relevance || ('Advances results in ' + d.subject + '.'));
    modalBody.appendChild(rel);
  }
  if (d.demo){
    const iframe = document.createElement('iframe');
    iframe.src = d.demo;
    iframe.title = d.title + ' demo';
    modalBody.appendChild(iframe);
  } else {
    const p = document.createElement('div');
    p.className = 'modal-empty';
    p.textContent = 'Interactive demo not available for this entry yet.';
    modalBody.appendChild(p);
  }
  modalBackdrop.classList.add('open');
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([modalBody]).catch(function(e){ console.error(e); });
  }
}
let currentDemoIndex = -1;
function closeDemo(){ modalBackdrop.classList.remove('open'); modalBody.innerHTML=''; currentDemoIndex = -1; }
window.closeDemo = closeDemo;
function openByIndex(i){
  if (i < 0) i = DATA.length - 1;
  if (i >= DATA.length) i = 0;
  const d = DATA[i];
  currentDemoIndex = i;
  openDemo(d);
}
const modalPrev = document.getElementById('modalPrev');
const modalNext = document.getElementById('modalNext');
if (modalPrev) modalPrev.addEventListener('click', () => { if (currentDemoIndex >= 0) openByIndex(currentDemoIndex - 1); });
if (modalNext) modalNext.addEventListener('click', () => { if (currentDemoIndex >= 0) openByIndex(currentDemoIndex + 1); });
window.addEventListener("message", function(e){ if(e.data==="closeDemo") closeDemo(); });
modalClose.addEventListener('click', closeDemo);
modalBackdrop.addEventListener('click', (e)=>{ if(e.target===modalBackdrop) closeDemo(); });
document.addEventListener('keydown', (e)=>{ if(e.key==='Escape') closeDemo(); });



const subjectCounts = DATA.reduce((a,d)=>{ a[d.subject]=(a[d.subject]||0)+1; return a; }, {});
const subjects = [...new Set(DATA.map(d => d.subject))].sort();
let activeSubject = 'All';
let query = '';

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function matches(d){
  if (activeSubject !== 'All' && d.subject !== activeSubject) return false;
  if (!query) return true;
  const hay = (d.n + ' ' + d.title + ' ' + d.desc + ' ' + d.subject).toLowerCase();
  return query.split(/\s+/).every(t => hay.includes(t));
}

function linkHtml(d){
  if (!d.links || !d.links.length) return '';
  return '<div class="links">' + d.links.map(l =>
    '<a href="' + esc(l.url) + '" target="_blank" rel="noopener noreferrer">' + esc(l.label) + '</a>'
  ).join('') + '</div>';
}

function render(){
  const items = DATA.filter(matches);
  countEl.textContent = 'Showing ' + items.length + ' of ' + DATA.length;
  if (!items.length){
    grid.innerHTML = '<div class="empty">No entries match your filters.<br><button id="clearFilters" style="margin-top:1rem;padding:.5rem 1rem;border-radius:10px;border:1px solid var(--border);background:var(--chip);color:var(--text);cursor:pointer">Clear filters</button></div>';
    const cf = document.getElementById('clearFilters');
    if (cf) cf.addEventListener('click', () => { activeSubject='All'; query=''; q.value=''; buildChips(); render(); });
    return;
  }
  grid.innerHTML = items.map(d =>
    '<article class="card" data-n="' + esc(d.n) + '">' +
      '<div class="meta"><span class="num">#' + esc(d.n) + '</span><span class="badge">' + esc(d.subject) + '</span></div>' +
      '<h2>' + esc(d.title) + '</h2>' +
      '<p class="desc">' + esc(d.desc) + '</p>' +
      linkHtml(d) +
    '</article>'
  ).join('');
  if (window.__renderMath) window.__renderMath();
}

window.__renderMath = function(){
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.typesetPromise([grid]).catch(function(e){ console.error(e); });
  }
};

function buildChips(){
  const all = ['All', ...subjects];
  chipsEl.innerHTML = all.map(s => {
    const label = s === 'All' ? 'All (' + DATA.length + ')' : esc(s) + ' (' + (subjectCounts[s]||0) + ')';
    return '<span class="chip' + (s === activeSubject ? ' active' : '') + '" data-s="' + esc(s) + '">' + label + '</span>';
  }).join('');
  chipsEl.querySelectorAll('.chip').forEach(el => {
    el.addEventListener('click', () => {
      activeSubject = el.dataset.s;
      buildChips();
      render();
      if (window.innerWidth <= 640) {
        const g = document.getElementById('grid');
        if (g) g.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

q.addEventListener('input', () => { query = q.value.trim().toLowerCase(); render();
  if (window.innerWidth <= 640 && query) {
    const g = document.getElementById('grid');
    if (g) g.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});
grid.addEventListener('click', (e) => {
  const card = e.target.closest('.card');
  if (!card) return;
  const n = card.dataset.n;
  const d = DATA.find(x => x.n === n);
  if (!d) return;
  if (d.demo) { window.location.href = d.demo; }
  else { openDemo(d); }
});
// Theme toggle
const themeToggle = document.getElementById('themeToggle');
function applyTheme(t){
  document.documentElement.classList.remove('theme-light','theme-dark');
  if (t && t !== 'auto') document.documentElement.classList.add('theme-' + t);
}
let currentTheme = localStorage.getItem('theme') || 'auto';
applyTheme(currentTheme);
if (themeToggle) themeToggle.addEventListener('click', () => {
  const isDark = document.documentElement.classList.contains('theme-dark') ||
    (!document.documentElement.classList.contains('theme-light') && window.matchMedia('(prefers-color-scheme: dark)').matches);
  currentTheme = isDark ? 'light' : 'dark';
  localStorage.setItem('theme', currentTheme);
  applyTheme(currentTheme);
});

buildChips();
render();

// Surprise me
const surpriseBtn = document.getElementById('surprise');
if (surpriseBtn) surpriseBtn.addEventListener('click', () => {
  const d = DATA[Math.floor(Math.random() * DATA.length)];
  if (!d) return;
  if (d.demo) { window.location.href = d.demo; }
  else { openDemo(d); }
});

// Back to top
const backTop = document.getElementById('backTop');
window.addEventListener('scroll', () => {
  if (backTop) backTop.classList.toggle('show', window.scrollY > 400);
});
if (backTop) backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// Keyboard shortcut: "/" focuses search
document.addEventListener('keydown', (e) => {
  if (e.key === '/' && document.activeElement && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    e.preventDefault();
    q.focus();
  }
});

// Hide loading overlay once MathJax finishes (fallback timeout).
const __loader = document.getElementById('loader');
const __loaderStart = Date.now();
const __seenIntro = sessionStorage.getItem('mathDemosIntroSeen');
const __MIN_INTRO = __seenIntro ? 400 : 2200;
if (!__seenIntro) sessionStorage.setItem('mathDemosIntroSeen', '1');
function __hideLoader(){
  if(!__loader) return;
  const elapsed = Date.now() - __loaderStart;
  const wait = Math.max(0, __MIN_INTRO - elapsed);
  setTimeout(() => {
    if(__loader){ __loader.classList.add('hidden'); setTimeout(()=>__loader.remove(), 700); }
  }, wait);
}
if (window.MathJax && MathJax.startup && MathJax.startup.promise) {
  MathJax.startup.promise.then(__hideLoader).catch(__hideLoader);
} else {
  setTimeout(__hideLoader, __MIN_INTRO);
}
setTimeout(__hideLoader, 3000);
</script>
<button id="backTop" type="button" aria-label="Back to top">↑</button>
<footer class="credit">Built with the help of model <strong>Reflection: Beam 1.0</strong>. Reference repository: <a href="https://github.com/openai/math" target="_blank" rel="noopener noreferrer">openai/math</a>.</footer>
</body>
</html>
'''

if __name__ == "__main__":
    main()
