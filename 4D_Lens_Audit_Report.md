# 4D Language-Aware Lens — Audit, Theory-Grounding, and Falsification Report

System treated as an energy pipeline: **text in → 4 parallel filter banks → composite scalar out.**
Everything below maps onto that pipeline: where signal is real, where it leaks across channels, where it's clipped, where it's pure narrative dressed as a number.

```
                    ┌─────────────────────────────────────────┐
                    │              RAW TEXT INPUT              │
                    └───────────────────┬───────────────────────┘
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
        ▼               ▼               ▼               ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
   │   D1    │     │   D2    │     │   D3    │     │   D4    │
   │ Agency  │     │ Affect  │     │ Reality │     │ Iconic  │
   │ regex   │     │ lexicon │     │ regex   │     │ regex   │
   └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘
        │  ⚡ LEAK ⚡    │               │  ⚡ LEAK ⚡    │
        │  (same token  │               │  (same token  │
        │   scores D1    │               │   scores D3    │
        │   AND D3)      │               │   twice via    │
        │               │               │   2 sub-rules) │
        └───────┬───────┴───────┬───────┴───────┬───────┘
                ▼               ▼               ▼
          hand-picked ceiling → hard clip at 1.0 (C7: destroys
          resolution above the ceiling — "URGENT!!! URGENT!!!"
          and "URGENT!!!" score identically once clipped)
                │
                ▼
        composite = 0.4·D1 + 0.3·D2 + 0.2·D3 + 0.1·D4
        (weights are narrative, not fitted — no corpus, no
         regression, no validation against human judgment)
                │
                ▼
        "manipulation_index" ── single scalar, presented with
                                  the authority of a measurement
```

Two structural bottlenecks sit upstream of everything else and explain most of the downstream distortion:

1. **No syntax, only surface strings.** Every dimension is regex-over-tokens. Real agency-routing, real evidentiality, real reification require a parse tree (who did what to whom) that plain regex cannot produce. This is a hard ceiling, not a bug — it bounds how far *any* patch can go.
2. **Constants presented as calibration.** `maxes`, dimension weights, and the 0.4/0.3/0.2/0.1 composite are hand-picked, not fit to data. They read as engineering precision; they are opinion with three decimal places.

---

## 1. Claim ledger — built, then broken, then fixed

Six claims implicit in the v1 code, tested against real sentences, then patched in v2. Full runnable proof: `original_4dlens.py`, `revised_4dlens_v2.py`, `falsification_tests.py`.

| # | Claim (what v1 implies it does) | Falsifying input | v1 result | v2 result |
|---|---|---|---|---|
| C1 | `was/were + word ending in ed/en/d/t` = passive voice | *"The room was pleasant and the coffee was excellent."* | **FALSIFIED** — D1 fires on `silent`, `excellent` (predicate adjectives, not participles) | **Fixed** — D1 = 0 (restricted to `-ed` + curated irregular-participle list, adjective stoplist excludes `excellent/silent/pleasant/reluctant/urgent`…) |
| C2 | `left/right/us/them/or` = binary/ideological framing | *"Turn left, then right, and find us a table for two or three."* | **FALSIFIED** — D3 = 5.2 on pure spatial/pronoun language | **Partially fixed** — D3 = 2.6, requires *both* pair members present or an explicit dichotomy operator. Literal-vs-ideological "left/right" is a genuine semantic ambiguity regex cannot fully resolve — flagged as residual, not solved. |
| C3 | D1 (agency) and D3 (reality construction) are independent dimensions | *"The organization announced the reorganization of the operation."* | **FALSIFIED** — `organization` scores under D1's nominalization rule **and** D3's countable-reification rule from the same token | **Mitigated, not eliminated** — shared span ledger now down-weights (0.3×) and *logs* the re-use (`leak_adjustments` counter) instead of hiding it. Honesty upgrade > independence upgrade — true orthogonality needs disjoint linguistic evidence, not disjoint regexes over the same evidence. |
| C4 | D2 sub-signals (`urgent`, `tragically` = injection; `noted`, `observed` = dampening) simply add | *"It was noted that the situation is tragically urgent."* | **FALSIFIED** — dampening and injection summed, so a text that hedges *and* alarms scores as maximally affective, when a human reads it as affect fighting itself | **Fixed** — D2 = `injection − 0.5·dampening`, net not gross. |
| C5 | manipulation_index ranks intuitively manipulative text above neutral text | neutral: *"The train departs at 6pm."* vs. manipulative: *"Sadly, a regrettable workforce optimization occurred…"* | **Survived** (0.0 vs 0.311) | Survived, unchanged |
| C6 | manipulation_index is robust to nominalization-dense but non-manipulative **bureaucratic/technical** prose | *"The Federation of National Associations (FNA) released its ACTION plan… the implementation, the allocation, and the distribution of resources…"* | **FALSIFIED** — adversarial-neutral text (0.58) outscored the genuinely manipulative layoff euphemism (0.311) | **Fixed for this case** — 0.324 vs 0.343 (manipulative now ranks higher), via a "named actor nearby" discount that down-weights nominalizations with a clear, stated agent |
| C7 | Normalized 0–1 scores stay below the ceiling for realistic dense text | *"Sadly, tragically, unfortunately, alarmingly, urgent, critical, immediate action must be taken!!!"* | **FALSIFIED** — normalized D2 clips at 1.0; a 3× denser version of the same text *also* clips at 1.0, indistinguishable from the original | **Fixed** — saturating curve `score/(score+midpoint)` replaces hard clipping; 3× denser text now resolves as 0.92 vs 0.80, never flatlines |

**Score: 5 of 6 tested claims broke on contact with adversarial input. 4 of 6 fully repaired, 2 structurally improved but bounded by the no-syntax ceiling.** That ratio is itself the most important finding — not any single bug.

---

## 2. Theory grounding — what's borrowed correctly, what's invented

The four-dimension *shape* is not arbitrary — each axis has a real home in linguistics or discourse theory. The failure mode is not "this is nonsense," it's "genuine categories, implemented with too blunt an instrument, then combined with an unvalidated scoring formula that borrows the *rhetoric* of measurement without the *practice* of measurement."

| Dimension | Real theoretical home | What the code gets right | What the code invents / overclaims |
|---|---|---|---|
| **D1 Agency Routing** | Halliday's transitivity system (Systemic Functional Linguistics) — who is Actor, who is Goal, who is deleted; Critical Discourse Analysis (Fairclough, van Dijk) on agent-deletion in institutional text | Passive voice and nominalization genuinely are the two main agent-deletion strategies studied in CDA | The folk-linguistic move of pattern-matching "was + X" *is exactly what linguist Geoffrey Pullum has spent years publicly debunking* (the "passive voice panic" — commentators, including political journalists, routinely mislabel predicate adjectives and even active sentences as "passive"). v1 reproduced that exact error mechanically. |
| **D2 Affective Impedance** | Appraisal Theory (Martin & White) — specifically the *Graduation* subsystem (force/intensity of evaluative language); sentiment lexicons (LIWC, NRC Emotion Lexicon, VADER) | Injection vs. dampening is a real distinction — Appraisal Theory separates *raising* and *lowering* graduation | "Impedance" implies a directional, resistance-like electrical property; the code computes an unweighted lexical count. No account of negation ("not urgent"), sarcasm, or intensifier stacking ("very very urgent") the way VADER's actual intensity modifiers do. |
| **D3 Reality Construction** | Nominalization/reification critique in CDA (Fairclough; Billig's argument that nominalization does the same agency-hiding work as passive voice); Framing Theory (Lakoff, Entman); Evidentiality as a grammatical category (Aikhenvald) | Reification-via-nominalization is real and well-studied; hedging language ("suggests," "may," "could") is a real epistemic phenomenon | "Evidentiality" is a specific, often *grammaticalized* category (some languages mark it obligatorily — Quechua, Turkish); English modal hedges are closer to epistemic *stance-taking*/politeness mitigation (Brown & Levinson) than to evidentiality proper. The binary-compressor rule conflates genuine rhetorical dichotomy (Lakoff's framing) with incidental co-occurrence of common words — this is the C2 failure. |
| **D4 Iconic/Graphic Mass** | Multimodal discourse analysis (Kress & van Leeuwen) — typography and layout as meaning-bearing; eye-tracking research on ALL-CAPS legibility/salience (Larson et al.); emoji pragmatics (Cramer et al.) | Visual salience genuinely modulates how text is processed and its perceived force ("shouting" convention for caps is real and studied) | Acronyms and all-caps words were double-counted in v1 (same token, two regexes) — fixed in v2 via shared-span dedup. |
| **"Energy estimate"** | Surprisal theory (Hale, Levy) and reading-time/processing-cost research — passives *do* measurably take longer to process (Ferreira 2003) | The intuition that certain constructions cost more to process is real and measurable (self-paced reading, eye-tracking corpora like Provo/Dundee) | The code's `energy_estimate` is `sum(scores) * 0.1` — a linear rescale of unrelated pattern counts, not calibrated against any reading-time data. It is a **metaphor wearing a number's clothes.** Fixable only by validating against real psycholinguistic norms, not just renaming the variable. **Resolved by removal** — the field is gone from `VectorSignature` rather than renamed; reintroducing it requires the validation described here. |
| **manipulation_index composite** | Modern manipulation/propaganda detection (Da San Martino et al. 2019 SemEval propaganda-technique corpus; 18 labeled techniques, transformer classifiers trained and scored against held-out human annotation) | The instinct that manipulation is multi-dimensional, not a single "lie detector" bit, is correct and matches the field | Field standard is **learned weights fit to labeled data with reported precision/recall**, not hand-set constants. `0.4/0.3/0.2/0.1` has exactly the epistemic status of "felt about right." |

**One-line summary of the audit:** the four axes are a legitimate decomposition of manipulative language; the instrument measuring them is a first-draft heuristic wearing the presentation layer of a validated psychometric tool. That gap is closeable — see §4 — but is not yet closed.

---

## 3. Opportunities and use cases — leverage vs. false-confidence zones

Mapped by where the *current* precision level (regex + lexicon, no parse tree, no calibration) is actually sufficient vs. where it would launder false confidence into a decision that matters.

**High-leverage now (low stakes, human stays in the loop, trace output is the product, not the score):**
- Writing-assistant flag for your *own* drafts — "this paragraph nominalization-hides the actor, want to name them?" — trace-as-nudge, not trace-as-verdict.
- Corporate-communications style audit — screening internal memos/PR drafts for agent-deletion and euphemism density before publication, as a first-pass flag for a human editor.
- Media-literacy teaching tool — showing students *why* "mistakes were made" reads as evasive, with the regex trace as the pedagogical artifact (the explanation is the value, not the composite score).
- LLM-output auditing — batch-scanning model outputs for hedge-stacking, euphemism, or agent-deletion patterns as one signal among several in a QA pipeline, not a pass/fail gate.

**Requires the v2 fixes minimum, still human-reviewed (medium stakes):**
- Political-speech / press-release comparative analysis across time (tracking a spokesperson's agent-deletion rate over a news cycle) — directional trend tracking is more defensible than any single-document score.
- Forensic-linguistics-adjacent triage — flagging documents worth a trained analyst's attention, never as evidence itself.

**Do not deploy at current fidelity (high stakes, irreversible, or adversarial-input-facing):**
- Automated content moderation / de-platforming decisions — C6 showed *bureaucratic-but-innocent* text can outscore genuine manipulation; false positives here have real consequences.
- Hiring/vendor-trust scoring, insurance/legal-risk scoring, or anything feeding an automated gate — an unvalidated composite index with no reported precision/recall should not touch a decision with consequences for a specific person.
- Any public-facing "manipulation score" badge — a single decimal invites exactly the false authority the audit above warns against.

**Genuinely new development directions (leverage points, cheapest fix first):**
1. Swap regex passive/agency detection for a real dependency parse (spaCy `en_core_web_sm` gives POS + dependency labels in a few lines) — kills the entire C1-class failure mode at the root instead of patching a stoplist.
2. Build the labeled corpus (`calibration_corpus.py` scaffold already staged) — 300+ examples, 3+ independent raters, stratified across genre (corporate/political/advertising/news/casual) — then fit composite weights by regression instead of hand-picking them, and report R² + per-dimension residuals.
3. Validate against an existing benchmark instead of inventing one from scratch — the SemEval-2019/2020 propaganda-technique corpus already has human-labeled examples across categories that overlap D1–D3 closely (loaded language, name-calling, doubt, flag-waving, black-and-white fallacy — that last one is literally D3's binary-compression target, already correctly operationalized by domain experts).
4. Report a confusion matrix, not just a trace — once labeled data exists, publish precision/recall/F1 per dimension, so users know the tool's actual error rate instead of trusting an unvalidated trace.
5. Multi-lingual extension is a real opportunity *specifically because* evidentiality is grammaticalized in many non-English languages (Quechua, Turkish, Tibetic languages) — D3 could become a genuinely stronger instrument outside English, where the phenomenon it's trying to detect is structural rather than inferred.

---

## 4. What actually changed (v1 → v2), and what didn't

**Fixed:** predicate-adjective false positives in passive detection (C1); D2 additive-vs-net affect (C4); ceiling clipping destroying resolution on dense text (C7); construct-validity failure on bureaucratic-neutral vs. genuinely manipulative text, for the tested case (C6).

**Improved but structurally bounded — flagged, not hidden:** binary-compression semantic ambiguity (C2 — "turn left" vs. "the political left" cannot be disambiguated by co-occurrence alone; needs sense disambiguation or context window, not just a stricter regex); cross-dimension independence (C3 — the shared-span ledger makes the leak *visible and down-weighted* instead of silent, but true orthogonality requires each dimension to draw on genuinely distinct evidence, which regex-over-tokens cannot guarantee by construction).

**Not attempted here, named as the real next step:** empirical calibration of weights and ceilings (scaffold only, `calibration_corpus.py`); syntactic parsing to replace regex heuristics at the root; benchmark validation against an existing labeled propaganda-technique corpus.

---

## Files delivered

- `original_4dlens.py` — unmodified input, for reference/reproducibility. **Not present in this repository** — it was described in the audit but was never part of the supplied source set. Every v1 result in the ledger above is transcribed from the original run, not reproducible here.
- `falsification_tests.py` — the six-claim adversarial test suite, runnable at the time of the audit, output above is real (not illustrative). **Archived**: it imports `original_4dlens.py`, so it cannot run in this repository and exits with an explanation instead. It is kept verbatim as the record of which input broke which claim. The runnable check against the current implementation is `tests/test_v2_regressions.py`.
- `revised_4dlens_v2.py` — patched implementation with inline changelog tying every change to the claim it fixes
- `calibration_corpus.py` — scaffold for the actual next step (empirical weight-fitting); intentionally raises `NotImplementedError` until real labeled data exists, so it can't be mistaken for a finished validation
