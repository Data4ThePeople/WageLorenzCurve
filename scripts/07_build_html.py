"""Build dist/index.html: one self-contained page (no CDN, no library).

Inlines src/core.js, the data (data/build/lorenz.json, gzip + base64, decoded in
the browser with the native DecompressionStream) and both D4TP logos. Then
parse-checks the script with macOS jsc and loads the page in headless Chrome
(full page, embed, change-over-time view) and stops on any JavaScript error.
"""
import base64, gzip, os, re, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DIST = os.path.join(ROOT, "src"), os.path.join(ROOT, "dist")
JSC = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def inline_logo(path, cls):
    svg = open(path).read()
    svg = svg[svg.index("<svg"):]
    svg = svg.replace("<svg ", f'<svg class="{cls}" role="img" aria-label="Data 4 The People" ', 1)
    svg = svg.replace("<style>.cls-1{fill:#fff;}</style>", "").replace('class="cls-1"', 'fill="#fff"')
    return svg


html = open(os.path.join(SRC, "template.html")).read()
core = open(os.path.join(SRC, "core.js")).read()
data = open(os.path.join(ROOT, "data/build/lorenz.json"), "rb").read()
b64 = base64.b64encode(gzip.compress(data, 9)).decode("ascii")
for marker, value in [("/*__CORE__*/", core), ("/*__DATA__*/", f'const DATA_B64 = "{b64}";'),
                      ("<!--__LOGO_ON_LIGHT__-->", inline_logo(os.path.join(ROOT, "assets/d4tp-text-dark.svg"), "logo logo-light")),
                      ("<!--__LOGO_ON_DARK__-->", inline_logo(os.path.join(ROOT, "assets/d4tp-text-light_3.svg"), "logo logo-dark"))]:
    assert html.count(marker) == 1, f"marker {marker} must appear exactly once"
    html = html.replace(marker, value)
assert not re.search(r"""(src|href)=["']https?://""", html), "external resource found; the page must be self-contained"

if os.path.exists(JSC):
    i = html.index("<script>") + 8
    js = html[i:html.index("</script>", i)].replace(b64, "")
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/page.js", "w").write(js)
        open(f"{d}/chk.js", "w").write('try{ new Function("return (async()=>{})")(); new Function(read("%s/page.js")); print("ok") }catch(e){ print("PARSE ERROR: "+e) }' % d)
        out = subprocess.run([JSC, f"{d}/chk.js"], capture_output=True, text=True).stdout.strip()
    assert out == "ok", out

os.makedirs(DIST, exist_ok=True)
out_path = os.path.join(DIST, "index.html")
open(out_path, "w").write(html)
print(f"wrote {out_path}: {os.path.getsize(out_path) / 1e6:.2f} MB (data {len(b64) / 1e6:.2f} MB base64)")

if os.path.exists(CHROME):
    probe = html.replace("<script>", '<script>window.onerror=(m,u,l,c)=>{document.body.setAttribute("data-err",m+" @"+l+":"+c)};'
                         'window.addEventListener("unhandledrejection",e=>document.body.setAttribute("data-err","promise: "+e.reason));', 1)
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/probe.html", "w").write(probe)
        for mode in ("", "#embed=1", "#area=36&view=history", "#area=35620&cmp=00000&embed=1"):
            dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=6000", "--window-size=1200,900",
                                  "--dump-dom", f"file://{d}/probe.html{mode}"], capture_output=True, text=True, timeout=180).stdout
            err = re.search(r'data-err="([^"]*)"', dom)
            assert dom and not err, f"JavaScript error ({mode or 'full page'}): {err.group(1) if err else 'no output from Chrome'}"
            sub = re.search(r'id="sub"[^>]*>([^<]*)<', dom)
            print(f"  ok {mode or 'full page':32s} -> {sub.group(1) if sub else '?'}")
