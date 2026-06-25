"""
Ambiguity detection engine.
"""
from typing import List, Dict
from parser import CFGParser, Node


class AmbiguityChecker:
    """Analyzes parse trees to detect ambiguity."""

    def __init__(self, parser: CFGParser):
        self.parser = parser

    def analyze(self, tokens: List[str]) -> Dict:
        trees = self.parser.find_all_parse_trees(tokens)

        result = {
            'trees': trees,
            'tree_count': len(trees),
            'ambiguous': len(trees) > 1,
            'leftmost_derivations': [],
            'rightmost_derivations': [],
            'messages': [],
            'debug': self.parser.debug_log,
        }

        if len(trees) == 0:
            result['messages'].append("No parse trees found. String does not belong to the language.")
        elif len(trees) == 1:
            result['messages'].append("Exactly one parse tree found.")
            result['messages'].append("Grammar is UNAMBIGUOUS for this input string.")
        else:
            result['messages'].append(f"Found {len(trees)} distinct parse trees.")
            result['messages'].append("Grammar is AMBIGUOUS for this input string.")

        for tree in trees:
            result['leftmost_derivations'].append(self.parser.get_leftmost_derivation(tree))
            result['rightmost_derivations'].append(self.parser.get_rightmost_derivation(tree))

        return result
