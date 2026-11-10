"""Fig. 1: gender decisions in translation and the context-partitioned protocol.

All outputs shown in panel a are verbatim outputs of the reported run for held-out item
mit_6ec9bca6b456d95182111906807e4e26c0fcd1337c218b8954443af4_tr (see analysis/examples_states.json and
Results/pilot/records/records_items.jsonl). Held-out counts per condition come from
analysis/outputs/heldout_paired_exact_p.csv (n column).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "common"))
from svgkit import (SVG, render, text_width, INK, GREY, LIGHT, PALE, BLUE, SLATE, VERM, EVID, EVID_S, PT)  # noqa: E402

W, H = 180, 92
s = SVG(W, H)


def check(x, y, color=BLUE, size=2.0, sw=0.45):
    s.path(f"M{x:.2f},{y - size * 0.45:.2f} L{x + size * 0.35:.2f},{y:.2f} L{x + size:.2f},{y - size * 0.95:.2f}", stroke=color, sw=sw)


def cross(x, y, color=VERM, size=1.7, sw=0.45):
    s.line(x, y - size, x + size, y, stroke=color, sw=sw)
    s.line(x, y, x + size, y - size, stroke=color, sw=sw)


def chip(x, y, w, h, letter, fill, txt="#FFFFFF", style="b", size=6.5):
    s.rect(x, y, w, h, fill=fill, rx=0.6)
    s.text(x + w / 2, y + h / 2 + size * PT * 0.35, [(letter, style)], size_pt=size, fill=txt, anchor="middle")


# ------------------------------------------------------------------ panel a
s.label(0.3, 3.6, "a")
s.text(5, 3.6, [("One target sentence, with and without its evidence", "b")], size_pt=7)
# evidence sentence
s.rect(1.5, 6.4, 84, 9.0, fill=EVID, stroke=EVID_S, sw=0.25, rx=1.0)
chip(3.0, 8.6, 4.4, 4.4, "E", EVID_S)
s.text(9.6, 10.4, [("Sarah benim büyükannem.", "i")], size_pt=7)
s.text(9.6, 13.9, "‘Sarah is my grandmother.’", size_pt=6, fill=GREY)
# target sentence
s.rect(1.5, 17.0, 84, 9.0, fill=PALE, stroke=GREY, sw=0.25, rx=1.0)
chip(3.0, 19.2, 4.4, 4.4, "T", GREY)
s.text(9.6, 21.0, [("Onun", "bi"), (" şakalarını gerçekten seviyorum.", "i")], size_pt=7)
s.text(9.6, 24.5, [("‘I really like ", "n"), ("3SG.GEN", "n"), (" jokes.’   ", "n"), ("onun", "i"),
                   (" does not mark gender", "n")], size_pt=6, fill=GREY)

# with evidence
s.text(2.0, 31.6, [("Adjacent input (E + T)", "b")], size_pt=6.5, fill=GREY)
s.text(4.0, 36.6, "All six systems", size_pt=6.5)
s.text(36.0, 36.6, [("I really … ", "n"), ("her", "b"), (" jokes.", "n")], size_pt=6.5)
s.text(36.0 + text_width([("I really … ", "n")], 6.5), 36.6, [("her", "b")], size_pt=6.5, fill=SLATE)
check(68.6, 36.2, color=SLATE)
s.text(84.5, 36.6, "correct", size_pt=5.5, fill=SLATE, anchor="end")
s.line(1.5, 39.4, 85.5, 39.4, stroke=LIGHT, sw=0.2)

# without evidence
s.text(2.0, 44.4, [("Isolated input (T only)", "b")], size_pt=6.5, fill=GREY)
rows = [("Plain prompting", "I really like ", "his", " jokes.", False),
        ("Cautious prompting", "I really like ", "his", " jokes.", False),
        ("Chain-of-thought", "I really like ", "his", " jokes.", False),
        ("Infer-then-tag", "I really like ", "her", " jokes.", False),
        ("Gold-label reference", "I really like ", "his", " jokes.", False),
        ("CCL-Gate", "I really like ", "their", " jokes.", True)]
y0, dy = 49.6, 6.15
for i, (name, pre, pron, post, ours) in enumerate(rows):
    y = y0 + i * dy
    if ours:
        s.rect(1.5, y - 4.1, 84, 5.6, fill="#E7F1F9", rx=0.8)
    s.text(4.0, y, [(name, "b" if ours else "n")], size_pt=6.5, fill=BLUE if ours else INK)
    s.text(36.0, y, [(pre, "n")], size_pt=6.5)
    xw = 36.0 + text_width([(pre, "n")], 6.5)
    s.text(xw, y, [(pron, "b")], size_pt=6.5, fill=BLUE if ours else VERM)
    s.text(xw + text_width([(pron, "b")], 6.5), y, [(post, "n")], size_pt=6.5)
    if ours:
        check(68.6, y - 0.4, color=BLUE)
        s.text(84.5, y, "defers", size_pt=5.5, fill=BLUE, anchor="end")
    else:
        cross(68.8, y - 0.3)
        s.text(84.5, y, "unwarranted", size_pt=5.5, fill=VERM, anchor="end")

# ------------------------------------------------------------------ panel b
X0 = 92.0
s.label(X0, 3.6, "b")
s.text(X0 + 5, 3.6, [("Context-partitioned protocol", "b")], size_pt=7)
s.text(X0 + 1, 9.6, "Condition", size_pt=6, fill=GREY)
s.text(113.0, 9.6, "Model input", size_pt=6, fill=GREY)
s.text(164.0, 9.6, "Gold", size_pt=6, fill=GREY, anchor="middle")
s.text(179.5, 9.6, "Held-out n", size_pt=6, fill=GREY, anchor="end")
s.line(X0 + 1, 11.0, 179.5, 11.0, stroke=LIGHT, sw=0.2)
conds = [("Adjacent", 896), ("Distant", 280), ("Memory", 501), ("Isolated", 157)]
bh, bw = 5.0, 7.0


def block(x, yc, letter, kind):
    if kind == "E":
        s.rect(x, yc - bh / 2, bw, bh, fill=EVID, stroke=EVID_S, sw=0.25, rx=0.6)
        s.text(x + bw / 2, yc + 0.8, [(letter, "b")], size_pt=6.5, fill=EVID_S, anchor="middle")
    else:
        s.rect(x, yc - bh / 2, bw, bh, fill=PALE, stroke=GREY, sw=0.25, rx=0.6)
        s.text(x + bw / 2, yc + 0.8, [(letter, "b")], size_pt=6.5, fill=GREY, anchor="middle")


for i, (name, n) in enumerate(conds):
    yc = 16.6 + i * 10.0
    s.text(X0 + 1, yc + 0.8, [(name, "b")], size_pt=6.5)
    s.text(179.5, yc + 0.8, f"{n:,}", size_pt=6.5, anchor="end")
    if name == "Adjacent":
        block(113, yc, "E", "E"); block(121.0, yc, "T", "T")
        s.text(113, yc + 5.2, "evidence directly before target", size_pt=5.5, fill=GREY)
    elif name == "Distant":
        block(113, yc, "E", "E")
        x = 121.0
        for k in range(8):
            s.rect(x, yc - bh / 2, 2.6, bh, fill="#E6E8EB", rx=0.4)
            x += 3.15
        block(x + 0.6, yc, "T", "T")
        s.text(113, yc + 5.2, "8 person-free FLORES sentences between", size_pt=5.5, fill=GREY)
    elif name == "Memory":
        s.rect(112.2, yc - bh / 2 - 0.8, bw + 1.6, bh + 1.6, fill="none", stroke=EVID_S, sw=0.25, rx=0.8, dash="0.8,0.6")
        block(113, yc, "E", "E")
        s.line(124.4, yc - 3.0, 124.4, yc + 3.0, stroke=LIGHT, sw=0.3)
        block(127.0, yc, "T", "T")
        s.text(113, yc + 5.2, "E only as earlier text of the story", size_pt=5.5, fill=GREY)
    else:
        s.rect(113, yc - bh / 2, bw, bh, fill="none", stroke=LIGHT, sw=0.25, rx=0.6, dash="0.8,0.6")
        block(121.0, yc, "T", "T")
        s.text(113, yc + 5.2, "evidence removed", size_pt=5.5, fill=GREY)
    if name != "Isolated":
        s.rect(161.4, yc - 2.3, 5.2, 4.6, fill=SLATE, rx=0.6)
        s.text(164.0, yc + 0.8, [("g", "bi")], size_pt=6.5, fill="#FFFFFF", anchor="middle")
    else:
        s.rect(161.4, yc - 2.3, 5.2, 4.6, fill=LIGHT, rx=0.6)
        s.text(164.0, yc + 0.8, [("N", "b")], size_pt=6.5, fill=INK, anchor="middle")
s.text(X0 + 1, 55.2, [("g", "i"), (", referent's gender;  ", "n"), ("N", "b"), (", neutral wording is correct", "n")], size_pt=5.5, fill=GREY)

# ------------------------------------------------------------------ panel c
s.label(X0, 62.6, "c")
s.text(X0 + 5, 62.6, [("Scoring", "b")], size_pt=7)
s.text(X0 + 1, 68.4, [("Determinable instances (gold ", "b"), ("g", "bi"), (")", "b")], size_pt=6.2)
items1 = [(SLATE, "correct gender", "ACC"), (LIGHT, "neutral wording", "neutral"),
          (VERM, "opposite gender", "WGR")]
for i, (col, a, b) in enumerate(items1):
    y = 73.0 + i * 4.6
    s.rect(X0 + 1, y - 2.5, 3.0, 3.0, fill=col, rx=0.4)
    s.text(X0 + 5.4, y, a, size_pt=6.2)
    s.text(X0 + 5.4 + text_width([(a, "n")], 6.2) + 1.2, y, b, size_pt=5.6, fill=GREY)
X1 = 135.5
s.text(X1, 68.4, [("Unrecoverable or ambiguous (gold ", "b"), ("N", "b"), (")", "b")], size_pt=6.2)
assert X1 + text_width([("Unrecoverable or ambiguous (gold N)", "b")], 6.2) < 179.8
items2 = [(SLATE, "neutral wording", "abstention"), (VERM, "gendered pronoun", "UCR")]
for i, (col, a, b) in enumerate(items2):
    y = 73.0 + i * 4.6
    s.rect(X1, y - 2.5, 3.0, 3.0, fill=col, rx=0.4)
    s.text(X1 + 4.4, y, a, size_pt=6.2)
    s.text(X1 + 4.4 + text_width([(a, "n")], 6.2) + 1.2, y, b, size_pt=5.6, fill=GREY)
s.rect(X0 + 1, 84.6, 86.6, 6.4, fill=PALE, rx=0.8)
s.text(136.0, 89.0, [("BAL = ", "b"), ("½ ACC + ½ (1 − UCR)", "n"), ("     balanced accuracy", "n")],
       size_pt=6.8, anchor="middle")

out_svg = HERE / "fig1_overview.svg"
s.save(out_svg)
root = HERE.parent.parent
render(out_svg, root / "overleaf" / "figures" / "fig1_overview.pdf", HERE / "fig1_overview.png", W, H)
print("Fig. 1 written")
