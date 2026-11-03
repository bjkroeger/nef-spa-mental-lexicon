"""Generate labelled matrices, CSVs, vector data and multi-seed checks."""
import argparse
import csv
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).parent / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from lexicon_vectors import load_data, representations, similarity_matrices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dimensions', type=int, default=512)
    parser.add_argument('--seed', type=int, default=10)
    parser.add_argument('--repeats', type=int, default=100)
    args = parser.parse_args()
    if args.dimensions < 2 or args.repeats < 2:
        parser.error('dimensions and repeats must be at least 2')
    data = load_data()
    words = [e['word'] for e in data['entries']]
    matrices = similarity_matrices(data, args.dimensions, args.seed)
    out = Path(__file__).parent / 'results' / f'd{args.dimensions}_seed{args.seed}'
    out.mkdir(parents=True, exist_ok=True)
    np.savez(out / 'vectors.npz', **representations(data, args.dimensions, args.seed))
    for level, matrix in matrices.items():
        with (out / f'{level}.csv').open('w') as f:
            writer = csv.writer(f)
            writer.writerow(['Wort'] + words)
            writer.writerows([[word] + list(row) for word, row in zip(words, matrix)])

    fig, axes = plt.subplots(1, 3, figsize=(17, 6), layout='constrained')
    titles = ['Konzepte', 'Lemmata', 'Phonologische Formen']
    for ax, (level, matrix), title in zip(axes, matrices.items(), titles):
        im = ax.imshow(matrix, vmin=-1, vmax=1, cmap='RdBu_r')
        ax.set_xticks(range(8), words, rotation=45, ha='right', fontsize=10)
        ax.set_yticks(range(8), words, fontsize=10)
        ax.set_title(title, fontsize=15, pad=14, weight='bold')
        for i in range(8):
            for j in range(8):
                ax.text(j, i, f'{matrix[i,j]:.2f}', ha='center', va='center', fontsize=9,
                        color='white' if abs(matrix[i,j]) > .65 else '#172536')
    fig.colorbar(im, ax=axes, shrink=.65, label='Kosinusähnlichkeit (normierte Vektoren)')
    fig.suptitle(f'Mentales Lexikon · rekursive WWT-Kodierung\n8 Wörter · {args.dimensions} Dimensionen · Seed {args.seed} · keine neuronale Simulation', fontsize=16)
    fig.savefig(out / 'similarity_matrices.png', dpi=180)
    fig.savefig(out / 'similarity_matrices.svg')
    plt.close(fig)

    runs = [similarity_matrices(data, args.dimensions, seed) for seed in range(args.repeats)]
    summary = dict(dimensions=args.dimensions, seed=args.seed, repeats=args.repeats,
                   robustness_seeds=list(range(args.repeats)), words=words, levels={})
    for level in matrices:
        values = np.array([run[level] for run in runs])
        summary['levels'][level] = dict(single=matrices[level].tolist(),
                                        mean=values.mean(axis=0).tolist(), sd=values.std(axis=0, ddof=1).tolist())
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    for a,b,level in [('Tasse','Kanne','concept'),('Tasse','Teller','concept'),('Stuhl','Schrank','concept'),('Tasse','Tasche','phonology'),('Kanne','Katze','phonology')]:
        i,j=words.index(a),words.index(b)
        s=summary['levels'][level]
        print(f'{level}: {a}–{b}: {s["single"][i][j]:.3f}; {args.repeats} seeds mean {s["mean"][i][j]:.3f}, SD {s["sd"][i][j]:.3f}')
    print(out)


if __name__ == '__main__':
    main()
