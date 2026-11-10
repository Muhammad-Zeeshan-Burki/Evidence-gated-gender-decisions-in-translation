"""Minimal SVG toolkit for the schematic figures (units: millimetres).

Text is set in Arial (Liberation Sans, which has identical metrics, is used when Arial is absent). The SVG masters keep
all text as editable text. render() writes a vector PDF with embedded fonts and a 300-dpi PNG preview through headless
Chromium.
"""
import html
from pathlib import Path

from PIL import ImageFont

FONT_FAMILY = "Arial, 'Liberation Sans', Helvetica, sans-serif"
# Text widths are measured with Liberation Sans or Arial (identical metrics); the first file found is used.
_CANDIDATES = {
    "n": ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "C:/Windows/Fonts/arial.ttf",
          "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"],
    "b": ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
          "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"],
    "i": ["/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf", "C:/Windows/Fonts/ariali.ttf",
          "/System/Library/Fonts/Supplemental/Arial Italic.ttf", "/Library/Fonts/Arial Italic.ttf"],
    "bi": ["/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf", "C:/Windows/Fonts/arialbi.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf", "/Library/Fonts/Arial Bold Italic.ttf"],
}
_FONT_FILES = {k: next((p for p in v if Path(p).exists()), v[0]) for k, v in _CANDIDATES.items()}
_FONTS = {}
PT = 0.352778  # mm per point

# Palette (Okabe-Ito based, restrained)
INK = "#1F2328"
GREY = "#6B7178"
LIGHT = "#C9CED4"
PALE = "#F1F3F5"
BLUE = "#0072B2"       # CCL-Gate accent
SKY = "#56B4E9"
SLATE = "#355C7D"      # correct
VERM = "#D55E00"       # wrong / unwarranted
EVID = "#E3ECF5"       # evidence sentence fill
EVID_S = "#4F7396"
LLMF = "#F4EFE6"       # LLM-call header
LLMS = "#9C8A6A"
DETF = "#E6F0F8"       # deterministic / calibrated header
DETS = "#4F7396"


def _font(style, size_pt):
    key = (style, round(size_pt * 20))
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(_FONT_FILES[style], size=int(size_pt * 20))
    return _FONTS[key]


def text_width(segments, size_pt):
    """Width in mm of a run given as [(text, style)], style in n, b, i, bi, sub, sup, isub."""
    w = 0.0
    for t, st in segments:
        base = {"sub": "n", "sup": "n", "isub": "i", "isup": "i"}.get(st, st)
        f = 0.7 if st in ("sub", "sup", "isub", "isup") else 1.0
        w += _font(base, size_pt * f).getlength(t) / 20 * PT
    return w


class SVG:
    def __init__(self, width_mm, height_mm):
        self.w, self.h = width_mm, height_mm
        self.items = []

    # ------------------------------------------------------------------ primitives
    def rect(self, x, y, w, h, fill="none", stroke="none", sw=0.25, rx=0.0, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.items.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" rx="{rx:.3f}" '
                          f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:.3f}"{d}{o}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=0.25, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{stroke}" '
                          f'stroke-width="{sw:.3f}" stroke-linecap="{cap}"{d}/>')

    def path(self, d, stroke=INK, sw=0.25, fill="none", dash=None):
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw:.3f}" fill="{fill}"{dd}/>')

    def circle(self, cx, cy, r, fill="none", stroke="none", sw=0.25):
        self.items.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:.3f}"/>')

    def arrow(self, x1, y1, x2, y2, stroke=INK, sw=0.3, head=1.1):
        """Straight arrow with a filled triangular head at (x2, y2)."""
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, stroke=stroke, sw=sw)
        px, py = -math.sin(ang) * head * 0.45, math.cos(ang) * head * 0.45
        self.items.append(f'<path d="M{x2:.3f},{y2:.3f} L{bx + px:.3f},{by + py:.3f} L{bx - px:.3f},{by - py:.3f} Z" '
                          f'fill="{stroke}" stroke="none"/>')

    def text(self, x, y, segments, size_pt=6.5, fill=INK, anchor="start", weight=None, strike=False, opacity=None):
        """Text run. segments: str or [(text, style)] with style in n, b, i, bi, sub, sup, isub, isup.
        (x, y) is the baseline start (or middle/end for other anchors)."""
        if isinstance(segments, str):
            segments = [(segments, "b" if weight == "bold" else "n")]
        size = size_pt * PT
        out = []
        shift = 0.0
        for t, st in segments:
            t_esc = html.escape(t)
            attrs = []
            if st in ("b", "bi"):
                attrs.append('font-weight="bold"')
            if st in ("i", "bi", "isub", "isup"):
                attrs.append('font-style="italic"')
            if st in ("sub", "isub", "sup", "isup"):
                target = size * 0.32 if st in ("sub", "isub") else -size * 0.38
                attrs.append(f'font-size="{size * 0.7:.3f}" dy="{target - shift:.3f}"')
                shift = target
            elif shift:
                attrs.append(f'dy="{-shift:.3f}"')
                shift = 0.0
            out.append(f'<tspan {" ".join(attrs)}>{t_esc}</tspan>' if attrs else f"<tspan>{t_esc}</tspan>")
        deco = ' text-decoration="line-through"' if strike else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.items.append(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size:.3f}" fill="{fill}" text-anchor="{anchor}"'
                          f'{deco}{o} xml:space="preserve">{"".join(out)}</text>')

    def strike(self, x, y, w, size_pt, stroke=VERM, sw=0.3):
        """Horizontal strike line through a text run starting at x with baseline y."""
        yy = y - size_pt * PT * 0.32
        self.line(x - 0.3, yy, x + w + 0.3, yy, stroke=stroke, sw=sw)

    def label(self, x, y, letter):
        self.text(x, y, [(letter, "b")], size_pt=8)

    # ------------------------------------------------------------------ output
    def svg(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" '
                f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT_FAMILY}">')
        return head + "\n<rect width=\"100%\" height=\"100%\" fill=\"#FFFFFF\"/>\n" + "\n".join(self.items) + "\n</svg>\n"

    def save(self, path):
        Path(path).write_text(self.svg(), encoding="utf-8")


def render(svg_path, pdf_path, png_path, width_mm, height_mm, dpi=300):
    from playwright.sync_api import sync_playwright
    svg = Path(svg_path).read_text(encoding="utf-8")
    page_html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
    @page {{ size: {width_mm}mm {height_mm}mm; margin: 0; }}
    html, body {{ margin: 0; padding: 0; background: #fff; }}
    svg {{ display: block; }}</style></head><body>{svg}</body></html>"""
    px_w = round(width_mm / 25.4 * 96)
    px_h = round(height_mm / 25.4 * 96)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": px_w, "height": px_h}, device_scale_factor=dpi / 96)
        pg.set_content(page_html)
        pg.wait_for_timeout(200)
        pg.pdf(path=str(pdf_path), width=f"{width_mm}mm", height=f"{height_mm}mm", print_background=True,
               margin=dict(top="0", bottom="0", left="0", right="0"))
        pg.screenshot(path=str(png_path), full_page=False, clip=dict(x=0, y=0, width=px_w, height=px_h))
        b.close()
