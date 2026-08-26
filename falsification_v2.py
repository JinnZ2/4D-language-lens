"""
Falsification suite for the 4D Language-Aware Lens v2.

The v1 suite (`falsification_tests.py`, archived) is spent: v2 was derived
from those exact seven claims, so re-running them against v2 measures the
patch, not the instrument. This file continues the ledger at C8 with claims
v2 makes that were never tested, using the same method — state the claim the
code implies, then construct the minimal text designed to break it.

Runnable, and reports real output:

    python3 falsification_v2.py

This is a research harness, not a gate. It always exits 0; a FALSIFIED result
is a finding to record in `4D_Lens_Audit_Report.md`, not a build failure.
The behaviors it documents are pinned in `tests/test_known_false_positives.py`
so that fixing one breaks a test loudly instead of passing silently.
"""

from revised_4dlens_v2 import FourDLensV2


def trace_hits(signature, needle):
    """Count trace lines describing a particular rule firing."""
    return sum(1 for line in signature.trace if needle in line)


def analyze(text):
    return FourDLensV2().analyze(text)


# Each claim: (id, what the code implies, falsifying text, check, why it matters)
# `check` returns True if the claim SURVIVES the input.
CLAIMS = [
    (
        "C8",
        "The -tion/-ment/-ance suffix identifies a nominalization, i.e. a "
        "deverbal noun that deletes an agent.",
        "The document was on the desk.",
        lambda s: s.dimension_scores["D1_agency"] == 0.0,
        "'document' is a plain concrete noun. This is C1's failure class "
        "(morphological suffix mistaken for a linguistic category) in D1's "
        "second rule, which the v1 audit never tested. No stoplist guards it.",
    ),
    (
        "C8b",
        "Same claim, ordinary concrete nouns.",
        "I waited at the station near the monument.",
        lambda s: s.dimension_scores["D1_agency"] == 0.0,
        "'station' and 'monument' both score, and both re-score in D3 as "
        "countable reification.",
    ),
    (
        "C9",
        "Restricting the passive rule to -ed plus a curated irregular list, "
        "minus an adjective stoplist, removes predicate-adjective false "
        "positives.",
        "The sky was red.",
        lambda s: s.dimension_scores["D1_agency"] == 0.0,
        "'red'.endswith('ed') is True. A lexical stoplist cannot cover this "
        "class by construction — red/bed/fed/wed/shed are open-ended. This is "
        "the recurrence the audit predicted for C1 under §'Known limitation "
        "ceiling'.",
    ),
    (
        "C10",
        "An explicit dichotomy operator indicates binary framing.",
        "Coffee or tea?",
        lambda s: s.dimension_scores["D3_reality"] == 0.0,
        "Bare 'or' is in EXPLICIT_DICHOTOMY, so ordinary disjunction scores "
        "1.3. C2 tightened the paired-opposition rule but left this operator "
        "list untouched.",
    ),
    (
        "C11",
        "The affect lexicon matches whole words, so each token is counted "
        "under exactly one rule.",
        "Unfortunately, the meeting moved.",
        lambda s: trace_hits(s, "Amplifier/softener") == 0,
        "Lexicon matching is `if word in text_lower` — substring, not word "
        "boundary. 'unfortunately' contains the softener 'unfortunate', so "
        "one token scores as both softener (1.0) and injector (1.2).",
    ),
    (
        "C12",
        "Affect scales with the density of affective language.",
        "excellent excellent excellent excellent",
        lambda s: s.dimension_scores["D2_affect"]
        > analyze("excellent").dimension_scores["D2_affect"],
        "Lexicon hits are presence-based (+1.0 once) while regex hits are "
        "count-based (x len(matches)). Four intensifiers score as one; four "
        "'urgent's score as four. The two halves of D2 use different units.",
    ),
    (
        "C13",
        "The shared claimed-span ledger makes cross-dimension double-counting "
        "visible wherever it occurs.",
        "URGENT!!!",
        lambda s: s.leak_adjustments > 0,
        "'!!!' scores in D2 (emotional injector) and again in D4 "
        "(punctuation mass) from the same span, but _claim() and "
        "_span_overlaps_claimed() are only called in D1 and D3. Half the "
        "dimensions never touch the ledger, so the leak counter reads 0.",
    ),
    (
        "C14",
        "The trace reports every pattern that contributed to a score.",
        "Sadly, tragically, unfortunately, alarmingly.",
        lambda s: trace_hits(s, "Emotional injector") == 4,
        "Previously falsified: findall passes scored len(matches) but traced "
        "matches[0] only, so the trace under-reported what the score charged "
        "for. Fixed — one trace line per scored hit.",
    ),
]


def main():
    print(__doc__.strip().split("\n\n")[0])
    print()
    results = []
    for claim_id, claim, text, check, why in CLAIMS:
        signature = analyze(text)
        survives = bool(check(signature))
        results.append((claim_id, survives))
        print(f"[{'SURVIVES' if survives else 'FALSIFIED'}] {claim_id}")
        print(f"  Claim: {claim}")
        print(f'  Text:  "{text}"')
        scores = signature.dimension_scores
        print(f"  D1={scores['D1_agency']:.2f}  D2={scores['D2_affect']:.2f}  "
              f"D3={scores['D3_reality']:.2f}  D4={scores['D4_iconic']:.2f}  "
              f"MI={signature.manipulation_index}  leak_adj={signature.leak_adjustments}")
        for line in signature.trace:
            print(f"    - {line}")
        print(f"  Why:   {why}")
        print()

    broken = [cid for cid, ok in results if not ok]
    print(f"{len(results) - len(broken)} of {len(results)} claims survive.")
    if broken:
        print("Falsified: " + ", ".join(broken))
        print("Record these in 4D_Lens_Audit_Report.md before changing any scoring.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
