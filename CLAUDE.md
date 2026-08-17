# CLAUDE.md

Guidance for Claude Code when working in this repository.

**Live demo:** https://4dlanglens-qagmyjff.manus.space/ — hosted interactive version of the lens. It is a separate deployment; nothing in this repo builds or deploys it, so changes here do not automatically reach it.

## What this project is

A regex-and-lexicon heuristic (`FourDLensV2`) that scores English text across four dimensions of rhetorical/manipulative patterning — D1 agency routing, D2 affective impedance, D3 reality construction, D4 iconic mass — and combines them into a single `manipulation_index`.

It is **not** a parser, a classifier, or a validated instrument. There is no dependency parse, no fitted weights, and no labeled validation corpus. `4D_Lens_Audit_Report.md` is the authoritative account of what the tool does and does not support; `README.md` is the operating manual, including an explicit list of cleared and prohibited uses.

## Commands

Python 3.10+, standard library only. No install step, no external dependencies.

```bash
python3 revised_4dlens_v2.py                 # run the built-in example set
python3 -m unittest discover -s tests -v     # run the v2 regression suite (6 tests)
```

`falsification_tests.py` is an archived v1 harness. It imports `original_4dlens.py`, which is not in this repo, so it does not run — leave it as a historical artifact rather than "fixing" the import. The runnable check is `tests/test_v2_regressions.py`.

## Layout

- `revised_4dlens_v2.py` — the whole implementation. The module docstring carries a change log mapping every v2 change to the falsified v1 claim (C1–C7) that motivated it. Keep that mapping current when changing scoring behavior.
- `tests/test_v2_regressions.py` — regression checks pinned to the audited fixes.
- `calibration_corpus.py` — scaffold for empirical weight fitting. `fit_weights()` raises `NotImplementedError` on purpose, so it cannot be mistaken for completed validation. Do not implement it against the placeholder examples; it needs real labeled data first.
- `4D_Lens_Audit_Report.md` — falsification ledger, theory grounding, and the prioritized list of next steps.
- `README.md` — operating manual and use-case boundaries.

## Working conventions

**The trace is the product; the scalar is not.** `sig.trace` explains exactly which pattern fired and why. `manipulation_index` is a weighted sum of hand-picked constants with no reported precision or recall. Any new feature should make the trace more legible rather than make the number look more authoritative.

**Do not strengthen claims the audit has bounded.** The report records which fixes are complete (C1, C4, C6, C7) and which are structurally limited by the absence of a syntax parse (C2 sense ambiguity, C3 cross-dimension leakage). Do not describe a bounded fix as solved, and do not remove the caveats in `README.md` or the audit report as part of an unrelated change.

**Do not retune the composite weights (0.4/0.3/0.2/0.1) or the normalization midpoints without data.** They are explicitly labeled as unfitted. Changing them by feel makes the score worse in the one way the audit calls out most sharply — added false confidence. The legitimate path is the `calibration_corpus.py` route: labeled corpus first, regression fit second, reported residuals third.

**Regression tests assert exact numeric values and exact trace strings** (e.g. `D2` netting to `2.0`, and the literal `"D2: net = injection(2.4) - 0.5*dampening(0.8) = 2.0"` trace line). Any change to scoring or trace formatting will break them. When that happens, decide whether the new behavior is actually correct against the audit before updating the expected values — a test breaking is the intended alarm, not noise.

**Cross-dimension leakage is tracked, not eliminated.** Scoring passes share a claimed-span ledger; a span already claimed by an earlier dimension scores at 0.3× and increments `leak_adjustments`. New patterns that consume text spans should go through `_span_overlaps_claimed()` / `_claim()` so the leak stays visible instead of silently double-counting.

**Scope is English only.** The lexicons (`IRREGULAR_PARTICIPLES`, `ADJECTIVE_STOPLIST`, `POSITIVE_AMPLIFIERS`, …) are hand-typed English word lists, spot-checked only on corporate, political, and casual registers. Nothing here is tested cross-genre or cross-language.

## Highest-value directions

From audit §3, cheapest first: replace the regex passive/agency detection with a real dependency parse (kills the C1 failure class at the root); build the labeled corpus and fit the weights; validate against the SemEval propaganda-technique corpus rather than inventing a benchmark; report a confusion matrix per dimension.
