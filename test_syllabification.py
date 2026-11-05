"""Lexical readout invariants, including failed and incorrect retrieval."""
import copy
import json
from pathlib import Path
import unittest
from syllabification import readout, for_live_result


class SyllabificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexicon = json.loads(Path('data/wwt_full_lexicon.json').read_text())

    def test_all_eight_sequences_and_stress(self):
        expected = {'Tasse': ['ta', 'se'], 'Tasche': ['ta', 'Se'],
                    'Kanne': ['ka', 'ne'], 'Katze': ['ka', 'tse'],
                    'Teller': ['tE', 'lEA'], 'Topf': ['tOpf'],
                    'Stuhl': ['Stuul'], 'Schrank': ['SraNk']}
        before = copy.deepcopy(self.lexicon)
        for word, forms in expected.items():
            with self.subTest(word=word):
                result = readout(self.lexicon, word)
                self.assertEqual([s['output_form'] for s in result['syllables']], forms)
                self.assertEqual([s['stressed'] for s in result['syllables']], [True] + [False]*(len(forms)-1))
                self.assertEqual([s['position'] for s in result['syllables']], list(range(1,len(forms)+1)))
                net = self.lexicon['phonology_network']
                self.assertEqual([s['lexical_node'] for s in result['syllables']], [t for r,t in net[result['root']]])
                for node in result['nodes']:
                    self.assertEqual([(e['relation'],e['target']) for e in result['edges'] if e['source']==node], [tuple(link) for link in net[node]])
                    self.assertTrue(all(t in result['nodes'] for _,t in net[node]))
        self.assertEqual(self.lexicon, before)

    def test_output_follows_retrieved_word_not_input(self):
        result = for_live_result(self.lexicon, dict(task='production', input='Kanne', winner='Tasse'))
        self.assertEqual(result['word'], 'Tasse')
        self.assertEqual([s['output_form'] for s in result['syllables']], ['ta','se'])

    def test_failed_retrieval_and_perception(self):
        result = for_live_result(self.lexicon, dict(task='production', input='Kanne', winner=None))
        self.assertEqual(result['status'], 'no_retrieval')
        self.assertEqual(result['syllables'], [])
        self.assertNotIn('graph_text', result)
        self.assertIsNone(for_live_result(self.lexicon, dict(task='perception', winner='Kanne')))

    def test_background_winner_has_graph_but_no_unaudited_sequence(self):
        result = readout(self.lexicon, 'Fressen')
        self.assertEqual(result['status'], 'unsupported')
        self.assertTrue(result['graph_text'])
        self.assertEqual(result['syllables'], [])

if __name__ == '__main__':
    unittest.main()
