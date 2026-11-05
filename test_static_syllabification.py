"""Verify that the static readout preserves the recorded neural evidence."""
import hashlib
import json
from pathlib import Path
import unittest

from syllabification import for_live_result

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'website/deploy/perception-production-model'
VERSION = '613-syllabification-20261105'


class StaticSyllabificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexicon = json.loads((ROOT / 'data/wwt_full_lexicon.json').read_text())
        cls.manifest = json.loads((PUBLIC / f'manifest-{VERSION}.json').read_text())

    def test_all_recorded_observations_are_preserved(self):
        self.assertEqual(len(self.manifest['recordings']), 48)
        for item in self.manifest['recordings']:
            with self.subTest(file=item['file']):
                original = (PUBLIC / 'runs-613-20261104' / item['file']).read_bytes()
                result = json.loads((PUBLIC / f'runs-{VERSION}' / item['file']).read_text())
                for key, value in json.loads(original).items():
                    self.assertEqual(result[key], value, key)
                self.assertEqual(result['neural_recording_sha256'], hashlib.sha256(original).hexdigest())
                self.assertEqual(result['presentation_version'], VERSION)

    def test_readout_follows_actual_retrieval_in_every_case(self):
        failures = 0
        for item in self.manifest['recordings']:
            result = json.loads((PUBLIC / f'runs-{VERSION}' / item['file']).read_text())
            self.assertEqual(result['syllabification'], for_live_result(self.lexicon, result))
            if result['task'] == 'production' and result['winner'] is None:
                failures += 1
                self.assertEqual(result['syllabification']['syllables'], [])
                self.assertNotIn('graph_text', result['syllabification'])
        self.assertGreater(failures, 0)

    def test_static_ui_exposes_readouts_without_simulation_api(self):
        js = (PUBLIC / f'app-{VERSION}.js').read_text()
        html = (PUBLIC / 'index.html').read_text()
        self.assertNotIn('/api/', js)
        self.assertNotIn('calculationFeedback', js + html)
        self.assertIn("panel.hidden = task !== 'production';", js)
        self.assertIn('From sound to meaning.<br><em>And back to words.</em>', html)
        self.assertIn('no simulation runs on the web server', html)
        self.assertIn('data-mode="recorded"', html)


if __name__ == '__main__':
    unittest.main()
