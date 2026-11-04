# NEF-SPA mental lexicon: experimental 613-entry lab

Development snapshot, 4 November 2026. This branch contains 613 lexical entries with dependency-complete semantic and phonological networks, spiking perception/production pathways, and reproducible neuron ablation. The live interface exposes only eight test words: Tasse, Tasche, Kanne, Katze, Teller, Topf, Stuhl, Schrank.

The published website and existing v0.1.0 release are unchanged. This branch contains no deployment scripts or workflows. The original documentation is retained in [docs/eight-word-model.md](docs/eight-word-model.md).

## Run the live lab

Requires Python 3.13 or later. Tested with the pinned dependencies, including Nengo 4.1.0 and NengoSPA 2.0.0.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
OPENBLAS_NUM_THREADS=1 .venv/bin/python demo_server.py
```

Open http://127.0.0.1:8765/. The server binds only to localhost. On macOS, `Lexikon-Labor.command` can also start the lab. Sliders specify remaining neurons (100–0%); labels also show ablation. Five production presets retain the selected word, with explanations referring to Kanne. An uncached run took about 40 seconds on the development machine; repeated requests reuse a session cache.

## Data and model

- `data/wwt_full_lexicon.json`: 613 entries, 1,205 concept nodes and 1,616 phonology nodes, source indices/hashes and 13 audited phonological corrections.
- `data/wwt_eight_words.json`: unchanged historical fixture.
- `lexicon_vectors.py`: recursive relation binding and stable per-node vectors; the eight historical vectors remain exactly unchanged.
- `production.py`, `perception.py`: all 613 entries compete in both associative memories. The live retrieval decision checks the entire lexicon.
- `ablation.py`: nested reproducible masks, applied after decoder construction without refitting.
- `demo_server.py`, `demo/`: local server and interface.

Each pathway has 199,400 LIF neurons. Buffer sizes are unchanged, but associative memories grow linearly with the entry count. This comparison does not hold the total neural budget constant. Lemma-level word-class grouping has not yet been added. See [measured results and interpretation](docs/experiment-613.md).

## Tests and analyses

The bundled data suffice for running the lab and ordinary tests; historical WWT sources are not required.

```sh
.venv/bin/python -m unittest discover -v
.venv/bin/python analyze_full_lexicon.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python benchmark_full_lexicon.py
```

The analysis creates a PNG/SVG showing five nearest semantic and phonological neighbours for each test word and a JSON audit in `results/lexicon613/`. The benchmark resets the simulator between inputs and checks all 16 undamaged retrievals against all 613 candidates. Results and large recordings are generated locally and ignored by Git. A compact measured report is included in `docs/baseline_benchmark.json`.

Two source-fidelity tests are optional. If you possess the original WWT files:

```sh
WWT_SOURCE_DIR=/path/to/2024_Dysfunctions/wwt .venv/bin/python -m unittest discover -v
.venv/bin/python extract_wwt.py --full --source /path/to/2024_Dysfunctions/wwt
```

Extraction parses data assignments without importing or modifying the original scripts. Corrections are explicitly recorded rather than inferred by fuzzy matching.

## Scientific basis and provenance

- Stille, Bekolay, Blouw & Kröger (2020): https://doi.org/10.3389/fpsyg.2020.01594
- Kröger (2023): https://doi.org/10.31083/j.jin2205124

See [PROVENANCE.md](PROVENANCE.md) for provenance and license status. Developed under the scientific direction of Bernd J. Kröger with assistance from ChatGPT.
