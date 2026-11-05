# NEF-SPA mental lexicon: published 613-entry lab

Published model, 5 November 2026. This repository contains 613 lexical entries with dependency-complete semantic and phonological networks, spiking perception/production pathways, and reproducible neuron ablation. The live interface exposes only eight test words: Tasse, Tasche, Kanne, Katze, Teller, Topf, Stuhl, Schrank.

This repository contains the current 613-entry version published on speechtrainer.eu, including the live lab, neighbour matrices, five production cases, 48 neural recordings and the graph-based syllabification extension. The existing v0.1.0 release remains historical. There is no automatic deployment workflow. The original documentation is retained in [docs/eight-word-model.md](docs/eight-word-model.md).

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
- `syllabification.py`: graph readout, learned lexical order and explicit simplifications after accepted production retrieval.

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
- `website/lexicon-syllabification-20261105-upload-manifest.json`: SHA-256 hashes of the 54 current release files. The previous 56-file manifest and original neural recordings remain as provenance.

Preview the recorded lab with `python -m http.server 8768 --directory website/deploy`, then open http://localhost:8768/perception-production-model/. The scientific page retains links to the parent website and its shared stylesheet/navigation; those unrelated site resources are not bundled. The lab's brain illustrations use the original speechtrainer.eu image.

`export_demo.py --ui-only` rebuilds the player, neighbour JSON and stored-graph readouts from the existing neural recordings, without running Nengo. `export_demo.py` additionally recomputes all 48 runs via `export_ablation_runs.py`; rebuilding is not necessary to replay the archived version. Recalculation can produce environment-dependent numerical differences. For exact published traces use the bundled JSON files.

Remaining-neuron settings (concept / concept-to-lemma memory / lemma): 100/100/100, 50/100/50, 50/70/50, 50/55/50, 50/55/75. Vector seed 10, neural seed 11, ablation seed 2026. Case 3 fails for six of eight test words; Case 4 retrieves six of eight. See `docs/experiment-613.md` for exceptions and threshold interpretation.

Neighbour matrices show static similarities of undamaged stored pointers; ablation affects their neural processing, not these reference similarities. Public sliders are locked to the five cases, while the local live lab retains adjustable sliders.

The archived recordings retain their original source fingerprint. The portable dataset differs from the development dataset only in its source-directory metadata (local absolute path replaced by `2024_Dysfunctions/wwt`), so a new export has a different byte-level fingerprint without changing the model vectors.


## Stored-graph syllabification (5 November 2026)

The visible title remains **From sound to meaning. And back to words.**
The Concept-to-Phono Pathway now ends in a Syllabification panel: complete
reachable phonological graph, ordered lexical syllables, simplified output.
The readout follows the actual accepted winner, not the selected input.
Failed retrieval releases no graph or sequence. Background words can expose
their graph but have no unaudited syllable simplification.

Direct word-link order is interpreted as learned lexical knowledge. This is
not a measurement of neural syllable activation or temporal sequencing.
Original graph nodes, relations and vectors remain unchanged. First-syllable
final consonants are removed for Tasse, Tasche, Kanne, Katze and Teller;
second syllables stay unchanged, including Teller's lEA. Original model
symbols are retained, with e denoting schwa. The separate Phono-to-Gesture
player is not automatically connected to this lexical demo.

The `runs-613-syllabification-20261105` files extend the 48 original
`runs-613-20261104` recordings with lexical readouts. Every original field,
including all neural traces, decisions, recording dates and source fingerprints,
is preserved. Each new file also records the original file's SHA-256 and a
separate syllabification fingerprint. The fingerprint excludes local source
path metadata and covers the readout code, lexical entries and phonological
graph. Model builders, ablation, vectors and numerical readout were compared
with the previous published sources and are unchanged.

The public player contains no neural simulation API calls. Ablation sliders
remain locked to the five recorded cases; the local live lab supports new
calculations. Regression tests check all 48 records for unchanged observations
and correct winner-dependent readouts.
