# Mentaler Lexikonkern: acht Wörter

Stand: 3. November 2026. Stufe 1 erzeugt Semantic-Pointer-Vektoren und Ähnlichkeitsmatrizen. Stufe 2 (`perception.py`) implementiert einen ersten ungeschädigten neuronalen Wahrnehmungsversuch. Stufe 3 (`production.py`) ergänzt den entsprechenden Produktionsversuch. Die Vektoranalyse startet weiterhin keine neuronalen Simulationen.

Wörter: Tasse, Tasche, Kanne, Katze, Teller, Topf, Stuhl, Schrank.

## Herkunft und Dokumentation

Entwickelt nach den fachlichen Vorgaben von Bernd J. Kröger mit Unterstützung von ChatGPT. Diese Python-Implementierung ist eine neue, reduzierte Umsetzung des bestehenden Modellansatzes.

[Dokumentation mit allen Abbildungen auf speechtrainer.eu](https://www.speechtrainer.eu/nef-spa-model.htm)

Die mitgelieferten Beziehungsdaten stammen aus der vorhandenen WWT-Implementierung. Siehe [PROVENANCE.md](PROVENANCE.md) zur Herkunft und zum noch offenen Lizenzstatus. Es wird derzeit keine pauschale Open-Source-Lizenz vergeben.

## Wissenschaftliche Grundlage

- Kröger (2023), primäre Grundlage des Gesamtmodells: https://doi.org/10.31083/j.jin2205124
- Stille, Bekolay, Blouw, Kröger (2020), mentales Lexikon: https://doi.org/10.3389/fpsyg.2020.01594
- Kröger, Crawford, Bekolay, Eliasmith (2016), Unterscheidung zwischen Semantic-Pointer-Netz und neuronalem Netz: https://doi.org/10.3389/fncom.2016.00051
- Crawford, Gingerich, Eliasmith (2016), strukturierte Wissensrepräsentation: https://doi.org/10.1111/cogs.12261

## Erhaltene WWT-Kodierung

Für jeden Knoten x gilt:

    v(x) = normalize(b(x) + sum(r(Relation) ⊛ v(Zielknoten)))

`b(x)` ist ein zufälliger Einheitsvektor als Eigenanteil, `r` ein zufälliger Einheitsvektor für die Relation, `⊛` die zirkuläre Faltung. Jeder Zielvektor wird nach derselben Regel berechnet, bevor er in den übergeordneten Knoten eingeht. Blätter haben keine ausgehenden Beziehungen und bestehen aus ihrem Eigenanteil. Jeder Knoten wird nach der Addition normiert.

Dies erhält die rekursive WWT-Variante mit `use_id_vecs=False`. Separate, von den Zielrepräsentationen unabhängige Identitätsvektoren werden nicht eingesetzt. Die Relationen `AssocWith` und `InclPhon`, alle ausgewählten Knoten und sämtliche transitiv benötigten Zielknoten bleiben unverändert. Der Ausschnitt umfasst 16 Konzeptknoten und 41 phonologische Knoten. Lemmata erhalten unabhängige Zufallsvektoren wie im WWT-Ansatz; grammatische Merkmale werden in dieser Stufe nicht ergänzt.

Die acht Wörter wurden über den gemeinsamen Index der ursprünglichen Konzept-, Wort- und Phonologielisten zugeordnet. `data/wwt_eight_words.json` dokumentiert Originalnamen, Quellindizes, relative Herkunftsangaben und SHA-256-Prüfsummen. Die Originaldateien wurden nicht verändert.

## Bewusste Unterschiede zum alten Lauf

- Hauptdarstellung mit 512 Dimensionen; der vorgefundene WWT-Start verwendete 64. Eine zusätzliche Auswertung mit 64 Dimensionen liegt ebenfalls unter `results`.
- Die zufälligen Basis- und Relationsvektoren werden deterministisch pro Knoten, Ebene und Seed erzeugt. Dadurch ändern sich gemeinsame Vektoren nicht, wenn unbeteiligte Wörter hinzugefügt oder entfernt werden. Im alten WWT-Code wurde `SemanticPointer(D)` ohne den lokalen Zufallsgenerator aufgerufen; der Modell-Seed kontrollierte deshalb nicht sämtliche Zufallsanteile.
- Der neue Zufallszahlengenerator und die Zuweisung seiner Streams unterscheiden sich vom alten Vokabular-Generator. Es handelt sich um dieselbe rekursive Konstruktionsregel und unveränderte Beziehungsdaten, **nicht** um eine bitgenaue Reproduktion historischer Vektoren oder publizierter Ergebnisse. Die damalige Vokabular-Erzeugung mit eventueller Zurückweisung zu ähnlicher Zufallsvektoren wird nicht nachgebildet.
- Keine Ablation, keine WWT-Aufgabensteuerung, kein Simulator-Pickling.

## Ergebnisse lesen

Die Matrizen zeigen Skalarprodukte normierter Vektoren, also Kosinusähnlichkeiten. Die Diagonale ist 1. Werte nahe 0 bedeuten geringe Vektorähnlichkeit; kleine negative Werte sind keine semantischen Gegensätze und keine neuronale Hemmung. Werte sind keine Wahrscheinlichkeiten und keine Aktivierungsverläufe.

Semantische Überschneidungen entstehen u.a. durch `C_Henkel_vis` (Tasse/Kanne/Topf), `C_Geschirr_vis` (Tasse/Teller), `C_Moebel_vis` (Stuhl/Schrank). Die Phonologie übernimmt die ursprüngliche hierarchische Zerlegung: Tasse/Tasche teilen `P_St_ta`, Kanne/Katze `P_St_ka`. Auch weitere Wörter teilen tiefere Bestandteile, etwa einen Anlaut. Diese Struktur ist keine nachträglich gesetzte Ähnlichkeitstabelle und kein universelles phonetisches Distanzmaß.

Ein einzelner Seed enthält Zufallsschwankungen. `summary.json` enthält deshalb zusätzlich Mittelwerte und Standardabweichungen über Seeds 0–99. Diese Streuung beschreibt die Vektorkonstruktion, keine Messung menschlichen Verhaltens. Der dargestellte Seed 10 wurde vor der Auswertung gewählt.

## Ausführen

Die isolierte Projektumgebung verwendet CPython 3.13, Nengo 4.1.0 und NengoSPA 2.0.0. NengoSPA liefert die Vektoroperationen sowie die Zustände und assoziativen Speicher der neuronalen Experimente. Die tatsächlich installierten Paketversionen stehen in `requirements.lock.txt`.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python plot_similarities.py
.venv/bin/python plot_similarities.py --dimensions 64
.venv/bin/python -m unittest -v
```

Die Darstellung benötigt kein Notebook und keinen Browser. PNG und SVG sowie CSV-Matrizen, NPZ-Vektoren und JSON-Statistiken werden unter `results/d512_seed10` bzw. `results/d64_seed10` gespeichert. Die Analyse funktioniert mit dem beigefügten Datenausschnitt ohne Zugriff auf die alten Dateien.

`extract_wwt.py` wird nur benötigt, um den Ausschnitt aus der ursprünglichen Ablage neu zu erzeugen. Ein Test prüft zusätzlich die Übereinstimmung mit dieser lokalen Originalablage; dieser Test wird ohne gesetztes `WWT_SOURCE_DIR` übersprungen. Vier eigenständige Tests laufen ohne die alten Dateien. Weitere Tests prüfen die rekursive Regel gegen eine explizite Faltungsrechnung, Normierung, Reproduzierbarkeit, unveränderte Vektoren bei Auswahl eines Teilnetzes sowie die Ablehnung von Zyklen und fehlenden Zielknoten.

## Stufe 2: ungeschädigte Perzeption von Kanne

Start: `.venv/bin/python perception.py`

Der vollständige phonologische Pointer von Kanne wird von 0,15 bis 0,75 s eingespeist. Der Ablauf ist phonologischer Puffer → kompetitiver assoziativer Speicher → Lemmapuffer → schwellwertbasierter assoziativer Speicher → Konzeptpuffer. Keine akustische Erkennung, Aufgabensteuerung, Rückkopplung zwischen den lexikalischen Ebenen, Lernregel oder Ablation wird implementiert. Die Zuordnungen sind vorgegeben und durch NEF-Decoder umgesetzt.

Die Konzeptrepräsentation entspricht direkt dem strukturierten Konzept-Pointer. Der zusätzliche Umweg des alten WWT-Programms über `concept_lex` und dessen Kognitionskomponente entfällt. Der erste Speicher verwendet wie der WWT-Wahrnehmungsweg eine kompetitive Auswahl; dies ist eine reduzierte Neuimplementierung, keine Reproduktion der vollständigen alten Architektur oder ihrer Zeitverläufe.

Parameter: 512 Dimensionen, unveränderte Vektoren mit Seed 10; neuronaler Seed 11; drei `spa.State`-Puffer ohne Rückkopplung, je 50 LIF-Neuronen pro Dimension und Subdimensionsgröße 1. Zwei Speicher mit je 100 LIF-Neuronen für jeden der acht Einträge, Schwelle 0,3. Der erste Speicher verwendet `WTAAssocMem` mit konstanter Zielfunktion 1 oberhalb der Schwelle und lateraler Hemmung; der zweite `ThresholdingAssocMem` mit amplitudenabhängiger Ausgabe. Insgesamt 78.400 LIF-Neuronen. Die externen Verbindungen haben 10-ms-Tiefpassfilter, interne Speicherverbindungen die Bibliotheksvorgaben. Zeitschritt 1 ms, Laufzeit 1,1 s, Auslesefilter 20 ms.

Ergebnis des ersten Laufs: Kanne wird auf Lemma- und Konzeptebene ausgewählt. Im Auswertefenster 0,45–0,70 s betragen die mittleren Skalarprodukte für Kanne 0,952 (Lemma) und 0,933 (Konzept). Im Konzeptpuffer erscheinen außerdem Topf mit 0,508 und Tasse mit 0,422; diese Werte entsprechen sehr gut der Überlappung mit dem reinen Kanne-Pointer. Die amplitudenangepassten Erwartungen sind 0,507 bzw. 0,423. Katze liegt bei 0,043 gegenüber einer Erwartung von 0,046. Der größte absolute Unterschied zwischen gemessenen und erwarteten Skalarprodukten der acht Konzepte ist ca. 0,0067.

Die assoziativen Eintragsausgänge für sämtliche Konkurrenten sind in diesem Lauf null, auch während der Übergänge. Die aufgezeichneten Auswahlpopulationen zeigen Spikes nur für Kanne. Die allgemeine neuronale Pufferaktivität darf nicht mit diesen einzelnen Auswahlpopulationen gleichgesetzt werden: die Puffer kodieren verteilte Vektoren. Der über das Auswertefenster gemittelte Konzeptvektor hat einen relativen Restfehler von ca. 6,6 % gegenüber einem amplitudenangepassten Kanne-Pointer; die neuronale Darstellung ist daher nicht exakt, obwohl die acht Ähnlichkeitswerte gut übereinstimmen.

Dies ist ein erster Funktionsnachweis mit einem Wort und einem neuronalen Seed, keine Robustheitsstudie. Die Werte der Puffer sind Skalarprodukte mit den normierten Vorlagen; der neuronale Zustand wird vor der Auswertung nicht normiert. Die Kurven sind deshalb keine Kosinuswerte, Wahrscheinlichkeiten oder direkt gemessenen Feuerraten.

Ergebnisse unter `results/perception_kanne`: Zeitverläufe als PNG/SVG, Konzeptvergleich als PNG, Rohaufzeichnungen einschließlich Auswahl-Spikes als NPZ, Konzeptähnlichkeiten als CSV und Zusammenfassung als JSON. Das Programm prüft LIF-Neuronentypen, tatsächliche Spikes sowie den korrekten Zielabruf auf Lemma- und Konzeptebene.

## Stufe 3: ungeschädigte Produktion von Kanne

Start: `.venv/bin/python production.py`

Der vollständige Konzept-Pointer Kanne wird direkt von 0,15 bis 0,75 s vorgegeben; eine visuelle Vorverarbeitung ist noch nicht enthalten. Der Weg ist Konzeptpuffer → kompetitiver assoziativer Speicher → Lemmapuffer → schwellwertbasierter assoziativer Speicher → phonologischer Puffer. Die neuronalen Parameter, Seeds, acht Einträge, rekursiven Vektoren, Eingabedauer und Auswertung entsprechen dem Wahrnehmungsexperiment. Die Speicher haben entsprechend umgekehrte Zuordnungen; beide Versuche laufen getrennt und sind noch nicht als innerer Regelkreis verbunden.

Im ersten Produktionslauf beträgt das mittlere Skalarprodukt mit Kanne im Konzeptpuffer 0,975, im Lemmapuffer 0,951 und im phonologischen Puffer 0,940. Die semantischen Nachbarn Tasse (0,441) und Topf (0,532) erscheinen im Konzeptpuffer durch Vektorüberlappung. Im kompetitiven Speicher wird ausschließlich Kanne ausgewählt. Auch im zweiten Speicher bleibt Kanne der einzige aktive Eintrag; sämtliche Konkurrentenausgänge und deren aufgezeichnete Auswahl-Spikes sind über den gesamten Versuch null.

Am phonologischen Ausgang hat Katze einen Ähnlichkeitswert von 0,393. Die Erwartung aus dem amplitudenangepassten reinen Kanne-Pointer beträgt 0,394. Dies ist phonologische Vektorüberlappung und kein zusätzlicher Abruf der Wortform Katze. Der größte absolute Unterschied zwischen den acht gemessenen Skalarprodukten und dem reinen Kanne-Vergleich beträgt ca. 0,0034. Der relative Restfehler des gemittelten phonologischen Vektors beträgt ca. 5,6 %. Die Restfehler sind neuronale Darstellungsabweichungen und wurden nicht als Schädigungen eingebaut.

Ausgabe ist ein Pointer für die gesamte phonologische Wortform, noch keine zeitliche Phonemfolge, Artikulationsbewegung oder Schallausgabe. Wie beim Wahrnehmungsversuch ist dies ein Funktionsnachweis für ein Wort und einen neuronalen Seed, keine Robustheitsstudie.

Unter `results/production_kanne` liegen `production_traces.png` und `.svg`, `phonology_comparison.png`, `recordings.npz`, `phonology_similarities.csv` und `summary.json`. Die Abbildungen verwenden dieselben Farben und Skalen wie im Wahrnehmungsexperiment. Die eingebauten Prüfungen bestätigen spikende LIF-Neuronen und den korrekten Zielabruf auf Lemma- und phonologischer Ebene.

## Optionale Prüfung gegen die historischen Dateien

Die historischen Dateien sind nicht Bestandteil dieses Repositorys. Wer sie besitzt, kann den vollständigen Vergleich so ausführen:

```sh
WWT_SOURCE_DIR=/path/to/2024_Dysfunctions/wwt .venv/bin/python -m unittest -v
.venv/bin/python extract_wwt.py --source /path/to/2024_Dysfunctions/wwt
```

Die Extraktion überschreibt den mitgelieferten JSON-Ausschnitt. Für die normale Ausführung ist sie nicht erforderlich.
