"""Compact nearest-neighbour plot and full similarity audit; no neural simulation."""
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).parent / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from lexicon_vectors import load_data, load_lexicon, representations

OUT = Path(__file__).parent / 'results' / 'lexicon613'


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    data = load_lexicon()
    vectors = representations(data)
    words = [e['word'] for e in data['entries']]
    visible = data['display_words']
    indices = [words.index(w) for w in visible]
    old = representations(load_data())
    report = dict(lexical_entries=len(words), network_counts=data['network_counts'],
                  dimensions=512, vector_seed=10, phonology_repairs=data['phonology_repairs'],
                  preserved_display_vectors={k: bool(np.array_equal(v[indices], old[k]))
                                             for k, v in vectors.items()}, levels={})
    fig, axes = plt.subplots(1, 2, figsize=(16, 8.7))
    for ax, level, title in zip(axes, ('concept', 'phonology'),
                               ('Semantic neighbours', 'Phonological neighbours')):
        matrix = vectors[level] @ vectors[level].T
        pair_values = matrix[np.triu_indices(len(words), 1)]
        ranked = matrix.copy()
        np.fill_diagonal(ranked, -np.inf)
        neighbours = np.argsort(ranked[indices], axis=1)[:, -5:][:, ::-1]
        scores = np.take_along_axis(matrix[indices], neighbours, axis=1)
        nearest = {word: [dict(word=words[j], similarity=float(matrix[i, j])) for j in ns]
                   for word, i, ns in zip(visible, indices, neighbours)}
        report['levels'][level] = dict(nearest_neighbours=nearest,
            pair_similarity_quantiles={str(q): float(np.quantile(pair_values, q)) for q in (0, .5, .9, .99, 1)},
            pairs_above_099=int(np.count_nonzero(pair_values > .99)))
        im = ax.imshow(scores, cmap='YlGnBu', vmin=0, vmax=1, aspect='auto')
        ax.set_title(title, fontsize=16, loc='left', pad=18)
        ax.set_xticks(range(5), ['1st', '2nd', '3rd', '4th', '5th'])
        ax.xaxis.tick_top()
        ax.set_yticks(range(8), visible, fontsize=11)
        ax.tick_params(length=0, pad=8)
        for row in range(8):
            for col in range(5):
                name = words[neighbours[row, col]]
                ax.text(col, row, f'{name}\n{scores[row, col]:.3f}', ha='center', va='center',
                        fontsize=9, color='white' if scores[row, col] > .57 else '#172b3a',
                        weight='bold' if name in visible else 'normal')
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle('Eight test words in a lexicon of 613 entries', fontsize=21, x=.055, ha='left', y=.98)
    fig.subplots_adjust(left=.065, right=.91, bottom=.12, top=.85, wspace=.22)
    cax = fig.add_axes([.935, .23, .012, .49])
    fig.colorbar(im, cax=cax, label='Cosine similarity')
    fig.text(.055, .035, 'Five nearest other entries per word · searched across all 613 words · bold: one of the eight test words\n'
             'Recursive WWT semantic pointers · 512 dimensions · seed 10 · similarities, not neural activations or probabilities',
             fontsize=10, color='#415466')
    fig.savefig(OUT / 'nearest_neighbours.png', dpi=160)
    fig.savefig(OUT / 'nearest_neighbours.svg')
    plt.close(fig)
    (OUT / 'network_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('lexical_entries', 'network_counts', 'preserved_display_vectors')}, indent=2))


if __name__ == '__main__':
    main()
