# Evidence-gated gender decisions in translation (CCL-Gate)

Code and aggregate results for the article

> **A calibrated character ledger for evidence-based gender decisions in machine translation**
> Muhammad Zeeshan Burki, Muhammad Rizwan and Rashid Naseem
> School of Computing Sciences, Pak-Austria Fachhochschule: Institute of Applied Sciences and Technology (PAF-IAST), Haripur, Pakistan.

Many languages leave a person's gender unmarked (Turkish *o*, Persian *او*, Indonesian *dia*, dropped subjects), yet English
forces a choice between *he*, *she* and neutral wording. **CCL-Gate** is a training-free, inference-time architecture that
separates the gender decision from text generation. It wraps an unmodified instruction-following LLM (Qwen3-8B, 4-bit)
and has two calibrated scalars, a temperature *a* and a gate threshold *τ*<sub>gate</sub>.

| Stage | What happens | Component |
|---|---|---|
| 1. Ledger extraction | The LLM lists every character with verbatim, typed gender cues (JSON schema); a cue survives only if its quote occurs verbatim in the source | LLM call |
| 2. Ledger hygiene | Removes typologically impossible cues, name-only cues and pseudo-entities; sets a name prior from US SSA birth records | deterministic |
| 3. Referent resolution | One constrained call maps every third-person slot to a ledger entry; the referent distribution and ambiguity mass are read from token probabilities | LLM call |
| 4. Evidence model | Intercept-free logistic model over weighted cue counts and the name prior gives the slot posterior *P*<sub>k</sub>(F) | calibrated |
| 5. Evidence gate | **DEFER** (no evidence, or ambiguous between characters of opposite gender), **COMMIT** (confidence ≥ *τ*<sub>gate</sub>) or **KEEP** the translator's choice | calibrated |
| 6. Translate and verify | Decisions become one-line instructions in the plain translation prompt; a verifier with monotone targeted repair enforces them | LLM call |

Headline held-out result (X→EN, 1,834 instances from 675 items in 14 source languages; `Results/pilot/tables/T1_headline_heldout.md`):

| System | ACC ↑ | UCR ↓ | BAL ↑ |
|---|---:|---:|---:|
| Plain prompting | 0.552 | 0.828 | 0.362 |
| Cautious prompting | 0.543 | 0.856 | 0.344 |
| Chain-of-thought | 0.551 | 0.864 | 0.344 |
| Infer-then-tag | 0.601 | 0.918 | 0.342 |
| CCL (full conditioning) | 0.350 | 0.165 | 0.593 |
| **CCL-Gate** | **0.469** | **0.257** | **0.606** |
| Gold-label reference | 0.893 | 0.812 | 0.540 |

ACC: exact-gender accuracy on 1,445 determinable instances. UCR: unwarranted commitment rate (gendered pronoun) on 389
unrecoverable or referent-ambiguous instances. BAL = ½ ACC + ½ (1 − UCR); a system that always writes neutral wording
scores 0.50. See the article for confidence intervals, paired tests and limitations.

---

## Repository layout

```
CCL_final.ipynb            The complete implementation: data acquisition at pinned commits, benchmark construction,
                           LLM backend + response cache, prompts, CCL / CCL-Gate, baselines, dev-only calibration,
                           scoring, statistics, analyses, figures and export to Results/. Stored with the outputs of
                           the reported run (machine-specific paths replaced by <project>).
requirements_ccl.txt       Python dependencies (minimum versions).
requirements_lock.txt      Exact package versions of the environment used for the reported run (pip freeze).
data/
  dev_inspected_test_items.json      92 test items inspected during development; excluded from every held-out result.
  name_gender_lexicon__qwen3-8b.json Name priors elicited from the translator for two capitalised words absent from the SSA table.
Results/pilot/             Aggregate results of the reported run, exactly as exported by the notebook
  config_used.json         Full configuration of the run.
  records/                 Calibrated parameters (ccl_weights.json, ccl_tau.json, ccl_tau_gate.json) and manifest.json
                           (dataset commits, package versions, hardware, cache statistics).
  tables/                  T0–T19 result tables (CSV + Markdown), data card, tau selection, decision-layer lab.
  figures/                 Notebook figures F1–F6 (PNG + PDF).
analysis/                  Scripts that compute the statistics reported in the article from a run's Results folder
  outputs/                 Their outputs for the reported run (headline intervals, exact McNemar tests, per-language,
                           ablation, calibration, risk–coverage, knowing-versus-using, hygiene and EN→X summaries).
  tex/ed_tables.tex        Extended Data Tables written by make_ed_tables.py.
  examples_*.json          Cached states of the worked examples shown in Figs 1–2 and Extended Data Table 5.
figure_sources/            Scripts and Source Data workbooks for Figs 1–5 and Extended Data Figs 1–5.
scripts/windows/           PowerShell scripts used on the laptop: setup, model server, server check, cache repair, run.
```

## Requirements

* Python 3.12 (the reported run used 3.12.6). `pip install -r requirements_ccl.txt ipykernel nbconvert`
  (exact versions: `requirements_lock.txt`). The NLLB baseline needs a CUDA build of PyTorch; it is not part of the
  reported system profile and can be skipped.
* An OpenAI-compatible server that returns token log-probabilities and supports JSON-schema constrained decoding. The
  reported run used **llama.cpp build b11642** (CUDA 12.4) serving **Qwen3-8B Q4_K_M GGUF**
  (`https://huggingface.co/Qwen/Qwen3-8B-GGUF`), thinking mode disabled, four parallel slots.
* Hardware of the reported run: NVIDIA GeForce RTX 4070 Laptop GPU (8 GB), AMD Ryzen 9 7845HX, 32 GB RAM, Windows 11.
* `git` and internet access: the notebook clones the datasets at pinned commits and downloads the FLORES-200 tarball.

## Reproducing the experiments

### 1. Full run (Windows, as in the article)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\1_setup.ps1          # llama.cpp b11642, Qwen3-8B Q4_K_M (~5 GB), venv
powershell -ExecutionPolicy Bypass -File scripts\windows\2b_start_server_8k.ps1 # keep this window open
powershell -ExecutionPolicy Bypass -File scripts\windows\3_check_server.ps1     # 1-minute pre-flight check
powershell -ExecutionPolicy Bypass -File scripts\windows\run_final_notebook.ps1 # executes CCL_final.ipynb, writes Results\pilot
```

Everything local (venv, binaries, model, `ccl_work/` with the data, the SQLite response cache and run outputs) is created
under `_runtime/`, which is git-ignored. Every model call is cached by (model, messages, decoding settings), so an
interrupted run resumes where it stopped. A complete run issues tens of thousands of model calls (the reported run
comprises 56,866) and takes more than a day on the laptop above.

The reported run first served 4,096 tokens per slot with a 16-bit KV cache (`2_start_server.ps1`); requests that
exceeded this context or came back empty were removed from the cache with `fix_failed_calls.ps1` and reissued with
8,192 tokens per slot and an 8-bit KV cache (`2b_start_server_8k.ps1`). See Methods, "Translator and inference".

### 2. Any platform

Start an OpenAI-compatible server (e.g. llama.cpp: `llama-server -m Qwen3-8B-Q4_K_M.gguf --alias qwen3-8b -c 32768 -np 4
-ngl 99 -fa on -ctk q8_0 -ctv q8_0 --port 8080 --jinja`), then:

```bash
mkdir -p _runtime/ccl_work/data && cp data/*.json _runtime/ccl_work/data/
export CCL_WORK_DIR=$PWD/_runtime/ccl_work CCL_RESULTS_DIR=$PWD/Results CCL_RUN_MODE=pilot \
       CCL_LLM_BACKEND=openai CCL_OPENAI_BASE_URL=http://localhost:8080/v1 CCL_TRANSLATOR=qwen3-8b \
       CCL_SERVER_KIND=llamacpp CCL_CONCURRENCY=4 CCL_SKIP_INSTALL=1
jupyter nbconvert --to notebook --execute CCL_final.ipynb --output-dir _runtime/runs \
       --output CCL_final_executed.ipynb --ExecutePreprocessor.timeout=-1
```

Run modes (`CCL_RUN_MODE`): `dry_run` (mock model, plumbing test only; numbers are meaningless and stamped as synthetic),
`smoke` (4 items per group), `pilot` (20 items per dataset, subset, language and split: **the configuration reported in
the article**), `full`. If a server requires a key, set `CCL_OPENAI_API_KEY`; no key is stored in this repository.

### 3. Statistics, Extended Data tables and figures

Run from `analysis/` against the `Results/pilot` folder of a run (per-instance files `records/scores_items.csv` and
`records/records_items.jsonl`, and `test_instances.pkl` from `_runtime/ccl_work/outputs/pilot/qwen3-8b/`, are written by
the notebook):

| Script | Produces |
|---|---|
| `paper_stats.py <Results/pilot> ../data/dev_inspected_test_items.json outputs <test_instances.pkl>` | held-out headline intervals, per-language, ablation, gender-gap, risk–coverage, reliability, knowing-versus-using, gate-profile, counterfactual, hygiene and EN→X tables |
| `paired_exact.py <Results/pilot> outputs` | `outputs/heldout_paired_exact_p.csv` (Fig. 3c, Extended Data Table 2) |
| `composition.py <Results/pilot> ../data/dev_inspected_test_items.json outputs` | `benchmark_composition.csv`, `synthbio_passage_accuracy.csv` |
| `extra_stats.py <Results/pilot> ../data/dev_inspected_test_items.json outputs` | overall correctness, both-direction knowing-versus-using, counterfactual both-correct, posterior informativeness |
| `make_ed_tables.py` | `tex/ed_tables.tex` (reads `CCL_RESULTS`, default `../Results/pilot`) |
| `make_supplementary.py <CCL_final.ipynb> <Results/pilot> <out.tex>` | Supplementary Information source with every prompt rendered by the notebook's own prompt functions |
| `hygiene_stats.py`, `run_examples.py`, `run_raw.py` | hygiene audit and the worked examples, by replaying the notebook against a run's response cache through `replay_harness.py` (set `CCL_NOTEBOOK` and `CCL_REPLAY_WORK`) |

The figure scripts need only files in this repository: `analysis/outputs/` and `Results/pilot/tables/`. From each folder
in `figure_sources/`, run `python <script>.py` (matplotlib, pandas, openpyxl). Figs 1 and 2 are drawn with
`common/svgkit.py` and rendered to PDF with Playwright and Chromium. Set `CCL_RESULTS` to use another run.

## Calibrated settings of the reported run

| Setting | Value |
|---|---|
| Expert cue weights **w**<sup>(0)</sup> | gendered pronoun, kinship noun, gendered title, narrator statement 3.0; gendered noun, verb agreement 2.5; adjective agreement 2.0; name prior 0.8 |
| Temperature *a* | 0.415 (maximum likelihood on 1,001 development slots, λ = 10<sup>−3</sup>, L-BFGS-B) |
| Full-conditioning threshold *τ* | 0.70 (development balanced accuracy) |
| Gate threshold *τ*<sub>gate</sub> | 0.60 (simulated development outputs) |
| Name prior | SSA female share 1880–2008 (6,782 names), clipped to [0.05, 0.95] |
| Decoding | greedy; JSON-schema constraints for extraction, resolution, probe and inference; ten most probable tokens per position |
| Statistics | item-cluster bootstrap, 10,000 resamples (500 for the decision-layer analysis); exact McNemar; Holm; seed 20261006 |

All parameters were estimated on development data only. Fitted values: `Results/pilot/records/`.

## Data

The benchmark is built from public datasets that are **not redistributed here**; the notebook downloads them at the
pinned commits below and builds every instance deterministically.

| Dataset | Source (pinned commit) | Terms |
|---|---|---|
| MiTTenS | `google-research-datasets/mittens` @ `1635a8076672d022695213942bda98ce046892a4` | CC BY 4.0 |
| Translate-with-Care (TWC) | `pardissz/Translate-With-Care` @ `84e280cd5ce5e45a4d158d8a7177103294c20c3e` | see the source repository |
| MT-GenEval (contextual) | `amazon-science/machine-translation-gender-eval` @ `c77132ccd248d0b09ac185aebebc94f1051dbc9e` | CC BY-SA 3.0 |
| FLORES-200 devtest (filler) | `https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz` | CC BY-SA 4.0 |
| SSA birth names 1880–2008 | `hadley/data-baby-names` @ `b6525579cf7d2816e77fa885299445d15a09c906`; original data at `https://www.ssa.gov/oact/babynames/limits.html` | US government data |

The cached model outputs and the per-instance scores of the reported run are not included in this public repository (see
the Data availability statement of the article). This repository therefore contains the code and the aggregate results;
regenerating per-instance outputs requires running the model (Section 1 above). The BWB and Urdu components of the
notebook are optional extensions that were not used for the reported results.

## Notes on this public release

The following changes were made when preparing the repository; none affects the method, the code logic or any result.

* Machine-specific absolute paths in the stored notebook outputs and in `Results/pilot/config_used.json` and
  `records/manifest.json` were replaced by `<project>`.
* Default paths in `analysis/*.py` and `figure_sources/common/mplstyle.py` that pointed to the authors' working
  directories now point to locations inside this repository (all remain overridable by the same arguments and
  environment variables).
* The PowerShell scripts originally lived in `_runtime/scripts/`; `env.ps1` now resolves `_runtime/` relative to the
  repository root, `server_check.py` writes its log there, and `run_final_notebook.ps1` copies the two files in `data/`
  into the work directory before running.
* `requirements_lock.txt` was converted from UTF-16 to UTF-8.
* Markdown cells of the notebook mention the authors' full project archive (development notebooks, experiment log,
  response cache); those materials are not part of this repository.

## License

No license has been attached yet. Until one is added, all rights are reserved by the authors; please contact the
corresponding author (Rashid Naseem, PAF-IAST) about reuse.

## Citation

See `CITATION.cff`. Please cite the article when using this code or its results.
