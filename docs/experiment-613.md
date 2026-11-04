# 613-entry lab: validation snapshot, 2026-11-04

All eight visible words were correctly retrieved in both pathways, evaluated against all 613 candidates (16/16 undamaged runs). Full measured scores and timing are in `baseline_benchmark.json`. The unchanged seeds are vector 10, neural 11, ablation 2026; each simulation lasts 1.1 s. Target values are mean dot products over 0.45–0.70 s, not probabilities.

| Kanne production case | Remaining concept / C→L / lemma (%) | Phonological target value | Retrieved |
|---|---|---|---|
| Reference | 100 / 100 / 100 | 0.9729 | Kanne |
| Two buffers reduced | 50 / 100 / 50 | 0.5275 | Kanne |
| Memory at 70% | 50 / 70 / 50 | 0.2982 | Below threshold |
| Memory at 55% | 50 / 55 / 50 | 0.0007 | No retrieval |
| Lemma restored to 75% | 50 / 55 / 75 | 0.3248 | Kanne |

The three buffers still have 25,600 neurons each. Each associative memory has 100 neurons per entry, hence 61,300 neurons, for 199,400 neurons per pathway. This is not a fixed-total-neuron comparison with the eight-entry model. The larger memories also have different ablation masks and neural realizations; improvement cannot be attributed to vocabulary size alone.

All original eight vectors are bitwise unchanged. The concept graph contains 1,205 nodes, including 593 deep-layer nodes; one lexical root is already defined in the source deep layer. The phonology graph contains 1,616 nodes, including 1,003 deep-layer nodes. Deep nodes support the representations but are not extra retrieval candidates.

The nearest-neighbour analysis uses all 613 entries. It reflects the original WWT task-context associations, not an independently validated lexical similarity norm. For example, the source links Tasche to C_Automat_vis, explaining its neighbours Drehen and Druecken. This relationship is preserved. No concept or phonology pair had cosine similarity above 0.99 at seed 10.

The live interface still exposes only eight input words and eight rows per level. An incorrect retrieval of a background word can be reported, but no unknown IPA transcription is invented. Lemma vectors are independent; word-class grouping is deferred to a future experiment.

## Published cases and validation

Retrieval requires a mean target dot product above 0.30 and a margin above 0.10 against all 613 candidates. Case 2 is borderline for Kanne; Case 4 succeeds but is only 0.025 above the target threshold. These are fixed-seed demonstrations, not a general success rate for the full lexicon.

Case 3 fails for six of eight words; Tasse and Topf remain retrievable. Case 4 retrieves six of eight; Teller and Stuhl fail. The author accepted these word-dependent results and retained the settings. All per-word results are in the published manifest and the website's outcomes table.

All 56 published files were verified by HTTPS SHA-256 on 4 November 2026. Browser checks confirmed Kanne Case 3 failure, Case 4 retrieval, undamaged perception retrieval, both neighbour tables and the expanded outcomes table. All five Kanne production traces and its perception trace match the prior live recordings exactly.

The concept buffer, concept-to-lemma memory and lemma buffer follow dysfunction sites studied by Stille et al. (2020). Perception and comprehension play a role in the WWT framework; this demonstration focuses on word retrieval for production and does not replicate the paper's experimental conditions or results.
