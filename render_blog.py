"""The blog: content model, validation, thumbnails, pages, search index and RSS.

    src/blog/posts/<slug>.md       one post: front matter + Markdown (see docs/writing-a-blog-post.md)
    src/blog/categories.json       slug, name, description
    src/blog/tags.json             slug, name
    src/blog/authors.json          slug, name, role, bio, avatar (optional)
    src/assets/blog/<file>         thumbnails (16:10 recommended; other ratios warn)

URLs (under resources/blog/, every link relative to the page's folder like the rest of the site):
    resources/blog/  ·  page/<n>/  ·  category/<slug>/ (+ page/<n>/)  ·  tag/<slug>/ (+ page/<n>/)  ·  search/?q=  ·  <post-slug>/
Markdown is Python-Markdown (pinned in requirements.txt); thumbnails are resized with Pillow.
"""
import json, re, math, html, datetime, pathlib, unicodedata, sys
from urllib.parse import quote
import markdown
from render_feature import ROOT, E, ICON, CHEV_R, ARROW

BLOG = ROOT / "src" / "blog"
THUMBS = ROOT / "src" / "assets" / "blog"
BASE = "resources/blog/"
NEW_TAB = ' target="_blank" rel="noopener"'
PER_PAGE = 12
WIDTHS = (640, 960, 1440)
SPARKLE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z"/></svg>')
LINK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>')
SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">'
          '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>')
VIEWS = [("2", '<rect x="4" y="4" width="7" height="16" rx="1.5"/><rect x="13" y="4" width="7" height="16" rx="1.5"/>', "Two columns"),
         ("3", '<rect x="3" y="4" width="5" height="16" rx="1.2"/><rect x="9.5" y="4" width="5" height="16" rx="1.2"/><rect x="16" y="4" width="5" height="16" rx="1.2"/>', "Three columns"),
         ("4", '<rect x="2.5" y="4" width="4" height="16" rx="1"/><rect x="7.5" y="4" width="4" height="16" rx="1"/><rect x="12.5" y="4" width="4" height="16" rx="1"/><rect x="17.5" y="4" width="4" height="16" rx="1"/>', "Four columns"),
         ("list", '<rect x="3" y="4.5" width="6" height="6" rx="1.2"/><path d="M12 6h9M12 9h6"/><rect x="3" y="13.5" width="6" height="6" rx="1.2"/><path d="M12 15h9M12 18h6"/>', "List")]


class BlogError(SystemExit):
    pass


def fail(msg):
    raise BlogError(f"\nBlog build failed: {msg}\n")


# ---------------------------------------------------------------- content model
def slugify(text, sep="-"):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)


def scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'": return v[1:-1]
    if v in ("true", "false"): return v == "true"
    if v.startswith("[") and v.endswith("]"): return [scalar(x) for x in v[1:-1].split(",") if x.strip()]
    return v


def front_matter(text, path):
    """A small YAML subset: `key: value`, `key: [a, b]`, and `key:` followed by `  - item` lines."""
    if not text.startswith("---\n"): fail(f"{path.name}: missing front matter (start the file with ---)")
    end = text.find("\n---", 4)
    if end < 0: fail(f"{path.name}: front matter is not closed with ---")
    meta, key = {}, None
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        if line.startswith((" ", "\t")) and line.strip().startswith("- ") and key:
            meta.setdefault(key, []); meta[key].append(scalar(line.strip()[2:])); continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if not m: fail(f"{path.name}: cannot read front matter line: {line!r}")
        key, val = m.group(1), m.group(2)
        meta[key] = scalar(val) if val.strip() else []
    return meta, text[end + 4:].lstrip("\n")


def load():
    cats = json.loads((BLOG / "categories.json").read_text())["categories"]
    tags = json.loads((BLOG / "tags.json").read_text())["tags"]
    authors = {a["slug"]: a for a in json.loads((BLOG / "authors.json").read_text())["authors"]}
    C = {c["slug"]: c for c in cats}; T = {t["slug"]: t for t in tags}
    posts, seen = [], {}
    for f in sorted((BLOG / "posts").glob("*.md")):
        m, body = front_matter(f.read_text(), f)
        for k in ("title", "slug", "excerpt", "category", "author", "date", "thumbnail", "summary"):
            if not m.get(k): fail(f"{f.name}: missing '{k}'")
        if not m.get("thumbnail_alt"): fail(f"{f.name}: missing 'thumbnail_alt' (describe the thumbnail)")
        if m["slug"] in seen: fail(f"duplicate slug '{m['slug']}' in {f.name} and {seen[m['slug']]}")
        seen[m["slug"]] = f.name
        if len(m["excerpt"]) > 160: fail(f"{f.name}: excerpt is {len(m['excerpt'])} chars (max 160)")
        if m["category"] not in C: fail(f"{f.name}: unknown category '{m['category']}' (add it to src/blog/categories.json)")
        m["tags"] = m.get("tags") or []
        for t in m["tags"]:
            if t not in T: fail(f"{f.name}: unknown tag '{t}' (add it to src/blog/tags.json)")
        if m["author"] not in authors: fail(f"{f.name}: unknown author '{m['author']}' (add it to src/blog/authors.json)")
        if not (THUMBS / m["thumbnail"]).exists(): fail(f"{f.name}: thumbnail src/assets/blog/{m['thumbnail']} not found")
        if not 3 <= len(m["summary"]) <= 5: fail(f"{f.name}: summary needs 3-5 bullets")
        for k in ("date", "updated"):
            if m.get(k):
                try: datetime.date.fromisoformat(m[k])
                except ValueError: fail(f"{f.name}: {k} must be YYYY-MM-DD")
        m["featured"] = m.get("featured") is True
        m["body"] = body
        m["words"] = len(re.findall(r"\w+", body))
        m["minutes"] = max(1, math.ceil(m["words"] / 225))
        m["url"] = f"{BASE}{m['slug']}/"
        posts.append(m)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return {"cats": cats, "C": C, "tags": tags, "T": T, "authors": authors, "posts": posts}


# ---------------------------------------------------------------- markdown
def md_html(body):
    md = markdown.Markdown(extensions=["tables", "toc", "attr_list", "sane_lists", "fenced_code"],
                           extension_configs={"toc": {"toc_depth": "2-3", "slugify": lambda v, sep: slugify(v, sep)}})
    out = md.convert(body)
    toc = [{"id": t["id"], "name": html.unescape(t["name"]), "children": [{"id": c["id"], "name": html.unescape(c["name"])} for c in t["children"]]}
           for t in md.toc_tokens]

    def callout(m):                                    # > [!NOTE] blocks -> an aside
        kind, inner = m.group(1).lower(), m.group(2)
        title = {"note": "Note", "tip": "Tip", "warning": "Watch out"}.get(kind, kind.title())
        return f'<aside class="bcall bcall--{kind}" role="note"><p class="bcall__title">{title}</p><p>{inner}</aside>'
    out = re.sub(r"<blockquote>\s*<p>\[!(NOTE|TIP|WARNING)\]\s*(.*?)</blockquote>", callout, out, flags=re.S)
    out = re.sub(r'<p><img alt="([^"]*)" src="([^"]*)" title="([^"]*)"\s*/?></p>',      # image with a title -> figure + caption
                 r'<figure class="bfig"><img src="\2" alt="\1" loading="lazy"><figcaption>\3</figcaption></figure>', out)
    out = out.replace("<blockquote>", '<blockquote class="bquote">')
    out = re.sub(r"<li>\[x\]\s*", '<li class="bcheck">', out); out = re.sub(r"<li>\[ \]\s*", '<li class="bcheck bcheck--todo">', out)
    out = re.sub(r"(<ul>\s*<li class=\"bcheck)", r'<ul class="bchecks">\n<li class="bcheck', out)
    out = re.sub(r"<table>", '<div class="btable" tabindex="0" role="region" aria-label="Table"><table>', out).replace("</table>", "</table></div>")
    def anchor(m):
        lvl, hid, text = m.group(1), m.group(2), m.group(3)
        return (f'<h{lvl} id="{hid}">{text}<a class="banchor" href="#{hid}" data-copy-link aria-label="Copy link to this section">{LINK}</a></h{lvl}>')
    out = re.sub(r'<h([23]) id="([^"]+)">(.*?)</h\1>', anchor, out)
    return out, toc


# ---------------------------------------------------------------- thumbnails
def thumbs(post, site):
    """Responsive WebP versions (640/960/1440 wide) in site/resources/blog/img/; warns when the ratio is not 16:10."""
    from PIL import Image
    src = THUMBS / post["thumbnail"]; out = site / BASE / "img"; out.mkdir(parents=True, exist_ok=True)
    im = Image.open(src); w, h = im.size
    if abs(w / h - 1.6) > .01:
        print(f"  warning: {src.name} is {w}x{h}, not 16:10; it will render at its own ratio", file=sys.stderr)
    stem = pathlib.Path(post["thumbnail"]).stem; files = []
    for tw in WIDTHS:
        tw = min(tw, w); th = round(h * tw / w); dst = out / f"{stem}-{tw}.webp"
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            im.convert("RGB").resize((tw, th), Image.LANCZOS).save(dst, "WEBP", quality=80, method=6)
        files.append((tw, th, f"{BASE}img/{dst.name}"))
    return {"w": w, "h": h, "files": files}


def img_tag(post, root, sizes, eager=False, cls=""):
    t = post["thumb"]; srcset = ", ".join(f"{root}{u} {tw}w" for tw, _, u in t["files"])
    mid = t["files"][min(1, len(t["files"]) - 1)]
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img class="{cls}" src="{root}{mid[2]}" srcset="{srcset}" sizes="{sizes}" width="{t["w"]}" height="{t["h"]}" '
            f'alt="{E(post["thumbnail_alt"])}" {load} decoding="async">')


# ---------------------------------------------------------------- shared bits
def fmt_date(d):
    return datetime.date.fromisoformat(d).strftime("%-d %b %Y")


def pill(cat, root, cls="bpill"):
    return f'<a class="{cls}" href="{root}{BASE}category/{cat["slug"]}/">{E(cat["name"])}</a>'


def card(p, D, root, heading="h3"):
    cat = D["C"][p["category"]]
    return (f'<li class="bcard"><a class="bcard__media" href="{root}{p["url"]}" tabindex="-1" aria-hidden="true">'
            f'{img_tag(p, root, "(max-width: 600px) 100vw, (max-width: 1100px) 50vw, 33vw", cls="bcard__img")}</a>'
            f'<div class="bcard__body">{pill(cat, root)}<{heading} class="bcard__title"><a href="{root}{p["url"]}">{E(p["title"])}</a></{heading}>'
            f'<p class="bcard__excerpt">{E(p["excerpt"])}</p>'
            f'<div class="bcard__meta"><time datetime="{p["date"]}">{fmt_date(p["date"])}</time><span aria-hidden="true">·</span><span>{p["minutes"]} min read</span></div></div></li>')


def cat_bar(D, root, active=None):
    counts = {c["slug"]: sum(p["category"] == c["slug"] for p in D["posts"]) for c in D["cats"]}
    CUR = ' aria-current="page"'
    pills = [f'<li><a class="bbar__pill{" is-active" if active is None else ""}" href="{root}{BASE}"{CUR if active is None else ""}>All <span>{len(D["posts"])}</span></a></li>']
    for c in D["cats"]:
        on = c["slug"] == active
        cur = ' aria-current="page"' if on else ""
        pills.append(f'<li><a class="bbar__pill{" is-active" if on else ""}" href="{root}{BASE}category/{c["slug"]}/"{cur}>{E(c["name"])} <span>{counts[c["slug"]]}</span></a></li>')
    views = "".join(f'<button class="bview__btn" type="button" data-view="{v}" aria-pressed="{"true" if v == "3" else "false"}" aria-label="{E(n)}" title="{E(n)}">'
                    f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">{ic}</svg></button>' for v, ic, n in VIEWS)
    return (f'<div class="bbar"><nav class="bbar__nav" aria-label="Blog categories"><ul class="bbar__list">{"".join(pills)}</ul>'
            f'<div class="bbar__more"><button class="bbar__more-btn" type="button" aria-expanded="false" aria-haspopup="true" hidden>More</button>'
            f'<div class="bbar__pop" hidden><label class="sr-only" for="bbar-q">Find a category</label><input id="bbar-q" class="bbar__q" type="search" placeholder="Find a category" autocomplete="off">'
            f'<ul class="bbar__all">{"".join(pills)}</ul></div></div></nav>'
            f'<div class="bview" role="group" aria-label="Layout">{views}</div></div>')


def pagination(n, cur, base, root):
    if n <= 1: return ""
    href = lambda k: f"{root}{base}" if k == 1 else f"{root}{base}page/{k}/"
    nums = sorted({1, n, cur - 1, cur, cur + 1} & set(range(1, n + 1)))
    items, last = [], 0
    for k in nums:
        if k - last > 1: items.append('<li><span class="bpage__gap" aria-hidden="true">…</span></li>')
        cur_attr = ' aria-current="page"' if k == cur else ""
        items.append(f'<li><a class="bpage__num" href="{href(k)}"{cur_attr}>{k}</a></li>'); last = k
    prev = f'<a class="bpage__step" href="{href(cur - 1)}" rel="prev">Previous</a>' if cur > 1 else '<span class="bpage__step is-off" aria-hidden="true">Previous</span>'
    nxt = f'<a class="bpage__step" href="{href(cur + 1)}" rel="next">Next</a>' if cur < n else '<span class="bpage__step is-off" aria-hidden="true">Next</span>'
    return f'<nav class="bpage" aria-label="Pagination">{prev}<ul>{"".join(items)}</ul>{nxt}</nav>'


def newsletter(copy):
    n = copy["newsletter"]
    return f"""<section class="fsec fsec--dark bnews" aria-labelledby="b-news">
    <div class="container bnews__in">
      <div class="bnews__text"><h2 class="fsec__title" id="b-news"><span class="h-line">{E(n["title"][0])}</span> <span class="h-line h-muted">{E(n["title"][1])}</span></h2><p>{E(n["lead"])}</p></div>
      {news_form(n, "bn")}
    </div>
  </section>"""


def news_form(n, pid):
    return (f'<form class="form bnews__form" data-form="newsletter" data-endpoint="{{{{NEWSLETTER_ENDPOINT}}}}" method="post" novalidate>'
            f'<p class="form__note" hidden>{E(n["not_connected"])}</p>'
            f'<div class="bnews__row"><label class="field"><span class="sr-only">{E(n["email"])}</span><input name="email" type="email" inputmode="email" autocomplete="email" placeholder="{E(n["email"])}" required data-err="{E(n["error"])}" aria-describedby="{pid}-err"></label>'
            f'<button class="btn btn--primary form__submit" type="submit" data-sending="{E(n["sending"])}"><span class="btn__label" aria-hidden="true"><span data-text="{E(n["button"])}">{E(n["button"])}</span></span><span class="sr-only">{E(n["button"])}</span></button></div>'
            f'<span class="field__err" id="{pid}-err" aria-live="polite"></span>'
            f'<div class="form__hp" aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>'
            f'<div class="bnews__consent">{E(n["consent"])}</div>'
            f'<p class="form__status" role="status" aria-live="polite" data-ok="{E(n["success"])}" data-fail="{E(n["fail"])}" data-off="{E(n["not_connected"])}"></p></form>')


# ---------------------------------------------------------------- SEO
def seo(site_url, path, title, desc, image=None, kind="website", jsonld=(), prev=None, nxt=None, noindex=False):
    url = site_url + path
    tags = [f'<link rel="canonical" href="{E(url)}">',
            f'<meta property="og:type" content="{kind}">', f'<meta property="og:title" content="{E(title)}">', f'<meta property="og:description" content="{E(desc)}">',
            f'<meta property="og:url" content="{E(url)}">', '<meta property="og:site_name" content="InkyBay">',
            f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">', f'<meta name="twitter:title" content="{E(title)}">',
            f'<meta name="twitter:description" content="{E(desc)}">']
    if image: tags += [f'<meta property="og:image" content="{E(site_url + image)}">', f'<meta name="twitter:image" content="{E(site_url + image)}">']
    if prev: tags.append(f'<link rel="prev" href="{E(site_url + prev)}">')
    if nxt: tags.append(f'<link rel="next" href="{E(site_url + nxt)}">')
    if noindex: tags.append('<meta name="robots" content="noindex">')
    for j in jsonld: tags.append(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>')
    return "\n".join(tags)


def crumbs_ld(site_url, items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": n, "item": site_url + u} for k, (n, u) in enumerate(items)]}


def shell(home, body, title, desc, head_extra):
    head = home[:home.index("<main>")]
    css = "".join((ROOT / "src" / n).read_text() for n in ("feature.css", "forms.css", "blog.css"))
    head = head.replace("</style>", css + "\n</style>", 1)
    head = re.sub(r"<title>.*?</title>", f"<title>{E(title)}</title>\n<meta name=\"description\" content=\"{E(desc)}\">", head, count=1)
    head = head.replace("</head>", head_extra + "\n</head>", 1)
    return head + body + home[home.index("</main>") + len("</main>"):]


# ---------------------------------------------------------------- pages
def depth_root(path):
    return "../" * path.count("/")


def listing_body(D, copy, posts, page, n_pages, base, root, head_html, featured=None, bar_active=None, after_bar="", title=True):
    feat = ""
    if featured:
        cls = "bfeat bfeat--one" if len(featured) == 1 else "bfeat bfeat--two"
        items = []
        for p in featured:
            cat = D["C"][p["category"]]; au = D["authors"][p["author"]]
            items.append(f'<article class="bfcard"><a class="bfcard__media" href="{root}{p["url"]}" tabindex="-1" aria-hidden="true">'
                         f'{img_tag(p, root, "(max-width: 960px) 100vw, 50vw", eager=True, cls="bfcard__img")}</a>'
                         f'<div class="bfcard__body">{pill(cat, root)}<h2 class="bfcard__title"><a href="{root}{p["url"]}">{E(p["title"])}</a></h2>'
                         f'<p class="bfcard__excerpt">{E(p["excerpt"])}</p><div class="bcard__meta"><span>{E(au["name"])}</span><span aria-hidden="true">·</span>'
                         f'<time datetime="{p["date"]}">{fmt_date(p["date"])}</time><span aria-hidden="true">·</span><span>{p["minutes"]} min read</span></div></div></article>')
        feat = f'<section class="bsec bsec--feat" aria-label="{E(copy["featured_label"])}"><div class="container"><div class="{cls}">{"".join(items)}</div></div></section>'
    grid = f'<ul class="bgrid" data-view="3">{"".join(card(p, D, root) for p in posts)}</ul>'
    return f"""{head_html}
  {feat}
  <section class="fsec fsec--tint blatest" aria-labelledby="b-latest">
    <div class="container">
      <h2 class="{"fsec__title blatest__title" if title else "sr-only"}" id="b-latest">{E(copy["latest"] if title else "Articles")}</h2>
      {cat_bar(D, root, bar_active)}
      {after_bar}
      {grid}
      {pagination(n_pages, page, base, root)}
    </div>
  </section>"""


def pages_of(items):
    return [items[i:i + PER_PAGE] for i in range(0, max(len(items), 1), PER_PAGE)] or [[]]


def build_all(build, write, site, site_url, home):
    """Write every blog page, the search index, the RSS feed and the logo file. Returns [(path, lastmod)] for the sitemap."""
    D = load(); copy = json.loads((BLOG / "blog.json").read_text())
    for p in D["posts"]:
        p["thumb"] = thumbs(p, site)
        p["html"], p["toc"] = md_html(p["body"])
    (site / "assets").mkdir(parents=True, exist_ok=True)
    (site / "assets" / "inkybay-logo.svg").write_text((ROOT / "src/assets/brand/logo_mark.svg").read_text())
    pub = {"@type": "Organization", "name": copy["meta"]["publisher"], "logo": {"@type": "ImageObject", "url": site_url + "assets/inkybay-logo.svg"}}
    out = []

    def emit(path, title, desc, body, head_extra, lastmod=None):
        root = depth_root(path)
        write(site / path / "index.html", build(shell(home, f"<main>\n{body}\n</main>", title, desc, head_extra), root=root, home=root))
        out.append((path, lastmod))

    hero = f"""<section class="bhero" aria-labelledby="b-title">
    <div class="container bhero__in">
      <h1 class="bhero__title" id="b-title"><span class="h-line">{E(copy["hero"]["title"][0])}</span> <span class="h-line h-muted">{E(copy["hero"]["title"][1])}</span></h1>
      <p class="bhero__lead">{E(copy["hero"]["lead"])}</p>
      <form class="bsearch" role="search" action="{{ROOT}}{BASE}search/" method="get"><label class="sr-only" for="b-q">{E(copy["hero"]["search_label"])}</label>
        <span class="bsearch__icon">{SEARCH}</span><input id="b-q" class="bsearch__input" name="q" type="search" placeholder="{E(copy["hero"]["search_placeholder"])}" autocomplete="off">
        <kbd class="bsearch__key" title="{E(copy["hero"]["search_hint"])}">/</kbd></form>
    </div>
  </section>"""

    # listing: resources/blog/ and page/<n>/
    allp = D["posts"]; chunks = pages_of(allp); featured = [p for p in allp if p["featured"]][:2]
    for k, chunk in enumerate(chunks, 1):
        path = BASE if k == 1 else f"{BASE}page/{k}/"; root = depth_root(path)
        title = copy["meta"]["title"] if k == 1 else f"Blog, page {k} | InkyBay"
        jl = [crumbs_ld(site_url, [("Home", ""), ("Blog", BASE)]),
              {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": site_url + path, "description": copy["meta"]["description"]}]
        prev = (BASE if k == 2 else f"{BASE}page/{k - 1}/") if k > 1 else None; nxt = f"{BASE}page/{k + 1}/" if k < len(chunks) else None
        body = listing_body(D, copy, chunk, k, len(chunks), BASE, root, hero.replace("{ROOT}", root), featured if k == 1 else None) + "\n  " + newsletter(copy)
        emit(path, title, copy["meta"]["description"], body, seo(site_url, path, title, copy["meta"]["description"], jsonld=jl, prev=prev, nxt=nxt))

    def results_head(kind, name, count, desc, root, chip_label, extra=""):
        crumb = f'{copy["results"][kind]}: {name}' if kind != "search" else copy["results"]["search"]
        noun = copy["results"]["article"] if count == 1 else copy["results"]["articles"]
        h1 = E(name)
        return f"""<section class="bres" aria-labelledby="b-title">
    <div class="container">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{root}">Home</a>{CHEV_R}<a href="{root}{BASE}">Blog</a>{CHEV_R}<span aria-current="page">{E(crumb)}</span></nav>
      <div class="bres__label">{E(copy["results"][kind])}</div>
      <h1 class="bres__title" id="b-title">{h1}</h1>
      <p class="bres__count" aria-live="polite">{count} {noun}</p>
      {f'<p class="bres__desc">{E(desc)}</p>' if desc else ""}
      <div class="bchips"><a class="bchip" href="{root}{BASE}" aria-label="{E(copy["results"]["remove"])}: {E(chip_label)}">{E(chip_label)} <span aria-hidden="true">×</span></a></div>
      {extra}
    </div>
  </section>"""

    # category and tag result pages
    for c in D["cats"]:
        posts = [p for p in allp if p["category"] == c["slug"]]; chunks = pages_of(posts); base = f"{BASE}category/{c['slug']}/"
        for k, chunk in enumerate(chunks, 1):
            path = base if k == 1 else f"{base}page/{k}/"; root = depth_root(path)
            title = f'{c["name"]} articles | InkyBay blog' + (f", page {k}" if k > 1 else "")
            head = results_head("category", c["name"], len(posts), c["description"], root, c["name"])
            jl = [crumbs_ld(site_url, [("Home", ""), ("Blog", BASE), (c["name"], base)]),
                  {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": site_url + path, "description": c["description"]}]
            body = listing_body(D, copy, chunk, k, len(chunks), base, root, head, bar_active=c["slug"], title=False) + "\n  " + newsletter(copy)
            emit(path, title, c["description"], body, seo(site_url, path, title, c["description"], jsonld=jl,
                 prev=((base if k == 2 else f"{base}page/{k - 1}/") if k > 1 else None), nxt=(f"{base}page/{k + 1}/" if k < len(chunks) else None)))
    for t in D["tags"]:
        posts = [p for p in allp if t["slug"] in p["tags"]]
        if not posts: continue
        chunks = pages_of(posts); base = f"{BASE}tag/{t['slug']}/"
        co = {}
        for p in posts:
            for o in p["tags"]:
                if o != t["slug"]: co[o] = co.get(o, 0) + 1
        for k, chunk in enumerate(chunks, 1):
            path = base if k == 1 else f"{base}page/{k}/"; root = depth_root(path)
            rel = sorted(co, key=lambda o: (-co[o], o))[:6]
            related = (f'<div class="brel"><div class="brel__label">{E(copy["results"]["related_tags"])}</div><ul class="btags">'
                       + "".join(f'<li><a class="btag" href="{root}{BASE}tag/{o}/">{E(D["T"][o]["name"])}</a></li>' for o in rel) + "</ul></div>") if rel else ""
            desc = f'Articles tagged {t["name"]} on the InkyBay blog.'
            title = f'{t["name"]} articles | InkyBay blog' + (f", page {k}" if k > 1 else "")
            head = results_head("tag", t["name"], len(posts), "", root, t["name"], related)
            jl = [crumbs_ld(site_url, [("Home", ""), ("Blog", BASE), (t["name"], base)]),
                  {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": site_url + path, "description": desc}]
            body = listing_body(D, copy, chunk, k, len(chunks), base, root, head, title=False) + "\n  " + newsletter(copy)
            emit(path, title, desc, body, seo(site_url, path, title, desc, jsonld=jl,
                 prev=((base if k == 2 else f"{base}page/{k - 1}/") if k > 1 else None), nxt=(f"{base}page/{k + 1}/" if k < len(chunks) else None)))

    # search (client-side from search-index.json); noindex
    path = f"{BASE}search/"; root = depth_root(path)
    counts = {c["slug"]: sum(p["category"] == c["slug"] for p in allp) for c in D["cats"]}
    popular = sorted(D["cats"], key=lambda c: -counts[c["slug"]])[:3]
    sugg = "".join(f'<li>{pill(c, root, "bpill bpill--lg")}</li>' for c in popular)
    r = copy["results"]
    body = f"""<section class="bres bres--search" aria-labelledby="b-title">
    <div class="container">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{root}">Home</a>{CHEV_R}<a href="{root}{BASE}">Blog</a>{CHEV_R}<span aria-current="page">{E(r["search"])}</span></nav>
      <div class="bres__label">{E(r["search"])}</div>
      <h1 class="bres__title" id="b-title"><span class="bres__q">""</span></h1>
      <form class="bsearch bsearch--page" role="search" action="" method="get"><label class="sr-only" for="b-q">{E(copy["hero"]["search_label"])}</label>
        <span class="bsearch__icon">{SEARCH}</span><input id="b-q" class="bsearch__input" name="q" type="search" placeholder="{E(copy["hero"]["search_placeholder"])}" autocomplete="off"></form>
      <p class="bres__count" aria-live="polite"></p>
      <div class="bchips" hidden><a class="bchip bchip--q" href="{root}{BASE}"><span></span> <span aria-hidden="true">×</span></a></div>
    </div>
  </section>
  <section class="fsec fsec--tint blatest bsearch-results" aria-label="Results">
    <div class="container">
      {cat_bar(D, root, "__none__")}
      <ul class="bgrid" data-view="3" data-index="{root}{BASE}search-index.json" data-root="{root}"></ul>
      <div class="bempty" hidden><p class="bempty__title">{E(r["empty"])} “<span></span>”</p><p>{E(r["suggest"])}</p><ul class="bempty__pills">{sugg}</ul>
        <button class="btn btn--secondary bempty__clear" type="button">{E(r["clear"])}</button></div>
    </div>
  </section>"""
    title = "Search the blog | InkyBay"
    emit(path, title, copy["meta"]["description"], body, seo(site_url, path, title, copy["meta"]["description"],
         jsonld=[crumbs_ld(site_url, [("Home", ""), ("Blog", BASE), ("Search", path)])], noindex=True))
    out.pop()          # search results are not in the sitemap

    # articles
    a = copy["article"]
    for i, p in enumerate(allp):
        path = p["url"]; root = depth_root(path); cat = D["C"][p["category"]]; au = D["authors"][p["author"]]
        related = sorted([q for q in allp if q is not p], key=lambda q: (q["category"] != p["category"], -len(set(q["tags"]) & set(p["tags"])), allp.index(q)))[:3]
        newer = allp[i - 1] if i > 0 else None; older = allp[i + 1] if i + 1 < len(allp) else None
        toc_items = "".join(f'<li><a href="#{t["id"]}">{E(t["name"])}</a>' + (("<ol>" + "".join(f'<li><a href="#{c["id"]}">{E(c["name"])}</a></li>' for c in t["children"]) + "</ol>") if t["children"] else "") + "</li>" for t in p["toc"])
        toc = f'<ol class="btoc__list">{toc_items}</ol>'
        url_abs = site_url + path
        share = [("X", f"https://twitter.com/intent/tweet?url={quote(url_abs, safe='')}&text={quote(p['title'], safe='')}"),
                 ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={quote(url_abs, safe='')}"),
                 ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={quote(url_abs, safe='')}"),
                 ("Email", f"mailto:?subject={quote(p['title'])}&body={quote(url_abs)}")]
        share_html = (f'<button class="bshare__btn" type="button" data-copy-url="{E(url_abs)}">{LINK}<span>{E(a["copy_link"])}</span></button>'
                      + "".join(f'<a class="bshare__btn" href="{E(u)}"{"" if n == "Email" else NEW_TAB}>{E(n)}</a>' for n, u in share)
                      + f'<span class="bshare__ok" aria-live="polite" data-copied="{E(a["copied"])}"></span>')
        avatar = f'<img class="bauthor__avatar" src="{root}{au["avatar"]}" alt="" width="40" height="40">' if au.get("avatar") else f'<span class="bauthor__avatar" aria-hidden="true">{E(au["name"][:1])}</span>'
        meta = (f'<p class="bmeta">{avatar}<span>{E(a["written_by"])} <strong>{E(au["name"])}</strong></span><span aria-hidden="true">·</span>'
                f'<time datetime="{p["date"]}">{fmt_date(p["date"])}</time>'
                + (f'<span aria-hidden="true">·</span><span>{E(a["updated"])} <time datetime="{p["updated"]}">{fmt_date(p["updated"])}</time></span>' if p.get("updated") else "")
                + f'<span aria-hidden="true">·</span><span>{p["minutes"]} min read</span></p>')
        bullets = "".join(f"<li>{E(s)}</li>" for s in p["summary"])
        pi = copy["promo_install"]; pn = copy["promo_news"]
        promos = (f'<div class="bpromo bpromo--news"><p class="bpromo__title">{E(pn["title"])}</p><p>{E(pn["text"])}</p>{news_form(copy["newsletter"], "bp")}</div>'
                  f'<div class="bpromo bpromo--install"><p class="bpromo__title">{E(pi["title"])}</p><ul class="bpromo__list">{"".join(f"<li>{E(x)}</li>" for x in pi["items"])}</ul>'
                  f'{{{{BTN_PRIMARY:{pi["button"]}|{pi["href"]}}}}}</div>')
        nav_pn = ('<nav class="bpn" aria-label="More articles">'
                  + (f'<a class="bpn__link bpn__link--prev" href="{root}{older["url"]}"><span>{E(a["prev"])}</span>{E(older["title"])}</a>' if older else "<span></span>")
                  + (f'<a class="bpn__link bpn__link--next" href="{root}{newer["url"]}"><span>{E(a["next"])}</span>{E(newer["title"])}</a>' if newer else "<span></span>") + "</nav>")
        body = f"""<div class="bprogress" aria-hidden="true"><i></i></div>
  <article class="bart" aria-labelledby="b-title">
    <div class="container bart__grid">
      <div class="bart__main">
        <header class="bart__head">
          <nav class="crumbs" aria-label="Breadcrumb"><a href="{root}">Home</a>{CHEV_R}<a href="{root}{BASE}">Blog</a>{CHEV_R}<a href="{root}{BASE}category/{cat["slug"]}/">{E(cat["name"])}</a></nav>
          {pill(cat, root)}
          <h1 class="bart__title" id="b-title">{E(p["title"])}</h1>
          {meta}
        </header>
        <figure class="bart__fig">{img_tag(p, root, "(max-width: 960px) 100vw, 760px", eager=True, cls="bart__img")}</figure>
        <section class="bsum" aria-labelledby="b-sum"><div class="bsum__head"><h2 class="bsum__title" id="b-sum">{E(a["summary_title"])}</h2>
          <button class="bsum__btn" type="button" aria-expanded="false" aria-controls="b-sum-list" data-hide="{E(a["hide"])}">{SPARKLE}<span>{E(a["summarize"])}</span></button></div>
          <ul class="bsum__list" id="b-sum-list">{bullets}</ul></section>
        <details class="btoc btoc--inline"><summary>{E(a["toc"])}</summary><nav aria-label="Table of contents">{toc}</nav></details>
        <div class="bbody">{p["html"]}</div>
        <footer class="bart__foot">
          <div class="bart__tags"><p class="sr-only">{E(a["tags"])}</p><ul class="btags">{"".join(f'<li><a class="btag" href="{root}{BASE}tag/{t}/">{E(D["T"][t]["name"])}</a></li>' for t in p["tags"])}</ul></div>
          <div class="bshare"><p class="bshare__label">{E(a["share"])}</p><div class="bshare__row">{share_html}</div></div>
          <div class="bauthor">{avatar}<div><div class="bauthor__label">{E(a["about_author"])}</div><p class="bauthor__name">{E(au["name"])} <span>· {E(au["role"])}</span></p><p class="bauthor__bio">{E(au["bio"])}</p></div></div>
        </footer>
      </div>
      <aside class="bart__side" aria-label="On this page and more">
        <nav class="btoc btoc--side" aria-label="Table of contents"><p class="btoc__title">{E(a["toc"])}</p>{toc}</nav>
        <div class="bpromos">{promos}</div>
      </aside>
    </div>
  </article>
  <section class="fsec fsec--tint bmore" aria-labelledby="b-more">
    <div class="container">
      <h2 class="fsec__title" id="b-more">{E(a["keep_reading"])}</h2>
      <ul class="bgrid" data-view="3" data-fixed>{"".join(card(q, D, root) for q in related)}</ul>
      {nav_pn}
    </div>
  </section>"""
        title = p.get("seo_title") or f'{p["title"]} | InkyBay blog'; desc = p.get("seo_description") or p["excerpt"]
        big = p["thumb"]["files"][-1][2]
        jl = [{"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"], "description": desc, "image": site_url + big,
               "author": {"@type": "Person", "name": au["name"]}, "datePublished": p["date"], "dateModified": p.get("updated") or p["date"],
               "publisher": pub, "mainEntityOfPage": {"@type": "WebPage", "@id": url_abs}},
              crumbs_ld(site_url, [("Home", ""), ("Blog", BASE), (cat["name"], f"{BASE}category/{cat['slug']}/"), (p["title"], path)])]
        emit(path, title, desc, body, seo(site_url, path, title, desc, image=big, kind="article", jsonld=jl), p.get("updated") or p["date"])

    # search index and RSS
    idx = [{"title": p["title"], "excerpt": p["excerpt"], "category": D["C"][p["category"]]["name"], "category_slug": p["category"],
            "tags": [D["T"][t]["name"] for t in p["tags"]], "tag_slugs": p["tags"], "url": p["url"], "date": p["date"], "date_label": fmt_date(p["date"]),
            "minutes": p["minutes"], "thumb": {"w": p["thumb"]["w"], "h": p["thumb"]["h"], "files": p["thumb"]["files"]}, "alt": p["thumbnail_alt"]} for p in allp]
    (site / BASE / "search-index.json").write_text(json.dumps(idx, ensure_ascii=False))
    rfc = lambda d: datetime.datetime.combine(datetime.date.fromisoformat(d), datetime.time(9)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = "".join(f"<item><title>{html.escape(p['title'])}</title><link>{site_url}{p['url']}</link><guid isPermaLink=\"true\">{site_url}{p['url']}</guid>"
                    f"<pubDate>{rfc(p['date'])}</pubDate><category>{html.escape(D['C'][p['category']]['name'])}</category><description>{html.escape(p['excerpt'])}</description></item>" for p in allp)
    feed = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{html.escape(copy["meta"]["feed_title"])}</title>'
            f'<link>{site_url}{BASE}</link><description>{html.escape(copy["meta"]["description"])}</description><language>en</language>'
            f'<atom:link href="{site_url}{BASE}feed.xml" rel="self" type="application/rss+xml"/>{items}</channel></rss>\n')
    (site / BASE / "feed.xml").write_text(feed)
    print(f"ok -> {BASE} ({len(allp)} posts, {len(out)} blog pages, search-index.json, feed.xml)")
    return out
