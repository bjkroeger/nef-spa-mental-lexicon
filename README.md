# NEF-SPA mental lexicon: published 613-entry lab

Development snapshot, 4 November 2026. This branch contains 613 lexical entries with dependency-complete semantic and phonological networks, spiking perception/production pathways, and reproducible neuron ablation. The live interface exposes only eight test words: Tasse, Tasche, Kanne, Katze, Teller, Topf, Stuhl, Schrank.

This branch archives the 613-entry version published on speechtrainer.eu on 4 November 2026, including the live lab, neighbour matrices, five production cases and 48 exact public recordings. The existing v0.1.0 release remains historical. There is no automatic deployment workflow. The original documentation is retained in [docs/eight-word-model.md](docs/eight-word-model.md).

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

The analysis creates a PNG/SVG showing five nearest semantic and phonological neighbours for each test word and a JSON audit in `results/lexicon613/`. The benchmark resets the simulator between inputs and checks all 16 undamaged retrievals against all 613 candidates. Analysis results are generated locally and ignored by Git; the 48 published recordings are explicitly tracked under `website/deploy/`. A compact measured report is included in `docs/baseline_benchmark.json`.

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

## Published snapshot

- [Lexicon Lab](https://speechtrainer.eu/perception-production-model/)
- [Scientific documentation](https://speechtrainer.eu/nef-spa-lexical-model.htm)
- `website/deploy/`: exact published HTML, versioned player assets, neighbour data, figures and 48 neural recordings (eight undamaged perception runs plus five production cases for eight words).
- `website/lexicon613-upload-manifest.json`: SHA-256 hashes of all 56 release files, verified against public HTTPS downloads.

Preview the recorded lab with `python -m http.server 8768 --directory website/deploy`, then open http://localhost:8768/perception-production-model/. The scientific page retains links to the parent website and its shared stylesheet/navigation; those unrelated site resources are not bundled. The lab's brain illustrations use the original speechtrainer.eu image.

`export_demo.py --ui-only` rebuilds the player and neighbour JSON. `export_demo.py` additionally recomputes all 48 runs via `export_ablation_runs.py`; rebuilding is not necessary to replay the archived version. Recalculation can produce environment-dependent numerical differences. For exact published traces use the bundled JSON files.

Remaining-neuron settings (concept / concept-to-lemma memory / lemma): 100/100/100, 50/100/50, 50/70/50, 50/55/50, 50/55/75. Vector seed 10, neural seed 11, ablation seed 2026. Case 3 fails for six of eight test words; Case 4 retrieves six of eight. See `docs/experiment-613.md` for exceptions and threshold interpretation.

Neighbour matrices show static similarities of undamaged stored pointers; ablation affects their neural processing, not these reference similarities. Public sliders are locked to the five cases, while the local live lab retains adjustable sliders.

The archived recordings retain their original source fingerprint. The portable dataset differs from the development dataset only in its source-directory metadata (local absolute path replaced by `2024_Dysfunctions/wwt`), so a new export has a different byte-level fingerprint without changing the model vectors.
