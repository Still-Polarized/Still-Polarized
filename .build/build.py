#!/usr/bin/env python
"""Build a static HTML site from the Still Polarized interlinked Markdown vault."""
import os, re, sys, html
import markdown as md

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(VAULT, "docs")
# clean rebuild: remove previous output so deleted pages don't linger in docs/
import shutil
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT, exist_ok=True)

# slug: lower-case, replace spaces with '-', keep alphanumerics
def slug(name):
    return re.sub(r"\s+", "-", name.lower()).rstrip(".md")

# collect all pages
pages = {}
def walk(d):
    for entry in os.listdir(d):
        p = os.path.join(d, entry)
        if os.path.isdir(p):
            if entry in (".build", "site", "docs", ".git", "assets"):
                continue
            walk(p)
        elif entry.endswith(".md"):
            pages[os.path.basename(entry)[:-3]] = (p, os.path.dirname(p))
walk(VAULT)

# map page name -> relative url (depth-aware: links must resolve from the
# page's own directory, since the site is served from a subfolder of the domain)
def page_url(name, depth=0):
    src, d = pages[name]
    rel = os.path.relpath(d, VAULT)
    base = "" if rel == "." else rel + "/"
    prefix = "../" * depth
    return prefix + base + slug(name) + ".html"

# find links from a file's own dir (like Obsidian: [[Name]] resolves against vault)
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|#]+)?(?:\|[^\]]+)?\]\]")

# EVE fit blocks: ```fit ... ```  ->  <pre><code class="language-fit">...</code></pre>
FIT_RE = re.compile(r'<pre><code class="(?:language-)?fit">(.*?)</code></pre>', re.DOTALL)
def add_fit_buttons(html_str):
    """Wrap each EVE fit code block in a .fit card with a copy-to-clipboard button."""
    def repl(m):
        content = m.group(1)
        first_line = content.split("\n", 1)[0]
        label = html.unescape(first_line).strip()
        if label.startswith("[") and "," in label:
            inner = label.strip("[]")
            parts = inner.split(",", 1)
            ship = parts[0].strip()
            fitn = parts[1].strip() if len(parts) > 1 else ""
            label = ship + (" — " + fitn if fitn else "")
        return (
            f'<div class="fit"><div class="fitbar"><span class="fitlabel">'
            f'{html.escape(label)}</span>'
            f'<button class="copybtn" type="button" onclick="copyFit(this)">Copy</button>'
            f'</div><pre><code class="language-fit">{content}</code></pre></div>'
        )
    return FIT_RE.sub(repl, html_str)

def depth_of(d):
    """How many directory levels d is below the vault root (0 for root)."""
    rel = os.path.relpath(d, VAULT)
    if rel in (".", ""):
        return 0
    return len([p for p in rel.split(os.sep) if p and p != "."])

def convert(body, name, depth=0):
    def repl(m):
        target = m.group(1).strip()
        if target in pages:
            return f'<a class="wiki" href="{page_url(target, depth)}">{html.escape(target)}</a>'
        return f'<span class="wikibroken" title="Missing page">{html.escape(m.group(0))}</span>'
    body = LINK_RE.sub(repl, body)
    out = md.markdown(body, extensions=["tables", "fenced_code", "sane_lists", "toc"])
    return add_fit_buttons(out)

CSS = """
:root {
  --orange: #ff6a00; --ink: #111; --panel: #1c1c1f;
  --line: #2e2e33; --text: #e8e6e3; --muted: #9a978f;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: "Segoe UI", system-ui, sans-serif; background: #0a0a0b; color: var(--text); display: grid; grid-template-columns: 280px 1fr; min-height: 100vh; }
nav { background: var(--panel); border-right: 1px solid var(--line); padding: 20px 14px; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
nav h1 { color: var(--orange); font-size: 1.05rem; letter-spacing: .04em; margin: 0 0 2px; }
nav h2 { color: var(--muted); font-size: .7rem; text-transform: uppercase; margin: 0 0 14px; letter-spacing: .1em; }
nav a { display: block; color: var(--text); text-decoration: none; padding: 5px 10px; border-radius: 6px; font-size: .88rem; }
nav a:hover, nav a.active { background: #2a2a30; color: var(--orange); }
nav .group { margin-top: 14px; }
nav .group > div.title { color: var(--muted); font-size: .68rem; text-transform: uppercase; letter-spacing: .09em; margin: 6px 10px; }
main { padding: 34px 44px; max-width: 980px; }
main h1 { color: var(--orange); border-bottom: 2px solid var(--line); padding-bottom: 10px; }
a.wiki { color: var(--orange); text-decoration: none; border-bottom: 1px dotted var(--orange); }
a.wiki:hover { background: #241a10; }
.wikibroken { color: #b05040; }
table { border-collapse: collapse; margin: 14px 0; width: 100%; }
th, td { border: 1px solid var(--line); padding: 7px 10px; font-size: .9rem; }
th { background: #202024; color: var(--orange); text-align: left; }
code { background: #1d1d22; padding: 2px 6px; border-radius: 4px; }
pre { background: #141417; padding: 12px; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
img { max-width: 100%; }
hr { border: none; border-top: 1px solid var(--line); }
.fit { margin: 16px 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; }
.fitbar { display: flex; align-items: center; justify-content: space-between; gap: 10px; background: #202024; padding: 7px 12px; }
.fitlabel { color: var(--orange); font-size: .85rem; font-weight: 600; }
.copybtn { background: var(--orange); color: #111; border: none; padding: 4px 12px; border-radius: 5px; font-size: .75rem; font-weight: 700; cursor: pointer; }
.copybtn:hover { background: #ff8a3d; }
.copybtn:active { transform: translateY(1px); }
.copybtn.copied { background: #2f9e6f; color: #fff; }
.fit pre { margin: 0; border-top: 1px solid var(--line); }
.search { margin: 10px 0 18px; }
.search input { width: 100%; padding: 8px 10px; background: #141417; border: 1px solid var(--line); border-radius: 6px; color: var(--text); font-size: .85rem; }
@media (max-width: 800px) { body { grid-template-columns: 1fr; } nav { position: static; height: auto; } }
"""

COPYJS = """
function copyFit(btn) {
  var fit = btn.closest('.fit');
  var code = fit.querySelector('pre code');
  var text = code.textContent;
  function done(ok) {
    btn.textContent = ok ? 'Copied!' : 'Error';
    btn.classList.add('copied');
    setTimeout(function(){ btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1400);
  }
  function fallback() {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.top = '0'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.focus(); ta.select();
    try { document.execCommand('copy'); done(true); } catch(e) { done(false); }
    document.body.removeChild(ta);
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(function(){ done(true); }, fallback);
  } else {
    fallback();
  }
}
"""

def build():
    # index tree for sidebar
    tree = {}
    for name in sorted(pages):
        src, d = pages[name]
        rel = os.path.relpath(d, VAULT)
        group = rel if rel != "." else "Home"
        tree.setdefault(group, []).append(name)

    for name, (src, d) in pages.items():
        depth = depth_of(d)
        body = open(src, encoding="utf-8").read()
        # Rebuild the sidebar for THIS page's depth so its links resolve too.
        nav_html = ['<h1>Still Polarized</h1>', '<h2>Wormhole Corp · Low Sec</h2>']
        nav_html.append('<div class="search"><input id="q" type="text" placeholder="Filter pages…" oninput="filterNav(this.value)"></div>')
        for group, names in tree.items():
            nav_html.append(f'<div class="group"><div class="title">{html.escape(group)}</div>')
            for n in names:
                nav_html.append(f'<a data-name="{html.escape(n.lower())}" href="{page_url(n, depth)}">{html.escape(n)}</a>')
            nav_html.append('</div>')
        nav_html.append("""
<script>
function filterNav(q) {
  q = q.toLowerCase();
  document.querySelectorAll('nav a[data-name]').forEach(a => {
    a.style.display = !q || a.dataset.name.includes(q) ? '' : 'none';
  });
}
const here = location.pathname.split('/').pop() || 'Home.html';
document.querySelectorAll('nav a').forEach(a => { if (a.getAttribute('href').endsWith(here)) a.classList.add('active'); });
</script>""")
        content = convert(body, name, depth)
        page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(name)} — Still Polarized</title><style>{CSS}</style></head>
<body>
<aside><nav>{''.join(nav_html)}</nav></aside>
<main><article>{content}</article>
<footer style="margin-top:40px;color:var(--muted);font-size:.75rem">Still Polarized — Wormhole Corp · Low Sec. Tag <strong style="color:var(--orange)">STLPO</strong>. Home base: Bayuka (Sazdih, Derelik), 0.4 lowsec.</footer>
</main><script>{COPYJS}</script></body></html>"""
        url = page_url(name)
        target = os.path.join(OUT, url)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(page)

    # index.html -> Home page
    import shutil
    home_src = None
    for cand in ("home.html", "Home.html", "home.md.html"):
        if os.path.exists(os.path.join(OUT, cand)):
            home_src = cand
            break
    if home_src is None:
        # fallback: page whose name is 'Home'
        for name in pages:
            if name.lower() == "home":
                home_src = page_url(name)
                break
    assert home_src, "Could not locate the Home page in the built site"
    shutil.copyfile(os.path.join(OUT, home_src), os.path.join(OUT, "index.html"))

    # copy assets (logo etc.) into the site
    assets_src = os.path.join(VAULT, "assets")
    if os.path.isdir(assets_src):
        shutil.copytree(assets_src, os.path.join(OUT, "assets"), dirs_exist_ok=True)
        print("Copied assets/ -> docs/assets/")

    # GitHub Pages: this is a pre-built static site, so skip Jekyll entirely.
    # Without it, Jekyll tries to render .scss and the build fails.
    with open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")
    print("Wrote docs/.nojekyll (disables Jekyll on GitHub Pages)")

    # count broken links
    broken = 0
    for name, (src, d) in pages.items():
        body = open(src, encoding="utf-8").read()
        for m in LINK_RE.finditer(body):
            if m.group(1).strip() not in pages:
                broken += 1
    print(f"Built {len(pages)} pages + index.html into {OUT}")
    print(f"Broken links found: {broken}")
    if broken:
        print("Pages with missing link targets:")
        for name, (src, d) in pages.items():
            body = open(src, encoding="utf-8").read()
            miss = {m.group(1).strip() for m in LINK_RE.finditer(body) if m.group(1).strip() not in pages}
            if miss:
                print(f"  {name}: {sorted(miss)}")

if __name__ == "__main__":
    build()
