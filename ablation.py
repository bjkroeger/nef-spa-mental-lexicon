"""Reproducible neuron ablation applied AFTER decoder construction, before a run.

Percentages refer to the complete neuron population of a buffer/memory, not
separately to each ensemble. Increasing percentages extend the same random mask.
No decoder refitting or amplitude compensation is performed after damage.
"""
import math
import numpy as np

COMPONENTS = (
    'production_concept', 'production_c2l', 'production_lemma',
    'production_l2p', 'production_phonology',
    'perception_concept', 'perception_l2c', 'perception_lemma',
    'perception_p2l', 'perception_phonology',
)
ABLATION_SEED = 2026


def normalize_ablation(values=None):
    if values is None:
        values = {}
    if not isinstance(values, dict) or set(values) - set(COMPONENTS):
        raise ValueError('Unknown ablation component.')
    normalized = {}
    for key in COMPONENTS:
        value = values.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Ablation must be a number between 0 and 100.')
        if not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError('Ablation must be a number between 0 and 100.')
        normalized[key] = float(value)
    return normalized


def neuron_mask(key, total, percentage):
    rng = np.random.default_rng(np.random.SeedSequence([ABLATION_SEED, COMPONENTS.index(key)]))
    mask = np.zeros(total, dtype=bool)
    mask[rng.permutation(total)[:int(total * percentage / 100 + .5)]] = True
    return mask


def apply_ablation(sim, targets, percentages=None):
    """Silence selected LIF neurons; call once on a fresh, built simulator."""
    percentages = normalize_ablation(percentages)
    report = {}
    for key, network in targets.items():
        ensembles = network.all_ensembles
        total = sum(e.n_neurons for e in ensembles)
        mask = neuron_mask(key, total, percentages[key])
        offset = 0
        for ensemble in ensembles:
            local = mask[offset:offset + ensemble.n_neurons]
            offset += ensemble.n_neurons
            if not local.any():
                continue
            # Disable encoded input AND spontaneous firing. The WTA's direct
            # neuron input is inhibitory; the negative bias also silences it.
            for signal, value in ((sim.model.sig[ensemble]['encoders'], 0.),
                                  (sim.model.sig[ensemble.neurons]['bias'], -1e9)):
                array = sim.signals[signal]
                writable = array.flags.writeable
                array.setflags(write=True)
                array[local] = value
                array.setflags(write=writable)
        report[key] = dict(requested_percent=percentages[key], total=total,
                           ablated=int(mask.sum()), remaining=int(total-mask.sum()),
                           actual_percent=100*int(mask.sum())/total)
    return report
