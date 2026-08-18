"""Tests for the command-line interface.

These cover the CLI's contract, not the validity of the underlying heuristic:
the trace is reported in full, the composite index is suppressible, JSON output
is machine-readable, and the exit code never depends on a score.
"""

import io
import json
import unittest
from contextlib import redirect_stdout

import fourdlens_cli
from fourdlens_cli import main


NEUTRAL = "The train departs at 6pm from platform two."
MANIPULATIVE = (
    "Sadly, a regrettable workforce optimization occurred; the "
    "affected parties' separation was processed."
)


def run(*argv):
    """Invoke the CLI with argv, returning (exit_code, stdout)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = main(list(argv))
    return code, buffer.getvalue()


class ExitCodeTests(unittest.TestCase):
    """The tool is not a gate — no score may influence the exit code."""

    def test_manipulative_text_still_exits_zero(self) -> None:
        code, _ = run(MANIPULATIVE, "--width", "80")
        self.assertEqual(code, 0)

    def test_neutral_text_exits_zero(self) -> None:
        code, _ = run(NEUTRAL, "--width", "80")
        self.assertEqual(code, 0)


class ReportTests(unittest.TestCase):
    def test_every_trace_entry_appears_in_the_report(self) -> None:
        from revised_4dlens_v2 import FourDLensV2

        signature = FourDLensV2().analyze(MANIPULATIVE)
        _code, output = run(MANIPULATIVE, "--width", "100")
        for entry in signature.trace:
            _prefix, _sep, rest = entry.partition(": ")
            self.assertIn(rest.split(" (")[0][:40], output)

    def test_index_is_shown_by_default_and_hidden_on_request(self) -> None:
        _code, shown = run(MANIPULATIVE, "--width", "80")
        self.assertIn("manipulation_index", shown)
        _code, hidden = run(MANIPULATIVE, "--width", "80", "--no-index")
        self.assertNotIn("manipulation_index", hidden)
        self.assertIn("RAW SCORES", hidden)

    def test_report_states_the_semantics_of_the_scalar(self) -> None:
        _code, output = run(MANIPULATIVE, "--width", "80")
        self.assertIn("not validated", output)

    def test_leak_adjustments_are_surfaced_when_they_occur(self) -> None:
        _code, output = run(
            "The organization announced the reorganization of the operation.",
            "--width", "100",
        )
        self.assertIn("leak adjustment", output)

    def test_text_with_no_matches_says_so_explicitly(self) -> None:
        _code, output = run(NEUTRAL, "--width", "80")
        self.assertIn("nothing fired", output)


class JsonOutputTests(unittest.TestCase):
    def test_single_input_emits_one_parsable_object(self) -> None:
        _code, output = run(MANIPULATIVE, "--json")
        payload = json.loads(output.strip())
        self.assertEqual(payload["text"], MANIPULATIVE)
        self.assertEqual(set(payload["dimension_scores"]), {
            "D1_agency", "D2_affect", "D3_reality", "D4_iconic"})
        self.assertGreater(len(payload["trace"]), 0)

    def test_multiple_inputs_emit_one_object_per_line(self) -> None:
        _code, output = run("--demo", "--json")
        lines = [line for line in output.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(fourdlens_cli.DEMO_CASES))
        for line in lines:
            json.loads(line)

    def test_json_output_carries_no_ansi_escapes(self) -> None:
        _code, output = run(MANIPULATIVE, "--json")
        self.assertNotIn("\033", output)


class TraceGroupingTests(unittest.TestCase):
    def test_netting_arithmetic_is_separated_from_patterns_that_fired(self) -> None:
        trace = [
            "D2: Emotional injector: 'urgent'",
            "D2: net = injection(2.4) - 0.5*dampening(0.8) = 2.0",
        ]
        hits, notes = fourdlens_cli.group_trace(trace)
        self.assertEqual(hits["D2"], ["Emotional injector: 'urgent'"])
        self.assertEqual(len(notes), 1)
        self.assertIn("net =", notes[0])


class DemoTests(unittest.TestCase):
    def test_demo_analyzes_the_full_audited_example_set(self) -> None:
        code, output = run("--demo", "--width", "100")
        self.assertEqual(code, 0)
        for label, _text in fourdlens_cli.DEMO_CASES:
            self.assertIn(label, output)


if __name__ == "__main__":
    unittest.main()
