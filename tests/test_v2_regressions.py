"""Regression tests for the available 4D Language-Aware Lens v2 implementation.

The tests cover the bounded fixes recorded in ``4D_Lens_Audit_Report.md``.
They validate implementation behavior, not the validity of the underlying
heuristic or its uncalibrated composite score.
"""

import unittest

from revised_4dlens_v2 import FourDLensV2


class FourDLensV2RegressionTests(unittest.TestCase):
    """Verify specific behaviors retained from the post-falsification revision."""

    def setUp(self) -> None:
        self.lens = FourDLensV2()

    def test_predicate_adjectives_do_not_score_as_passive_voice(self) -> None:
        signature = self.lens.analyze(
            "The lake was silent. She seemed reluctant, but the room was "
            "pleasant and the coffee was excellent."
        )
        self.assertEqual(signature.dimension_scores["D1_agency"], 0.0)

    def test_single_member_of_an_opposition_does_not_trigger_binary_rule(self) -> None:
        signature = self.lens.analyze("Turn left at the next intersection.")
        self.assertEqual(signature.dimension_scores["D3_reality"], 0.0)

    def test_affect_injection_and_dampening_are_netted(self) -> None:
        signature = self.lens.analyze(
            "It was noted that the situation is tragically urgent."
        )
        self.assertEqual(signature.dimension_scores["D2_affect"], 2.0)
        self.assertIn("D2: net = injection(2.4) - 0.5*dampening(0.8) = 2.0", signature.trace)

    def test_manipulative_example_outranks_neutral_example(self) -> None:
        neutral = self.lens.analyze("The train departs at 6pm from platform two.")
        manipulative = self.lens.analyze(
            "Sadly, a regrettable workforce optimization occurred; the "
            "affected parties' separation was processed."
        )
        self.assertGreater(manipulative.manipulation_index, neutral.manipulation_index)

    def test_named_actor_case_does_not_outscore_the_audited_euphemism_case(self) -> None:
        adversarial_neutral = self.lens.analyze(
            "The Federation of National Associations (FNA) released its ACTION "
            "plan. The document mentions the implementation, the allocation, "
            "and the distribution of resources across several divisions."
        )
        manipulative = self.lens.analyze(
            "Sadly, a regrettable workforce optimization occurred; the "
            "affected parties' separation was processed."
        )
        self.assertLessEqual(
            adversarial_neutral.manipulation_index,
            manipulative.manipulation_index,
        )

    def test_saturating_normalization_never_hard_clips(self) -> None:
        signature = self.lens.analyze(
            "Sadly, tragically, unfortunately, alarmingly, urgent, critical, "
            "immediate action must be taken!!!"
        )
        self.assertGreater(signature.normalized_scores["D2_affect"], 0.0)
        self.assertLess(signature.normalized_scores["D2_affect"], 1.0)


if __name__ == "__main__":
    unittest.main()
