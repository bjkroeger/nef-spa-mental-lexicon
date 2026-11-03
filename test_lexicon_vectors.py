import unittest

import numpy as np

from extract_wwt import SOURCE, dependency_closure, read_assignments
from lexicon_vectors import encode_network, load_data, representations, similarity_matrices, unit_vector


class VectorTests(unittest.TestCase):
    def test_recursive_rule_against_explicit_circular_convolution(self):
        graph = {'leaf': [], 'middle': [('R', 'leaf')], 'root': [('R', 'middle')]}
        d, seed, namespace = 16, 7, 'test'
        actual = encode_network(graph, d, seed, namespace)
        relation = unit_vector(d, seed, namespace + ':relation', 'R')
        expected = {}
        for key in ['leaf', 'middle', 'root']:
            value = unit_vector(d, seed, namespace + ':base', key)
            for _, target in graph[key]:
                # Independent reference: direct sum, no SPA operations or FFT.
                child = expected[target]
                value = value + np.array([sum(relation[j] * child[(i-j) % d] for j in range(d)) for i in range(d)])
            expected[key] = value / np.linalg.norm(value)
            np.testing.assert_allclose(actual[key], expected[key], atol=1e-12)
        id_only = unit_vector(d, seed, namespace + ':base', 'middle')
        self.assertGreater(np.linalg.norm(actual['middle'] - id_only), .1)

    @unittest.skipUnless(SOURCE is not None and SOURCE.is_dir(), 'Optional comparison requires WWT_SOURCE_DIR')
    def test_subset_preserves_every_relation_and_vector(self):
        data = load_data()
        for level, filename, deep, surface, entry_key in [
            ('concept', 'wwt_concepts.py', 'concepts_deep', 'concepts', 'concept'),
            ('phonology', 'wwt_phonos.py', 'phonos_deep', 'phonos', 'phonology'),
        ]:
            original = read_assignments(SOURCE / filename)
            full = {**original[deep], **original[surface]}
            expected = dependency_closure(full, [e[entry_key] for e in data['entries']])
            self.assertEqual(data[level + '_network'], expected)
            # At low dimensions this is a fast preservation test, not a scientific run.
            full_vectors = encode_network(full, 16, 10, level)
            subset_vectors = encode_network(expected, 16, 10, level)
            for node in expected:
                np.testing.assert_array_equal(full_vectors[node], subset_vectors[node])

    def test_subset_vectors_are_independent_of_unrelated_nodes(self):
        graph = {'leaf': [], 'root': [('R', 'leaf')], 'unrelated': []}
        subset = dependency_closure(graph, ['root'])
        full_vectors = encode_network(graph, 16, 10, 'test')
        subset_vectors = encode_network(subset, 16, 10, 'test')
        for node in subset:
            np.testing.assert_array_equal(full_vectors[node], subset_vectors[node])

    def test_reproducibility_and_unit_vectors(self):
        data = load_data()
        first = representations(data)
        second = representations(data)
        for level in first:
            np.testing.assert_array_equal(first[level], second[level])
            np.testing.assert_allclose(np.linalg.norm(first[level], axis=1), 1)
        for matrix in similarity_matrices(data).values():
            np.testing.assert_allclose(matrix, matrix.T)
            np.testing.assert_allclose(np.diag(matrix), 1)

    def test_missing_target_and_cycles_are_rejected(self):
        with self.assertRaises(KeyError):
            encode_network({'a': [('R', 'absent')]})
        with self.assertRaisesRegex(ValueError, 'cycle'):
            encode_network({'a': [('R', 'b')], 'b': [('R', 'a')]})


if __name__ == '__main__':
    unittest.main()
