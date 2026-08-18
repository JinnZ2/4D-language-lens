# 4D Language-Aware Lens (v2)

Regex/lexicon heuristic that scores text across four dimensions of linguistic manipulation. No syntax parser, no calibrated weights, no validation corpus (yet) — see `4D_Lens_Audit_Report.md` for the full audit. This README is the operating manual: what it's for, how to read its output, and where it must not go.

**Live demo:** https://4dlanglens-qagmyjff.manus.space/ — read the not-to-be-used flags below before drawing any conclusion from a score it produces.

```
text → [D1 agency] [D2 affect] [D3 reality] [D4 iconic] → composite scalar
        └─ each dimension is pattern-matching, not comprehension ─┘
```

---

## Install / run

No external dependencies — Python standard library only, 3.10+.

### Command line

```bash
python3 fourdlens_cli.py "Mistakes were made during the operational realignment."
```

Or install once to get a `4dlens` command on your PATH:

```bash
pip install -e .
4dlens "Mistakes were made during the operational realignment."
```

The output puts the trace first, on purpose — the patterns that fired are the
finding, and the composite scalar is printed last with the one sentence that
describes what it actually means:

```
  WHAT FIRED  — read this before the number

  D1  agency routing         2 patterns
      · Passive voice found: 'were made'
      · Agentless nominalization: 'realignment'

  D3  reality construction   1 pattern
      · Countable reification: 'realignment'

  nothing fired in: D2 affective impedance, D4 iconic mass

  RAW SCORES   D1 2.50   D2 0.00   D3 1.20   D4 0.00

  manipulation_index  0.203
  Not a probability, not a percentile, not validated against ground truth.
  It means only: more of these hand-picked patterns fired, weighted by
  hand-picked constants.
```

| Invocation | What it does |
|---|---|
| `4dlens -f draft.md` | analyze a file; repeatable, and `-` means stdin |
| `cat draft.md \| 4dlens` | read from stdin |
| `4dlens --demo` | analyze the audited example set from the falsification ledger |
| `4dlens --json` | JSON Lines, one object per input, for pipelines |
| `4dlens --no-index` | trace and raw scores only, composite scalar suppressed |

**The command never exits non-zero on the basis of a score.** A non-zero exit
means a usage or I/O error. This is deliberate and tested: an exit code is a
gate, and the flags below explain why this instrument must not be one.

### Tests

```bash
python3 -m unittest discover -s tests -v     # v2 regressions + CLI contract
python3 revised_4dlens_v2.py                 # the built-in example set, scores only
```

### Python API

```python
from revised_4dlens_v2 import FourDLensV2

lens = FourDLensV2()
sig = lens.analyze("Mistakes were made during the operational realignment.")

sig.dimension_scores      # {'D1_agency': .., 'D2_affect': .., 'D3_reality': .., 'D4_iconic': ..}
sig.normalized_scores     # same, saturating-curve normalized (0-1, never hard-clips)
sig.manipulation_index    # single scalar composite — READ THE WARNINGS BELOW FIRST
sig.trace                 # human-readable list of every pattern that fired — THIS is the product
sig.leak_adjustments      # count of cross-dimension double-count corrections applied
```

**Always read `sig.trace` before `sig.manipulation_index`.** The trace shows exactly what fired and why; the scalar hides it. Every use case below assumes a human reads the trace.

---

## ✅ Cleared uses

Conditions common to all of these: a human reviews the trace, no automated action is gated solely on the scalar, and being wrong costs nothing worse than "re-read the paragraph."

| Use case | What to actually look at |
|---|---|
| Auditing your own draft (email, memo, PR statement) before sending | D1 trace — did you accidentally passive-voice/nominalize away your own responsibility? |
| Media-literacy teaching — showing *why* "mistakes were made" reads as evasive | The trace as the lesson artifact, not the score |
| First-pass triage flag in an editorial workflow (a human still edits) | Which dimension fired, not the composite |
| Tracking a spokesperson's agent-deletion rate across a news cycle (directional trend, not single-document verdict) | Trend line across many documents, never one document's score in isolation |
| One signal among several in an LLM-output QA pipeline (hedge-stacking, euphemism density) | Flag for review, not pass/fail gate |

---

## 🚫 Not-to-be-used flags

Each flag names the specific finding from the audit that makes this use unsafe **today**, not a generic disclaimer.

**🚫 Content moderation / de-platforming decisions.**
C6 (audit report) showed nominalization-dense but entirely innocent bureaucratic text can outscore a genuine manipulative euphemism. A false positive here removes someone's speech on a false signal.

**🚫 Any automated gate — hiring, vendor trust, insurance/legal risk scoring, credit-adjacent decisions.**
`manipulation_index` has no reported precision/recall, no ROC curve, no labeled validation corpus (`calibration_corpus.py` is an empty scaffold, not data). An unvalidated score should never touch a decision with consequences for a specific, named person.

**🚫 Public-facing "manipulation score" badges on third-party text (news outlets, political speech, a person's social posts).**
Composite weights (0.4/0.3/0.2/0.1) are hand-picked, not fit to data — see audit §2. Publishing them as a score on someone else's words launders opinion as measurement.

**🚫 Detecting genuine ideological/political binary framing.**
C2: the binary-compressor rule cannot distinguish "turn left, then right" from "the political left." It requires both pair members present or an explicit dichotomy operator, which reduces false positives but does not resolve the underlying sense ambiguity — this needs real word-sense disambiguation, not a stricter regex.

**🚫 Cross-document or cross-author comparison claiming statistical significance.**
No inter-rater reliability has been established for what "human-intuitive manipulation" even means here — `calibration_corpus.py` explicitly requires 3+ independent human raters and a reported Krippendorff's alpha before any comparison claim is defensible.

**🚫 Any use where the four dimensions are treated as independent/orthogonal measurements.**
C3: a single token (e.g. "organization") can and does score under two dimensions from the same lexical evidence. v2 logs this (`leak_adjustments`) and down-weights it, but does not eliminate it — regex-over-tokens cannot guarantee disjoint evidence by construction. Treat the four scores as correlated, not independent axes.

**🚫 Non-English text, or English text from a domain outside the ones spot-checked here (corporate/political/casual).**
Nothing here has been tested cross-genre or cross-language. The lexicons (`POSITIVE_AMPLIFIERS`, `IRREGULAR_PARTICIPLES`, etc.) are hand-typed English word lists.

**🚫 As evidence in any adversarial, legal, journalistic, or forensic-linguistics context.**
Flag documents for a trained analyst's attention only. The instrument's output is not admissible-quality evidence — it's a first-pass filter with known, documented failure modes.

---

## Reading the scalar, if you must

`manipulation_index` is not a probability, not a percentile, and not validated against any ground truth. Treat it only as: *"higher means more of these specific hand-picked patterns fired, weighted by hand-picked constants."* That sentence is the actual semantics of the number — anything beyond it is borrowed authority. If a decision needs more than that sentence can support, this tool is the wrong instrument for that decision.

---

## Known limitation ceiling (won't be fixed by patching regex further)

No dependency parse → no real syntactic passive/agency detection, only lexical approximation. This is why C1-class bugs (predicate adjectives mistaken for participles) can recur on new inputs even after the v2 patch — the stoplist approach caps the failure rate, it doesn't remove the mechanism. Closing this requires swapping the regex layer for a real parser (e.g. spaCy dependency labels) — see audit report §3, item 1.

## Files in this repo

- `revised_4dlens_v2.py` — the current implementation; import `FourDLensV2` from this module.
- `fourdlens_cli.py` — the `4dlens` command; trace-first reporting, JSON Lines output, no score-dependent exit codes.
- `tests/test_v2_regressions.py` — standard-library regression checks for the available v2 implementation.
- `tests/test_cli.py` — CLI contract checks: the full trace is reported, the scalar is suppressible, and no score can change the exit code.
- `falsification_tests.py` — archived v1 falsification harness. It targets `original_4dlens.py`, which the audit describes but which was not part of the supplied source set, so it does not run; it exits with an explanation pointing at the v2 regression suite. Its recorded results are transcribed in the audit's claim ledger.
- `calibration_corpus.py` — scaffold for empirical weight fitting; intentionally raises `NotImplementedError` until real labeled data exists.
- `4D_Lens_Audit_Report.md` — full audit: theory grounding, claim-by-claim before/after, and development opportunities.
- `pyproject.toml` — project metadata and the `4dlens` entry point; Python 3.10+, no runtime dependencies.
- `conftest.py` — puts the repo root on `sys.path` so `pytest` works as well as the stdlib runner.
