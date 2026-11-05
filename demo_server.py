"""Local, dependency-free HTTP bridge to the existing spiking Nengo models."""
from collections import OrderedDict
from ablation import normalize_ablation, apply_ablation, ABLATION_SEED
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import time
import threading
import uuid
import numpy as np
import nengo
import perception
import production
from syllabification import for_live_result
from lexicon_vectors import load_lexicon, representations
from functools import lru_cache

ROOT = Path(__file__).parent
LEXICON = load_lexicon()
ENTRIES = LEXICON['entries']
WORDS = LEXICON['display_words']
# Display convention only; no claim of compatibility with the future Dynart adapter.
IPA = dict(zip(WORDS, ['ˈtasə', 'ˈtaʃə', 'ˈkanə', 'ˈkatsə', 'ˈtɛlɐ', 'tɔpf', 'ʃtuːl', 'ʃʁaŋk']))
EXECUTOR = ThreadPoolExecutor(max_workers=1)
JOBS = {}
LOCK = threading.Lock()
CACHE = OrderedDict()
CACHE_LIMIT = 64


@lru_cache(maxsize=1)
def neighbours():
    """Undamaged template similarities, independent of task and ablation."""
    words = [e['word'] for e in ENTRIES]
    indices = [words.index(w) for w in WORDS]
    result = dict(words=WORDS, lexicon_size=len(words), dimensions=512, vector_seed=10,
                  measure='cosine similarity of undamaged templates', levels={})
    for level, vectors in representations(LEXICON).items():
        if level == 'lemma':
            continue
        scores = vectors[indices] @ vectors.T
        rows = []
        for row, index in enumerate(indices):
            scores[row, index] = -np.inf
            nearest = np.argsort(scores[row])[-5:][::-1]
            rows.append([dict(word=words[i], similarity=float(scores[row, i])) for i in nearest])
        result['levels'][level] = rows
    return result


def simulate(task, word, ablation=None):
    if task not in ('perception', 'production') or word not in WORDS:
        raise ValueError('Invalid task or display word')
    started = time.monotonic()
    ablation = normalize_ablation(ablation)
    key = (task, word, tuple(ablation.items()))
    if key in CACHE:
        return {**CACHE[key], 'cached': True}
    module = perception if task == 'perception' else production
    model, probes, words, vectors, target = module.build_model(word)
    nengo.rc.set('decoder_cache', 'enabled', 'False')
    with nengo.Simulator(model, dt=.001, progress_bar=False) as sim:
        damage = apply_ablation(sim, model.ablation_targets, ablation)
        sim.run(1.1)
        result = recording_from_sim(sim, model, probes, words, vectors, task, word,
                                    ablation, damage, started)
    result['syllabification'] = for_live_result(LEXICON, result)
    CACHE[key] = result
    if len(CACHE) > CACHE_LIMIT:
        CACHE.popitem(last=False)
    return result


def recording_from_sim(sim, model, probes, words, vectors, task, word, ablation, damage, started):
    """Export the same observations for a live run or a reset offline simulator."""
    times = sim.trange()
    steady = (times >= .45) & (times < .70)
    levels = {k: sim.data[probes[k]] @ v.T for k, v in vectors.items()}
    end = 'concept' if task == 'perception' else 'phonology'
    # Decide against the entire lexicon, not just the eight visible rows.
    all_means = sim.data[probes[end]][steady].mean(axis=0) @ model.lexicon_vectors[end].T
    means = all_means[model.display_indices]
    winner = int(np.argmax(all_means))
    # Reject an absent/ambiguous retrieval instead of copying the input to output.
    ordered = np.sort(all_means)
    accepted = bool(ordered[-1] > .3 and ordered[-1] - ordered[-2] > .1)
    winner_word = model.lexicon_words[winner] if accepted else None
    result = dict(task=task, input=word, words=words, time=times[::10].round(3).tolist(),
                  levels={k: v[::10].round(4).tolist() for k, v in levels.items()},
                  selections={k: sim.data[p][::10].round(4).tolist() for k,p in probes.items() if k.endswith('_entries')},
                  means=means.round(4).tolist(), winner=winner_word,
                  correct=accepted and winner_word == word, cached=False,
                  lexicon_size=len(model.lexicon_words),
                  elapsed_seconds=time.monotonic()-started,
                  top_candidates=[dict(word=model.lexicon_words[i], similarity=float(all_means[i]))
                                  for i in np.argsort(all_means)[-5:][::-1]],
                  ablation=ablation, damage=damage, ablation_seed=ABLATION_SEED,
                  neurons=sum(e.n_neurons for e in model.all_ensembles),
                  code=IPA.get(winner_word) if accepted and task == 'production' else None,
                  pointer=model.lexicon_entries[winner]['phonology'] if accepted and task == 'production' else None)
    return result


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/neighbours':
            return self.reply(200, neighbours())
        if self.path == '/api/words':
            return self.reply(200, WORDS)
        if self.path.startswith('/api/jobs/'):
            job_id = self.path.removeprefix('/api/jobs/')
            with LOCK:
                future = JOBS.get(job_id)
            if future is None:
                return self.reply(404, {'error': 'Unbekannter Lauf.'})
            if not future.done():
                return self.reply(200, {'status': 'running'})
            try:
                return self.reply(200, {'status': 'done', 'result': future.result()})
            except Exception as exc:
                return self.reply(500, {'error': 'Simulation fehlgeschlagen: ' + str(exc)})
        files = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}
        if self.path not in files:
            return self.reply(404, {'error': 'Nicht gefunden.'})
        path = ROOT / 'demo' / files[self.path]
        body = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[path.suffix])
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != '/api/run':
            return self.reply(404, {'error': 'Nicht gefunden.'})
        # Browser requests are same-origin; refuse cross-origin mutation.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.reply(403, {'error': 'Nur lokale Anfragen erlaubt.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length < 2048:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            task, word = data['task'], data['word']
            ablation = normalize_ablation(data.get('ablation'))
            if task not in ('perception', 'production') or word not in WORDS:
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            return self.reply(400, {'error': 'Bitte ein gültiges Wort, eine Aufgabe und Ablationswerte zwischen 0 und 100 wählen.'})
        with LOCK:
            if any(not job.done() for job in JOBS.values()):
                return self.reply(409, {'error': 'Ein Modelllauf wird bereits berechnet. Bitte kurz warten.'})
            job_id = uuid.uuid4().hex
            JOBS.clear()
            JOBS[job_id] = EXECUTOR.submit(simulate, task, word, ablation)
        self.reply(202, {'id': job_id})


if __name__ == '__main__':
    print('Lexikon-Labor: http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
