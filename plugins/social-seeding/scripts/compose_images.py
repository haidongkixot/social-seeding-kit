"""Compose post pictures (1080x1350) from source pictures, driven by a JSON spec.

Usage: python scripts/compose_images.py spec.json
Spec (paths relative to the spec file):
  {"jobs": [
    {"layout": "top_and_strip", "out": "01.jpg", "top": "design.png", "top_crop_ratio": 0.79,
     "products": ["a.png", "b.png", "c.png"]},
    {"layout": "two_stacked", "out": "02.jpg", "a": "x.png", "a_y": 0.17, "b": "y.png", "b_y": 0.04}]}
top_crop_ratio crops the bottom band off a design (for example a QR code or contact band) when a
warm-up period forbids links or contact codes.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

W, H = 1080, 1350


def load(p: Path) -> Image.Image:
    im = Image.open(p)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")


def trim(im: Image.Image, pad: int = 10) -> Image.Image:
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    diff = diff.point(lambda v: 255 if v > 18 else 0)
    box = diff.getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height)))


def fit(im: Image.Image, w: int, h: int) -> Image.Image:
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def top_and_strip(top: Image.Image, top_crop_ratio: float, products: list[Image.Image]) -> Image.Image:
    """A Page design (QR band cropped off) on top, a white strip of product packs below."""
    t = top.crop((0, 0, top.width, int(top.height * top_crop_ratio)))
    t = t.resize((W, int(t.height * W / t.width)), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(t, (0, 0))
    strip_top = t.height + 10
    strip_h = H - strip_top - 20
    cell = W // len(products)
    for i, p in enumerate(products):
        f = fit(trim(p), cell - 30, strip_h)
        canvas.paste(f, (i * cell + (cell - f.width) // 2, strip_top + (strip_h - f.height) // 2))
    return canvas


def two_stacked(a: Image.Image, a_y: float, b: Image.Image, b_y: float) -> Image.Image:
    """Two square Page designs, each cropped to a 1080x675 band starting at the given height ratio."""
    canvas = Image.new("RGB", (W, H), "white")
    for k, (im, y) in enumerate(((a, a_y), (b, b_y))):
        src_h = int(im.width * 675 / W)
        y0 = int(im.height * y)
        band = im.crop((0, y0, im.width, y0 + src_h)).resize((W, 675), Image.LANCZOS)
        canvas.paste(band, (0, 675 * k))
    return canvas


def main(spec_path: str) -> int:
    spec_file = Path(spec_path)
    spec = json.loads(spec_file.read_text(encoding="utf-8-sig"))
    base = spec_file.parent
    for job in spec["jobs"]:
        if job["layout"] == "top_and_strip":
            im = top_and_strip(load(base / job["top"]), job["top_crop_ratio"], [load(base / q) for q in job["products"]])
        elif job["layout"] == "two_stacked":
            im = two_stacked(load(base / job["a"]), job["a_y"], load(base / job["b"]), job["b_y"])
        else:
            raise SystemExit(f"unknown layout {job['layout']!r}")
        out = base / job["out"]
        im.save(out, quality=90)
        print(out)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
