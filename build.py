"""Build every page as a single self-contained HTML file.

    python3 build.py   ->  site/index.html                   (homepage)
                           site/features/<slug>/index.html   (one per src/features/<slug>.json)
                           site/404.html                     (copy of the homepage for now)

site/ is build output and is not in git. Internal links are relative to each page's folder (the site is served
under /inkybay-website/, so never start a link with "/"): every link is <root><path>, where <root> is "" on the
homepage and "../../" on a feature page (so a feature page links home with ../../).

The navbar mega menus, their mobile sheet sub-lists and promos come from src/nav.json (see render_nav).

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

def primary_html(text, href="#"):
    e = html.escape(text, quote=True)
    return f'<a class="btn btn--primary" href="{html.escape(href, quote=True)}" aria-label="{e}">{label(text)}<span class="btn__icon" aria-hidden="true">{ARROW}{ARROW}</span></a>'

def webp_size(path):
    """(width, height) of a WebP file, read from its header (stdlib only)."""
    b = (ASSETS / path).read_bytes()
    kind = b[12:16]
    if kind == b"VP8X": return 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
    if kind == b"VP8 ": return int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF
    if kind == b"VP8L":
        v = int.from_bytes(b[21:25], "little"); return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
    raise ValueError(f"not a WebP: {path}")

EXT = '<svg class="mega__ext" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 4h6v6M12 4l-7.5 7.5"/></svg>'
NAV = json.loads((ROOT / "src" / "nav.json").read_text())["menus"]

def menu_items(m):
    """A menu's items: from its items_from index file (the file's list of entries) or its own items."""
    if "items_from" in m:
        data = json.loads((ROOT / m["items_from"]).read_text())
        return next(v for v in data.values() if isinstance(v, list))
    return m.get("items", [])

def link(item, base, root):
    """href and extra attributes. Internal links are relative to the page's folder (<root> + path)."""
    if item.get("external"):
        return item["href"], ' target="_blank" rel="noopener"'
    href = item.get("href") or f'{base}{item["slug"]}/'
    if href.startswith(("#", "http", "mailto:")): return href, ""
    return root + href, ""

def nav_item(item, base, root, current):
    href, extra = link(item, base, root)
    cur = ' aria-current="page"' if current and item.get("slug") == current else ""
    act = f' data-action="{html.escape(item["action"])}"' if item.get("action") else ""
    ext = EXT if item.get("external") else ""
    desk = (f'<li><a class="mega__item" href="{href}"{extra}{act}{cur}><span class="mega__icon">{ICON[item["icon"]]}</span>'
            f'<span><span class="mega__title">{html.escape(item["title"])}{ext}</span><span class="mega__desc">{html.escape(item["short"])}</span></span></a></li>')
    mob = f'<li><a href="{href}"{extra}{act}{cur}>{html.escape(item["title"])}{ext}</a></li>'
    return desk, mob

def render_nav(root, current):
    """Desktop triggers, mobile sheet entries and mega panels for every menu in nav.json.
    current = (menu id, slug) of the page being built, so its own item is highlighted."""
    triggers, sheet, panels = [], [], []
    for m in NAV:
        mid, lab, base = m["id"], html.escape(m["label"]), m.get("base", "")
        cur = current[1] if current and current[0] == mid else None
        if m["layout"] == "groups":
            cols, mob = [], []
            for g in m["groups"]:
                pairs = [nav_item(i, i.get("base", base), root, cur) for i in g["items"]]
                cols.append(f'<div class="mega__group"><p class="mega__label">{html.escape(g["title"])}</p><ul class="mega__list">{"".join(d for d, _ in pairs)}</ul></div>')
                mob.append(f'<li class="sheet-group">{html.escape(g["title"])}</li>' + "".join(x for _, x in pairs))
            main = f'<div class="mega__main"><div class="mega__groups">{"".join(cols)}</div></div>'
        else:
            pairs = [nav_item(i, base, root, cur) for i in menu_items(m)]
            mob = [x for _, x in pairs]
            main = f'<div class="mega__main">\n        <p class="mega__label">{lab}</p>\n        <ul class="mega__grid">{"".join(d for d, _ in pairs)}</ul>\n      </div>'
        p = m["promo"]
        if p.get("visual") == "video":
            media = (f'<span class="mega__video"><img class="mega__img" src="{b64("hero-editor.webp")}" alt="" width="2240" height="1836" loading="lazy" decoding="async">'
                     f'<span class="mega__play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l11-6.5z"/></svg></span></span>')
        else:
            w, h = webp_size(p["image"])
            pos = f' style="object-position: {html.escape(p["position"])}"' if p.get("position") else ""
            media = f'<img class="mega__img" src="{b64(p["image"])}" alt="" width="{w}" height="{h}"{pos} loading="lazy" decoding="async">'
        phref, _ = link({"href": p["href"]}, "", root)
        promo = (f'<aside class="mega__promo">\n        {media}\n        <p class="mega__promo-title">{html.escape(p["title"])}</p>\n'
                 f'        <p class="mega__promo-text">{html.escape(p["text"])}</p>\n        {primary_html(p["cta"], phref)}\n      </aside>')
        triggers.append(f'<li><button class="nav__link nav__link--mega" id="nav-{mid}" aria-expanded="false" aria-controls="mega-{mid}">{lab} {{{{CHEVRON}}}}</button></li>')
        sheet.append(f'<li><button class="nav__link sheet-toggle" aria-expanded="false" aria-controls="sheet-{mid}">{lab} {{{{CHEVRON}}}}</button><ul class="sheet-sub" id="sheet-{mid}">{"".join(mob)}</ul></li>')
        panels.append(f'<div class="mega mega--{m["layout"]}" id="mega-{mid}" role="region" aria-label="{lab}" data-open="false">\n    <div class="mega__panel">\n      {main}\n      {promo}\n    </div>\n  </div>')
    return "\n          ".join(triggers), "\n        ".join(sheet), "\n  ".join(panels)

def foot_cols(mid, root):
    """Footer columns for one menu (its "footer" list in nav.json): {"title", "groups"?, "limit"?, "more"?, "extra"?}."""
    m = next(x for x in NAV if x["id"] == mid)
    cols = []
    for c in m["footer"]:
        if m["layout"] == "groups":
            items = [dict(i, base=i.get("base", m.get("base", ""))) for g in m["groups"] if g["title"] in c.get("groups", [g["title"]]) for i in g["items"]]
        else:
            items = [dict(i, base=m.get("base", "")) for i in menu_items(m)]
        items = items[:c["limit"]] if c.get("limit") and len(items) > c["limit"] else items
        items += [dict(x, base="") for x in c.get("extra", [])]
        if c.get("more") and len(menu_items(m) if m["layout"] != "groups" else items) > c.get("limit", 99): items.append(dict(c["more"], base=""))
        lis = []
        for i in items:
            href, extra = link(i, i["base"], root)
            act = f' data-action="{html.escape(i["action"])}"' if i.get("action") else ""
            lis.append(f'<li><a href="{href}"{extra}{act}>{html.escape(i["title"])}{EXT if i.get("external") else ""}</a></li>')
        cols.append(f'<div class="foot__col"><h3>{html.escape(c["title"])}</h3><ul>{"".join(lis)}</ul></div>')
    return "\n          ".join(cols)

def build(t, root="", home="#", current=None):
    triggers, sheet, panels = render_nav(root, current)
    t = t.replace("{{NAV_TRIGGERS}}", triggers).replace("{{SHEET_MENUS}}", sheet).replace("{{MEGA_PANELS}}", panels).replace("{{HOME}}", home)
    t = re.sub(r"\{\{FOOT_COLS:(.*?)\}\}", lambda m: foot_cols(m.group(1), root), t)
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

SITE = ROOT / "site"
homepage = build((ROOT / "src" / "template.html").read_text())
write(SITE / "index.html", homepage)
write(SITE / "404.html", homepage)
for j in sorted(p for p in (ROOT / "src" / "features").glob("*.json") if not p.name.startswith("_")):   # _index.json is data, not a page
    write(SITE / "features" / j.stem / "index.html", build(render(j.stem), root="../../", home="../../", current=("features", j.stem)))
