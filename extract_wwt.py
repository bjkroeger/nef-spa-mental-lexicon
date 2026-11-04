"""Extract a dependency-complete subset without importing or executing old scripts."""
import ast
import argparse
import os
import hashlib
import json
from pathlib import Path

SOURCE = Path(os.environ['WWT_SOURCE_DIR']) if os.environ.get('WWT_SOURCE_DIR') else None
WORDS = ['Tasse', 'Tasche', 'Kanne', 'Katze', 'Teller', 'Topf', 'Stuhl', 'Schrank']

# Audited source-name mismatches, not fuzzy matches. Approved 2026-11-04.
PHONOLOGY_DEFINITIONS = {
    'Fressen': 'Pw_St_frE_sen',
    'Stricken': 'Pw_St_StrI_ken',
    'Hilfsmittel': 'Pw_St_hIlfs_mIt_el',
    'Richtig': 'Pw_St_rIc_tIk',
    'Fahrkarten': 'Pw_St_faA_kaA_ten',
    'Baeume': 'Pw_St_bOi_me',
    'Aussehen': 'Pw_St_aUs_see_hen',
    'Reisetasche': 'Pw_St_raI_se_St_taS_Se',
    'Kinderwagen': 'Pw_St_kIn_dA_St_vaa_gen',
    'Verbringen': 'Pw_EA_St_brIN_Nen',
    'Herunterspringen': 'Pw_hEA_St_rUn_tEA_St_SprIN_gen',
    'Lehrer': 'Pw_St_lee_reA',
    'Wand': 'Pw_St_vant',
}


def lexical_words(word_keys):
    """Source's two word blocks; exclude prompts, Nil, cues and sound fragments.

    These are stored word forms, not a lemmatized or POS-tagged dictionary.
    The explicit boundaries fail loudly if the source layout changes.
    """
    first = word_keys[4:word_keys.index('W_SchiebeWagen')]
    competitors = word_keys[word_keys.index('W_Hocken'):word_keys.index('W_BeginntMitSch1')]
    words = [key[2:] for key in first + competitors if not key.startswith('W_Nil')]
    if len(words) != 613 or len(set(words)) != 613:
        raise ValueError('Expected 613 distinct lexical entries in audited WWT source')
    return words


def read_assignments(path):
    values = {}

    def value(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, (ast.List, ast.Tuple)):
            return [value(x) for x in node.elts]
        if isinstance(node, ast.Dict):
            return {value(k): value(v) for k, v in zip(node.keys, node.values)}
        raise ValueError(f'Unsupported expression in {path}: {ast.dump(node)}')

    for statement in ast.parse(path.read_text()).body:
        if not isinstance(statement, ast.Assign):
            raise ValueError(f'Only data assignments allowed: {path}')
        for target in statement.targets:
            if not isinstance(target, ast.Name):
                raise ValueError('Only named assignments allowed')
            values[target.id] = value(statement.value)
    return values


def dependency_closure(network, roots):
    selected = {}
    active = set()

    def visit(key):
        if key in active:
            raise ValueError(f'Cycle at {key}')
        if key in selected:
            return
        active.add(key)
        for _, target in network[key]:
            visit(target)
        active.remove(key)
        selected[key] = network[key]

    for key in roots:
        visit(key)
    return selected


def extract(full=False, source=SOURCE):
    if source is None:
        raise ValueError("Set WWT_SOURCE_DIR or pass --source to re-extract; bundled data need no extraction")
    files = ['wwt_concepts.py', 'wwt_words.py', 'wwt_phonos.py']
    data = {}
    for filename in files:
        data.update(read_assignments(source / filename))
    entries = []
    for word in lexical_words(data['word_keys']) if full else WORDS:
        index = data['word_keys'].index('W_' + word)
        entries.append(dict(word=word, source_index=index,
                            concept=data['concept_keys'][index],
                            lemma=data['word_keys'][index],
                            phonology=data['phono_keys'][index]))
    phonology = {**data['phonos_deep'], **data['phonos']}
    repairs = []
    if full:
        for entry in entries:
            word = entry['word']
            if word not in PHONOLOGY_DEFINITIONS:
                continue
            definition = PHONOLOGY_DEFINITIONS[word]
            key = entry['phonology']
            if key in phonology:
                raise ValueError(f'Source changed: {key} now has its own definition')
            links = [list(link) for link in phonology[definition]]
            original_links = [list(link) for link in links]
            if word == 'Verbringen':
                assert links[0] == ['InclPhon', 'P_EA']
                links[0] = ['InclPhon', 'P_fEA']
            # Keep the mapping-list identity; restore the missing structural links.
            phonology[key] = links
            repairs.append(dict(word=word, pointer=key, source_definition=definition,
                                original_links=original_links, restored_links=links))
    result = {
        'source_directory': '2024_Dysfunctions/wwt',
        'source_sha256': {f: hashlib.sha256((source / f).read_bytes()).hexdigest() for f in files + ['run_wwt.py']},
        'entries': entries,
        'concept_network': dependency_closure({**data['concepts_deep'], **data['concepts']}, [e['concept'] for e in entries]),
        'phonology_network': dependency_closure(phonology, [e['phonology'] for e in entries]),
    }
    if full:
        result.update(schema_version=2, display_words=WORDS, phonology_repairs=repairs,
                      lemma_encoding='independent identity vectors; no POS grouping',
                      lexical_count=len(entries))
        result['network_counts'] = {
            'concept_nodes': len(result['concept_network']),
            'concept_deep_nodes': len(set(result['concept_network']) & data['concepts_deep'].keys()),
            'phonology_nodes': len(result['phonology_network']),
            'phonology_deep_nodes': len(set(result['phonology_network']) & data['phonos_deep'].keys()),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='Extract all 613 lexical entries and dependencies')
    parser.add_argument('--source', type=Path, default=SOURCE, help='Original WWT directory (or WWT_SOURCE_DIR)')
    args = parser.parse_args()
    if args.source is None:
        parser.error('Provide --source or WWT_SOURCE_DIR; bundled data need no extraction')
    result = extract(full=args.full, source=args.source)
    destination = Path(__file__).parent / 'data' / ('wwt_full_lexicon.json' if args.full else 'wwt_eight_words.json')
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'Extracted {len(result["entries"])} words; {len(result["concept_network"])} concept nodes; {len(result["phonology_network"])} phonology nodes.')


if __name__ == '__main__':
    main()
