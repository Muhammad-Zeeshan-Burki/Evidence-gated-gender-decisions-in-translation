"""Writes the Supplementary Information (XeLaTeX source) from the final notebook and the result files.

Usage:
    python3 make_supplementary.py <CCL_final.ipynb> <Results/pilot> <output .tex>

Every prompt is produced by calling the notebook's own prompt functions with placeholder arguments, so the prompt text in
the Supplementary Information is verbatim. Lexicons, validity checks, counterfactual counts and package versions are read
from the notebook and from Results/pilot/records/manifest.json, and the synthetic-biography table from scores_items.csv.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

NB, RES, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
CELLS = [''.join(c['source']) for c in json.load(open(NB, encoding='utf-8'))['cells'] if c['cell_type'] == 'code']
MAN = json.load(open(RES / 'records' / 'manifest.json', encoding='utf-8'))


def cell_with(sig):
    hits = [c for c in CELLS if sig in c]
    assert len(hits) == 1, (sig, len(hits))
    return hits[0]


# ---------------------------------------------------------------- load the notebook's definitions
ns = {}
exec("import json, re, math, hashlib, collections, unicodedata, string, random\nfrom pathlib import Path\n"
     "import numpy as np\nimport pandas as pd\nCONFIG = {'seed': 0}\nOUT = Path('.')\n", ns)
exec(cell_with("def numbered(lines)"), ns)
exec(re.search(r"CUE_TYPES = \[.*?\]", cell_with("CUE_TYPES = ["), re.S).group(0), ns)
exec(cell_with("def p_extract_v3b"), ns)
c029 = cell_with("def committed_x2en")
exec(c029.split("VALIDITY = {}")[0], ns)
exec(cell_with("def ledger_hygiene("), ns)
exec(cell_with("def instructions_for("), ns)
c047 = cell_with("def oracle_instr")
exec(c047, ns)
c045 = cell_with("def run_ccl(")
ns["V3"] = {"hygiene", "prior", "pseudo", "slots", "tauguard", "prompts", "prompts2", "monotone", "gate"}
assert sorted(ns["V3"]) == sorted(MAN["config"]["v3"]["enabled"]), MAN["config"]["v3"]["enabled"]

PH = lambda s: f"\u00ab{s}\u00bb"          # placeholder marker, typeset as an italic angle-bracketed slot
ns["LANG_NAMES"].update({PH("src"): PH("source language"), PH("tgt"): PH("target language")})
SRC, TGT = PH("src"), PH("tgt")
LINES = [PH("source line 1"), PH("source line 2")]
EARLIER = PH("earlier text of the story")
ENT = [dict(english_name=PH("English name of character A"), description=PH("description"), source_names=[PH("source forms")]),
       dict(english_name=PH("English name of character B"), description=PH("description"), source_names=[PH("source forms")])]


def user(msgs):
    assert msgs[0]["role"] == "system" and msgs[0]["content"] == ns["SYSTEM"] and len(msgs) == 2
    return msgs[1]["content"]


def once(s, old, new):
    assert s.count(old) == 1, (old, s.count(old))
    return s.replace(old, new)


# ---------------------------------------------------------------- render the prompts
P = {}
P["system"] = ns["SYSTEM"]
P["translate"] = user(ns["p_translate"](SRC, TGT, LINES, context_note=EARLIER, instructions=PH("instruction lines")))
assert '"\\nOutput ONLY the numbered lines."' in c047
P["reminder"] = "\nOutput ONLY the numbered lines.".strip()
P["cautious"] = ns["CAUTIOUS_INSTR"]
P["cot"] = user(ns["p_cot_translate"](SRC, TGT, LINES, EARLIER))
P["infer"] = user(ns["p_infer_gender"](SRC, LINES, PH("n"), EARLIER))
assert ("f\"Line {r['target_idx'] + 1}: the third-person person referred to in this line is {'female' if g == 'F' else 'male'}.\""
        in c047)
r_det = dict(target_idx=1, gold_kind="determinable", gold_gender="F", direction="x2en")
P["tag_f"] = once(ns["oracle_instr"](r_det), "Line 2:", f"Line {PH('n')}:")
P["tag_m"] = once(ns["oracle_instr"](dict(r_det, gold_gender="M")), "Line 2:", f"Line {PH('n')}:")
P["neutral"] = ns["oracle_instr"](dict(r_det, gold_kind="unrecoverable", gold_gender=None))
assert P["neutral"] == ns["NEUTRAL_INSTR"]
P["probe"] = user(ns["p_probe"](SRC, LINES, PH("n"), EARLIER))
KNOWN = [("K1", dict(english_name=PH("English name"), description=PH("description"), source_names=[PH("source forms")])),
         ("K2", dict(english_name=PH("English name"), description=PH("description"), source_names=[PH("source forms")]))]
P["extract"] = user(ns["p_extract_v3b"](SRC, PH("passage"), KNOWN))
P["extract_noknown"] = user(ns["p_extract_v3b"](SRC, PH("passage")))
assert P["extract"].startswith(P["extract_noknown"].split("\nPASSAGE:")[0])
ns["_CLITIC_HINT"][SRC] = " " + PH("language-specific hint")
P["resolve"] = once(user(ns["p_resolve_lp_v3b"](SRC, "x2en", "en", ENT, LINES, 2)), "lines 2 to 2",
                    f"lines {PH('first target line')} to {PH('last line')}")
del ns["_CLITIC_HINT"][SRC]
P["resolve_en2x"] = once(user(ns["p_resolve_lp"]("en", "en2x", TGT, ENT, LINES, 2)), "lines 2 to 2",
                         f"lines {PH('first target line')} to {PH('last line')}")
EB = {"L1": dict(english_name=PH("NAME"))}
dec = lambda d: dict(line=PH("n"), slot=1, referent="L1", decision=d)
P["commit_f"] = ns["instructions_for"]([dec("F")], EB, "x2en", "en")
P["commit_m"] = ns["instructions_for"]([dec("M")], EB, "x2en", "en")
P["defer"] = ns["instructions_for"]([dec("DEFER")], EB, "x2en", "en")
P["defer_noslot"] = ns["instructions_for"]([dict(dec("DEFER"), referent="none")], EB, "x2en", "en")
P["commit_en2x"] = ns["instructions_for"]([dec("F")], EB, "en2x", TGT)
assert ns["instructions_for"]([dec("DEFER")], EB, "en2x", TGT) == ""
assert 'f"Use these English names for the characters: {names}.\\n"' in c045 and '"; ".join(' in c045
P["names"] = f"Use these English names for the characters: {PH('English names of the ledger entries, separated by semicolons')}."
probs = []
for d, out in [("F", "He went home."), ("M", "She went home."), ("DEFER", "He went home.")]:
    pr, fl = ns["find_problems"]([out], [dict(line=1, slot=1, referent="L1", decision=d)], 1)
    assert len(pr) == 1 and fl == {1}
    probs.append(once(pr[0], "Line 1:", f"Line {PH('n')}:"))
P["problems"] = "\n".join(probs)
P["repair"] = user(ns["p_repair"](SRC, LINES, [PH("translation line 1"), PH("translation line 2")],
                                  [PH("problem 1"), PH("problem 2")]))
P["span"] = user(ns["p_span_find"](SRC, PH("source sentence"), PH("English name")))
P["name_gender"] = user(ns["p_name_gender"]([PH("name 1"), PH("name 2")]))
for k, v in P.items():
    assert "{" + "}" not in v and "None" not in v, k

SCHEMAS = [("Stage 1, ledger extraction", "The \\texttt{same\\_as} values are \\texttt{new} and the identifiers of the "
            "known characters (K1, K2 and so on).", ns["schema_extract_v3"](["K1", "K2"])),
           ("Stage 3, referent resolution", "The \\texttt{referent} values are one capital letter per listed character, "
            "\\texttt{unknown} and \\texttt{ambiguous}.", ns["schema_resolve"](["A", "B", "unknown", "ambiguous"])),
           ("Knowing-versus-using probe", "", ns["SCHEMA_PROBE"]),
           ("Infer-then-tag, gender inference", "", ns["SCHEMA_INFER"]),
           ("Span finder", "", ns["SCHEMA_SPAN"]),
           ("Name-gender estimate", "", ns["SCHEMA_NAME_GENDER"])]

# ---------------------------------------------------------------- TeX helpers
AR = "\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF"
RUNS = [(re.compile(f"[{AR}]+(?:[ \u200c]+[{AR}]+)*"), "AR"), (re.compile("[\u0980-\u09FF]+(?: [\u0980-\u09FF]+)*"), "BN"),
        (re.compile("[\u0900-\u097F]+(?: [\u0900-\u097F]+)*"), "DV")]
SPECIAL = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "#": r"\#", "%": r"\%", "_": r"\_",
           "^": r"\textasciicircum{}", "~": r"\textasciitilde{}"}


def esc(s, breaks=False):
    t = "".join(SPECIAL.get(ch, ch) for ch in s)
    for rx, mac in RUNS:
        t = rx.sub(lambda m: f"\\{mac}{{{m.group(0)}}}", t)
    t = re.sub("\u00ab(.*?)\u00bb", lambda m: f"\\ph{{{m.group(1)}}}", t)
    if breaks:
        t = t.replace("|", "|\\allowbreak{}").replace("/", "/\\allowbreak{}").replace("\\_", "\\_\\allowbreak{}")
    return t


def box(title, text):
    lines = text.split("\n")
    body = "\n".join("\\pskip" if not ln.strip() else esc(ln, breaks=True) + "\\par" for ln in lines)
    return f"\\begin{{promptbox}}{{{title}}}\n{body}\n\\end{{promptbox}}\n"


def fmt_int(x):
    return f"{int(x):,}"


# ---------------------------------------------------------------- document
L = []
A = L.append
A(r"""%% Supplementary Information. Generated by analysis/make_supplementary.py from the final notebook and Results/pilot.
%% Compile with XeLaTeX (the prompts and lexicons contain Arabic-script, Bengali-script and Devanagari text).
\documentclass[10pt,a4paper]{article}
\usepackage[a4paper,top=25mm,bottom=25mm,left=25mm,right=25mm]{geometry}
\usepackage{fontspec}
\usepackage{xcolor}
\usepackage{booktabs,array,longtable}
\usepackage[most]{tcolorbox}
\usepackage{titlesec}
\usepackage[font=small,labelfont=bf,labelsep=space,justification=raggedright,singlelinecheck=false]{caption}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=black,citecolor=black,pdftitle={Supplementary Information}}
\TeXXeTstate=1
\IfFontExistsTF{DejaVu Sans Mono}{\setmonofont{DejaVu Sans Mono}[Scale=0.80]}{}
\IfFontExistsTF{FreeSerif}{\def\xserif{FreeSerif}}{\IfFontExistsTF{FreeSerif.otf}{\def\xserif{FreeSerif.otf}}{\def\xserif{Latin Modern Roman}}}
\newfontfamily\arabicfam{\xserif}[Script=Arabic]
\newfontfamily\bengalifam{\xserif}[Script=Bengali]
\newfontfamily\devafam{\xserif}[Script=Devanagari]
\newfontfamily\lexfam{\xserif}
\newcommand{\AR}[1]{{\arabicfam\beginR#1\endR}}
\newcommand{\BN}[1]{{\bengalifam#1}}
\newcommand{\DV}[1]{{\devafam#1}}
\newcommand{\ph}[1]{{\normalfont\itshape\color{black!65}$\langle$#1$\rangle$}}
\newcommand{\pskip}{\par\vspace{0.45\baselineskip}}
\newtcolorbox{promptbox}[1]{breakable,enhanced,colback=black!3,colframe=black!25,boxrule=0.4pt,arc=0pt,
  left=5pt,right=5pt,top=4pt,bottom=4pt,fonttitle=\small\bfseries,coltitle=black,colbacktitle=black!8,title={#1},
  before upper={\ttfamily\small\raggedright\setlength{\parskip}{1pt}}}
\titleformat{\section}[block]{\large\bfseries\raggedright}{Supplementary Note \thesection.}{0.4em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{16pt}{6pt}
\titlespacing*{\subsection}{0pt}{10pt}{4pt}
\renewcommand{\tablename}{Supplementary Table}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\raggedbottom
\sloppy
\newcommand{\xen}{X$\rightarrow$EN}
\newcommand{\enx}{EN$\rightarrow$X}
\begin{document}
\begin{center}
{\Large\bfseries Supplementary Information}\\[8pt]
{\large A calibrated character ledger for evidence-based gender decisions in machine translation}\\[10pt]
Muhammad Zeeshan Burki, Muhammad Rizwan and Rashid Naseem\\[4pt]
{\small School of Computing Sciences, Pak-Austria Fachhochschule: Institute of Applied Sciences and Technology, Mang, Haripur 22621, Khyber Pakhtunkhwa, Pakistan}\\[4pt]
{\small Corresponding author: rashid.naseem@fecid.paf-iast.edu.pk}
\end{center}
\vspace{6pt}
\noindent\textbf{Contents}\\[2pt]
Supplementary Note 1. Prompts\\
Supplementary Note 2. Output schemas\\
Supplementary Note 3. Ledger hygiene resources\\
Supplementary Note 4. Scoring\\
Supplementary Note 5. Benchmark validity checks and counterfactual construction\\
Supplementary Note 6. Passage-level results on synthetic biographies\\
Supplementary Note 7. Software, data versions and run records
""")

A(r"""\section{Prompts}\label{si:prompts}
All model calls of the reported run used the system message and user prompts below. Each prompt was produced by the prompt
functions of the experiment notebook, so the text is verbatim. Slots in angle brackets are filled per instance, and source
lines are numbered as \texttt{[1]}, \texttt{[2]} and so on. Every call sent one system message and one user message to
Qwen3-8B with thinking mode disabled.
""")
A(box("System message (all calls)", P["system"]))
A(r"\subsection{Translation and prompting strategies}" "\n")
A("The translation prompt serves plain prompting and, with added instruction lines, every other translating system. "
  "The background block appears only when earlier text is supplied, which happens in the memory condition for the four "
  "prompting strategies, the probe and CCL-Gate. The instruction block appears only when a system adds instructions. For plain, "
  "cautious and infer-then-tag prompting and the gold-label reference, a translation whose numbered lines could not be parsed "
  "was requested once more with the reminder line appended to the instructions.\n")
A(box("Translation prompt", P["translate"]))
A(box("Format reminder (one retry after a parsing failure)", P["reminder"]))
A(box("Cautious prompting (instruction block)", P["cautious"]))
A(box("Chain-of-thought prompting (complete prompt)", P["cot"]))
A("Infer-then-tag first asks for the gender of the target referent under the inference schema "
  "(Supplementary Note~2) and then translates with the corresponding tag line in the instruction block. "
  "The gold-label reference receives the same tag line with the gold gender for determinable instances and, in translation "
  "into English, the neutral-wording instruction otherwise. The gold-label reference receives no background block.\n")
A(box("Infer-then-tag, gender inference", P["infer"]))
A(box("Tag line (infer-then-tag and gold-label reference)", P["tag_f"] + "\n" + P["tag_m"]))
A(box("Neutral-wording instruction (gold-label reference, unrecoverable and referent-ambiguous instances)", P["neutral"]))
A(r"\subsection{CCL-Gate stages}" "\n")
A("Stage 1 extracts the ledger. When earlier text exists, it is extracted first with the prompt below without the "
  "block of known characters, and the current passage is then extracted with that block, which lists the earlier entries "
  "as K1, K2 and so on.\n")
A(box("Stage 1, ledger extraction", P["extract"]))
A(r"Stage 3 resolves the third-person slots of the target lines. The characters remaining after hygiene are listed under "
  r"capital letters, and the resolver returns the ten most probable tokens at each output position. The language-specific "
  r"hint is inserted directly after the words \texttt{third-person pronouns} (Supplementary Table~\ref{tab:clitic})."
  "\n")
A(box("Stage 3, referent resolution (\\xen)", P["resolve"]))
A("\\begin{table}[ht]\n\\caption{\\textbf{Language-specific hints in the resolver prompt.} The hint text is inserted "
  "verbatim, including its leading space. Source languages without an entry receive no hint.}\\label{tab:clitic}\n"
  "\\small\n\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{11.5cm}@{}}\n\\toprule\nSource language & Hint \\\\\n\\midrule\n")
for code in ["tr", "az", "fa", "id", "fi", "et", "es"]:
    A(f"{ns['LANG_NAMES'][code]} & \\texttt{{{esc(ns['_CLITIC_HINT'][code])}}} \\\\\n")
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
A("For translation from English the resolver identifies the references that need grammatical gender in the target "
  "language.\n")
A(box("Stage 3, referent resolution (\\enx)", P["resolve_en2x"]))
A("Stage 5 turns the gate decision for each target slot into an instruction line. Lines are added to the instruction block "
  "of the translation prompt in the order of line and slot, and duplicate lines are removed. A target without a resolved "
  "slot and with an unobservable ledger receives a deferral line naming the person mentioned for every target line.\n")
A(box("Stage 5, gate instruction lines (\\xen)", "\n".join([P["commit_f"], P["commit_m"], P["defer"], P["defer_noslot"]])))
A(box("Stage 5, commitment line (\\enx)", P["commit_en2x"]))
A("Full ledger conditioning (CCL) prefixes its instruction lines with the list of character names.\n")
A(box("Character-name line (full conditioning only)", P["names"]))
A("Stage 6 checks each target line whose decisions refer to one character and describes every violation with one of the "
  "problem lines below. A flagged line receives one targeted repair request, and the repaired line is kept only if it "
  "no longer violates its decisions.\n")
A(box("Stage 6, problem lines", P["problems"]))
A(box("Stage 6, targeted repair", P["repair"]))
A(r"\subsection{Knowing-versus-using probe}" "\n")
A(box("Probe", P["probe"]))
A(r"\subsection{Benchmark construction}" "\n")
A("Two helper prompts supported the construction of TWC counterfactuals. The span finder copies the source spelling of an "
  "English name when the name does not occur exactly once in the source sentence. The name-gender estimate was requested only "
  "for capitalised words absent from the SSA records (Supplementary Note~5).\n")
A(box("Span finder", P["span"]))
A(box("Name-gender estimate", P["name_gender"]))

A(r"""\section{Output schemas}\label{si:schemas}
Structured calls used JSON-schema-constrained decoding. The schemas below are reproduced as sent to the server.
""")
for title, desc, sch in SCHEMAS:
    if desc:
        A(desc + "\n")
    A(box(title, json.dumps(sch, ensure_ascii=False)))

# ---------------------------------------------------------------- hygiene
gl = ns["GENDERLESS_SRC"]
assert 'c["type"] in {"gendered_pronoun", "verb_agreement", "adjective_agreement"}' in cell_with("def cue_is_valid(")
A(r"""\section{Ledger hygiene resources}\label{si:hygiene}
\subsection{Cue types and the typology rule}
The extractor assigns each cue one of seven types: """ + ", ".join(f"\\texttt{{{esc(t, True)}}}" for t in ns["CUE_TYPES"]) + r""".
In """ + ", ".join(sorted(ns["LANG_NAMES"][l] for l in gl)[:-1]) + " and " + sorted(ns["LANG_NAMES"][l] for l in gl)[-1] + r""",
cues of type \texttt{gendered\_pronoun}, \texttt{verb\_agreement} and \texttt{adjective\_agreement} are removed. A cue of any
type other than \texttt{gendered\_title} is also removed when every token of its quote belongs to the character's own source
or English names.

\subsection{Pseudo-entities}
An entry is a narrator entry if its English name matches the case-insensitive pattern \texttt{""" + esc(ns["_NARRATOR_EN"].pattern, True) + r"""}.
It is a pronoun entry if every token of every source name is a personal pronoun of the source language or of English
(Supplementary Table~\ref{tab:pron}). It is a generic entry if its English name matches the case-insensitive pattern
\texttt{""" + esc(ns["_GENERIC_EN"].pattern, True) + r"""}. These entries are removed before resolution. In \xen{}, a resolved
slot whose source text contains a token of a known character's name and no pronoun of the source language is discarded.

\subsection{Name prior}
The name prior is the female share of SSA birth records for the first token of the English name. No table prior is used when
that token is one of the words """ + ", ".join(f"\\textit{{{esc(t)}}}" for t in sorted(ns["_TITLES"])) + r""". The prior is
clipped to $[""" + f"{MAN['config']['v3']['name_prior_clip']:.2f}, {1 - MAN['config']['v3']['name_prior_clip']:.2f}" + r"""]$.
For names without a table prior the extractor's own estimate is used, clipped in the same way.
""")
A("\\begin{longtable}{@{}l>{\\raggedright\\arraybackslash}p{12.2cm}@{}}\n"
  "\\caption{\\textbf{Personal-pronoun lexicons used by the pseudo-entity and slot rules.} Closed-class pronouns with common "
  "case forms. Languages without an entry use the English list only.}\\label{tab:pron}\\\\\n"
  "\\toprule\nLanguage & Pronouns \\\\\n\\midrule\n\\endfirsthead\n\\toprule\nLanguage & Pronouns \\\\\n\\midrule\n\\endhead\n")
for code in ["tr", "az", "fa", "id", "fi", "et", "bn", "as", "es", "en"]:
    A(f"{ns['LANG_NAMES'][code]} & {{\\lexfam {esc(ns['_PRON_SRC'][code])}}} \\\\\n")
A("\\bottomrule\n\\end{longtable}\n")

# ---------------------------------------------------------------- scoring
ep = ns["EN_PRON"]
A(r"""\section{Scoring}\label{si:scoring}
For translation into English the scorer tokenises the target lines of the output and maps the pronouns """ +
  ", ".join(f"\\textit{{{w}}}" for w in ep["M"]) + r""" to masculine and """ + ", ".join(f"\\textit{{{w}}}" for w in ep["F"]) +
  r""" to feminine. The committed gender is masculine or feminine when only pronouns of that gender occur, MIXED when both
occur and neutral (N) when neither occurs. An empty output is scored as EMPTY. For synthetic biographies the same rule is
applied to the whole passage translation.

For translation from English the scorer compares the output tokens with the words that distinguish the correct reference from
its counterfactual reference after lower-casing and removing punctuation. Words unique to the correct reference count as
correct, words unique to the counterfactual reference as the opposite gender, both as MIXED and neither as undetermined,
which MT-GenEval counts as correct.
""")

# ---------------------------------------------------------------- validity and counterfactuals
V = MAN["validity"]
cf = MAN["counterfactual_construction"]
SUBN = {"mittens|late_binding": "MiTTenS, late binding", "mittens|late_binding_same_sentence": "MiTTenS, late binding, one sentence",
        "mittens|nouns_then_pronouns": "MiTTenS, nouns then pronouns", "mtgeneval|contextual": "MT-GenEval, contextual",
        "twc|bias": "TWC, bias", "twc|neutrality": "TWC, neutrality", "twc|reasoning": "TWC, reasoning",
        "twc|reasoning_same_sentence": "TWC, reasoning, one sentence"}
A(r"""\section{Benchmark validity checks and counterfactual construction}\label{si:validity}
Five checks were run on the base items before sampling (Supplementary Table~\ref{tab:validity}). Items whose gold English
reference was not scored as its own gold label were removed (""" + fmt_int(V["filter_scorer_invalid_items_dropped"]) + r""" items).
""")
GRP = lambda t: A(f"\\multicolumn{{2}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{14.2cm}}@{{}}}}{{\\textit{{{t}}}}} \\\\\n")
ROW = lambda t, v: A(f"\\quad {t} & {v} \\\\\n")
A("\\begin{longtable}{@{}>{\\raggedright\\arraybackslash}p{12.4cm}r@{}}\n"
  "\\caption{\\textbf{Benchmark validity checks.} Checks V1 to V5 on the base items before sampling. V5 is given in "
  "Supplementary Table~\\ref{tab:v5}.}\\label{tab:validity}\\\\\n\\toprule\nCheck and subset & Value \\\\\n\\midrule\n"
  "\\endfirsthead\n\\toprule\nCheck and subset & Value \\\\\n\\midrule\n\\endhead\n")
v1 = V["V1_twc_split"]
GRP("V1. Recovery of the released TWC test split")
ROW("Test rows matched exactly", fmt_int(v1["exact_match_test_rows_v1"]))
ROW("Test rows after normalising case, punctuation and whitespace", fmt_int(v1["split_counts"]["test"]))
ROW("Remaining rows, used as the development split", fmt_int(v1["split_counts"]["dev"]))
A("\\addlinespace\n")
GRP("V2. Share of determinable two-part items whose target sentence itself marks gender")
for k, v in sorted(V["V2_target_marks_gender_share"].items()):
    ROW(SUBN[k], f"{v:.3f}")
GRP("V2. Share of MT-GenEval items whose target sentence contains a name from the context")
ROW(SUBN["mtgeneval|contextual"], f"{V['V2_mtg_target_has_context_name_share']:.3f}")
A("\\addlinespace\n")
GRP("V3. Share of gold English references that the scorer assigns their gold label (\\xen)")
for k, v in sorted(V["V3_x2en_scorer_valid_share"].items()):
    ROW(SUBN[k], f"{v:.3f}")
GRP("V3. MT-GenEval scorer on its own references (\\enx)")
ROW("Correct references scored correct", f"{V['V3_en2x_correct_ref_scored_correct']:.3f}")
ROW("Counterfactual references detected as wrong", f"{V['V3_en2x_counterfactual_ref_detected']:.3f}")
A("\\addlinespace\n")
v4 = V["V4_twc_reasoning_name_recoverability"]
GRP("V4. TWC items with a personal-name antecedent and gold F or M (Turkish rows), by the SSA names in the first sentence "
    "(female share at least 0.9 or at most 0.1)")
ROW("A confident name of the gold gender and one of the other gender", fmt_int(v4["opposite_pair"]))
ROW("A confident name of the gold gender only", fmt_int(v4["supported_only"]))
ROW("No confident name of the gold gender", fmt_int(v4["not_supported"]))
A("\\bottomrule\n\\end{longtable}\n")
v5 = V["V5_mittens_cue_type_by_lang"]
A("\\begin{table}[ht]\n\\caption{\\textbf{MiTTenS source cues (check V5).} Base items of the nouns-then-pronouns subset whose "
  "evidence sentence contains a gendered source noun or whose only cue is the person's name.}\\label{tab:v5}\n\\small\n"
  "\\begin{tabular}{@{}lrr@{}}\n\\toprule\nLanguage & Gendered source noun & Name only \\\\\n\\midrule\n")
for lang in sorted(v5["explicit_noun"], key=lambda l: ns["LANG_NAMES"][l]):
    A(f"{ns['LANG_NAMES'][lang]} & {v5['explicit_noun'][lang]} & {v5['name_only'][lang]} \\\\\n")
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
n_cand = cf["twc_names_from_table"] + 2
A(r"""Counterfactual variants were built as described in Methods (Supplementary Table~\ref{tab:cf}). For TWC, """ +
  fmt_int(cf["twc_names_from_table"]) + r""" capitalised words of the English evidence sentences had an SSA prior. The two
remaining words, \textit{Raj} and \textit{Spanish}, were scored with the name-gender prompt (female share 0.05 and 0.00). No
test counterfactual contains either word. For MiTTenS the name forms of Supplementary Table~\ref{tab:names} were exchanged.
""")
A("\\begin{table}[ht]\n\\caption{\\textbf{Counterfactual construction.} Counts over the sampled development and test items.}\\label{tab:cf}\n"
  "\\small\n\\begin{tabular}{@{}lr@{}}\n\\toprule\nOutcome & Items \\\\\n\\midrule\n")
CFN = [("mit_ok_conflict", "MiTTenS name swap with a gendered source noun (cue conflict, gold kept)"),
       ("mit_ok_flip", "MiTTenS name swap with the name as the only cue (gold flipped)"),
       ("mit_swap_failed", "MiTTenS swap not possible"),
       ("twc_ok", "TWC name swap built (gold flipped)"),
       ("twc_names_not_confident_opposite", "TWC names not confidently of opposite gender"),
       ("twc_not_two_names", "TWC sentence without exactly two names"),
       ("twc_span_not_found", "TWC name span not found in the source"),
       ("mtg_ok", "MT-GenEval context flip built (gold flipped)"),
       ("mtg_has_gendered_noun", "MT-GenEval context with a gendered noun (not flipped)")]
assert {k for k, _ in CFN} == set(cf) - {"twc_names_from_table"}, set(cf)
for k, lab in CFN:
    A(f"{lab} & {fmt_int(cf[k])} \\\\\n")
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
NF = MAN["mittens_name_forms"]
A("\\begin{table}[ht]\n\\caption{\\textbf{MiTTenS name forms exchanged in counterfactual variants.} Source spellings of the "
  "female name Sarah and the male name Benjamin observed in each language.}\\label{tab:names}\n\\small\n"
  "\\begin{tabular}{@{}lll@{}}\n\\toprule\nLanguage & Female form & Male form \\\\\n\\midrule\n")
for code in sorted(NF, key=lambda l: ns["LANG_NAMES"][l]):
    A(f"{ns['LANG_NAMES'][code]} & {{\\lexfam {esc(', '.join(NF[code]['F']))}}} & {{\\lexfam {esc(', '.join(NF[code]['M']))}}} \\\\\n")
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ---------------------------------------------------------------- synthetic biographies
sc = pd.read_csv(RES / "records" / "scores_items.csv", low_memory=False)
sb = sc[(sc.subset == "synthbio") & (sc.condition == "adjacent")]
ORDER = [("llm_plain", "Plain prompting"), ("llm_cautious", "Cautious prompting"), ("llm_cot_gender", "Chain-of-thought"),
         ("ccl", "CCL (full conditioning)"), ("ccl_no_repair", "CCL without repair"), ("ccl_posthoc", "CCL applied post hoc"),
         ("ccl_gate", "CCL-Gate"), ("ccl_gate_posthoc", "Gate applied post hoc"), ("oracle_goe", "Gold-label reference")]
assert set(sb.system) == {k for k, _ in ORDER}, set(sb.system)
langs = sorted(sb.lang.unique(), key=lambda l: ns["LANG_NAMES"][l])
n_sb = sb.groupby("system").size()
assert n_sb.nunique() == 1
A(r"""\section{Passage-level results on synthetic biographies}\label{si:synthbio}
The synthetic-biography subset of MiTTenS presents one passage per item, and every pronoun of the passage refers to the
person described. Each passage translation is scored by the gender of all English pronouns it contains
(Supplementary Note~4). The test set holds """ + fmt_int(n_sb.iloc[0]) + r""" passages in """ +
  ", ".join(ns["LANG_NAMES"][l] for l in langs[:-1]) + " and " + ns["LANG_NAMES"][langs[-1]] + r""" (Supplementary
Table~\ref{tab:synthbio}).
""")
A("\\begin{table}[ht]\n\\caption{\\textbf{Passage-level outcomes on synthetic biographies.} Shares of passages (\\%) whose "
  "translation uses only pronouns of the gold gender (correct), no gendered pronoun (neutral), pronouns of both genders "
  "(mixed) or only pronouns of the other gender (wrong), and empty outputs. Infer-then-tag, which tags a single target line, "
  "was not run on this subset.}\\label{tab:synthbio}\n\\small\n"
  "\\begin{tabular}{@{}lrrrrrr@{}}\n\\toprule\nSystem & $n$ & Correct & Neutral & Mixed & Wrong & Empty \\\\\n\\midrule\n")
for k, lab in ORDER:
    g = sb[sb.system == k]
    com = g.committed
    wrong = (com.isin(["F", "M"]) & (com != g.gold_gender)).mean()
    corr = g.correct.astype(float).mean()
    assert abs(corr - (com == g.gold_gender).mean()) < 1e-9, k
    empty = (com == "EMPTY").mean()
    assert abs(1 - corr - (com == "N").mean() - (com == "MIXED").mean() - wrong - empty) < 1e-9, k
    A(f"{lab} & {len(g)} & {100 * corr:.0f} & {100 * (com == 'N').mean():.0f} & {100 * (com == 'MIXED').mean():.0f} & "
      f"{100 * wrong:.0f} & {100 * empty:.0f} \\\\\n")
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")

# ---------------------------------------------------------------- software and data
pk = MAN["packages"]
ds = MAN["datasets"]
cal = MAN["calibration"]
PKN = dict(numpy="NumPy", pandas="pandas", scipy="SciPy", sklearn="scikit-learn", matplotlib="matplotlib",
           sacrebleu="sacreBLEU", statsmodels="statsmodels")
pkl = [f"{PKN[k]} {v}" for k, v in pk.items() if k in PKN]
A(r"""\section{Software, data versions and run records}\label{si:software}
The reported run used Python """ + MAN["python"].split()[0] + r""" under Windows 11 with """ + ", ".join(pkl[:-1]) + " and " +
  pkl[-1] + r""". The datasets were read at the fixed revisions of Supplementary Table~\ref{tab:rev}. The distant condition
drew on """ + fmt_int(ds["flores_filler"]["n_person_free"]) + r""" person-free FLORES-200 devtest sentences.
""")
A("\\begin{table}[ht]\n\\caption{\\textbf{Dataset revisions.} Commit identifiers of the dataset sources read by the experiment."
  " The SSA birth-name compilation is the repository github.com/hadley/data-baby-names (national SSA records, 1880--2008,"
  " top 1,000 names per year); FLORES-200 was read from the released archive."
  "}\\label{tab:rev}\n\\small\n\\begin{tabular}{@{}ll@{}}\n\\toprule\nSource & Revision \\\\\n\\midrule\n")
for key, lab in [("mittens", "MiTTenS"), ("twc", "Translate-with-Care"), ("mtgeneval", "MT-GenEval"),
                 ("names", f"SSA birth-name compilation ({fmt_int(ds['name_table']['n_names'])} names)")]:
    A(f"{lab} & \\texttt{{{ds[key]['commit_used']}}} \\\\\n")
A("FLORES-200 devtest & \\texttt{flores200\\_dataset.tar.gz} (dl.fbaipublicfiles.com/nllb) \\\\\n")  # added 24 Oct 2026
A("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
A(r"""The run comprised """ + fmt_int(MAN["llm_stats"]["cache_hit"]) + r""" cached model calls for """ +
  fmt_int(MAN["n_test_instances"]) + r""" test and """ + fmt_int(MAN["n_dev_instances"]) + r""" development instances.
Log-probabilities were returned for """ + f"{100 * MAN['resolver']['lp_share_with_logprobs']:.1f}" + r"""\% of resolver
responses. Calibration on development data gave the temperature """ + f"{cal['weights']['gendered_pronoun'] / 3.0:.3f}" + r""" on
""" + fmt_int(cal["meta"]["n"]) + r""" slots, the full-conditioning threshold """ + f"{cal['tau']:.2f}" + r""" on """ +
  fmt_int(cal["n_dev"]) + r""" instances and the gate threshold """ + f"{cal['tau_gate']:.2f}" + r""". The random seed was
""" + str(MAN["config"]["seed"]) + r""".
\end{document}
""")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("".join(L), encoding="utf-8")
print("written", OUT, sum(len(x) for x in L), "characters")
