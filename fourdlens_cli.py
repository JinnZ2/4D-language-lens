"""Command-line interface for the 4D Language-Aware Lens.

The trace is the product; the composite scalar is not. This CLI is built to
reflect that ordering literally: every pattern that fired is printed first and
in full, the raw dimension scores come second, and `manipulation_index` comes
last, attached to the one sentence that states its actual semantics.

This command never exits non-zero on the basis of a score. The tool is not a
gate, and `4D_Lens_Audit_Report.md` explains at length why it must not become
one. A non-zero exit here means a usage or I/O error, nothing more.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Iterator, List, Sequence, Tuple

from revised_4dlens_v2 import FourDLensV2, VectorSignature

# (score key, trace prefix, human label)
DIMENSIONS: Sequence[Tuple[str, str, str]] = (
    ("D1_agency", "D1", "agency routing"),
    ("D2_affect", "D2", "affective impedance"),
    ("D3_reality", "D3", "reality construction"),
    ("D4_iconic", "D4", "iconic mass"),
)

SCALAR_SEMANTICS = (
    "Not a probability, not a percentile, not validated against ground truth. "
    "It means only: more of these hand-picked patterns fired, weighted by "
    "hand-picked constants."
)

# The audited example set, kept in sync with the __main__ block of
# revised_4dlens_v2.py. Each case is the falsifying input for one claim in
# the audit report's ledger.
DEMO_CASES: Sequence[Tuple[str, str]] = (
    ("C1 predicate adjectives are not passives",
     "The lake was silent. She seemed reluctant, but the room was pleasant "
     "and the coffee was excellent."),
    ("C2 literal left/right is not binary framing",
     "Turn left, then right, and you'll find us a table for two or three."),
    ("C3 D1/D3 draw on the same token",
     "The organization announced the reorganization of the operation."),
    ("C4 affect nets rather than sums",
     "It was noted that the situation is tragically urgent."),
    ("C5 neutral baseline",
     "The train departs at 6pm from platform two."),
    ("C5 euphemism plus agent deletion",
     "Sadly, a regrettable workforce optimization occurred; the affected "
     "parties' separation was processed."),
    ("C6 bureaucratic but not manipulative",
     "The Federation of National Associations (FNA) released its ACTION plan. "
     "The document mentions the implementation, the allocation, and the "
     "distribution of resources across several divisions."),
)


class Style:
    """ANSI styling, disabled unless stdout is a terminal that wants it."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def dim(self, text: str) -> str:
        return self._wrap("2", text)


def want_color(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def terminal_width(default: int = 80) -> int:
    if not sys.stdout.isatty():
        return default
    try:
        return os.get_terminal_size().columns
    except OSError:
        return default


def group_trace(trace: Sequence[str]) -> Tuple[dict, List[str]]:
    """Split a flat trace into per-dimension hits plus arithmetic notes.

    Every trace line the lens emits is prefixed with its dimension ("D2: ...").
    The D2 netting line is arithmetic about the score rather than a pattern
    that fired, so it is separated out and reported with the scores instead.
    """
    hits = {prefix: [] for _, prefix, _ in DIMENSIONS}
    notes: List[str] = []
    for line in trace:
        prefix, sep, rest = line.partition(": ")
        if sep and prefix in hits:
            if rest.startswith("net = "):
                notes.append(f"{prefix} {rest}")
            else:
                hits[prefix].append(rest)
        else:
            notes.append(line)
    return hits, notes


def note_lines(text: str, style: Style, width: int, indent: str = "  ") -> Iterator[str]:
    """Yield a de-emphasized note, wrapped to the output width."""
    for line in textwrap.wrap(text, width=width - len(indent)) or [""]:
        yield indent + style.dim(line)


def render(text: str, sig: VectorSignature, label: str, style: Style,
           show_index: bool, width: int) -> Iterator[str]:
    """Yield the human-readable report for a single analyzed text."""
    hits, notes = group_trace(sig.trace)

    yield ""
    if label:
        yield style.bold(label)
    wrapped = textwrap.wrap(text, width=width - 6) or [""]
    for i, line in enumerate(wrapped):
        opener = '  "' if i == 0 else "   "
        closer = '"' if i == len(wrapped) - 1 else ""
        yield style.dim(f"{opener}{line}{closer}")

    yield ""
    yield style.bold("  WHAT FIRED") + style.dim("  — read this before the number")
    yield ""

    fired = False
    for _key, prefix, name in DIMENSIONS:
        entries = hits[prefix]
        if not entries:
            continue
        fired = True
        count = f"{len(entries)} pattern{'s' if len(entries) != 1 else ''}"
        yield f"  {style.bold(prefix)}  {name:<22} {style.dim(count)}"
        for entry in entries:
            for i, line in enumerate(textwrap.wrap(entry, width=width - 10) or [""]):
                yield f"      {'·' if i == 0 else ' '} {line}"
        yield ""

    silent = [f"{prefix} {name}" for _k, prefix, name in DIMENSIONS if not hits[prefix]]
    if not fired:
        yield from note_lines(
            "nothing fired — no pattern in any dimension matched this text", style, width)
        yield ""
    elif silent:
        yield from note_lines("nothing fired in: " + ", ".join(silent), style, width)
        yield ""

    scores = "   ".join(
        f"{prefix} {sig.dimension_scores[key]:.2f}" for key, prefix, _ in DIMENSIONS
    )
    yield f"  {style.bold('RAW SCORES')}   {scores}"
    for note in notes:
        yield from note_lines(note, style, width)
    if sig.leak_adjustments:
        n = sig.leak_adjustments
        yield from note_lines(
            f"{n} cross-dimension leak adjustment{'s' if n != 1 else ''} applied — "
            "some evidence was counted in two dimensions and down-weighted to 0.3x. "
            "Treat these dimensions as correlated, not independent.", style, width)

    if show_index:
        yield ""
        yield f"  {style.bold('manipulation_index')}  {sig.manipulation_index}"
        yield from note_lines(SCALAR_SEMANTICS, style, width)
    yield ""


def as_json(text: str, sig: VectorSignature, label: str) -> str:
    payload = {
        "source": label or None,
        "text": text,
        "dimension_scores": sig.dimension_scores,
        "normalized_scores": sig.normalized_scores,
        "manipulation_index": sig.manipulation_index,
        "leak_adjustments": sig.leak_adjustments,
        "trace": list(sig.trace),
    }
    return json.dumps(payload, ensure_ascii=False)


def collect_inputs(args: argparse.Namespace) -> List[Tuple[str, str]]:
    """Return (label, text) pairs from --demo, files, arguments, or stdin."""
    if args.demo:
        return [(label, text) for label, text in DEMO_CASES]

    inputs: List[Tuple[str, str]] = []
    for path in args.file or []:
        if path == "-":
            inputs.append(("<stdin>", sys.stdin.read()))
            continue
        try:
            with open(path, encoding="utf-8") as handle:
                inputs.append((path, handle.read()))
        except OSError as exc:
            raise SystemExit(f"4dlens: cannot read {path}: {exc.strerror}")
    if args.text:
        inputs.append(("", " ".join(args.text)))
    if not inputs and not sys.stdin.isatty():
        inputs.append(("<stdin>", sys.stdin.read()))
    return [(label, text) for label, text in inputs if text.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="4dlens",
        description="Show which rhetorical patterns fire in a piece of English text.",
        epilog=(
            "The trace is the output; the composite index is a weighted sum of "
            "hand-picked constants with no reported precision or recall. Read "
            "the not-to-be-used flags in README.md before acting on a score. "
            "This command never exits non-zero because of a score."
        ),
    )
    parser.add_argument("text", nargs="*", help="text to analyze; omit to read stdin")
    parser.add_argument("-f", "--file", action="append", metavar="PATH",
                        help="read text from PATH (repeatable; '-' means stdin)")
    parser.add_argument("--demo", action="store_true",
                        help="analyze the audited example set from the falsification ledger")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON Lines (one object per input) instead of a report")
    parser.add_argument("--no-index", action="store_true",
                        help="hide manipulation_index and show only the trace and raw scores")
    parser.add_argument("--width", type=int, default=None, metavar="N",
                        help="wrap output at N columns (default: terminal width, max 100)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    inputs = collect_inputs(args)
    if not inputs:
        parser.print_help()
        return 0

    width = args.width or min(terminal_width(), 100)
    style = Style(want_color(sys.stdout) and not args.json)
    lens = FourDLensV2()

    for label, text in inputs:
        text = text.strip()
        sig = lens.analyze(text)
        if args.json:
            print(as_json(text, sig, label))
        else:
            for line in render(text, sig, label, style, not args.no_index, width):
                print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
