"""Fig. 2: the CCL-Gate architecture with a worked held-out example.

Panel b values are those recorded in the reported run for held-out TWC item twc00519_tr (adjacent and isolated
conditions): raw extractor output and resolver probabilities from the response cache (analysis/examples_raw.json),
ledger after hygiene, posteriors and gate decisions (analysis/examples_states.json), and the verbatim translations
(Results/pilot/records/records_items.jsonl).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from svgkit import (SVG, render, text_width, INK, GREY, LIGHT, PALE, BLUE, SLATE, VERM, EVID, EVID_S, LLMF, LLMS,  # noqa
                    DETF, DETS, PT)

W, H = 180, 116.4
s = SVG(W, H)
BWS = [26.9, 26.9, 26.9, 26.9, 26.9, 30.4]
GAP = 2.94
XS = [sum(BWS[:i]) + i * GAP for i in range(6)]
BW = 26.9
FS = 6.0          # body font size (pt)
LH = 2.95         # line height (mm)


def fits(segs, size, width):
    w = text_width(segs if not isinstance(segs, str) else [(segs, "n")], size)
    assert w <= width, (segs, w, width)


def tline(x, y, segs, size=FS, fill=INK, width=BW - 1.4, **kw):
    fits(segs, size, width)
    s.text(x, y, segs, size_pt=size, fill=fill, **kw)


def cross(x, y, color=VERM, size=1.3, sw=0.4):
    s.line(x, y - size, x + size, y, stroke=color, sw=sw)
    s.line(x, y, x + size, y - size, stroke=color, sw=sw)


def check(x, y, color=BLUE, size=1.6, sw=0.42):
    s.path(f"M{x:.2f},{y - size * 0.45:.2f} L{x + size * 0.35:.2f},{y:.2f} L{x + size:.2f},{y - size * 0.95:.2f}", stroke=color, sw=sw)


# ------------------------------------------------------------------ panel a: architecture
s.label(0.3, 3.6, "a")
s.text(5, 3.6, [("Architecture", "b")], size_pt=7)
# legend
lx = 112.0
s.rect(lx, 1.3, 3.0, 2.6, fill=LLMF, stroke=LLMS, sw=0.25, rx=0.4)
s.text(lx + 4.0, 3.6, "LLM call", size_pt=6, fill=GREY)
lx2 = lx + 4.0 + text_width([("LLM call", "n")], 6) + 4.0
s.rect(lx2, 1.3, 3.0, 2.6, fill=DETF, stroke=DETS, sw=0.25, rx=0.4)
s.text(lx2 + 4.0, 3.6, "deterministic or calibrated", size_pt=6, fill=GREY)

boxes = [
    ("1", "Ledger extraction", "llm", [
        [("In: passage and earlier", "n")],
        [("text. Out: characters,", "n")],
        [("names and typed gender", "n")],
        [("cues, each a verbatim", "n")],
        [("quote (JSON schema)", "n")]]),
    ("2", "Ledger hygiene", "det", [
        [("Remove cues the source", "n")],
        [("language cannot express,", "n")],
        [("name-only cues and", "n")],
        [("pseudo-entities", "n")],
        [("Given-name prior ", "n"), ("π", "i"), ("e", "isub")]]),
    ("3", "Referent resolution", "llm", [
        [("Every third-person slot ", "n"), ("k", "i")],
        [("in one constrained call", "n")],
        [("Token probabilities give", "n")],
        [("q", "i"), ("k", "isub"), ("(", "n"), ("e", "i"), (") and ambiguity ", "n"), ("a", "i"), ("k", "isub")]]),
    ("4", "Evidence model", "det", [
        [("z", "i"), ("e", "isub"), (" = Σ", "n"), ("t", "isub"), (" ", "n"), ("w", "i"), ("t", "isub"), (" Δ", "n"), ("n", "i"), ("e,t", "isub")],
        [("       + ", "n"), ("w", "i"), ("name", "sub"), (" logit ", "n"), ("π", "i"), ("e", "isub")],
        [("p", "i"), ("e", "isub"), ("(F) = σ(", "n"), ("z", "i"), ("e", "isub"), (")", "n")],
        [("w", "i"), (" = ", "n"), ("a", "i"), (" ", "n"), ("w", "i"), ("(0)", "sup")],
        [("P", "i"), ("k", "isub"), ("(F), conf", "n"), ("k", "isub")]]),
    ("5", "Evidence gate", "det", [
        [("No evidence → ", "n"), ("DEFER", "b")],
        [("Ambiguous → ", "n"), ("DEFER", "b")],
        [("conf", "n"), ("k", "isub"), (" ≥ τ", "n"), ("gate", "sub"), (" → ", "n"), ("COMMIT", "b")],
        [("Otherwise → ", "n"), ("KEEP", "b")]]),
    ("6", "Translate and verify", "llm", [
        [("Plain prompt plus one", "n")],
        [("instruction per decision", "n")],
        [("Check gendered pronouns", "n")],
        [("Monotone targeted repair", "n")]]),
]
YB, HB = 6.6, 25.0
for x, bw_, (num, name, kind, lines) in zip(XS, BWS, boxes):
    fill, stroke = (LLMF, LLMS) if kind == "llm" else (DETF, DETS)
    s.rect(x, YB, bw_, HB, fill="#FFFFFF", stroke=stroke, sw=0.3, rx=1.0)
    s.rect(x, YB, bw_, 6.0, fill=fill, stroke="none", rx=1.0)
    s.rect(x, YB + 3.0, bw_, 3.0, fill=fill, stroke="none")
    s.line(x, YB + 6.0, x + bw_, YB + 6.0, stroke=stroke, sw=0.25)
    s.circle(x + 3.0, YB + 3.0, 1.85, fill=stroke)
    s.text(x + 3.0, YB + 3.75, [(num, "b")], size_pt=6, fill="#FFFFFF", anchor="middle")
    tline(x + 5.6, YB + 4.0, [(name, "b")], size=6.2, width=bw_ - 6.0)
    y = YB + 10.4
    for ln in lines:
        tline(x + 1.4, y, ln, width=bw_ - 1.8)
        y += LH
for i in range(5):
    s.arrow(XS[i] + BWS[i] + 0.2, YB + HB / 2, XS[i + 1] - 0.2, YB + HB / 2, stroke=GREY, sw=0.35, head=0.95)

# shared-model band
yb = 34.0
s.rect(0, yb, W, 6.0, fill=PALE, rx=1.0)
for i in (0, 2, 5):
    xc = XS[i] + BWS[i] / 2
    s.line(xc, YB + HB, xc, yb, stroke=LLMS, sw=0.3, dash="0.7,0.5")
band = [("One pretrained LLM (Qwen3-8B, 4-bit) serves stages 1, 3 and 6 without parameter updates.  ", "n"),
        ("a", "i"), (" and τ", "n"), ("gate", "sub"), (" are calibrated on development data.", "n")]
s.text(W / 2, yb + 3.9, band, size_pt=6.2, fill=INK, anchor="middle")

# ------------------------------------------------------------------ panel b: worked example
s.label(0.3, 47.0, "b")
s.text(5, 47.0, [("Worked example: a held-out TWC item in Turkish", "b")], size_pt=7)


def track_header(y, title, src, gloss):
    s.rect(0, y - 3.4, W, 9.0, fill=EVID, rx=1.0)
    s.text(1.5, y, [(title, "b")], size_pt=6.4, fill=EVID_S)
    x = 1.5 + text_width([(title, "b")], 6.4) + 3.0
    s.text(x, y, src, size_pt=6.4)
    s.text(x, y + 3.6, gloss, size_pt=5.8, fill=GREY)


def removed(x, y, segs, why):
    """A removed item: vermillion cross, grey struck text, reason."""
    cross(x, y - 0.25)
    tx = x + 2.2
    w = text_width(segs, FS)
    s.text(tx, y, segs, size_pt=FS, fill=GREY)
    s.strike(tx, y, w, FS, stroke=GREY, sw=0.22)
    tline(tx + w + 1.0, y, [(why, "n")], size=5.5, fill=VERM, width=BW - 3.2 - w - 1.0)


def chip(x, y, label, fill, txt="#FFFFFF", w=None):
    w = w or text_width([(label, "b")], 6.0) + 3.0
    s.rect(x, y - 3.0, w, 4.2, fill=fill, rx=0.7)
    s.text(x + w / 2, y, [(label, "b")], size_pt=6.0, fill=txt, anchor="middle")
    return w


# ---- track 1: adjacent input
y1 = 53.2
track_header(y1, "Adjacent input",
             [("[1] Oscar bir fırıncı, Diana ise bir uçuş görevlisidir.   [2] ", "i"), ("O", "bi"), (" lezzetli ekmek yapar.", "i")],
             "‘Oscar is a baker, and Diana is a flight attendant. 3SG makes delicious bread.’")
yy = 64.8
# column 1: raw ledger
c = XS[0] + 1.0
tline(c, yy - 0.2, [("Raw ledger", "b")], size=5.8, fill=GREY)
rows1 = [[("E1 ", "b"), ("Oscar", "n")], [("   cue ‘Oscar’ → M", "n")],
         [("E2 ", "b"), ("Diana", "n")], [("   cue ‘Diana’ → F", "n")],
         [("E3 ", "b"), ("Unnamed person", "n")], [("   cue ‘", "n"), ("O", "b"), ("’ → M (pronoun)", "n")]]
for k, r in enumerate(rows1):
    tline(c, yy + 3.2 + k * LH, r)
# column 2: hygiene
c = XS[1] + 1.0
tline(c, yy - 0.2, [("After hygiene", "b")], size=5.8, fill=GREY)
removed(c, yy + 3.2, [("‘Oscar’", "n")], "name only")
removed(c, yy + 3.2 + LH, [("‘Diana’", "n")], "name only")
removed(c, yy + 3.2 + 2 * LH, [("‘O’ → M", "n")], "not in Turkish")
removed(c, yy + 3.2 + 3 * LH, [("E3", "n")], "pronoun entity")
tline(c, yy + 3.2 + 4 * LH + 0.6, [("π", "i"), ("Oscar", "sub"), (" = 0.05", "n")])
tline(c, yy + 3.2 + 5 * LH + 0.6, [("π", "i"), ("Diana", "sub"), (" = 0.95", "n")])
# column 3: resolution
c = XS[2] + 1.0
tline(c, yy - 0.2, [("Slot ‘O’ in line 2", "b")], size=5.8, fill=GREY)
bars = [("A  Oscar", 1.0, "1.00"), ("B  Diana", 0.0, "<0.01"), ("ambiguous", 0.0, "<0.01"), ("unknown", 0.0, "<0.01")]
for k, (lab, v, txt) in enumerate(bars):
    y = yy + 3.2 + k * LH
    s.text(c, y, lab, size_pt=FS)
    bx = c + 12.0
    s.rect(bx, y - 1.9, 8.0, 2.0, fill=PALE)
    if v > 0:
        s.rect(bx, y - 1.9, 8.0 * v, 2.0, fill=SLATE)
    else:
        s.rect(bx, y - 1.9, 0.25, 2.0, fill=SLATE)
    s.text(bx + 8.6, y, txt, size_pt=5.6)
tline(c, yy + 3.2 + 4 * LH + 0.6, [("q", "i"), ("k", "isub"), ("(A) = 1.00,  ", "n"), ("a", "i"), ("k", "isub"), (" < 0.01", "n")])
# column 4: evidence model
c = XS[3] + 1.0
tline(c, yy - 0.2, [("Posterior", "b")], size=5.8, fill=GREY)
ev = [[("p", "i"), ("A", "isub"), ("(F) = σ(", "n"), ("a", "i"), ("·0.8·logit 0.05)", "n")],
      [("          = 0.27", "n")],
      [("p", "i"), ("B", "isub"), ("(F) = 0.73", "n")],
      [("P", "i"), ("k", "isub"), ("(F) = 0.27", "n")],
      [("conf", "n"), ("k", "isub"), (" = 0.73", "n")]]
for k, r in enumerate(ev):
    tline(c, yy + 3.2 + k * LH, r)
# column 5: gate
c = XS[4] + 1.0
tline(c, yy - 0.2, [("Gate", "b")], size=5.8, fill=GREY)
gl = [[("evidence observable", "n")], [("not ambiguous", "n")], [("0.73 ≥ τ", "n"), ("gate", "sub"), (" = 0.60", "n")]]
for k, r in enumerate(gl):
    tline(c, yy + 3.2 + k * LH, r)
chip(c, yy + 3.2 + 3 * LH + 2.2, "COMMIT  male", BLUE)
# column 6: translation
c = XS[5] + 1.0
W6 = BWS[5] - 1.4
tline(c, yy - 0.2, [("Instruction and output", "b")], size=5.8, fill=GREY, width=W6)
tline(c, yy + 3.2, [("\u2018Line 2: Oscar is male; use", "i")], width=W6)
tline(c, yy + 3.2 + LH, [("he/him/his.\u2019", "i")], width=W6)
tline(c, yy + 3.2 + 2 * LH + 0.6, [("CCL-Gate", "b")], size=5.8, fill=BLUE, width=W6)
check(c + text_width([("CCL-Gate", "b")], 5.8) + 1.0, yy + 3.2 + 2 * LH + 0.3)
tline(c, yy + 3.2 + 3 * LH + 0.6, [("He", "b"), (" makes delicious bread.", "n")], width=W6)
s.text(c, yy + 3.2 + 3 * LH + 0.6, [("He", "b")], size_pt=FS, fill=BLUE)
tline(c, yy + 3.2 + 4 * LH + 1.2, [("Plain prompting", "b")], size=5.8, fill=GREY, width=W6)
cross(c + text_width([("Plain prompting", "b")], 5.8) + 1.0, yy + 3.2 + 4 * LH + 0.9)
tline(c, yy + 3.2 + 5 * LH + 1.2, [("She", "b"), (" makes delicious bread.", "n")], width=W6)
s.text(c, yy + 3.2 + 5 * LH + 1.2, [("She", "b")], size_pt=FS, fill=VERM)

# ---- track 2: isolated input
y2 = 91.6
track_header(y2, "Isolated input", [("[1] ", "i"), ("O", "bi"), (" lezzetli ekmek yapar.", "i")],
             "‘" + "3SG makes delicious bread.’")
yy = 103.2
c = XS[0] + 1.0
tline(c, yy, [("E1 ", "b"), ("He/She", "n")])
tline(c, yy + LH, [("   cue ‘", "n"), ("O", "b"), ("’ → M (pronoun)", "n")])
c = XS[1] + 1.0
removed(c, yy, [("‘O’ → M", "n")], "not in Turkish")
removed(c, yy + LH, [("E1", "n")], "pronoun entity")
tline(c, yy + 2 * LH + 0.6, [("ledger empty", "n")])
c = XS[2] + 1.0
tline(c, yy, [("Slot ‘O’ in line 1", "n")])
tline(c, yy + LH, [("unknown 1.00", "n")])
c = XS[3] + 1.0
tline(c, yy, [("no character carries", "n")])
tline(c, yy + LH, [("evidence: ", "n"), ("O", "i"), (" = 0", "n")])
c = XS[4] + 1.0
tline(c, yy, [("unobservable", "n")])
chip(c, yy + LH + 2.2, "DEFER", SLATE)
c = XS[5] + 1.0
tline(c, yy, [("CCL-Gate", "b")], size=5.8, fill=BLUE, width=W6)
check(c + text_width([("CCL-Gate", "b")], 5.8) + 1.0, yy - 0.3)
tline(c, yy + LH, [("They", "b"), (" make a delicious bread.", "n")], width=W6)
s.text(c, yy + LH, [("They", "b")], size_pt=FS, fill=BLUE)
tline(c, yy + 2 * LH + 0.6, [("Plain prompting", "b")], size=5.8, fill=GREY, width=W6)
cross(c + text_width([("Plain prompting", "b")], 5.8) + 1.0, yy + 2 * LH + 0.3)
tline(c, yy + 3 * LH + 0.6, [("She", "b"), (" makes delicious bread.", "n")], width=W6)
s.text(c, yy + 3 * LH + 0.6, [("She", "b")], size_pt=FS, fill=VERM)

# faint column guides linking panel b to the stages above
T1Y, T1H, T2Y, T2H = 59.6, 27.8, 98.0, 17.6
for x, bw_ in zip(XS, BWS):
    s.rect(x, T1Y, bw_, T1H, fill="none", stroke=LIGHT, sw=0.2, rx=0.8)
    s.rect(x, T2Y, bw_, T2H, fill="none", stroke=LIGHT, sw=0.2, rx=0.8)
for i in range(5):
    for (ya, hb) in ((T1Y, T1H), (T2Y, T2H)):
        s.arrow(XS[i] + BWS[i] + 0.25, ya + hb / 2, XS[i + 1] - 0.25, ya + hb / 2, stroke=LIGHT, sw=0.3, head=0.85)

out_svg = HERE / "fig2_architecture.svg"
s.save(out_svg)
root = HERE.parent.parent
render(out_svg, root / "overleaf" / "figures" / "fig2_architecture.pdf", HERE / "fig2_architecture.png", W, H)
print("Fig. 2 written")
