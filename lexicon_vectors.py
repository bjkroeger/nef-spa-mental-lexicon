"""WWT vector construction, without neural ensembles or simulation.

v(node) = normalize(base(node) + sum(bind(relation, v(target))))
Relations bind to the recursively constructed target, NOT an independent target ID.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import nengo_spa as spa

DATA = Path(__file__).parent / 'data' / 'wwt_eight_words.json'


def load_data():
    return json.loads(DATA.read_text())


def unit_vector(dimensions, seed, namespace, key):
    # Stable per-node streams: extracting a subgraph cannot change its base vectors.
    digest = hashlib.sha256(f'{seed}:{namespace}:{key}'.encode()).digest()
    rng = np.random.default_rng(int.from_bytes(digest[:16], 'little'))
    v = rng.standard_normal(dimensions)
    return v / np.linalg.norm(v)


def encode_network(network, dimensions=512, seed=10, namespace='concept'):
    vectors, active = {}, set()
    relations = {r: spa.SemanticPointer(unit_vector(dimensions, seed, namespace + ':relation', r))
                 for links in network.values() for r, _ in links}

    def encode(key):
        if key in active:
            raise ValueError(f'Directed cycle at {key}')
        if key not in vectors:
            active.add(key)
            pointer = spa.SemanticPointer(unit_vector(dimensions, seed, namespace + ':base', key))
            for relation, target in network[key]:
                pointer = pointer + relations[relation] * spa.SemanticPointer(encode(target))
            vectors[key] = pointer.normalized().v.copy()
            active.remove(key)
        return vectors[key]

    for key in sorted(network):
        encode(key)
    return vectors


def representations(data, dimensions=512, seed=10):
    concepts = encode_network(data['concept_network'], dimensions, seed, 'concept')
    phonology = encode_network(data['phonology_network'], dimensions, seed, 'phonology')
    entries = data['entries']
    return {
        'concept': np.array([concepts[e['concept']] for e in entries]),
        'lemma': np.array([unit_vector(dimensions, seed, 'lemma', e['lemma']) for e in entries]),
        'phonology': np.array([phonology[e['phonology']] for e in entries]),
    }


def similarity_matrices(data, dimensions=512, seed=10):
    return {level: vectors @ vectors.T for level, vectors in representations(data, dimensions, seed).items()}
