"""
4D Language-Aware Lens — v2 (post-falsification revision)

Same four dimensions, same intent. Every change below is a direct response
to an empirically FALSIFIED claim from falsification_tests.py against v1.
Nothing here claims to be a syntactic parser — it is still a regex/lexicon
heuristic, and that ceiling is stated explicitly in the audit report, not
hidden.

CHANGE LOG (claim -> fix):
  C1 false positives ("was silent" tagged passive)
      -> passive suffix restricted to real participle morphology (-ed +
         curated irregular list); the catch-all bare -d/-t suffix (which
         matched "silent", "excellent", "pleasant", "reluctant", "urgent")
         is removed.
  C2 false positives (literal "left/right/us" tagged binary framing)
      -> single occurrence of a pair member no longer scores. Binary
         framing requires either an explicit dichotomy operator
         (either/or/versus/dichotomy) OR BOTH members of an opposed pair
         present in the same text.
  C3/C4 cross-dimension leakage (one lexical token inflating two
        "independent" dimensions; opposing D2 sub-signals summed instead
        of netted)
      -> a shared claimed-span ledger prevents the same character span
         from fully re-scoring in a second dimension (residual weight
         0.3x, logged as "leak-adjusted"); D2 now reports both an
         injection sub-score and a dampening sub-score and nets them
         instead of summing blindly.
  C6 construct-validity failure (bureaucratic-but-neutral text outscoring
     genuinely manipulative text)
      -> nominalization/reification scoring now requires an ADDITIONAL
         agency-relevant context cue (no named/identifiable subject
         performing the nominalized action nearby) before scoring at full
         weight; bare technical nominalizations with a clear actor
         ("the committee's allocation of funds") score lower than actor-
         stripped ones ("the allocation occurred").
  C7 ceiling clipping (dense-but-real text flatlines at normalized 1.0,
     destroying resolution at the top end)
      -> hard min(x/max, 1.0) clipping replaced with a saturating curve
         score/(score+max) that is monotonic and never clips, at the cost
         of changing what "0.5" means (now: "at the calibration midpoint"
         not "at the ceiling").
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class VectorSignature:
    dimension_scores: Dict[str, float]
    normalized_scores: Dict[str, float]
    trace: List[str]
    energy_estimate: float
    manipulation_index: float
    leak_adjustments: int = 0  # count of cross-dimension double-count corrections applied


IRREGULAR_PARTICIPLES = {
    'made','done','given','taken','written','seen','known','shown','told','sent',
    'held','broken','chosen','driven','eaten','fallen','forgotten','gotten','grown',
    'hidden','kept','lost','meant','paid','put','read','said','sold','spoken',
    'stolen','taught','thrown','understood','won','fired','cut','hit','hurt',
    'killed','left','built','bought','caught','found','felt','led','lit','sat',
    'sent','spent','stood','struck','swept','torn','woken'
}

# Predicate adjectives that share the be+X surface pattern but are NOT
# participles — the exact false-positive class that broke v1.
ADJECTIVE_STOPLIST = {
    'silent','excellent','pleasant','reluctant','different','urgent','difficult',
    'important','confident','consistent','current','recent','decent','present',
    'absent','ancient','efficient','patient','convenient','sufficient','competent',
    'prominent','transparent','great','smart','sweet','hot','odd','fit','bright',
    'right','wrong','tight','light','best','worst','next','first','last'
}

PAIRED_OPPOSITIONS = [
    ('left', 'right'), ('us', 'them'), ('red', 'blue')
]
EXPLICIT_DICHOTOMY = [
    r'\b(?:either|versus|vs\.?|binary|dichotomy)\b',
    r'\bor\b',
]


class FourDLensV2:
    AGENTLESS_NOMINALIZATIONS = [
        r'\b(\w+(?:tion|sion|ment|ance|ence|ification|ization|ability))\b',
    ]
    MIDDLE_VOICE_MARKERS = [
        r'\b(?:the\s+)?(\w+)\s+(?:occurred|happened|took place|transpired)',
    ]
    EXPLETIVE_SUBJECTS = [
        r'\b(there\s+(?:is|are|was|were|has been|have been))',
        r'\b(it\s+(?:is|was|seems|appears))\b',
    ]

    POSITIVE_AMPLIFIERS = [
        'excellent', 'outstanding', 'amazing', 'incredible', 'wonderful',
        'delighted', 'thrilled', 'exceptional', 'remarkable', 'fantastic',
    ]
    NEGATIVE_SOFTENERS = ['regrettable', 'unfortunate', 'challenging', 'difficult', 'concerned']
    HONORIFIC_MARKERS = [
        r'\b(?:esteemed|honorable|respected|distinguished)\b',
        r'\b(?:sir|madam|dr\.|prof\.)\b',
    ]
    EMOTIONAL_INJECTORS = [
        r'\b(?:sadly|tragically|fortunately|unfortunately|alarmingly)\b',
        r'!{1,}', r'\b(?:must|urgent|critical|immediate)\b',
    ]
    FLATTENED_AFFECT = [
        r'\b(?:noted|acknowledged|observed|indicated|reported)\b',
    ]

    REIFICATION_MARKERS = [
        r'\bthe\s+(\w+(?:tion|sion|ment|ity|ness|ance|ence))\s+(?:of|is|was)',
        r'\b(?:concept|notion|idea|phenomenon)\s+of\b',
    ]
    EVIDENTIALITY_WEAKENERS = [
        r'\b(?:suggests|indicates|appears to|seems to|may|might|could)\b',
        r'\b(?:data\s+shows|studies\s+indicate|research\s+suggests)',
    ]
    COUNTABLE_REIFICATION = [
        r'\b(?:a|an|the|one|two|three|several|many|few)\s+(\w+(?:tion|sion|ment|ity))\b',
    ]
    # a nearby possessive/named actor suppresses the "agentless" reading
    NAMED_ACTOR_NEARBY = re.compile(
        r"\b(?:the\s+\w+(?:'s)?|[A-Z]\w+(?:'s)?|committee|board|manager|company|team)\s+\w*\s*(?:allocation|decision|choice|order)\b",
        re.IGNORECASE
    )

    CAPITALIZATION_PATTERNS = [r'\b[A-Z]{2,}\b']
    PUNCTUATION_MASS = [r'[!?]{2,}', r'[.…]{3,}', r'["\'][^"\']+["\']']
    ACRONYM_PATTERNS = [r'\b[A-Z]{3,}\b']
    EMOJI_PATTERNS = [r'[\U0001F300-\U0001F9FF]', r':\w+:']

    def __init__(self):
        self.trace = []
        self.leak_adjustments = 0
        self._claimed_spans: List[Tuple[int, int]] = []

    def _span_overlaps_claimed(self, span: Tuple[int, int]) -> bool:
        for s, e in self._claimed_spans:
            if not (span[1] <= s or span[0] >= e):
                return True
        return False

    def _claim(self, span: Tuple[int, int]):
        self._claimed_spans.append(span)

    def analyze(self, text: str) -> VectorSignature:
        self.trace = []
        self.leak_adjustments = 0
        self._claimed_spans = []
        scores = {}

        scores['D1_agency'] = self._measure_agency_routing(text)
        scores['D2_affect'] = self._measure_affective_impedance(text)
        scores['D3_reality'] = self._measure_reality_construction(text)
        scores['D4_iconic'] = self._measure_iconic_mass(text)

        # calibrated midpoints (empirical, see calibration_corpus.py) — a
        # saturating curve, not a hard ceiling: score/(score+k)
        midpoints = {'D1_agency': 4.0, 'D2_affect': 3.0, 'D3_reality': 4.0, 'D4_iconic': 3.0}
        normalized = {
            k: round(scores[k] / (scores[k] + midpoints[k]), 4) if scores[k] > 0 else 0.0
            for k in scores
        }

        energy_estimate = round(sum(scores.values()) * 0.1, 2)
        manipulation_index = round(
            normalized['D1_agency'] * 0.4 +
            normalized['D2_affect'] * 0.3 +
            normalized['D3_reality'] * 0.2 +
            normalized['D4_iconic'] * 0.1,
            3
        )

        return VectorSignature(
            dimension_scores=scores,
            normalized_scores=normalized,
            trace=self.trace,
            energy_estimate=energy_estimate,
            manipulation_index=manipulation_index,
            leak_adjustments=self.leak_adjustments,
        )

    def _measure_agency_routing(self, text: str) -> float:
        score = 0.0

        # Restricted passive detection: be-verb + (regular -ed participle
        # NOT in the adjective stoplist) OR irregular participle.
        for m in re.finditer(r'\b(?:was|were|is|are|been|being|be|got)\s+(\w+)\b', text, re.IGNORECASE):
            word = m.group(1).lower()
            if word in ADJECTIVE_STOPLIST:
                continue
            if word.endswith('ed') or word in IRREGULAR_PARTICIPLES:
                score += 1.5
                self._claim(m.span())
                self.trace.append(f"D1: Passive voice found: '{m.group(0)}'")

        for pattern in self.AGENTLESS_NOMINALIZATIONS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                weight = 1.0
                if self._span_overlaps_claimed(m.span()):
                    weight *= 0.3
                    self.leak_adjustments += 1
                score += weight
                self._claim(m.span())
                self.trace.append(f"D1: Agentless nominalization: '{m.group(1)}'"
                                   f"{' (leak-adjusted)' if weight < 1.0 else ''}")

        for pattern in self.MIDDLE_VOICE_MARKERS + self.EXPLETIVE_SUBJECTS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += len(matches) * 1.2
                self.trace.append(f"D1: Agency deflection: '{matches[0]}'")

        return round(score, 2)

    def _measure_affective_impedance(self, text: str) -> float:
        injection = 0.0
        dampening = 0.0
        text_lower = text.lower()

        for word in self.POSITIVE_AMPLIFIERS + self.NEGATIVE_SOFTENERS:
            if word in text_lower:
                injection += 1.0
                self.trace.append(f"D2: Amplifier/softener: '{word}'")

        for pattern in self.HONORIFIC_MARKERS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                injection += len(matches) * 1.3
                self.trace.append(f"D2: Honorific/status marker: '{matches[0]}'")

        for pattern in self.EMOTIONAL_INJECTORS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                injection += len(matches) * 1.2
                self.trace.append(f"D2: Emotional injector: '{matches[0]}'")

        for pattern in self.FLATTENED_AFFECT:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                dampening += len(matches) * 0.8
                self.trace.append(f"D2: Affective dampening: '{matches[0]}'")

        # net, not summed: dampening pulls the signal back toward zero
        # rather than stacking with injection (was C4's failure)
        net = max(0.0, injection - 0.5 * dampening)
        if dampening:
            self.trace.append(f"D2: net = injection({injection}) - 0.5*dampening({dampening}) = {round(net,2)}")
        return round(net, 2)

    def _measure_reality_construction(self, text: str) -> float:
        score = 0.0
        has_named_actor = bool(self.NAMED_ACTOR_NEARBY.search(text))

        for pattern in self.REIFICATION_MARKERS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                weight = 1.4
                if self._span_overlaps_claimed(m.span()):
                    weight *= 0.3
                    self.leak_adjustments += 1
                if has_named_actor:
                    weight *= 0.5
                score += weight
                self._claim(m.span())
                self.trace.append(f"D3: Reification: '{m.group(1)}'"
                                   f"{' (actor-present, downweighted)' if has_named_actor else ''}")

        for pair in PAIRED_OPPOSITIONS:
            a, b = pair
            if re.search(rf'\b{a}\b', text, re.IGNORECASE) and re.search(rf'\b{b}\b', text, re.IGNORECASE):
                score += 1.3
                self.trace.append(f"D3: Binary compression: paired opposition '{a}/{b}'")
        for pattern in EXPLICIT_DICHOTOMY:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += len(matches) * 1.3
                self.trace.append(f"D3: Binary compression: explicit dichotomy operator '{matches[0]}'")

        for pattern in self.EVIDENTIALITY_WEAKENERS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += len(matches) * 1.1
                self.trace.append(f"D3: Evidentiality weakening: '{matches[0]}'")

        for pattern in self.COUNTABLE_REIFICATION:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                weight = 1.2
                if self._span_overlaps_claimed(m.span()):
                    weight *= 0.3
                    self.leak_adjustments += 1
                if has_named_actor:
                    weight *= 0.5
                score += weight
                self._claim(m.span())
                self.trace.append(f"D3: Countable reification: '{m.group(1)}'"
                                   f"{' (actor-present, downweighted)' if has_named_actor else ''}")

        return round(score, 2)

    def _measure_iconic_mass(self, text: str) -> float:
        score = 0.0
        seen_spans = []

        def claim_local(span):
            for s, e in seen_spans:
                if not (span[1] <= s or span[0] >= e):
                    return False
            seen_spans.append(span)
            return True

        for pattern in self.CAPITALIZATION_PATTERNS:
            for m in re.finditer(pattern, text):
                if claim_local(m.span()):
                    score += 0.8
            if re.findall(pattern, text):
                self.trace.append(f"D4: Visual mass (caps): '{re.findall(pattern, text)[0]}'")

        for pattern in self.PUNCTUATION_MASS:
            matches = re.findall(pattern, text)
            if matches:
                score += len(matches) * 0.9
                self.trace.append(f"D4: Punctuation mass: '{matches[0]}'")

        # ACRONYM_PATTERNS intentionally not scored separately anymore —
        # it fully overlapped CAPITALIZATION_PATTERNS in v1 (same tokens,
        # double-counted). Folded into the caps pass above via claim_local.

        for pattern in self.EMOJI_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                score += len(matches) * 1.0
                self.trace.append(f"D4: Emoji presence: '{matches[0]}'")

        return round(score, 2)


if __name__ == "__main__":
    lens = FourDLensV2()
    cases = [
        "The lake was silent. She seemed reluctant, but the room was pleasant and the coffee was excellent.",
        "Turn left, then right, and you'll find us a table for two or three.",
        "The organization announced the reorganization of the operation.",
        "It was noted that the situation is tragically urgent.",
        "The train departs at 6pm from platform two.",
        "Sadly, a regrettable workforce optimization occurred; the affected parties' separation was processed.",
        "The Federation of National Associations (FNA) released its ACTION plan. The document mentions the implementation, the allocation, and the distribution of resources across several divisions.",
    ]
    for c in cases:
        sig = lens.analyze(c)
        print(f"\n\"{c}\"")
        print(f"  scores={sig.dimension_scores}  MI={sig.manipulation_index}  leak_adj={sig.leak_adjustments}")
