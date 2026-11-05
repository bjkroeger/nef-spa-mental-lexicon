"""Stored phonological graph readout after neural lexical retrieval.

No neural syllable activations or timing are inferred. Ordered direct word links
are treated as learned lexical order for the eight audited demonstration words.
Original identifiers, edges and semantic pointers remain unchanged.
"""

# Explicit, audited model simplifications; not a general German syllabifier.
FIRST_SYLLABLE_RULES = {
    'Tasse': ('P_St_tas', 'P_St_ta'),
    'Tasche': ('P_St_taS', 'P_St_ta'),
    'Kanne': ('P_St_kan', 'P_St_ka'),
    'Katze': ('P_St_kat', 'P_St_ka'),
    'Teller': ('P_St_tEl', 'P_St_tE'),
}
SUPPORTED_WORDS = frozenset((*FIRST_SYLLABLE_RULES, 'Topf', 'Stuhl', 'Schrank'))


def readout(lexicon, winner):
    """Read the actual accepted winner, never the requested input word."""
    if winner is None:
        return dict(status='no_retrieval', word=None, syllables=[])
    entry = next(e for e in lexicon['entries'] if e['word'] == winner)
    network = lexicon['phonology_network']
    root = entry['phonology']
    nodes, edges, lines = [], [], [root]
    seen = set()

    def visit(node, prefix='', ancestors=frozenset()):
        if node in ancestors:
            raise ValueError('Cycle in phonological graph: ' + node)
        if node not in seen:
            nodes.append(node)
            seen.add(node)
            edges.extend(dict(source=node, relation=r, target=t)
                         for r, t in network[node])
        links = network[node]
        for i, (relation, target) in enumerate(links):
            last = i == len(links) - 1
            lines.append(prefix + ('└── ' if last else '├── ') + target
                         + ('' if relation == 'InclPhon' else ' [' + relation + ']'))
            visit(target, prefix + ('    ' if last else '│   '), ancestors | {node})

    visit(root)
    result = dict(status='ready' if winner in SUPPORTED_WORDS else 'unsupported',
                  word=winner, root=root, nodes=nodes, edges=edges,
                  graph_text='\n'.join(lines), syllables=[],
                  order_source='stored direct word-link order; treated as learned lexical information')
    if winner not in SUPPORTED_WORDS:
        return result
    for index, (relation, node) in enumerate(network[root]):
        if relation != 'InclPhon':
            raise ValueError('Unexpected direct word relation')
        output_node = node
        changed = index == 0 and winner in FIRST_SYLLABLE_RULES
        if changed:
            expected, output_node = FIRST_SYLLABLE_RULES[winner]
            if node != expected or ['InclPhon', output_node] not in network[node]:
                raise ValueError('Simplification no longer matches stored graph')
        stressed = node.startswith('P_St_')
        def sound(key):
            return key.removeprefix('P_St_') if key.startswith('P_St_') else key.removeprefix('P_')
        result['syllables'].append(dict(position=index + 1, stressed=stressed,
            lexical_node=node, lexical_form=sound(node), output_node=output_node,
            output_form=sound(output_node), rule='remove_first_syllable_final_consonant' if changed else None))
    return result


def for_live_result(lexicon, result):
    """Perception has no syllabification output."""
    return readout(lexicon, result['winner']) if result['task'] == 'production' else None
