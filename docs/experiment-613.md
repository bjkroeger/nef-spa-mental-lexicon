# 613-entry lab: validation snapshot, 2026-11-04

All eight visible words were correctly retrieved in both pathways, evaluated against all 613 candidates (16/16 undamaged runs). Full measured scores and timing are in `baseline_benchmark.json`. The unchanged seeds are vector 10, neural 11, ablation 2026; each simulation lasts 1.1 s. Target values are mean dot products over 0.45–0.70 s, not probabilities.

| Kanne production case | Remaining concept / C→L / lemma (%) | Phonological target value | Retrieved |
|---|---|---|---|
| Reference | 100 / 100 / 100 | 0.9729 | Kanne |
| Two buffers reduced | 50 / 100 / 50 | 0.5275 | Kanne |
| Memory at 90% | 50 / 90 / 50 | 0.5296 | Kanne |
| Memory at 80% | 50 / 80 / 50 | 0.4110 | Kanne |
| Lemma restored to 75% | 50 / 80 / 75 | 0.6355 | Kanne |

The three buffers still have 25,600 neurons each. Each associative memory has 100 neurons per entry, hence 61,300 neurons, for 199,400 neurons per pathway. This is not a fixed-total-neuron comparison with the eight-entry model. The larger memories also have different ablation masks and neural realizations; improvement cannot be attributed to vocabulary size alone.

All original eight vectors are bitwise unchanged. The concept graph contains 1,205 nodes, including 593 deep-layer nodes; one lexical root is already defined in the source deep layer. The phonology graph contains 1,616 nodes, including 1,003 deep-layer nodes. Deep nodes support the representations but are not extra retrieval candidates.

The nearest-neighbour analysis uses all 613 entries. It reflects the original WWT task-context associations, not an independently validated lexical similarity norm. For example, the source links Tasche to C_Automat_vis, explaining its neighbours Drehen and Druecken. This relationship is preserved. No concept or phonology pair had cosine similarity above 0.99 at seed 10.

The live interface still exposes only eight input words and eight rows per level. An incorrect retrieval of a background word can be reported, but no unknown IPA transcription is invented. Lemma vectors are independent; word-class grouping is deferred to a future experiment.
