"""Scientific invariants for expansion, independent of neural run outcomes."""
import unittest
import numpy as np

from extract_wwt import SOURCE, PHONOLOGY_DEFINITIONS, extract, read_assignments
from lexicon_vectors import load_data, load_lexicon, representations


class FullLexiconTests(unittest.TestCase):
    def test_counts_closed_graphs_and_audited_repairs(self):
        data = load_lexicon()
        self.assertEqual(len(data['entries']), 613)
        self.assertEqual(len({e['word'] for e in data['entries']}), 613)
        self.assertEqual(len(data['phonology_repairs']), 13)
        for level in ('concept', 'phonology'):
            net = data[level + '_network']
            for links in net.values():
                self.assertTrue(all(target in net for _, target in links))
    @unittest.skipUnless(SOURCE is not None and SOURCE.is_dir(), 'Optional comparison requires WWT_SOURCE_DIR')
    def test_full_source_fidelity(self):
        data = load_lexicon()
        self.assertEqual(data, extract(full=True))
        for level, filename, deep, surface in [
            ('concept', 'wwt_concepts.py', 'concepts_deep', 'concepts'),
            ('phonology', 'wwt_phonos.py', 'phonos_deep', 'phonos'),
        ]:
            source = read_assignments(SOURCE / filename)
            original_network = {**source[deep], **source[surface]}
            repaired = {r['pointer'] for r in data['phonology_repairs']} if level == 'phonology' else set()
            for key, links in data[level + '_network'].items():
                if key not in repaired:
                    self.assertEqual(links, original_network[key], key)
        original = read_assignments(SOURCE / 'wwt_phonos.py')
        for repair in data['phonology_repairs']:
            expected = [list(link) for link in original['phonos'][PHONOLOGY_DEFINITIONS[repair['word']]]]
            if repair['word'] == 'Verbringen':
                expected[0] = ['InclPhon', 'P_fEA']
            self.assertEqual(data['phonology_network'][repair['pointer']], expected)

    def test_original_vectors_and_similarities_are_unchanged(self):
        old, full = load_data(), load_lexicon()
        old_v, full_v = representations(old), representations(full)
        words = [e['word'] for e in full['entries']]
        indices = [words.index(e['word']) for e in old['entries']]
        self.assertEqual(full['display_words'], [e['word'] for e in old['entries']])
        for level in old_v:
            np.testing.assert_array_equal(old_v[level], full_v[level][indices])
            np.testing.assert_allclose(np.linalg.norm(full_v[level], axis=1), 1)
            np.testing.assert_allclose(old_v[level] @ old_v[level].T,
                                       full_v[level][indices] @ full_v[level][indices].T)

    def test_live_model_contains_all_competitors_but_only_eight_display_rows(self):
        import production
        import perception
        for module in (production, perception):
            model, probes, words, vectors, target = module.build_model('Kanne')
            self.assertEqual(len(model.lexicon_words), 613)
            self.assertEqual(len(words), 8)
            self.assertEqual(words[target], 'Kanne')
            self.assertTrue(all(v.shape == (8, 512) for v in vectors.values()))
            memories = [net for key, net in model.ablation_targets.items()
                        if key.rsplit('_', 1)[1] in ('c2l', 'l2p', 'p2l', 'l2c')]
            for memory in memories:
                self.assertEqual(len(memory.selection.thresholding.ensembles), 613)
            self.assertEqual(sum(e.n_neurons for e in model.all_ensembles), 199400)
            self.assertEqual(probes['lemma_entries'].size_in, 8)


if __name__ == '__main__':
    unittest.main()
