"""Checks actual spiking silence, independent masks and complete lexical runs."""
import unittest
import numpy as np
import nengo
from ablation import COMPONENTS, normalize_ablation, neuron_mask, apply_ablation


class AblationTests(unittest.TestCase):
    def test_validation(self):
        for bad in ({'other': 1}, {'production_concept': -1},
                    {'production_concept': 101}, {'production_concept': float('nan')},
                    {'production_concept': True}, {'production_concept': '50'}, []):
            with self.assertRaises(ValueError):
                normalize_ablation(bad)
        self.assertEqual(len(normalize_ablation()), 10)

    def test_nested_masks(self):
        for key in COMPONENTS:
            small = neuron_mask(key, 800, 25)
            large = neuron_mask(key, 800, 50)
            self.assertEqual(small.sum(), 200)
            self.assertTrue(np.all(large[small]))
            np.testing.assert_array_equal(small, neuron_mask(key, 800, 25))
        self.assertFalse(np.array_equal(neuron_mask(COMPONENTS[0],800,50), neuron_mask(COMPONENTS[1],800,50)))

    def test_actual_spikes_and_combination(self):
        with nengo.Network(seed=11) as model:
            targets={}; probes={}
            for key in COMPONENTS:
                with nengo.Network() as net:
                    e=nengo.Ensemble(100,1,encoders=np.ones((100,1)))
                    nengo.Connection(nengo.Node([1]),e,synapse=None)
                    probes[key]=nengo.Probe(e.neurons)
                targets[key]=net
        values={key: [0,25,50,100][i%4] for i,key in enumerate(COMPONENTS)}
        with nengo.Simulator(model,progress_bar=False) as sim:
            report=apply_ablation(sim,targets,values)
            sim.run(.1)
            for key in COMPONENTS:
                mask=neuron_mask(key,100,values[key])
                self.assertEqual(report[key]['ablated'], int(mask.sum()))
                self.assertTrue(np.all(sim.data[probes[key]][:,mask]==0), key)
                if (~mask).any():
                    self.assertGreater(sim.data[probes[key]][:,~mask].sum(),0,key)


if __name__ == '__main__':
    unittest.main()
