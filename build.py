"""Build every page as a single self-contained HTML file.

    python3 build.py   ->  reference/homepage.html
                           reference/features/<slug>.html   (one per src/features/<slug>.json)

src/template.html is the homepage with {{TOKENS}}. Feature pages reuse its head, navbar, CTA,
footer, CSS and JS (see render_feature.py), so every page stays in sync with the homepage.
"""
import base64, re, html, pathlib
import json
from render_feature import render, ICON

ROOT = pathlib.Path(__file__).parent
ASSETS = ROOT / "src" / "assets"
ARROW = '<svg viewBox="0 0 24 24" fill="none"><path d="M14.4301 6L20.5001 12.07L14.4301 18.14" stroke="#FD7807" stroke-width="1.5" stroke-miterlimit="10" stroke-linejoin="round"/><path d="M4 12.07H20.83" stroke="#FD7807" stroke-width="1.5" stroke-miterlimit="10" stroke-linejoin="round"/></svg>'
CHEV = '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M5 7.5L10 12.5L15 7.5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def label(txt):
    e = html.escape(txt, quote=True)
    return f'<span class="btn__label" aria-hidden="true"><span data-text="{e}">{e}</span></span>'
def primary(m):
    e = html.escape(m.group(1), quote=True)
    return f'<a class="btn btn--primary" href="#" aria-label="{e}">{label(m.group(1))}<span class="btn__icon" aria-hidden="true">{ARROW}{ARROW}</span></a>'
def secondary(m):
    e = html.escape(m.group(1), quote=True)
    return f'<a class="btn btn--secondary" href="#" aria-label="{e}">{label(m.group(1))}</a>'
def b64(path):
    return "data:image/webp;base64," + base64.b64encode((ASSETS / path).read_bytes()).decode()

INDEX = json.loads((ROOT / "src" / "features" / "_index.json").read_text())["features"]

def mega(base, current):
    """Mega-menu items and the mobile sub-list, from _index.json. base = path prefix to the features folder."""
    items, mobile = [], []
    for f in INDEX:
        cur = ' aria-current="page"' if f["slug"] == current else ""
        href = f'{base}{f["slug"]}.html'
        items.append(f'<li><a class="mega__item" href="{href}"{cur}><span class="mega__icon">{ICON[f["icon"]]}</span>'
                     f'<span><span class="mega__title">{html.escape(f["title"])}</span><span class="mega__desc">{html.escape(f["short"])}</span></span></a></li>')
        mobile.append(f'<li><a href="{href}"{cur}>{html.escape(f["title"])}</a></li>')
    return "".join(items), "".join(mobile)

def build(t, base="features/", home="#", current=None):
    items, mobile = mega(base, current)
    t = t.replace("{{MEGA_ITEMS}}", items).replace("{{MEGA_MOBILE}}", mobile).replace("{{HOME}}", home)
    t = re.sub(r"\{\{BTN_PRIMARY:(.*?)\}\}", primary, t)
    t = re.sub(r"\{\{BTN_SECONDARY:(.*?)\}\}", secondary, t)
    t = t.replace("{{CHEVRON}}", CHEV)
    for token, name in [("WORDMARK_LIT", "wordmark_lit.svg"), ("WORDMARK", "wordmark.svg"), ("LOGO_MARK", "logo_mark.svg"), ("LOGO_TYPE", "logo_type.svg")]:
        t = t.replace("{{%s}}" % token, (ASSETS / "brand" / name).read_text())
    t = t.replace("{{EDITOR}}", b64("hero-editor.webp"))
    t = re.sub(r"\{\{IMG:(.*?)\}\}", lambda m: b64(m.group(1)), t)
    left = re.findall(r"\{\{.*?\}\}", t)
    assert not left, f"unresolved tokens: {left}"
    return t

def write(path, t):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(t)
    print(f"ok -> {path.relative_to(ROOT)} ({round(len(t) / 1024)} KB)")

write(ROOT / "reference" / "homepage.html", build((ROOT / "src" / "template.html").read_text()))
for j in sorted(p for p in (ROOT / "src" / "features").glob("*.json") if not p.name.startswith("_")):   # _index.json is data, not a page
    write(ROOT / "reference" / "features" / f"{j.stem}.html", build(render(j.stem), base="", home="../homepage.html", current=j.stem))
