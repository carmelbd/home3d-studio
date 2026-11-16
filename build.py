"""Build app/index.html (the web designer) from the Home Assistant card's designer.

The designer lives in the ha-home-3d repo (floor-designer.html). This script copies it and
switches it to web mode: no "Export to HA" or wall-display buttons, its own saved-design key,
and a link back to the site's home page. Run after every designer update:

    python3 build.py                      # expects ../ha-home-3d next to this repo
    python3 build.py path/to/floor-designer.html
"""
import pathlib, sys

root = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / "ha-home-3d" / "floor-designer.html"
html = src.read_text()


def swap(old, new):
    global html
    if html.count(old) != 1:
        sys.exit(f"build.py: expected exactly one {old!r} in {src} (the designer changed; update build.py)")
    html = html.replace(old, new)


swap("<title>Home Floor Designer</title>", "<title>Home 3D Studio — Designer</title>")
swap("const KEY='ha-floor-designer-v1'", "const KEY='home3d-studio-v1'")
swap('<div class="brand"><b>🏠 Floor Designer</b><small>for Home Assistant</small></div>',
     '<a class="brand" href="../" style="color:inherit;text-decoration:none" title="Back to Home 3D Studio">'
     '<b>🏠 Home 3D Studio</b><small>Design your home</small></a>')
swap("</head>", "<style>#exportBtn,#wallBtn{display:none!important}</style>\n</head>")

out = root / "app" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print(f"Built {out.relative_to(root)} from {src} ({len(html):,} bytes)")
