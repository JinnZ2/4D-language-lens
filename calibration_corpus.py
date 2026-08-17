"""
Calibration scaffold — NOT a validated dataset.

The v1 tool picked normalization ceilings (maxes = {10, 8, 8, 5}) and
composite weights (0.4/0.3/0.2/0.1) with no empirical basis. v2 fixed the
clipping mechanics but still has NO calibrated weights — this file is the
scaffold for the next real step: collecting human-labeled examples and
fitting the weights against them instead of hand-picking constants.

Structure only. Populate `LABELED_EXAMPLES` with real annotated text
(ideally 3+ independent human raters per item, report Krippendorff's
alpha for inter-rater agreement) before trusting any weight fit from it.
"""

from dataclasses import dataclass


@dataclass
class LabeledExample:
    text: str
    human_manipulation_score: float  # 0-1, mean of independent human raters
    n_raters: int
    notes: str = ""


LABELED_EXAMPLES = [
    # Placeholder shape — replace with real annotated data before use.
    LabeledExample(
        text="The train departs at 6pm from platform two.",
        human_manipulation_score=0.0,
        n_raters=0,
        notes="UNRATED placeholder — plainly neutral, informational.",
    ),
    LabeledExample(
        text="Sadly, a regrettable workforce optimization occurred; the "
             "affected parties' separation was processed.",
        human_manipulation_score=0.0,
        n_raters=0,
        notes="UNRATED placeholder — euphemism + agent deletion for layoffs.",
    ),
]


def fit_weights(examples):
    """
    Sketch only. Real version: extract [D1,D2,D3,D4] normalized vectors
    from FourDLensV2 for each example, then fit a constrained linear
    regression (weights sum to 1, all >= 0) against human_manipulation_score.
    Report R^2 and residual-by-dimension, not just a single fitted index —
    a single scalar hides which dimension the model actually trusts.
    """
    raise NotImplementedError(
        "Needs a real labeled corpus (target: 300+ items, 3+ raters each, "
        "stratified across genres: corporate comms, political speech, "
        "advertising, news, casual text) before fitting is meaningful."
    )
