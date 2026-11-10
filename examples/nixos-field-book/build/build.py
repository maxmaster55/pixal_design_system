"""Build the NixOS Frost Field Book HTML from src/*.md.
Usage: python3 build.py <workdir>   (workdir holds body.html from pandoc and optional pagenums.json)
Pipeline: pandoc (markdown) -> body.html -> this script -> book.html -> render.js -> PDF."""
import re, json, sys, html, os
from bs4 import BeautifulSoup, NavigableString, Tag

W = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, "..", "design")
pages = {}
try:
    pages = json.load(open(f"{W}/pagenums.json"))
except Exception:
    pass

soup = BeautifulSoup(open(f"{W}/body.html").read(), "html.parser")

# ---------- Nix and shell highlighters ----------
KW = r"let|in|with|rec|inherit|import|if|then|else|assert|or|true|false|null"
RX = re.compile(r"(#.*$)|(\"(?:[^\"\\]|\\.)*\"|''[\s\S]*?'')|((?:\.{0,2}|~)/[\w.\/-]+|<[\w.\/-]+>)|(\b(?:" + KW + r")\b)|(\b(?:lib|pkgs|config|builtins|self|nixpkgs|prev|final)\b)|(\b\d+(?:\.\d+)?\b)|(\b[a-zA-Z_][\w'-]*(?=(?:\.[\w${}\"-]+)*\s*=[^=]))", re.M)
CLS = ["c", "s", "l", "k", "t", "n", "a"]

def hl_nix(src):
    out, last = [], 0
    for m in RX.finditer(src):
        out.append(html.escape(src[last:m.start()], quote=False))
        i = next(k for k, g in enumerate(m.groups()) if g is not None)
        out.append(f'<span class="{CLS[i]}">{html.escape(m.group(0), quote=False)}</span>')
        last = m.end()
    out.append(html.escape(src[last:], quote=False))
    return "".join(out)

def hl_sh(src):
    lines = []
    for ln in src.split("\n"):
        if ln.startswith("$ "):
            cmd = ln[2:]; cm = ""
            k = cmd.find("  #")
            if k >= 0: cmd, cm = cmd[:k], cmd[k:]
            lines.append(f'<span class="p">{ln[0]}</span> ' + html.escape(cmd, quote=False) + (f'<span class="c">{html.escape(cm, quote=False)}</span>' if cm else ""))
        elif re.match(r"^(error|warning)", ln):
            lines.append(f'<span class="e">{html.escape(ln, quote=False)}</span>')
        else:
            lines.append(f'<span class="o">{html.escape(ln, quote=False)}</span>')
    return "\n".join(lines)

def hl_out(src):
    lines = []
    for ln in src.split("\n"):
        e = html.escape(ln, quote=False)
        if re.match(r"^\s*(error|warning|trace)", ln): e = f'<span class="e">{e}</span>'
        elif ln.startswith("$ "): e = f'<span class="g">{e}</span>'
        lines.append(e)
    return "\n".join(lines)

def keep_indent(h):
    # whitespace-only text between two tags is dropped by the HTML round trip, so pin indentation with no-break spaces
    return re.sub(r"\n( +)", lambda m: "\n" + "\u00a0" * len(m.group(1)), h)

def fix_pre(pre, term=False):
    code = pre.get_text().rstrip("\n")
    classes = (pre.get("class") or []) + ((pre.code.get("class") or []) if pre.code else [])
    new = soup.new_tag("pre")
    nlines = code.count("\n") + 1
    tail = ["long"] if nlines > 34 else ["px"]
    if "nix" in classes:
        new["class"] = ["nix"] + tail; new.append(BeautifulSoup(keep_indent(hl_nix(code)), "html.parser"))
    elif "sh" in classes and not term:
        new["class"] = ["sh"] + tail; new.append(BeautifulSoup(keep_indent(hl_sh(code)), "html.parser"))
    else:
        new["class"] = ["txt"] + (["long"] if nlines > 34 else [])
        new.append(BeautifulSoup(keep_indent(hl_out(code) if term else html.escape(code, quote=False)), "html.parser"))
    return new

ICON = {"worked": ("gear", "#b24d0a", "Worked"), "exer": ("q", "#6b2b8f", "Exercises"), "tip": ("key", "#2a6b33", "Tip"),
        "pit": ("warn", "#8a5200", "Pitfall"), "term": ("chip", "#17607a", "Terminal")}

def tag_html(kind, title):
    ic, col, default = ICON[kind]
    label = default if not title else (title if kind in ("exer",) else f"{default}: {title}")
    if kind == "worked" and title: label = f"Worked: {title}"
    return BeautifulSoup(f'<div class="tag"><canvas data-ember="icon" data-icon="{ic}" data-color="{col}" width="7" height="7"></canvas>{html.escape(label)}</div>', "html.parser")

# ---------- transform tree ----------
for pre in soup.find_all("pre"):
    in_term = any("term" in (p.get("class") or []) for p in pre.parents if isinstance(p, Tag))
    pre.replace_with(fix_pre(pre, in_term))
for t in soup.find_all("table"):
    t["class"] = ["t"]
    for a in ("style",):
        if t.has_attr(a): del t[a]
    for cg in t.find_all("colgroup"): cg.decompose()
for d in soup.find_all("div"):
    cls = d.get("class") or []
    kind = next((k for k in ICON if k in cls), None)
    if kind:
        title = d.get("data-t") or d.get("t")
        d["class"] = ["box", kind] + (["px", "short"] if len(d.get_text()) < 420 else [])
        d.insert(0, tag_html(kind, title))
        for p in d.find_all("p"):
            first = next((c for c in p.contents if not (isinstance(c, NavigableString) and not c.strip())), None)
            if isinstance(first, Tag) and first.name == "em" and first.get_text().strip().startswith("Answer"):
                p["class"] = ["ans"]
    elif "case" in cls:
        n, title = d.get("data-n"), d.get("data-t")
        d["class"] = ["casecard"]
        d.insert(0, BeautifulSoup(f'<div class="case"><b>Case {html.escape(n)}</b><span>{html.escape(title)}</span></div>', "html.parser"))
        for h in d.find_all("h4"):
            p = soup.new_tag("p"); p["class"] = ["lbl"]; p.string = h.get_text(); h.replace_with(p)

# keep headings with the block that follows them
for h in soup.find_all(["h2", "h3"]):
    nxt = h.find_next_sibling()
    if nxt is None or not isinstance(nxt, Tag): continue
    ok = nxt.name in ("p", "ul", "ol") or (nxt.name == "table" and len(nxt.find_all("tr")) <= 14) \
        or (nxt.name == "pre" and "long" not in (nxt.get("class") or []) and nxt.get_text().count("\n") < 22) \
        or (nxt.name == "div" and "short" in (nxt.get("class") or []))
    if not ok: continue
    w = soup.new_tag("div"); w["class"] = ["keep"]
    h.insert_before(w); w.append(h.extract()); w.append(nxt.extract())

# ---------- split into parts ----------
top = [c for c in soup.contents if isinstance(c, Tag)]
parts = []
for el in top:
    if el.name == "h1":
        parts.append({"h1": el, "items": []})
    elif parts:
        parts[-1]["items"].append(el)

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
def esc(s): return html.escape(s)

def chapter_head(h):
    t = " ".join(h.get_text(" ", strip=True).split())
    m = re.match(r"Chapter (\d+)\.\s*(.*)", t)
    h["id"] = slug(t)
    h["class"] = ["chap"]
    h.clear()
    if m:
        h.append(BeautifulSoup(f"<span><small>Chapter {m.group(1)}</small>{esc(m.group(2))}</span>", "html.parser"))
        return (f"Ch {m.group(1)}", m.group(1), m.group(2), h["id"])
    h.append(BeautifulSoup(f"<span>{esc(t)}</span>", "html.parser"))
    return ("", "", t, h["id"])

ACC = ["#ff8a2a", "#ffd36b", "#ff8a2a", "#ffd36b", "#ff8a2a", "#ffd36b", "#ff8a2a"]
sections, contents, named = [], [], []
for idx, part in enumerate(parts):
    title = " ".join(part["h1"].get_text(" ", strip=True).split())
    m = re.match(r"(Part \d+|Start here|Back):\s*(.*)", title)
    kicker, ptitle = m.group(1), m.group(2)
    items = part["items"]
    lead = items.pop(0) if items and items[0].name == "p" else None
    chs = [chapter_head(h) for it in items for h in ([it] if it.name == "h2" else it.find_all("h2", recursive=False))]
    pid = f"part-{idx}"
    short = {"Start here": "Start", "Back": "Back"}.get(kicker, kicker)
    contents.append(f'<div class="c-part"><b>{esc(short)}</b><i>{esc(ptitle)}</i><span>{pages.get(pid, "")}</span></div>')
    if kicker.startswith("Part"):
        for lab, num, t, cid in chs:
            contents.append(f'<div class="c-ch"><b>{num}</b><i>{esc(t)}</i><span>{pages.get(cid, "")}</span></div>')
    body = "".join(str(e) for e in items)
    if kicker == "Start here":
        # shares the contents sheet
        sections.append(("start", pid, body))
        continue
    named.append(f'@page p{idx} {{ @bottom-left {{ content: "{esc(kicker)} \\00B7  {esc(ptitle)}"; }} }}')
    toc = "".join(f'<div><b>{esc(lab)}</b><i>{esc(t)}</i><span>{pages.get(cid, "")}</span></div>' for lab, num, t, cid in chs if lab)
    if not toc:
        toc = "".join(f'<div><b>{"&#9632;"}</b><i>{esc(t)}</i><span>{pages.get(cid, "")}</span></div>' for lab, num, t, cid in chs)
    cls = "flow gl" if kicker == "Back" else "flow"
    sections.append(("part", pid, f'''
<section class="partwrap" id="{pid}" style="page:p{idx}">
  <div class="ophead">
    <div class="band"><canvas data-frost="band" data-seed="{idx * 13 + 7}" data-accent="{ACC[idx % len(ACC)]}" width="1360" height="176"></canvas></div>
    <div class="ophd">
      <div><div class="partno">{esc(kicker)}</div><h2 class="chap-h">{esc(ptitle)}</h2>{f'<p class="lead">{lead.decode_contents()}</p>' if lead else ''}</div>
      <div class="toc">{toc}</div>
    </div>
  </div>
  <div class="{cls}">{body}</div>
</section>'''))

start_body = next(b for k, p, b in sections if k == "start")
nparts = sum(1 for p in parts if p["h1"].get_text().startswith("Part"))
nch = len(soup.select("h2.chap small"))
front = f'''
<section class="flow ct" id="part-0" style="page:front">
  <div class="partno">Contents</div>
  <h2 class="bigh">What is inside</h2>
  {"".join(contents)}
  {start_body}
</section>'''

css = open(os.path.join(HERE, "book.css")).read() + "\n" + "\n".join(named)
js = open(os.path.join(DESIGN, "ember.js")).read() + "\n" + open(os.path.join(DESIGN, "frost.js")).read()
HEAD = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NixOS: The Declarative Manual</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;600;700&family=Silkscreen&family=VT323&family=IBM+Plex+Sans:ital,wght@0,400;0,600;1,400&display=swap">
<style>{css}
html{{counter-reset:page /*START*/0}}</style></head><body>'''
FOOT = f'''<script>{js.replace("</script", "<\\/script")}</script>
<script>Ember.frostInit(); document.documentElement.dataset.ready = "1";</script>
</body></html>'''
cover = f'''
<section class="cov" style="page:cover">
  <canvas class="art" data-frost="cover" data-seed="2605" width="1360" height="960"></canvas>
  <div class="ttl">
    <div class="kicker">A field book for systems you can rebuild</div>
    <h1>NIXOS<span>THE DECLARATIVE MANUAL</span></h1>
    <div class="sub">declare <i>&gt;</i> build <i>&gt;</i> switch <i>&gt;</i> roll back</div>
  </div>
  <div class="foot">Study on paper &middot; {nparts} parts &middot; {nch} chapters &middot; flakes in depth</div>
</section>'''
back = f'''
<section class="cov" style="page:cover">
  <canvas class="art" data-frost="cover" data-seed="1103" width="1360" height="960"></canvas>
  <div class="ttl">
    <div class="kicker">The end of the book, the start of your config</div>
    <div class="sub">If it builds, switch. <i>If it breaks, roll back.</i></div>
    <p class="blurb">{nch} chapters on the parts of Nix and NixOS that matter: the store, the language, the module system, everyday configuration, a full part on flakes, packaging, overlays, Home Manager, and a workshop of real errors, whole-config recipes and exercises with answers. Made to be printed and studied with a pencil.</p>
  </div>
</section>'''
parts_html = [b for k, p, b in sections if k == "part"]
# Each segment is printed on its own so the banner bleed never leaks onto the previous page.
segs = [cover + front] + parts_html[:-1] + [parts_html[-1] + back]
for i, s in enumerate(segs):
    open(f"{W}/seg-{i:02d}.html", "w").write(HEAD + s + FOOT)
open(f"{W}/book.html", "w").write(HEAD + "".join(segs) + FOOT)
print("parts", len(parts), "chapters", nch, "segments", len(segs))
