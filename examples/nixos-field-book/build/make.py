"""usage: python3 make.py <workdir> <out.pdf>  -- full two-pass build"""
import sys, os, glob, subprocess
from pypdf import PdfReader, PdfWriter
B = os.path.dirname(os.path.abspath(__file__)); W, OUT = sys.argv[1], sys.argv[2]
os.makedirs(W, exist_ok=True)
with open(f"{W}/book.md", "w") as f:
    for p in sorted(glob.glob(f"{B}/../src/*.md")): f.write(open(p).read() + "\n\n")
subprocess.run(["pandoc", f"{W}/book.md", "-f", "markdown-smart-auto_identifiers", "-t", "html5", "--no-highlight", "-o", f"{W}/body.html"], check=True)

def render(dst):
    for f in glob.glob(f"{W}/seg-*.html"): os.remove(f)
    subprocess.run(["python3", f"{B}/build.py", W], check=True)
    start, out = 0, PdfWriter()
    for seg in sorted(glob.glob(f"{W}/seg-*.html")):
        src = open(seg).read().replace("/*START*/0", str(start))
        open(seg, "w").write(src)
        pdf = seg[:-5] + ".pdf"
        subprocess.run(["node", f"{B}/render.js", seg, pdf], check=True)
        r = PdfReader(pdf); start += len(r.pages)
        for pg in r.pages: out.add_page(pg)
    out.write(dst); return start

if os.path.exists(f"{W}/pagenums.json"): os.remove(f"{W}/pagenums.json")
render(f"{W}/pass1.pdf")
subprocess.run(["python3", f"{B}/pagenums.py", f"{W}/pass1.pdf", W], check=True)
n = render(OUT)
print("pages", n)
