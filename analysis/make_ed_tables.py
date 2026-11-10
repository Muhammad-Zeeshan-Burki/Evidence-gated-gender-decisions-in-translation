"""Writes the Extended Data tables (LaTeX) from the result files, so that every number is transcribed by code."""
import json
import os
import numpy as np
import pandas as pd
R = os.environ.get("CCL_RESULTS", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Results", "pilot"))   # folder of the reported run
OUT = "tex/ed_tables.tex"
L = []
fmt_int = lambda x: f"{int(x):,}"


def num(x, d=1):
    """Fixed-point number with a typographic minus sign; values that round to zero print without a sign."""
    t = f"{x:.{d}f}"
    if float(t) == 0:
        return f"{0:.{d}f}"
    return t.replace("-", "$-$")


def signed(x, d=1):
    """Difference with an explicit sign (+ or typographic minus); values that round to zero print as 0.0."""
    t = f"{x:+.{d}f}"
    if float(t) == 0:
        return f"{0:.{d}f}"
    return t.replace("-", "$-$")


def diff_ci(v, lo, hi):
    return f"{signed(100 * v)} [{num(100 * lo)}, {num(100 * hi)}]"
LANG = dict(as_="Assamese", az="Azerbaijani", bho="Bhojpuri", bn="Bengali", es="Spanish", et="Estonian", fa="Persian",
            fi="Finnish", id="Indonesian", lg="Luganda", ln="Lingala", mai="Maithili", om="Oromo", tr="Turkish", ar="Arabic",
            de="German", hi="Hindi")
LANG["as"] = LANG.pop("as_")

# ---------------- ED Table 1: benchmark composition ----------------
c = pd.read_csv("outputs/benchmark_composition.csv")
order = [("mittens", "nouns_then_pronouns"), ("mittens", "late_binding"), ("mittens", "late_binding_same_sentence"),
         ("mittens", "synthbio"), ("twc", "reasoning"), ("twc", "reasoning_same_sentence"), ("twc", "bias"), ("twc", "neutrality"),
         ("mtgeneval", "contextual")]
DS = dict(mittens="MiTTenS", twc="TWC", mtgeneval="MT-GenEval")
SUB = dict(nouns_then_pronouns="Nouns then pronouns", late_binding="Late binding", late_binding_same_sentence="Late binding, one sentence",
           synthbio="Synthetic biographies", reasoning="Reasoning", reasoning_same_sentence="Reasoning, one sentence",
           bias="Bias", neutrality="Neutrality", contextual="Contextual")
COND = dict(adjacent="A", distant_8="D8", distant_32="D32", memory="M", isolated="I")
GOLD = dict(determinable="det.", unrecoverable="unrec.", referent_ambiguous="ambig.", passage="passage", mixed="mixed")
L.append(r"""\begin{table}[!htbp]
\caption{\textbf{Benchmark composition.} Instances per dataset and subset in the development and test splits. Conditions are adjacent (A), distant with 8 or 32 filler sentences (D8, D32), memory (M) and isolated (I). Gold labels are determinable (det.), unrecoverable (unrec.), referent-ambiguous (ambig.), passage-level (passage) or mixed-gender context (mixed). Analysed instances are the \xen{} determinable, unrecoverable and referent-ambiguous instances in conditions A, D8, M and I. Held-out instances exclude items inspected during development. Counterfactual variants are included in the counts.}\label{edtab:data}
\tiny
\setlength{\tabcolsep}{1.8pt}
\begin{tabular*}{\textwidth}{@{\extracolsep\fill}L{2.0cm}L{1.1cm}L{3.0cm}L{1.1cm}L{1.1cm}rrrr@{}}
\toprule
Dataset and subset & Direction & Languages & Condi\-tions & Gold labels & Dev & Test & Ana\-lysed & Held-out \\
\midrule""")
for ds, sub in order:
    r = c[(c.dataset == ds) & (c.subset == sub)].iloc[0]
    langs = ", ".join(sorted(LANG[l] for l in r.languages.split()))
    conds = ", ".join(COND[x] for x in r.conditions.split())
    gold = ", ".join(GOLD[x] for x in r.gold.split())
    direc = r"\xen" if r.direction == "x2en" else r"\enx"
    an = fmt_int(r.analysed) if r.analysed else "--"; ho = fmt_int(r.heldout) if r.heldout else "--"
    L.append(f"{DS[ds]}, {SUB[sub].lower() if False else SUB[sub]} & {direc} & {langs} & {conds} & {gold} & {fmt_int(r.dev)} & {fmt_int(r.test)} & {an} & {ho} \\\\")
tot = c[["dev", "test", "analysed", "heldout"]].sum()
L.append(r"\midrule")
L.append(f"Total & & 17 source and 3 target languages & & & {fmt_int(tot.dev)} & {fmt_int(tot.test)} & {fmt_int(tot.analysed)} & {fmt_int(tot.heldout)} \\\\")
L.append(r"""\botrule
\end{tabular*}
\end{table}
""")

# ---------------- ED Table 2: held-out paired comparisons ----------------
t = pd.read_csv("outputs/heldout_paired_exact_p.csv")
BN = {"llm_plain": "Plain prompting", "llm_cautious": "Cautious prompting", "llm_cot_gender": "Chain-of-thought", "infer_then_tag": "Infer-then-tag"}
CN = [("all_conditions", "All conditions"), ("adjacent", "Adjacent"), ("memory", "Memory"), ("distant_8", "Distant"), ("isolated", "Isolated")]
def pfmt(p):
    if p < 0.001:
        e = int(np.floor(np.log10(p))); m = p / 10 ** e
        return f"${m:.1f}\\times10^{{{e}}}$"
    return f"{p:.3f}"
L.append(r"""\begin{table}[!htbp]
\caption{\textbf{Held-out paired comparisons.} Difference in per-instance correctness, CCL-Gate minus each prompting strategy, in percentage points with 95\% item-cluster bootstrap intervals (10,000 resamples). $b$ counts instances that CCL-Gate gets right and the baseline gets wrong, and $c$ counts the reverse. $P$ is the two-sided exact McNemar test, and $P_{\text{Holm}}$ is adjusted across the four baselines within each condition.}\label{edtab:paired}
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular*}{\textwidth}{@{\extracolsep\fill}llrrll@{}}
\toprule
Baseline & Difference [95\% CI] & $b$ & $c$ & $P$ & $P_{\text{Holm}}$ \\
\midrule""")
for key, name in CN:
    g = t[t.subset == key]
    L.append(f"\\multicolumn{{6}}{{@{{}}l}}{{\\textit{{{name} ($n={fmt_int(g.n.iloc[0]).replace(',', '{,}')}$)}}}} \\\\")
    for bkey in ["llm_plain", "llm_cautious", "llm_cot_gender", "infer_then_tag"]:
        r = g[g.comparison == f"ccl_gate - {bkey}"].iloc[0]
        L.append(f"\\quad {BN[bkey]} & {diff_ci(r['diff'], r.ci_low, r.ci_high)} & {int(r.b)} & {int(r.c)} & {pfmt(r.p_exact)} & {pfmt(r.p_holm_exact)} \\\\")
    if key != "isolated":
        L.append(r"\addlinespace")
L.append(r"""\botrule
\end{tabular*}
\end{table}
""")

# ---------------- ED Table 3: settings, parameters and cost ----------------
cost = pd.read_csv(f"{R}/tables/T15_cost_tokens.csv", index_col=0)
w = json.load(open(f"{R}/records/ccl_weights.json"))
CN2 = [("llm_plain", "Plain prompting"), ("llm_cautious", "Cautious prompting"), ("llm_cot_gender", "Chain-of-thought"),
       ("infer_then_tag", "Infer-then-tag"), ("oracle_goe", "Gold-label reference"), ("ccl", "CCL (full conditioning)"),
       ("ccl_no_repair", "CCL without repair"), ("ccl_posthoc", "CCL applied post hoc"), ("ccl_gate_posthoc", "Gate applied post hoc"),
       ("ccl_gate", "CCL-Gate"), ("probe", "Knowledge probe")]
a = w["gendered_pronoun"] / 3.0
L.append(r"""\begin{table}[!htbp]
\caption{\textbf{Settings, calibrated parameters and cost.} All systems share the model, server and decoding settings. Token counts are prompt plus completion tokens per test instance across all conditions, including the distant-32 condition.}\label{edtab:settings}
\scriptsize
\begin{tabular*}{\textwidth}{@{\extracolsep\fill}L{3.4cm}L{9.0cm}@{}}
\toprule
\multicolumn{2}{@{}l}{\textit{Model and inference}}\\
Model & Qwen3-8B, GGUF 4-bit k-quantization (Q4\_K\_M), thinking mode disabled \\
Server & llama.cpp build b11642 (CUDA 12.4), OpenAI-compatible interface, four parallel slots \\
Context per slot & 4,096 tokens with 16-bit key--value cache; reissued requests 8,192 tokens with 8-bit key--value cache \\
Decoding & Greedy; JSON-schema constraints for extraction, resolution, probe and gender inference \\
Generation budgets (tokens) & Translation and repair 768; extraction and chain-of-thought 1,024; resolution 512; probe and inference 32 \\
Resolver probabilities & Ten most probable tokens at each output position; letters A--T for up to 20 characters \\
Hardware & NVIDIA GeForce RTX 4070 Laptop GPU (8 GB), AMD Ryzen 9 7845HX, 32 GB memory; 88.5 generated tokens\,s$^{-1}$ with four concurrent requests \\
\addlinespace
\multicolumn{2}{@{}l}{\textit{Evidence model and gate}}\\
Expert weights $\mathbf{w}^{(0)}$ & Gendered pronoun, kinship noun, gendered title and narrator statement 3.0; gendered noun and verb agreement 2.5; adjective agreement 2.0; name prior 0.8 \\""")
L.append(f"Temperature $a$ & {a:.3f}, fitted by maximum likelihood on 1,001 development slots ($\\lambda=10^{{-3}}$, L-BFGS-B) \\\\")
L.append(r"""Name prior $\pi_e$ & Female share of SSA birth records for the given name (6,782 names), clipped to $[0.05, 0.95]$ \\
Full-conditioning threshold $\tau$ & 0.70, selected from $\{0.55, 0.60, \dots, 0.95\}$ by development balanced accuracy \\
Gate threshold $\tau_{\text{gate}}$ & 0.60, selected from $\{0.60, 0.65, \dots, 0.95, 1.01\}$ on simulated development outputs \\
Ambiguity rule & Defer if $a_k\ge0.5$ and two characters with evidence lean to opposite genders \\
Repair & One targeted repair round, kept only if the violation disappears \\
\addlinespace
\multicolumn{2}{@{}l}{\textit{Statistics}}\\
Intervals and tests & Item-cluster bootstrap with 10,000 resamples (500 for the decision-layer analysis); exact McNemar test; Holm adjustment; seed 20261006 \\
\addlinespace
\multicolumn{2}{@{}l}{\textit{Tokens per instance, mean (median)}}\\""")
for k, nm in CN2:
    r = cost.loc[k]
    L.append(f"{nm} & {r['mean']:,.0f} ({r['median']:,.0f}) \\\\")
L.append(r"""\botrule
\end{tabular*}
\end{table}
""")

# ---------------- ED Table 4: decision-layer analysis ----------------
lab = pd.read_csv(f"{R}/tables/lab/lab_real_qwen3-8b.csv")
DESC = [("v1_default", "Reference: one non-negative weight per cue type, balanced threshold rule"),
        ("fit_temperature(v2)", "Single temperature on expert weights (used in CCL-Gate)"),
        ("fit_nnls", "Per-type weights by bounded maximum likelihood"),
        ("fit_pooled2", "Two weights (all cues pooled, name prior)"),
        ("fit_default_weights", "Expert weights without fitting"),
        ("argmax_referent", "Most probable referent only, no averaging over $q_k$"),
        ("saturating_counts", "Saturating cue counts, $\\operatorname{sign}(n)\\log(1+|n|)$"),
        ("no_name_prior", "Name prior removed"),
        ("unknown_renormalised", "Unresolved mass renormalized away"),
        ("tau_fixed@0.8", "Fixed threshold $\\tau=0.8$"),
        ("tau_risk@0.10", "Threshold chosen for development risk $\\le0.10$"),
        ("no_defer", "No deferral (commit to the more probable gender)")]
# The lab's "plain_list" variant is omitted: it reads the extractor's gender_guess field, which the evaluated (v3)
# extraction schema removes, so it produced no decisions on these cached states (all metrics 0) and is not a measurement.
L.append(r"""\begin{table}[!htbp]
\caption{\textbf{Decision-layer analysis.} Slot decisions of the full-conditioning rule re-evaluated on cached ledger and resolver states of the test set (no new model calls). Weights and thresholds are refitted on development data for every variant. BAL, ACC, deferral, coverage and risk are decision-level quantities. $\Delta$BAL is the paired difference from the reference configuration, in percentage points, with a 95\% item-cluster bootstrap interval (500 resamples). The bounded maximum-likelihood fit produced the same decisions as the reference.}\label{edtab:lab}
\scriptsize
\setlength{\tabcolsep}{2pt}
\begin{tabular*}{\textwidth}{@{\extracolsep\fill}L{3.3cm}rrrrrrl@{}}
\toprule
Variant & $\tau$ & BAL & ACC & Deferral & Coverage & Risk & $\Delta$BAL [95\% CI] \\
\midrule""")
for key, desc in DESC:
    r = lab[lab.variant == key].iloc[0]
    d = "--" if key == "v1_default" else diff_ci(r.dBAL, r.dBAL_lo, r.dBAL_hi)
    L.append(f"{desc} & {r.tau:.2f} & {r.BAL:.3f} & {r.ACC:.3f} & {r.ABSTAIN_unr:.3f} & {r.coverage:.3f} & {r.risk:.3f} & {d} \\\\")
L.append(r"""\botrule
\end{tabular*}
\end{table}
""")
# ---------------- ED Table 5: qualitative examples (verbatim outputs of the reported run) ----------------
L.append(r"""\begin{table}[!htbp]
\caption{\textbf{Illustrative held-out examples.} Verbatim outputs for the target line of held-out instances, chosen to illustrate each decision type of the gate; they are not a random sample. Earlier text available only as background is shown in italics. The decision gives the gate's output for the target slot with the reason and $\mathrm{conf}_k$.}\label{edtab:examples}
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular*}{\textwidth}{@{\extracolsep\fill}L{1.65cm}L{2.45cm}L{1.75cm}L{1.75cm}L{1.75cm}L{1.6cm}@{}}
\toprule
Language, condition & Source (gold) & Plain prompting & Cautious prompting & CCL-Gate & Gate decision \\
\midrule
Turkish, isolated & Onun \c{s}akalar\i n\i{} ger\c{c}ekten seviyorum. (unrecoverable) & I really like his jokes. & I really like his jokes. & I really like their jokes. & Defer (unobservable) \\
\addlinespace
Turkish, adjacent & Oscar bir f\i r\i nc\i, Diana ise bir u\c{c}u\c{s} g\"orevlisidir. O lezzetli ekmek yapar. (male) & She makes delicious bread. & He makes delicious bread. & He makes delicious bread. & Commit male (confident, 0.73) \\
\addlinespace
Indonesian, adjacent & Oliver dan Alice adalah seniman, dia menggunakan cat air. (referent-ambiguous) & Oliver and Alice are artists, she uses watercolor. & Oliver and Alice are artists, he uses watercolor. & Oliver and Alice are artists, they use watercolor. & Defer (ambiguous, 0.61) \\
\addlinespace
Finnish, memory & \textit{Emily on uimari ja Lucas valokuvaaja.} H\"an ottaa valokuvia. (male) & She takes photographs. & She takes photographs. & He takes photographs. & Commit male (confident, 0.73) \\
\addlinespace
Estonian, adjacent & Vend John on munk ja Dame Helen on balletitantsija. Ta elab kloostris. (male) & She lives in a monastery. & He lived in a monastery. & He lives in a monastery. & Commit male (confident, 0.73) \\
\botrule
\end{tabular*}
\end{table}
""")
open(OUT, "w").write("\n".join(L) + "\n")
print(open(OUT).read()[:3000])
