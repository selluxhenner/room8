"""Inline every asset into a single self-contained site/index.html.

Reads site/template.html, replaces {{TOKEN}} placeholders with data URIs built
from the project's logo, room photos, member avatars and app screenshots.
Run:  python site/build.py
"""
import base64
import io
import pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


def data_uri(mime, blob):
    return "data:%s;base64,%s" % (mime, base64.b64encode(blob).decode("ascii"))


def jpeg(path, width, quality=80):
    im = Image.open(path).convert("RGB")
    if im.width > width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return data_uri("image/jpeg", buf.getvalue())


def png_trimmed(path, width):
    im = Image.open(path).convert("RGBA")
    box = im.split()[3].getbbox()          # crop the transparent margin off the logo
    if box:
        im = im.crop(box)
    if im.width > width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return data_uri("image/png", buf.getvalue())


ASSETS = {
    "LOGO": lambda: png_trimmed(ROOT / "image-removebg-preview.png", 560),
    "ROOM1": lambda: jpeg(ROOT / "design/room1.jpg", 900),
    "ROOM2": lambda: jpeg(ROOT / "design/room2.jpg", 900),
    "ROOM3": lambda: jpeg(ROOT / "design/room3.jpg", 900),
    "AIMEE": lambda: jpeg(ROOT / "design/aimee.jpg", 200, 82),
    "SIMON": lambda: jpeg(ROOT / "design/simon.jpg", 200, 82),
    "VICTOR": lambda: jpeg(ROOT / "design/victor.jpg", 200, 82),
    "KEVIN": lambda: jpeg(ROOT / "design/kevin.jpg", 200, 82),
    "SHOT_SWIPE": lambda: jpeg(ROOT / "screenshots/room8-swipe.png", 620),
    "SHOT_GROUPS": lambda: jpeg(ROOT / "screenshots/room8-groups.png", 620),
    "SHOT_DETAIL": lambda: jpeg(ROOT / "screenshots/room8-group-detail.png", 620),
    "SHOT_PROGRESS": lambda: jpeg(ROOT / "screenshots/room8-in-progress.png", 620),
    "SHOT_PROFILE": lambda: jpeg(ROOT / "screenshots/room8-profile.png", 620),
    "SHOT_EMPTY": lambda: jpeg(ROOT / "screenshots/room8-swipe-empty.png", 620),
    "SHOT_BRAND": lambda: jpeg(ROOT / "screenshots/room8-brand.png", 1400, 84),
    # not an image: the small green check that bullets the feature lists
    "TICK": lambda: (
        '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2F5D50" '
        'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M4 12.5 L9.5 18 L20 6"></path></svg>'
    ),
}

WRAPPER = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="room8 - you swipe on households, not people. A preview of the Berlin flatshare app: interactive demo, every screen, and the design system.">
%(head)s
</head>
<body>
%(body)s
</body>
</html>
"""


def split_head(html):
    """Pull <title>/<link>/<style> out of the template so index.html gets a real <head>."""
    end = html.index("</style>") + len("</style>")
    return html[:end], html[end:].lstrip("\n")


def main():
    html = (SITE / "template.html").read_text(encoding="utf-8")
    for name, make in ASSETS.items():
        token = "{{%s}}" % name
        if token not in html:
            print("  ! unused asset:", name)
            continue
        value = make()
        html = html.replace(token, value)
        print("  %-14s %7.1f KB" % (name, len(value) / 1024))
    leftover = [t for t in html.split("{{")[1:] if "}}" in t]
    if leftover:
        raise SystemExit("unreplaced placeholders: %s" % [t.split("}}")[0] for t in leftover])

    # artifact.html keeps the flat form the Artifact publisher expects (no doctype/head/body)
    art = SITE / "artifact.html"
    art.write_text(html, encoding="utf-8")

    head, body = split_head(html)
    out = SITE / "index.html"
    out.write_text(WRAPPER % {"head": head, "body": body}, encoding="utf-8")

    for f in (out, art):
        print("wrote %s  (%.2f MB)" % (f, f.stat().st_size / 1048576))


if __name__ == "__main__":
    main()
