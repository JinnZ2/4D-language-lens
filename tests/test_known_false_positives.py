"""Pinned behavior for the defects recorded in `falsification_v2.py`.

These tests assert what the lens CURRENTLY does, not what it should do. Each
one documents a known false-positive class from the C8-C13 ledger so that the
behavior cannot change silently: fixing a defect breaks the matching test
here, which is the signal to update the audit report and the pinned
regression values together.

Do not "fix" a failure in this file by relaxing the assertion. A failure means
scoring changed; decide whether the new behavior is correct against
`4D_Lens_Audit_Report.md` first.
"""

import unittest

from revised_4dlens_v2 import FourDLensV2


class KnownFalsePositives(unittest.TestCase):
    def setUp(self) -> None:
        self.lens = FourDLensV2()

    def test_c8_suffix_matching_scores_concrete_nouns_as_nominalizations(self) -> None:
        """C8: 'document' is a plain noun; the -ment suffix scores it anyway."""
        signature = self.lens.analyze("The document was on the desk.")
        self.assertGreater(signature.dimension_scores["D1_agency"], 0.0)
        self.assertIn("D1: Agentless nominalization: 'document'", signature.trace)

    def test_c8b_concrete_nouns_score_in_two_dimensions(self) -> None:
        """C8b: 'station'/'monument' score in D1 and again in D3."""
        signature = self.lens.analyze("I waited at the station near the monument.")
        self.assertGreater(signature.dimension_scores["D1_agency"], 0.0)
        self.assertGreater(signature.dimension_scores["D3_reality"], 0.0)

    def test_c9_predicate_adjective_ending_in_ed_scores_as_passive(self) -> None:
        """C9: 'red' ends in 'ed', so the restricted passive rule still fires.

        The C1 stoplist is lexical and cannot close this class by
        construction — see the audit's known-limitation ceiling.
        """
        signature = self.lens.analyze("The sky was red.")
        self.assertEqual(signature.dimension_scores["D1_agency"], 1.5)
        self.assertIn("D1: Passive voice found: 'was red'", signature.trace)

    def test_c10_ordinary_disjunction_scores_as_binary_framing(self) -> None:
        """C10: bare 'or' is in EXPLICIT_DICHOTOMY."""
        signature = self.lens.analyze("Coffee or tea?")
        self.assertEqual(signature.dimension_scores["D3_reality"], 1.3)

    def test_c11_lexicon_substring_match_double_counts_one_token(self) -> None:
        """C11: 'unfortunately' contains the softener 'unfortunate'."""
        signature = self.lens.analyze("Unfortunately, the meeting moved.")
        self.assertIn("D2: Amplifier/softener: 'unfortunate'", signature.trace)
        self.assertIn("D2: Emotional injector: 'Unfortunately'", signature.trace)

    def test_c12_lexicon_hits_are_presence_based_not_count_based(self) -> None:
        """C12: repetition does not raise affect for lexicon terms."""
        once = self.lens.analyze("excellent")
        many = self.lens.analyze("excellent excellent excellent excellent")
        self.assertEqual(
            once.dimension_scores["D2_affect"], many.dimension_scores["D2_affect"]
        )

    def test_c12b_regex_hits_are_count_based(self) -> None:
        """C12: the other half of D2 does scale, so the units disagree."""
        once = self.lens.analyze("urgent")
        many = self.lens.analyze("urgent urgent urgent urgent")
        self.assertGreater(
            many.dimension_scores["D2_affect"], once.dimension_scores["D2_affect"]
        )

    def test_c13_leak_ledger_does_not_cover_d2_and_d4(self) -> None:
        """C13: '!!!' scores in D2 and D4 from one span, uncounted."""
        signature = self.lens.analyze("URGENT!!!")
        self.assertGreater(signature.dimension_scores["D2_affect"], 0.0)
        self.assertGreater(signature.dimension_scores["D4_iconic"], 0.0)
        self.assertEqual(signature.leak_adjustments, 0)


if __name__ == "__main__":
    unittest.main()
