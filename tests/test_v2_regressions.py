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
        """C4: dampening pulls affect toward zero instead of stacking with it.

        The netted value moved from 2.0 to 2.28 when C13 extended the
        claimed-span ledger to D2: "noted" is claimed by D1's passive rule
        ("was noted") first, so D2's dampening for the same token scores at
        0.3x. C4's claim is about netting, not about the magnitude, and is
        unaffected.
        """
        signature = self.lens.analyze(
            "It was noted that the situation is tragically urgent."
        )
        self.assertEqual(signature.dimension_scores["D2_affect"], 2.28)
        self.assertIn(
            "D2: net = injection(2.4) - 0.5*dampening(0.24) = 2.28", signature.trace
        )
        self.assertIn("D2: Affective dampening: 'noted' (leak-adjusted)", signature.trace)

    def test_affect_lexicon_matches_whole_words_only(self) -> None:
        """C11: "unfortunately" must not also score the softener "unfortunate"."""
        signature = self.lens.analyze("Unfortunately, the meeting moved.")
        softeners = [t for t in signature.trace if "Amplifier/softener" in t]
        self.assertEqual(softeners, [])
        self.assertIn("D2: Emotional injector: 'Unfortunately'", signature.trace)

    def test_affect_scales_with_density_in_both_halves_of_d2(self) -> None:
        """C12: lexicon and regex halves of D2 now use the same unit."""
        for once, many in (("excellent", "excellent excellent excellent excellent"),
                           ("urgent", "urgent urgent urgent urgent")):
            with self.subTest(term=once):
                self.assertGreater(
                    self.lens.analyze(many).dimension_scores["D2_affect"],
                    self.lens.analyze(once).dimension_scores["D2_affect"],
                )

    def test_leak_ledger_covers_all_four_dimensions(self) -> None:
        """C13: '!!!' scores in D2 and D4 from one span; the re-use is logged."""
        signature = self.lens.analyze("URGENT!!!")
        self.assertGreater(signature.leak_adjustments, 0)
        self.assertTrue(any("leak-adjusted" in t for t in signature.trace))

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

    def test_trace_reports_every_scored_hit(self) -> None:
        """C14: findall passes once scored len(matches) but traced only the first.

        Four emotional injectors must produce four trace lines, not one. The
        trace is the product; it may not under-report what the score charged.
        """
        signature = self.lens.analyze(
            "Sadly, tragically, unfortunately, alarmingly."
        )
        injectors = [t for t in signature.trace if "Emotional injector" in t]
        self.assertEqual(len(injectors), 4)

    def test_trace_reports_every_scored_hit_across_dimensions(self) -> None:
        """Same guarantee for D4, where caps and punctuation both repeat."""
        signature = self.lens.analyze("URGENT!!! ACT NOW!!!")
        caps = [t for t in signature.trace if "Visual mass (caps)" in t]
        punctuation = [t for t in signature.trace if "Punctuation mass" in t]
        self.assertEqual(len(caps), 3)
        self.assertEqual(len(punctuation), 2)

    def test_saturating_normalization_never_hard_clips(self) -> None:
        signature = self.lens.analyze(
            "Sadly, tragically, unfortunately, alarmingly, urgent, critical, "
            "immediate action must be taken!!!"
        )
        self.assertGreater(signature.normalized_scores["D2_affect"], 0.0)
        self.assertLess(signature.normalized_scores["D2_affect"], 1.0)


if __name__ == "__main__":
    unittest.main()
