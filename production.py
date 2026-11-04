"""Unlesioned concept -> lemma -> phonology task with spiking LIF neurons."""
import json
import os
from pathlib import Path
import time

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).parent / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nengo
import nengo_spa as spa
import numpy as np

from lexicon_vectors import load_lexicon, representations

OUT = Path(__file__).parent / 'results' / 'lexicon613' / 'production_kanne'


def build_model(word='Kanne'):
    data = load_lexicon()
    vectors = representations(data, dimensions=512, seed=10)
    words = [e['word'] for e in data['entries']]
    target = words.index(word)
    display_words = data['display_words']
    display_indices = [words.index(w) for w in display_words]
    if word not in display_words:
        raise ValueError('Choose one of the eight display words')
    vocabs = {}
    for level, values in vectors.items():
        vocab = spa.Vocabulary(512, strict=True)
        for i, vector in enumerate(values):
            # SPA identifiers are ASCII-only; labels such as Straße stay external.
            vocab.add(f'Entry{i}', spa.SemanticPointer(vector))
        vocabs[level] = vocab
    with spa.Network(seed=11, label=f'Ungeschaedigte Produktion: {word}') as model:
        model.config[nengo.Ensemble].neuron_type = nengo.LIF()
        states = {level: spa.State(vocab=vocab, subdimensions=1,
                                  neurons_per_dimension=50, feedback=0,
                                  represent_cc_identity=False, label=level)
                  for level, vocab in vocabs.items()}
        model.stimulus_index = target
        stimulus = nengo.Node(lambda t: vectors['concept'][model.stimulus_index] if .15 <= t < .75 else np.zeros(512), label=f'Konzeptueller Input {word}')
        nengo.Connection(stimulus, states['concept'].input, synapse=.01)
        # WWT production uses competitive cleanup at the concept-to-lemma step.
        c2l = spa.WTAAssocMem(threshold=.3, input_vocab=vocabs['concept'],
                             output_vocab=vocabs['lemma'], mapping='by-key',
                             n_neurons=100, function=lambda x: 1.,
                             label='Konzept zu Lemma: WTA')
        l2p = spa.ThresholdingAssocMem(threshold=.3, input_vocab=vocabs['lemma'],
                                     output_vocab=vocabs['phonology'], mapping='by-key',
                                     n_neurons=100, label='Lemma zu Phonologie')
        for source, dest in [(states['concept'].output, c2l.input),
                             (c2l.output, states['lemma'].input),
                             (states['lemma'].output, l2p.input),
                             (l2p.output, states['phonology'].input)]:
            nengo.Connection(source, dest, synapse=.01)
        probes = {level: nengo.Probe(state.output, synapse=.02) for level, state in states.items()}
        probes['lemma_entries'] = nengo.Probe(c2l.selection.output[display_indices], synapse=.02)
        # These are the selected mappings keyed by lemma, not phonological-buffer similarities.
        probes['phonology_entries'] = nengo.Probe(l2p.selection.output[display_indices], synapse=.02)
        # Probe only the displayed populations; all 613 populations participate.
        for label, memory in [('c2l', c2l), ('l2p', l2p)]:
            for i, ens in enumerate(memory.selection.thresholding.ensembles):
                if i in display_indices:
                    probes[f'spikes_{label}_{display_indices.index(i)}'] = nengo.Probe(ens.neurons)
    # Component references for optional post-build ablation in the live lab.
    model.ablation_targets = {f'production_{level}': state for level, state in states.items()}
    model.ablation_targets.update({'production_c2l': c2l, 'production_l2p': l2p})
    model.lexicon_words = words
    model.lexicon_vectors = vectors
    model.lexicon_entries = data['entries']
    model.display_indices = display_indices
    return (model, probes, display_words,
            {level: values[display_indices] for level, values in vectors.items()},
            display_words.index(word))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    nengo.rc.set('decoder_cache', 'enabled', 'False')
    started = time.monotonic()
    model, probes, words, vectors, target = build_model()
    neuron_count = sum(e.n_neurons for e in model.all_ensembles)
    assert all(isinstance(e.neuron_type, nengo.LIF) for e in model.all_ensembles)
    print(f'Built architecture: {neuron_count} LIF neurons; no lesions.', flush=True)
    with nengo.Simulator(model, dt=.001, progress_bar=False) as sim:
        print('Simulator ready. Running 1.1 seconds...', flush=True)
        sim.run(1.1)
        times = sim.trange()
        recordings = {name: sim.data[probe].copy() for name, probe in probes.items()}
    similarities = {level: recordings[level] @ vec.T for level, vec in vectors.items()}
    steady = (times >= .45) & (times < .70)
    baseline = (times >= .05) & (times < .14)
    late = (times >= 1.) & (times <= 1.1)
    mean_phonology = recordings['phonology'][steady].mean(axis=0)
    target_vector = vectors['phonology'][target]
    amplitude = float(mean_phonology @ target_vector)
    predicted = amplitude * (vectors['phonology'] @ target_vector)
    observed = similarities['phonology'][steady].mean(axis=0)
    spike_counts = {k: int(round(v.sum() * .001)) for k, v in recordings.items() if k.startswith('spikes_')}
    report = dict(task='complete concept Kanne -> lemma -> phonology',
                  dimensions=512, vector_seed=10, neural_seed=11,
                  input_on=.15, input_off=.75, duration=1.1, dt=.001,
                  probe_lowpass=.02, steady_window=[.45,.70],
                  neurons=neuron_count, neuron_type='LIF', lesions=False,
                  elapsed_seconds=time.monotonic()-started, words=words,
                  mean_similarities={k: v[steady].mean(axis=0).tolist() for k,v in similarities.items()},
                  mean_entry_activations={k: recordings[k][steady].mean(axis=0).tolist() for k in ['lemma_entries','phonology_entries']},
                  peak_entry_activations={k: recordings[k].max(axis=0).tolist() for k in ['lemma_entries','phonology_entries']},
                  baseline_phonology_similarity=similarities['phonology'][baseline].mean(axis=0).tolist(),
                  late_phonology_similarity=similarities['phonology'][late].mean(axis=0).tolist(),
                  pure_kanne_prediction=predicted.tolist(),
                  phonology_similarity_residual=(observed-predicted).tolist(),
                  phonology_vector_relative_residual=float(np.linalg.norm(mean_phonology-amplitude*target_vector)/np.linalg.norm(mean_phonology)),
                  selection_spike_counts=spike_counts)
    full_scores = model.lexicon_vectors['phonology'] @ recordings['phonology'][steady].mean(axis=0)
    report['lexicon_size'] = len(model.lexicon_words)
    report['lexicon_winner'] = model.lexicon_words[int(np.argmax(full_scores))]
    assert report['lexicon_winner'] == words[target]
    # Outcome checks target actual lexical transfer, not merely graph construction.
    for level in ['lemma','phonology']:
        assert int(np.argmax(report['mean_similarities'][level])) == target, level
        assert report['mean_similarities'][level][target] > .7, level
    assert sum(spike_counts.values()) > 0
    (OUT/'summary.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    np.savez_compressed(OUT/'recordings.npz', time=times, **recordings)
    np.savetxt(OUT/'phonology_similarities.csv', np.column_stack([times, similarities['phonology']]), delimiter=',', header=','.join(['time_s']+words), comments='')
    colors = ['#147d92','#9a8e00','#111111','#c83452','#5578b4','#dd7b27','#7a559c','#5c8d5d']
    fig, axes = plt.subplots(5,1,figsize=(13,14),sharex=True,layout='constrained')
    panels = [('Konzeptpuffer · Skalarprodukt',similarities['concept']),
              ('Konzept → Lemma · Eintragsausgänge nach Wettbewerb',recordings['lemma_entries']),
              ('Lemma-Puffer · Skalarprodukt',similarities['lemma']),
              ('Lemma → Phonologie · Eintragsausgänge',recordings['phonology_entries']),
              ('Phonologischer Puffer · Skalarprodukt',similarities['phonology'])]
    for ax,(title,values) in zip(axes,panels):
        ax.axvspan(.15,.75,color='#dce8ef',alpha=.55)
        for i,word in enumerate(words):
            ax.plot(times,values[:,i],label=word,color=colors[i],lw=2 if i==target else 1.3,alpha=.95)
        ax.set_title(title,loc='left',fontsize=12,weight='bold')
        ax.set_ylim(-.2,1.3);ax.grid(alpha=.2);ax.set_ylabel('Ausgabewert')
    axes[0].legend(ncol=8,loc='upper center',fontsize=9)
    axes[-1].set_xlabel('Simulationszeit (s) · blau hinterlegt: vollständiger Input Kanne')
    fig.suptitle('Erster neuronaler Produktionsversuch: Kanne\nUngeschädigt · 512 Dimensionen · LIF-Neuronen · geglättete Ausgaben (20 ms)',fontsize=16)
    fig.savefig(OUT/'production_traces.png',dpi=150)
    fig.savefig(OUT/'production_traces.svg')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
    x=np.arange(len(words))
    ax.bar(x-.18,observed,.36,label='Neuronales Ergebnis',color='#147d92')
    ax.bar(x+.18,predicted,.36,label='Erwartung aus reinem Kanne-Pointer, amplitudenangepasst',color='#c5a868')
    ax.set_xticks(x,words);ax.set_ylabel('Mittleres Skalarprodukt');ax.set_ylim(-.15,1.25)
    ax.set_title('Phonologischer Ausgang: Vektorüberlappung oder zusätzliche Aktivierung?\nMittelwert 0,45–0,70 s')
    ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.savefig(OUT/'phonology_comparison.png',dpi=180);plt.close(fig)
    print(json.dumps({k:report[k] for k in ['neurons','elapsed_seconds','mean_similarities','mean_entry_activations','phonology_vector_relative_residual']},indent=2))


if __name__=='__main__':
    main()
