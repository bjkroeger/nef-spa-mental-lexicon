"""Test the eight visible inputs against all 613 competitors in both pathways.

Build each simulator once, then reset all neural/filter state between inputs.
Only the externally supplied word pointer changes; no retraining or tuning.
"""
import json
import os
from pathlib import Path
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('VECLIB_MAXIMUM_THREADS', '1')
import nengo
import numpy as np
import perception
import production

OUT = Path(__file__).parent / 'results' / 'lexicon613'


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    nengo.rc.set('decoder_cache', 'enabled', 'False')
    report = dict(lexical_entries=613, dimensions=512, vector_seed=10,
                  neural_seed=11, duration_seconds=1.1, dt=.001,
                  retrieval_rule='largest full-lexicon dot product > 0.3, margin > 0.1',
                  pathways={})
    for task, module, end in [('production', production, 'phonology'),
                              ('perception', perception, 'concept')]:
        started = time.monotonic()
        model, probes, words, vectors, _ = module.build_model()
        with nengo.Simulator(model, dt=.001, progress_bar=False) as sim:
            build_seconds = time.monotonic() - started
            records = []
            for word in words:
                model.stimulus_index = model.lexicon_words.index(word)
                sim.reset()
                run_start = time.monotonic()
                sim.run(1.1)
                times = sim.trange()
                steady = (times >= .45) & (times < .70)
                mean = sim.data[probes[end]][steady].mean(axis=0)
                scores = model.lexicon_vectors[end] @ mean
                ranked = np.argsort(scores)[::-1]
                accepted = bool(scores[ranked[0]] > .3 and scores[ranked[0]]-scores[ranked[1]] > .1)
                winner = model.lexicon_words[ranked[0]] if accepted else None
                record = dict(input=word, winner=winner, correct=winner == word,
                              target_similarity=float(scores[model.stimulus_index]),
                              margin=float(scores[ranked[0]]-scores[ranked[1]]),
                              run_seconds=time.monotonic()-run_start,
                              top_candidates=[dict(word=model.lexicon_words[i], similarity=float(scores[i]))
                                              for i in ranked[:5]])
                records.append(record)
                print(task, json.dumps(record, ensure_ascii=False), flush=True)
            report['pathways'][task] = dict(build_seconds=build_seconds,
                neurons=sum(e.n_neurons for e in model.all_ensembles), runs=records)
        (OUT / 'baseline_benchmark.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    assert all(r['correct'] for path in report['pathways'].values() for r in path['runs']), 'Baseline retrieval failures: see report'


if __name__ == '__main__':
    main()
