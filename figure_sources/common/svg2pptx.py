"""Converts a figure SVG master into a PowerPoint file whose content is native, editable PowerPoint shapes and text.

Every path, line, rectangle, circle and text element of the SVG becomes a PowerPoint object at the same position, size and
colour, so text, colours and positions can be edited directly in PowerPoint. Text is set in Arial, which has the same
metrics as the Liberation Sans used to draw the figures. Clipping to plot areas is applied geometrically. The slide has
the size of the figure, and each plot panel is a separate group.

Usage:
    python3 svg2pptx.py input.svg output.pptx
"""
import math
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree
from PIL import ImageFont
from pptx import Presentation
from pptx.oxml import parse_xml
from pptx.util import Emu

SVGNS = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
NSDECL = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
EMU_PER_PT = 12700
ASCENT = 0.905          # Arial / Liberation Sans ascent (fraction of the font size)
LINE = 1.15             # single line height used for the text-box extent
INHERITED = {"fill", "stroke", "stroke-width", "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "font-size",
             "font-family", "font-weight", "font-style", "text-anchor", "fill-opacity", "stroke-opacity"}
NAMED = {"black": "000000", "white": "FFFFFF", "red": "FF0000", "blue": "0000FF", "green": "008000", "gray": "808080",
         "grey": "808080"}

# ---------------------------------------------------------------- fonts for measuring text widths
_FONT_CANDIDATES = {
    (False, False): ["/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "C:/Windows/Fonts/arial.ttf",
                     "/System/Library/Fonts/Supplemental/Arial.ttf"],
    (True, False): ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
                    "/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
    (False, True): ["/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf", "C:/Windows/Fonts/ariali.ttf",
                    "/System/Library/Fonts/Supplemental/Arial Italic.ttf"],
    (True, True): ["/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf", "C:/Windows/Fonts/arialbi.ttf",
                   "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"],
}
_FONTS = {}


def text_width_pt(text, size_pt, bold, italic):
    key = (bold, italic)
    if key not in _FONTS:
        path = next((p for p in _FONT_CANDIDATES[key] if Path(p).exists()), None)
        _FONTS[key] = ImageFont.truetype(path, 100) if path else None
    f = _FONTS[key]
    if f is None:
        return 0.55 * size_pt * len(text)
    return f.getlength(text) / 100.0 * size_pt


# ---------------------------------------------------------------- affine transforms (a, b, c, d, e, f)
IDENT = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mul(m, n):
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def parse_transform(s):
    m = IDENT
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(t) for t in re.split(r"[\s,]+", args.strip()) if t]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = mul(mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "matrix":
            t = tuple(v)
        else:
            raise ValueError(f"unsupported transform {name}")
        m = mul(m, t)
    return m


def scale_of(m):
    return math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))


# ---------------------------------------------------------------- styles
def num(v, default=0.0):
    if v is None:
        return default
    mt = re.match(r"\s*([-+]?[\d.]+(?:e[-+]?\d+)?)", str(v))
    return float(mt.group(1)) if mt else default


def colour(v):
    if v is None:
        return None
    v = v.strip()
    if v in ("none", "transparent"):
        return None
    if v.startswith("#"):
        h = v[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        return h.upper()
    if v.lower() in NAMED:
        return NAMED[v.lower()]
    mt = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", v)
    if mt:
        return "".join(f"{int(x):02X}" for x in mt.groups())
    raise ValueError(f"unsupported colour {v}")


def own_style(el):
    st = {}
    for k in INHERITED | {"opacity"}:
        if el.get(k) is not None:
            st[k] = el.get(k)
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            st[k.strip()] = v.strip()
    return st


def inherit(parent, el, extra=None):
    st = {k: v for k, v in parent.items() if k in INHERITED}
    st["_opacity"] = parent.get("_opacity", 1.0)
    if extra:
        st.update({k: v for k, v in extra.items() if k != "opacity"})
    own = own_style(el)
    st.update({k: v for k, v in own.items() if k != "opacity"})
    st["_opacity"] *= num(own.get("opacity"), 1.0)
    return st


# ---------------------------------------------------------------- path data
def parse_path(d):
    toks = re.findall(r"[MmLlHhVvCcSsQqTtZzAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d)
    i, cmd = 0, None
    subs, cur, x, y, sx, sy = [], None, 0.0, 0.0, 0.0, 0.0

    def nxt():
        nonlocal i
        i += 1
        return float(toks[i - 1])
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur["closed"] = True
                    x, y = sx, sy
                cur = None
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            nx, ny = nxt(), nxt()
            if rel:
                nx, ny = x + nx, y + ny
            x, y, sx, sy = nx, ny, nx, ny
            cur = {"segs": [("M", (x, y))], "closed": False}
            subs.append(cur)
            cmd = "l" if rel else "L"
        elif c in "LHV":
            if c == "L":
                nx, ny = nxt(), nxt()
                if rel:
                    nx, ny = x + nx, y + ny
            elif c == "H":
                nx, ny = nxt(), y
                if rel:
                    nx = x + nx
            else:
                nx, ny = x, nxt()
                if rel:
                    ny = y + ny
            if cur is None:
                cur = {"segs": [("M", (x, y))], "closed": False}
                subs.append(cur)
            cur["segs"].append(("L", (nx, ny)))
            x, y = nx, ny
        elif c == "C":
            p = [nxt() for _ in range(6)]
            if rel:
                p = [p[0] + x, p[1] + y, p[2] + x, p[3] + y, p[4] + x, p[5] + y]
            if cur is None:
                cur = {"segs": [("M", (x, y))], "closed": False}
                subs.append(cur)
            cur["segs"].append(("C", (p[0], p[1]), (p[2], p[3]), (p[4], p[5])))
            x, y = p[4], p[5]
        elif c == "Q":
            p = [nxt() for _ in range(4)]
            if rel:
                p = [p[0] + x, p[1] + y, p[2] + x, p[3] + y]
            c1 = (x + 2 / 3 * (p[0] - x), y + 2 / 3 * (p[1] - y))
            c2 = (p[2] + 2 / 3 * (p[0] - p[2]), p[3] + 2 / 3 * (p[1] - p[3]))
            if cur is None:
                cur = {"segs": [("M", (x, y))], "closed": False}
                subs.append(cur)
            cur["segs"].append(("C", c1, c2, (p[2], p[3])))
            x, y = p[2], p[3]
        else:
            raise ValueError(f"unsupported path command {cmd}")
    return subs


def transform_subs(subs, m):
    out = []
    for s in subs:
        segs = []
        for seg in s["segs"]:
            segs.append((seg[0],) + tuple(apply(m, *p) for p in seg[1:]))
        out.append({"segs": segs, "closed": s["closed"]})
    return out


def bbox_subs(subs):
    xs = [p[0] for s in subs for seg in s["segs"] for p in seg[1:]]
    ys = [p[1] for s in subs for seg in s["segs"] for p in seg[1:]]
    return min(xs), min(ys), max(xs), max(ys)


def flatten(sub, n=12):
    pts = []
    for seg in sub["segs"]:
        if seg[0] in ("M", "L"):
            pts.append(seg[1])
        else:
            p0 = pts[-1]
            c1, c2, p3 = seg[1], seg[2], seg[3]
            for k in range(1, n + 1):
                t = k / n
                mt = 1 - t
                pts.append((mt ** 3 * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t ** 3 * p3[0],
                            mt ** 3 * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t ** 3 * p3[1]))
    return pts


def clip_polygon(pts, r):
    xmin, ymin, xmax, ymax = r

    def clip(poly, inside, inter):
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]
            if inside(b):
                if not inside(a):
                    out.append(inter(a, b))
                out.append(b)
            elif inside(a):
                out.append(inter(a, b))
        return out

    def ix(a, b, x0):
        t = (x0 - a[0]) / (b[0] - a[0])
        return (x0, a[1] + t * (b[1] - a[1]))

    def iy(a, b, y0):
        t = (y0 - a[1]) / (b[1] - a[1])
        return (a[0] + t * (b[0] - a[0]), y0)
    poly = list(pts)
    for inside, inter in [(lambda p: p[0] >= xmin, lambda a, b: ix(a, b, xmin)), (lambda p: p[0] <= xmax, lambda a, b: ix(a, b, xmax)),
                          (lambda p: p[1] >= ymin, lambda a, b: iy(a, b, ymin)), (lambda p: p[1] <= ymax, lambda a, b: iy(a, b, ymax))]:
        if not poly:
            break
        poly = clip(poly, inside, inter)
    return poly


def clip_segment(a, b, r):
    xmin, ymin, xmax, ymax = r
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - xmin), (dx, xmax - a[0]), (-dy, a[1] - ymin), (dy, ymax - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if t0 > t1:
        return None
    return (a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy)


def clip_subs(subs, r, filled):
    eps = 1e-6
    x0, y0, x1, y1 = bbox_subs(subs)
    if x0 >= r[0] - eps and y0 >= r[1] - eps and x1 <= r[2] + eps and y1 <= r[3] + eps:
        return subs
    if x1 < r[0] or x0 > r[2] or y1 < r[1] or y0 > r[3]:
        return []
    out = []
    for s in subs:
        pts = flatten(s)
        if filled:
            poly = clip_polygon(pts, r)
            if len(poly) >= 3:
                out.append({"segs": [("M", poly[0])] + [("L", p) for p in poly[1:]], "closed": True})
        else:
            if s["closed"]:
                pts = pts + [pts[0]]
            run = []
            for a, b in zip(pts[:-1], pts[1:]):
                c = clip_segment(a, b, r)
                if c is None:
                    if len(run) > 1:
                        out.append({"segs": [("M", run[0])] + [("L", p) for p in run[1:]], "closed": False})
                    run = []
                    continue
                if not run or abs(run[-1][0] - c[0][0]) > 1e-9 or abs(run[-1][1] - c[0][1]) > 1e-9:
                    if len(run) > 1:
                        out.append({"segs": [("M", run[0])] + [("L", p) for p in run[1:]], "closed": False})
                    run = [c[0]]
                run.append(c[1])
            if len(run) > 1:
                out.append({"segs": [("M", run[0])] + [("L", p) for p in run[1:]], "closed": False})
    return out


# ---------------------------------------------------------------- converter
class Converter:
    def __init__(self, svg_path):
        self.tree = etree.parse(str(svg_path))
        self.root = self.tree.getroot()
        vb = [float(v) for v in re.split(r"[\s,]+", self.root.get("viewBox").strip())]
        self.vb = vb
        w = self.root.get("width")
        self.width_mm = self._to_mm(w, vb[2])
        self.height_mm = self._to_mm(self.root.get("height"), vb[3])
        self.emu = self.width_mm * 36000.0 / vb[2]                  # EMU per user unit
        self.ids = {el.get("id"): el for el in self.root.iter() if isinstance(el.tag, str) and el.get("id")}
        self.defaults = {"fill": "#000000"}
        for st in self.root.iter(f"{{{SVGNS}}}style"):
            for body in re.findall(r"\*\s*\{([^}]*)\}", st.text or ""):
                for part in body.split(";"):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        self.defaults[k.strip()] = v.strip()
        self.groups = []           # list of (name, [xml strings]) in drawing order
        self.cur = None
        self.next_id = 2

    @staticmethod
    def _to_mm(v, fallback):
        if v is None:
            return fallback * 25.4 / 72
        mt = re.match(r"([\d.]+)\s*(mm|pt|px|in|cm)?", v)
        val, unit = float(mt.group(1)), mt.group(2) or "px"
        return val * {"mm": 1, "cm": 10, "in": 25.4, "pt": 25.4 / 72, "px": 25.4 / 96}[unit]

    # ------------------------------------------------ traversal
    def run(self):
        st = dict(self.defaults)
        st["_opacity"] = 1.0
        root_style = inherit(st, self.root)
        m = (1, 0, 0, 1, -self.vb[0], -self.vb[1])
        self._open_group("Figure")
        for ch in self.root:
            self.walk(ch, m, root_style, None, top=True)
        return self

    def _open_group(self, name):
        self.cur = (name, [])
        self.groups.append(self.cur)

    def walk(self, el, m, st, clip, top=False):
        if not isinstance(el.tag, str):
            return
        tag = etree.QName(el).localname
        if tag in ("defs", "clipPath", "metadata", "title", "style", "desc"):
            return
        m2 = mul(m, parse_transform(el.get("transform"))) if tag != "text" else m
        st2 = inherit(st, el)
        clip2 = clip
        if el.get("clip-path"):
            ref = self.ids.get(re.search(r"#([^)]+)", el.get("clip-path")).group(1))
            rect = [c for c in ref if isinstance(c.tag, str) and etree.QName(c).localname == "rect"][0]
            x, y, w, h = (num(rect.get(k)) for k in ("x", "y", "width", "height"))
            corners = [apply(m2, x, y), apply(m2, x + w, y), apply(m2, x, y + h), apply(m2, x + w, y + h)]
            r = (min(c[0] for c in corners), min(c[1] for c in corners), max(c[0] for c in corners), max(c[1] for c in corners))
            clip2 = r if clip is None else (max(r[0], clip[0]), max(r[1], clip[1]), min(r[2], clip[2]), min(r[3], clip[3]))
        if tag == "g":
            gid = el.get("id") or ""
            if top or re.match(r"(axes|legend)_\d+$", gid):
                if re.match(r"(axes|legend)_\d+$", gid):
                    prev = self.cur
                    self._open_group(gid.replace("_", " ").capitalize())
                    for ch in el:
                        self.walk(ch, m2, st2, clip2)
                    self.cur = prev
                    self.groups.append(self.cur) if self.cur not in self.groups[-1:] else None
                    self._open_group("Figure")
                    return
            for ch in el:
                self.walk(ch, m2, st2, clip2)
        elif tag == "path":
            self.add_path(parse_path(el.get("d", "")), m2, st2, clip2)
        elif tag == "use":
            ref = self.ids[(el.get(f"{{{XLINK}}}href") or el.get("href"))[1:]]
            mu = mul(m2, (1, 0, 0, 1, num(el.get("x")), num(el.get("y"))))
            st3 = inherit(st2, ref)
            if etree.QName(ref).localname == "path":
                self.add_path(parse_path(ref.get("d", "")), mu, st3, clip2, name="Marker")
        elif tag == "line":
            x1, y1, x2, y2 = (num(el.get(k)) for k in ("x1", "y1", "x2", "y2"))
            self.add_path([{"segs": [("M", (x1, y1)), ("L", (x2, y2))], "closed": False}], m2, st2, clip2, name="Line")
        elif tag == "rect":
            self.add_rect(el, m2, st2, clip2)
        elif tag == "circle":
            cx, cy, r = (num(el.get(k)) for k in ("cx", "cy", "r"))
            self.add_ellipse(cx, cy, r, m2, st2, clip2)
        elif tag == "text":
            self.add_text(el, m, st, clip2)
        elif tag == "svg":
            for ch in el:
                self.walk(ch, m2, st2, clip2)

    # ------------------------------------------------ shape XML helpers
    def _id(self):
        self.next_id += 1
        return self.next_id

    def _fill_xml(self, st):
        c = colour(st.get("fill"))
        if c is None:
            return "<a:noFill/>"
        a = st.get("_opacity", 1.0) * num(st.get("fill-opacity"), 1.0)
        alpha = f'<a:alpha val="{int(round(a * 100000))}"/>' if a < 0.999 else ""
        return f'<a:solidFill><a:srgbClr val="{c}">{alpha}</a:srgbClr></a:solidFill>'

    def _ln_xml(self, st, m):
        c = colour(st.get("stroke"))
        if c is None:
            return "<a:ln><a:noFill/></a:ln>"
        sw = num(st.get("stroke-width"), 1.0) * scale_of(m)
        w = max(1, int(round(sw * self.emu)))
        cap = {"butt": "flat", "round": "rnd", "square": "sq"}.get(st.get("stroke-linecap", "butt"), "flat")
        join = {"round": "<a:round/>", "bevel": "<a:bevel/>"}.get(st.get("stroke-linejoin", "miter"), '<a:miter lim="800000"/>')
        a = st.get("_opacity", 1.0) * num(st.get("stroke-opacity"), 1.0)
        alpha = f'<a:alpha val="{int(round(a * 100000))}"/>' if a < 0.999 else ""
        dash = '<a:prstDash val="solid"/>'
        da = st.get("stroke-dasharray")
        if da and da != "none":
            vals = [num(v) * scale_of(m) for v in re.split(r"[\s,]+", da.strip()) if v]
            if len(vals) % 2:
                vals = vals * 2
            if sw > 0 and vals:
                ds = "".join(f'<a:ds d="{int(round(vals[k] / sw * 100000))}" sp="{int(round(vals[k + 1] / sw * 100000))}"/>'
                             for k in range(0, len(vals), 2))
                dash = f"<a:custDash>{ds}</a:custDash>"
        return (f'<a:ln w="{w}" cap="{cap}"><a:solidFill><a:srgbClr val="{c}">{alpha}</a:srgbClr></a:solidFill>'
                f"{dash}{join}</a:ln>")

    def _emit(self, xml):
        self.cur[1].append(xml)

    # ------------------------------------------------ paths
    def add_path(self, subs, m, st, clip, name="Shape"):
        if not subs:
            return
        subs = transform_subs(subs, m)
        filled = colour(st.get("fill")) is not None
        stroked = colour(st.get("stroke")) is not None
        if not filled and not stroked:
            return
        if clip is not None:
            subs = clip_subs(subs, clip, filled)
            if not subs:
                return
        x0, y0, x1, y1 = bbox_subs(subs)
        if (x0 <= 0.5 and y0 <= 0.5 and x1 >= self.vb[2] - 0.5 and y1 >= self.vb[3] - 0.5 and filled and not stroked
                and colour(st.get("fill")) == "FFFFFF"):
            return            # full-canvas white background
        E = self.emu
        ox, oy = int(round(x0 * E)), int(round(y0 * E))
        cx, cy = max(1, int(round((x1 - x0) * E))), max(1, int(round((y1 - y0) * E)))
        paths = []
        for s in subs:
            cmds = []
            for seg in s["segs"]:
                pts = [(int(round(p[0] * E)) - ox, int(round(p[1] * E)) - oy) for p in seg[1:]]
                pt = "".join(f'<a:pt x="{px}" y="{py}"/>' for px, py in pts)
                tag = {"M": "moveTo", "L": "lnTo", "C": "cubicBezTo"}[seg[0]]
                cmds.append(f"<a:{tag}>{pt}</a:{tag}>")
            if s["closed"]:
                cmds.append("<a:close/>")
            fill_attr = "" if (filled and s["closed"]) else ' fill="none"'
            stroke_attr = "" if stroked else ' stroke="0"'
            paths.append(f'<a:path w="{cx}" h="{cy}"{fill_attr}{stroke_attr}>{"".join(cmds)}</a:path>')
        sid = self._id()
        self._emit(f'<p:sp {NSDECL}><p:nvSpPr><p:cNvPr id="{sid}" name="{name} {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm><a:off x="{ox}" y="{oy}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                   f'<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
                   f'<a:pathLst>{"".join(paths)}</a:pathLst></a:custGeom>{self._fill_xml(st)}{self._ln_xml(st, m)}</p:spPr>'
                   f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-GB"/></a:p></p:txBody></p:sp>')

    def add_rect(self, el, m, st, clip):
        x, y = num(el.get("x")), num(el.get("y"))
        w = el.get("width")
        h = el.get("height")
        w = self.vb[2] if w == "100%" else num(w)
        h = self.vb[3] if h == "100%" else num(h)
        rx = num(el.get("rx"), 0.0)
        rotated = abs(m[1]) > 1e-9 or abs(m[2]) > 1e-9
        p0, p1 = apply(m, x, y), apply(m, x + w, y + h)
        X0, Y0, X1, Y1 = min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])
        inside = clip is None or (X0 >= clip[0] - 1e-6 and Y0 >= clip[1] - 1e-6 and X1 <= clip[2] + 1e-6 and Y1 <= clip[3] + 1e-6)
        if rotated or not inside:
            sub = [{"segs": [("M", (x, y)), ("L", (x + w, y)), ("L", (x + w, y + h)), ("L", (x, y + h))], "closed": True}]
            return self.add_path(sub, m, st, clip, name="Rectangle")
        filled = colour(st.get("fill")) is not None
        stroked = colour(st.get("stroke")) is not None
        if not filled and not stroked:
            return
        if (X0 <= 0.5 and Y0 <= 0.5 and X1 >= self.vb[2] - 0.5 and Y1 >= self.vb[3] - 0.5 and not stroked
                and colour(st.get("fill")) == "FFFFFF"):
            return
        E = self.emu
        ox, oy, cx, cy = int(round(X0 * E)), int(round(Y0 * E)), max(1, int(round((X1 - X0) * E))), max(1, int(round((Y1 - Y0) * E)))
        if rx > 0:
            adj = int(round(min(0.5, rx * scale_of(m) / max(1e-9, min(X1 - X0, Y1 - Y0))) * 100000))
            geom = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>'
        else:
            geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        sid = self._id()
        self._emit(f'<p:sp {NSDECL}><p:nvSpPr><p:cNvPr id="{sid}" name="Rectangle {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm><a:off x="{ox}" y="{oy}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>{geom}'
                   f'{self._fill_xml(st)}{self._ln_xml(st, m)}</p:spPr>'
                   f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-GB"/></a:p></p:txBody></p:sp>')

    def add_ellipse(self, cx, cy, r, m, st, clip):
        X, Y = apply(m, cx, cy)
        R = r * scale_of(m)
        if clip is not None and not (X - R >= clip[0] and Y - R >= clip[1] and X + R <= clip[2] and Y + R <= clip[3]):
            if X < clip[0] or X > clip[2] or Y < clip[1] or Y > clip[3]:
                return
        E = self.emu
        sid = self._id()
        self._emit(f'<p:sp {NSDECL}><p:nvSpPr><p:cNvPr id="{sid}" name="Circle {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm><a:off x="{int(round((X - R) * E))}" y="{int(round((Y - R) * E))}"/>'
                   f'<a:ext cx="{max(1, int(round(2 * R * E)))}" cy="{max(1, int(round(2 * R * E)))}"/></a:xfrm>'
                   f'<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>{self._fill_xml(st)}{self._ln_xml(st, m)}</p:spPr>'
                   f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-GB"/></a:p></p:txBody></p:sp>')

    # ------------------------------------------------ text
    def add_text(self, el, m_parent, st_parent, clip):
        m = mul(m_parent, parse_transform(el.get("transform")))
        st = inherit(st_parent, el)
        preserve = (el.get("{http://www.w3.org/XML/1998/namespace}space") == "preserve")
        base_x, base_y = num(el.get("x")), num(el.get("y"))
        pieces = []          # (text, style, x_or_None, y)
        cur_y = base_y

        def norm(t):
            if t is None:
                return ""
            if preserve:
                return t.replace("\n", " ")
            return re.sub(r"\s+", " ", t)
        if el.text and (preserve or el.text.strip()):
            pieces.append((norm(el.text) if preserve else el.text.strip(), st, None, cur_y))
        for ch in el:
            if not isinstance(ch.tag, str) or etree.QName(ch).localname != "tspan":
                continue
            cst = inherit(st, ch)
            x = num(ch.get("x")) if ch.get("x") is not None else None
            if ch.get("y") is not None:
                cur_y = num(ch.get("y"))
            if ch.get("dy") is not None:
                cur_y += num(ch.get("dy"))
            txt = ch.text or ""
            if not preserve and not txt.strip() and txt != "\u00a0":
                txt = ""
            if txt:
                pieces.append((txt if preserve else (txt if txt == "\u00a0" else txt.strip()), cst, x, cur_y))
            if ch.tail and (preserve or ch.tail.strip()):
                pieces.append((norm(ch.tail) if preserve else ch.tail.strip(), st, None, cur_y))
        if not pieces:
            return
        if all(p[2] is not None for p in pieces):
            pieces.sort(key=lambda p: p[2])
        # anchor point and baseline
        first_x = next((p[2] for p in pieces if p[2] is not None), base_x)
        sizes = [num(p[1].get("font-size"), 12.0) for p in pieces]
        base_size = max(sizes)
        ref_y = next(p[3] for p, s in zip(pieces, sizes) if s == base_size)
        anchor = st.get("text-anchor", "start") if all(p[2] is None for p in pieces) else "start"
        if all(p[2] is None for p in pieces):
            first_x = base_x
        sc = scale_of(m) * self.emu / EMU_PER_PT                      # points per user unit
        runs = []
        for (t, s, _, y), size in zip(pieces, sizes):
            bold = str(s.get("font-weight", "normal")) in ("bold", "700", "800", "900")
            italic = s.get("font-style", "normal") in ("italic", "oblique")
            off = (ref_y - y) / base_size if abs(ref_y - y) > 1e-6 else 0.0
            c = colour(s.get("fill")) or "000000"
            t = t.replace("\u00a0", " ")
            if runs and runs[-1]["bold"] == bold and runs[-1]["italic"] == italic and abs(runs[-1]["size"] - size * sc) < 1e-6 \
                    and runs[-1]["color"] == c and abs(runs[-1]["off"] - off) < 1e-6:
                runs[-1]["text"] += t
            else:
                runs.append(dict(text=t, bold=bold, italic=italic, size=size * sc, color=c, off=off))
        width = sum(text_width_pt(r["text"], r["size"], r["bold"], r["italic"]) for r in runs) * 1.02 + 0.3
        bsize = base_size * sc
        height = LINE * bsize
        ax, ay = apply(m, first_x, ref_y)
        if clip is not None and not (clip[0] - 1 <= ax <= clip[2] + 1 and clip[1] - 1 <= ay <= clip[3] + 1):
            return
        ang = math.degrees(math.atan2(m[1], m[0]))
        align = {"start": "l", "middle": "ctr", "end": "r"}.get(anchor, "l")
        frac = {"l": 0.0, "ctr": 0.5, "r": 1.0}[align]
        # box in the text's own frame (points), relative to the anchor
        left, top = -frac * width, -ASCENT * bsize
        cxr, cyr = left + width / 2, top + height / 2
        rad = math.radians(ang)
        rx = cxr * math.cos(rad) - cyr * math.sin(rad)
        ry = cxr * math.sin(rad) + cyr * math.cos(rad)
        ppu = self.emu / EMU_PER_PT
        cx_abs, cy_abs = ax * ppu + rx, ay * ppu + ry                  # in points
        off_x = int(round((cx_abs - width / 2) * EMU_PER_PT))
        off_y = int(round((cy_abs - height / 2) * EMU_PER_PT))
        rot = int(round((ang % 360) * 60000)) % 21600000
        rot_attr = f' rot="{rot}"' if rot else ""
        rxml = []
        for r in runs:
            base = int(round(r["off"] * 100000))
            battr = f' baseline="{base}"' if base else ""
            rxml.append(f'<a:r><a:rPr lang="en-GB" sz="{max(100, int(round(r["size"] * 100)))}" b="{int(r["bold"])}" '
                        f'i="{int(r["italic"])}"{battr} dirty="0"><a:solidFill><a:srgbClr val="{r["color"]}"/></a:solidFill>'
                        f'<a:latin typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{escape(r["text"])}</a:t></a:r>')
        label = escape(re.sub(r"\s+", " ", "".join(r["text"] for r in runs)).strip()[:40]).replace('"', "&quot;")
        sid = self._id()
        self._emit(f'<p:sp {NSDECL}><p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}: {label}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                   f'<p:spPr><a:xfrm{rot_attr}><a:off x="{off_x}" y="{off_y}"/>'
                   f'<a:ext cx="{max(1, int(round(width * EMU_PER_PT)))}" cy="{max(1, int(round(height * EMU_PER_PT)))}"/></a:xfrm>'
                   f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
                   f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t" rtlCol="0"><a:noAutofit/></a:bodyPr>'
                   f'<a:lstStyle/><a:p><a:pPr algn="{align}"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
                   f'<a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft></a:pPr>'
                   f'{"".join(rxml)}</a:p></p:txBody></p:sp>')

    # ------------------------------------------------ output
    def save(self, out_path):
        prs = Presentation()
        W, H = int(round(self.width_mm * 36000)), int(round(self.height_mm * 36000))
        prs.slide_width, prs.slide_height = Emu(W), Emu(H)
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        tree = slide.shapes._spTree
        gid = 10 ** 6
        for name, items in self.groups:
            if not items:
                continue
            els = [parse_xml(x) for x in items]
            if name == "Figure" or len(els) == 1:
                for e in els:
                    tree.append(e)
                continue
            xs, ys = [], []
            for e in els:
                off = e.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}off")
                ext = e.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
                x, y, cx, cy = int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy"))
                xs += [x, x + cx]
                ys += [y, y + cy]
            gx, gy, gw, gh = min(xs), min(ys), max(1, max(xs) - min(xs)), max(1, max(ys) - min(ys))
            gid += 1
            grp = parse_xml(f'<p:grpSp {NSDECL}><p:nvGrpSpPr><p:cNvPr id="{gid}" name="{escape(name)}"/><p:cNvGrpSpPr/><p:nvPr/>'
                            f'</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="{gx}" y="{gy}"/><a:ext cx="{gw}" cy="{gh}"/>'
                            f'<a:chOff x="{gx}" y="{gy}"/><a:chExt cx="{gw}" cy="{gh}"/></a:xfrm></p:grpSpPr></p:grpSp>')
            for e in els:
                grp.append(e)
            tree.append(grp)
        prs.save(str(out_path))


def convert(svg_path, pptx_path):
    Converter(svg_path).run().save(pptx_path)


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
    print("written", sys.argv[2])
