# Herkunft und Lizenzstatus

Dieses Repository wurde nach den fachlichen Vorgaben von Bernd J. Kröger mit Unterstützung von ChatGPT erstellt (Stand: 3. November 2026).

Die Python-Dateien sind eine neue, reduzierte Implementierung. Es werden keine vollständigen historischen WWT-Skripte oder Publikations-PDFs verteilt.

`data/wwt_eight_words.json` enthält einen dependency-vollständigen Ausschnitt der Beziehungsdaten aus `2024_Dysfunctions/wwt`: `wwt_concepts.py`, `wwt_words.py` und `wwt_phonos.py`. Originalbezeichner, Quellindizes und SHA-256-Prüfsummen (einschließlich `run_wwt.py`) sind im JSON dokumentiert. Absolute lokale Pfade wurden entfernt; die Beziehungen wurden nicht verändert.

Der wissenschaftliche Ansatz basiert insbesondere auf Stille, Bekolay, Blouw und Kröger (2020), DOI: 10.3389/fpsyg.2020.01594, und Kröger (2023), DOI: 10.31083/j.jin2205124. Weitere Grundlagen stehen in der README.

In der geprüften lokalen WWT-Ablage wurde keine Lizenzdatei oder ausdrückliche Lizenzangabe gefunden. Dieses öffentliche Repository erhält daher vorerst keine pauschale Open-Source-Lizenz. Die Veröffentlichung ist keine Behauptung, dass alle Bestandteile beliebig weiterverwendet oder neu lizenziert werden dürfen. Eine ausdrückliche Lizenzierung kann nach Klärung der Rechte ergänzt werden. Die externen Python-Abhängigkeiten unterliegen ihren jeweiligen eigenen Lizenzen.

## Development branch: 613 entries (2026-11-04)

`data/wwt_full_lexicon.json` extends the dependency-complete extraction to 613 word entries. All required concept and phonology dependencies are included. Thirteen missing phonological mappings were restored from existing definitions with the author’s approval; Verbringen uses the existing P_fEA component in place of P_EA. The JSON records each correction and source hashes. Absolute local paths are omitted. The eight-word fixture is retained unchanged. The previous license-status statement also applies to this development snapshot.
