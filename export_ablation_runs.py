"""Record the 613-entry model: 8 reference perception + 40 production runs.

Each group reuses built decoders, resetting all neural/filter state and restoring
undamaged encoder/bias signals before applying the same post-build ablation.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
import nengo
from demo_server import recording_from_sim, WORDS
from ablation import normalize_ablation, apply_ablation
import production
import perception
ROOT = Path(__file__).parent
VERSION = '613-20261104'
OUT = ROOT / 'website/deploy/perception-production-model' / ('runs-' + VERSION)
SOURCES = ['ablation.py','perception.py','production.py','lexicon_vectors.py','demo_server.py','data/wwt_full_lexicon.json','requirements.lock.txt']
FINGERPRINT = hashlib.sha256(b''.join((ROOT/p).read_bytes() for p in SOURCES)).hexdigest()
CASES = {'reference':(100,100,100),'buffers':(50,100,50),'memory70':(50,70,50),'memory55':(50,55,50),'lemma75-memory55':(50,55,75)}


def record_group(job):
    task, case = job
    model, probes, words, vectors, _ = (perception if task == 'perception' else production).build_model()
    nengo.rc.set('decoder_cache', 'enabled', 'False')
    damage_values = normalize_ablation({f'production_{part}':100-value for part,value in zip(['concept','c2l','lemma'], CASES[case])})
    summaries = []
    with nengo.Simulator(model, dt=.001, progress_bar=False) as sim:
        original = []
        for ensemble in model.all_ensembles:
            for signal in (sim.model.sig[ensemble]['encoders'], sim.model.sig[ensemble.neurons]['bias']):
                original.append((signal, sim.signals[signal].copy()))
        for word in words:
            started = time.monotonic()
            model.stimulus_index = model.lexicon_words.index(word)
            sim.reset()
            for signal, value in original:
                target = sim.signals[signal]
                writable = target.flags.writeable
                target.setflags(write=True); target[...] = value; target.setflags(write=writable)
            damage = apply_ablation(sim, model.ablation_targets, damage_values)
            sim.run(1.1)
            result = recording_from_sim(sim, model, probes, words, vectors, task, word, damage_values, damage, started)
            if case == 'reference':
                assert result['winner'] == word, (task, word, result['top_candidates'])
            result.update(source_fingerprint=FINGERPRINT, recorded=True, case_id=case,
                          dimensions=512, vector_seed=10, neural_seed=11, dt=.001,
                          recording_date='2026-11-04', model_version=VERSION)
            name = f'{task}-{word}' + ('' if case == 'reference' else '-'+case) + '.json'
            (OUT/name).write_text(json.dumps(result, ensure_ascii=False, separators=(',',':'))+'\n')
            summary = dict(file=name, task=task, word=word, case=case, winner=result['winner'],
                           target_mean=result['means'][words.index(word)], bytes=(OUT/name).stat().st_size)
            summaries.append(summary)
            print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summaries


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True, parents=True)
    jobs = [('perception','reference')] + [('production',case) for case in CASES]
    summaries = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(record_group,job) for job in jobs]
        for future in as_completed(futures): summaries.extend(future.result())
    assert len(summaries) == 48
    (OUT.parent/('manifest-'+VERSION+'.json')).write_text(json.dumps(dict(
        model_version=VERSION, source_fingerprint=FINGERPRINT, lexical_entries=613,
        vector_seed=10, neural_seed=11, ablation_seed=2026, cases=CASES,
        recordings=sorted(summaries,key=lambda r:r['file'])),ensure_ascii=False,indent=2)+'\n')
    print('DONE: 48 recordings',flush=True)
