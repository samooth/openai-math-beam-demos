# Mathematical Discoveries — Interactive Demo Catalog

A self-contained, offline-friendly web catalog of **372 result families** from the
[OpenAI mathematics manuscript collection](https://github.com/openai/math), spanning
**17 subjects** (number theory, algebraic geometry, probability, PDEs, operator
algebras, and more). Every family has a runnable, interactive demo.

> Built with the help of model **Reflection: Beam 1.0**.

![status](https://img.shields.io/badge/demos-372-5eead4) ![subjects](https://img.shields.io/badge/subjects-17-818cf8) ![offline](https://img.shields.io/badge/offline-ready-22d3ee)

---

## ✨ Features

- **372 interactive demos** — one per result family, with live sliders, canvases, and
  visualizations.
- **Fast, client-side search** across titles, descriptions, subjects, and numbers.
- **Subject filters** with per-subject counts.
- **"Surprise me"** button for random discovery.
- **Manual theme toggle** (light / dark / auto) with persisted preference.
- **Keyboard shortcut** `/` focuses the search box.
- **Loading intro** with animated math symbols (longer on first visit, short on
  return).
- **Responsive layout** — works on phones, tablets, and desktops; no horizontal
  scroll.
- **Offline-ready** — MathJax is vendored locally; no CDN or network required.
- **Back-to-top** button and smooth navigation between demos.
- **Reference link** to the upstream repository.

---

## 🚀 Quick start

```bash
# Serve locally (any static server works)
python3 -m http.server 8000
# then open http://localhost:8000
```

Or open `index.html` directly in a browser.

---

## 🛠️ Build & deploy

Regenerate `index.html` from `overview.tex`:

```bash
python3 build_demo.py
```

Deploy to the production host:

```bash
npm run deploy
```

This rsyncs the folder to
`bsv.direct:/home/t0m4s/nginx/webs/bsv.direct/beam-math-demos/`.

---

## 📁 Structure

```
demo/
├── index.html            # generated catalog (do not edit by hand)
├── build_demo.py         # parses overview.tex → index.html
├── demos/                # 372 standalone interactive demo pages
│   ├── 001.html
│   ├── ...
│   └── 377.html
├── vendor/mathjax/       # locally vendored MathJax
├── package.json          # deploy script
└── README.md
```

---

## 🧩 How it works

1. `build_demo.py` parses `../overview.tex`, extracting each `\resultentry`.
2. It cleans TeX notation into display-ready text.
3. It injects the data as JSON into the `TEMPLATE` and writes `index.html`.
4. Each demo is a standalone HTML page under `demos/`, opened as a separate page
   (not a modal) for a better reading experience.

---

## 🎨 Customization

- **Colors / theme** — edit the CSS variables in `:root` inside `build_demo.py`'s
  `TEMPLATE`.
- **Loader timing** — adjust `__MIN_INTRO` in the template's script.
- **Add a demo** — create `demos/NNN.html` and it is picked up automatically by
  the dynamic registry.

---

## 📜 Credits

- Mathematical content © the OpenAI mathematics manuscript collection.
- Reference repository: <https://github.com/openai/math>
- UI, demos, and tooling built with the help of model **Reflection: Beam 1.0**.

---

## 📄 License

See the upstream repository for licensing of the mathematical content. UI code in
this folder is provided as-is.
