"""Build the single-file homepage reference.

    python3 build.py            ->  reference/homepage.html

src/template.html holds the page with {{TOKENS}}; this script inlines buttons,
brand SVGs and images (as base64 WebP) so the output is one self-contained file.
"""
import base64, re, html, pathlib

ROOT = pathlib.Path(__file__).parent
SRC, ASSETS = ROOT / "src", ROOT / "src" / "assets"
t = (SRC / "template.html").read_text()

ARROW = '<svg viewBox="0 0 24 24" fill="none"><path d="M14.4301 6L20.5001 12.07L14.4301 18.14" stroke="#FD7807" stroke-width="1.5" stroke-miterlimit="10" stroke-linejoin="round"/><path d="M4 12.07H20.83" stroke="#FD7807" stroke-width="1.5" stroke-miterlimit="10" stroke-linejoin="round"/></svg>'
CHEV = '<svg viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M5 7.5L10 12.5L15 7.5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def label(txt):
    e = html.escape(txt, quote=True)
    return f'<span class="btn__label" aria-hidden="true"><span data-text="{e}">{e}</span></span>'

def primary(m):   # {{BTN_PRIMARY:Text}} -> rolling-label button with the double arrow
    e = html.escape(m.group(1), quote=True)
    return f'<a class="btn btn--primary" href="#" aria-label="{e}">{label(m.group(1))}<span class="btn__icon" aria-hidden="true">{ARROW}{ARROW}</span></a>'

def secondary(m): # {{BTN_SECONDARY:Text}}
    e = html.escape(m.group(1), quote=True)
    return f'<a class="btn btn--secondary" href="#" aria-label="{e}">{label(m.group(1))}</a>'

def b64(path):
    return "data:image/webp;base64," + base64.b64encode((ASSETS / path).read_bytes()).decode()

t = re.sub(r"\{\{BTN_PRIMARY:(.*?)\}\}", primary, t)
t = re.sub(r"\{\{BTN_SECONDARY:(.*?)\}\}", secondary, t)
t = t.replace("{{CHEVRON}}", CHEV)
for token, name in [("WORDMARK_LIT", "wordmark_lit.svg"), ("WORDMARK", "wordmark.svg"), ("LOGO_MARK", "logo_mark.svg"), ("LOGO_TYPE", "logo_type.svg")]:
    t = t.replace("{{%s}}" % token, (ASSETS / "brand" / name).read_text())
t = t.replace("{{EDITOR}}", b64("hero-editor.webp"))
t = re.sub(r"\{\{IMG:(.*?)\}\}", lambda m: b64(m.group(1)), t)

left = re.findall(r"\{\{.*?\}\}", t)
assert not left, f"unresolved tokens: {left}"
out = ROOT / "reference" / "homepage.html"
out.write_text(t)
print(f"ok -> {out.relative_to(ROOT)} ({round(len(t) / 1024)} KB)")
