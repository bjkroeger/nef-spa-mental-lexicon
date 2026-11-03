"""Extract a dependency-complete subset without importing or executing old scripts."""
import argparse
import os
import ast
import hashlib
import json
from pathlib import Path

SOURCE = Path(os.environ['WWT_SOURCE_DIR']) if os.environ.get('WWT_SOURCE_DIR') else None
WORDS = ['Tasse', 'Tasche', 'Kanne', 'Katze', 'Teller', 'Topf', 'Stuhl', 'Schrank']


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE, help='Path to the original WWT directory (or set WWT_SOURCE_DIR)')
    args = parser.parse_args()
    if args.source is None:
        parser.error('Provide --source or WWT_SOURCE_DIR; the bundled data need no extraction.')
    source = args.source
    files = ['wwt_concepts.py', 'wwt_words.py', 'wwt_phonos.py']
    data = {}
    for filename in files:
        data.update(read_assignments(source / filename))
    entries = []
    for word in WORDS:
        index = data['word_keys'].index('W_' + word)
        entries.append(dict(word=word, source_index=index,
                            concept=data['concept_keys'][index],
                            lemma=data['word_keys'][index],
                            phonology=data['phono_keys'][index]))
    result = {
        'source_directory': '2024_Dysfunctions/wwt',
        'source_sha256': {f: hashlib.sha256((source / f).read_bytes()).hexdigest() for f in files + ['run_wwt.py']},
        'entries': entries,
        'concept_network': dependency_closure({**data['concepts_deep'], **data['concepts']}, [e['concept'] for e in entries]),
        'phonology_network': dependency_closure({**data['phonos_deep'], **data['phonos']}, [e['phonology'] for e in entries]),
    }
    destination = Path(__file__).parent / 'data' / 'wwt_eight_words.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(f'Extracted {len(entries)} words; {len(result["concept_network"])} concept nodes; {len(result["phonology_network"])} phonology nodes.')


if __name__ == '__main__':
    main()
