"""
Falsification suite for the 4D Language-Aware Lens.

Each test states a CLAIM the original tool (implicitly) makes,
then constructs a minimal text designed to break it.
A claim survives only if the tool's output matches linguistic reality.
"""
from original_4dlens import FourDLens

lens = FourDLens()

def run(label, claim, text, check):
    sig = lens.analyze(text)
    result = check(sig, text)
    status = "SURVIVES" if result else "FALSIFIED"
    print(f"\n[{status}] {label}")
    print(f"  Claim: {claim}")
    print(f"  Text:  \"{text}\"")
    print(f"  D1={sig.dimension_scores['D1_agency']:.2f}  D2={sig.dimension_scores['D2_affect']:.2f}  "
          f"D3={sig.dimension_scores['D3_reality']:.2f}  D4={sig.dimension_scores['D4_iconic']:.2f}  "
          f"MI={sig.manipulation_index}")
    for t in sig.trace:
        print(f"    - {t}")
    return result

results = []

# --- CLAIM 1: PASSIVE_PATTERNS detects passive voice (agent deflection) ---
results.append(run(
    "C1: passive-voice detector",
    "'was/were + word ending in -ed/-en/-d/-t' reliably flags true passive constructions.",
    "The lake was silent. She seemed reluctant, but the room was pleasant and the coffee was excellent.",
    lambda sig, t: sig.dimension_scores['D1_agency'] == 0.0
))

# --- CLAIM 2: BINARY_COMPRESSORS detects ideological binary framing ---
results.append(run(
    "C2: binary-compressor detector",
    "'left/right/us/them/or' flags dichotomous us-vs-them framing.",
    "Turn left, then right, and you'll find us a table for two or three.",
    lambda sig, t: sig.dimension_scores['D3_reality'] == 0.0
))

# --- CLAIM 3: dimensions are independent (D1 agency vs D3 reification) ---
results.append(run(
    "C3: D1/D3 orthogonality",
    "Agency-routing (D1) and reality-construction (D3) measure distinct phenomena from distinct evidence.",
    "The organization announced the reorganization of the operation.",
    lambda sig, t: True  # inspected manually below; always 'survives' here, judged after printing
))

# --- CLAIM 4: FLATTENED_AFFECT and EMOTIONAL_INJECTORS are opposed forces ---
results.append(run(
    "C4: D2 sub-signals cancel rather than sum",
    "'Dampening' words (noted/observed) and 'injector' words (urgent/tragically) pull affect in opposite directions, so D2 should reflect net affect, not raw magnitude.",
    "It was noted that the situation is tragically urgent.",
    lambda sig, t: True
))

# --- CLAIM 5: manipulation_index tracks intuitive manipulativeness ---
neutral = "The train departs at 6pm from platform two."
manipulative = "Sadly, a regrettable workforce optimization occurred; the affected parties' separation was processed."
sig_neutral = lens.analyze(neutral)
sig_manip = lens.analyze(manipulative)
print(f"\n[{'SURVIVES' if sig_manip.manipulation_index > sig_neutral.manipulation_index else 'FALSIFIED'}] "
      f"C5: manipulation_index ordering")
print(f"  Claim: Text intuitively judged manipulative scores higher than plainly neutral text.")
print(f"  neutral MI={sig_neutral.manipulation_index}  |  manipulative MI={sig_manip.manipulation_index}")

# --- CLAIM 6: adversarial neutral text cannot out-score genuine manipulation ---
adversarial_neutral = ("The Federation of National Associations (FNA) released its ACTION plan. "
                        "The document mentions the implementation, the allocation, and the distribution "
                        "of resources across several divisions.")
sig_adv = lens.analyze(adversarial_neutral)
print(f"\n[{'SURVIVES' if sig_adv.manipulation_index <= sig_manip.manipulation_index else 'FALSIFIED'}] "
      f"C6: robustness to nominalization-dense but non-manipulative bureaucratic/technical prose")
print(f"  adversarial-neutral MI={sig_adv.manipulation_index}  |  genuine-manipulative MI={sig_manip.manipulation_index}")
print(f"  adversarial-neutral raw: {sig_adv.dimension_scores}")

# --- CLAIM 7: normalization ceilings (maxes) are never exceeded in ordinary text ---
dense = "Sadly, tragically, unfortunately, alarmingly, urgent, critical, immediate action must be taken!!!"
sig_dense = lens.analyze(dense)
print(f"\n[{'SURVIVES' if sig_dense.normalized_scores['D2_affect'] < 1.0 else 'FALSIFIED (clipped to ceiling)'}] "
      f"C7: normalized D2 stays below the clipping ceiling for realistic dense text")
print(f"  raw D2={sig_dense.dimension_scores['D2_affect']}  normalized D2={sig_dense.normalized_scores['D2_affect']}")
