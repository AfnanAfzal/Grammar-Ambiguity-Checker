"""
Core parser module — bulletproof implementation.
Handles grammar loading, tokenization, and parse tree generation.
"""
import re
from typing import List, Dict, Tuple, Optional


class Node:
    """Parse tree node."""
    def __init__(self, label: str, children: Optional[List['Node']] = None):
        self.label = label
        self.children = children if children is not None else []

    def copy(self):
        return Node(self.label, [c.copy() for c in self.children])

    def __repr__(self):
        if not self.children:
            return self.label
        return f"{self.label}({', '.join(repr(c) for c in self.children)})"


class CFGParser:
    """Robust parser for Context-Free Grammars."""

    def __init__(self):
        self.grammar: Dict[str, List[List[str]]] = {}
        self.start_symbol: Optional[str] = None
        self.nt_set: set = set()
        self.terminals: set = set()
        self.tokens: List[str] = []
        self.max_trees: int = 10
        self.debug_log: List[str] = []

    # ------------------------------------------------------------------
    # Grammar Loading
    # ------------------------------------------------------------------
    def load_grammar(self, raw_text: str) -> Tuple[bool, str]:
        try:
            self.grammar = {}
            self.nt_set = set()
            self.terminals = set()
            self.debug_log = []
            lines = [l.strip() for l in raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n') if l.strip()]
            if not lines:
                return False, "Grammar is empty."

            # Pass 1: identify non-terminals
            self.start_symbol = None  # will be set to first production's LHS
            for line in lines:
                arrow = self._detect_arrow(line)
                if arrow is None:
                    return False, f"Invalid production (no arrow '->', '→', '=>', '::='): {line}"
                lhs = line.split(arrow)[0].strip()
                if not lhs or ' ' in lhs:
                    return False, f"Invalid left-hand side (must be single non-terminal): {lhs}"
                self.nt_set.add(lhs)
                if self.start_symbol is None:
                    self.start_symbol = lhs  # first production = start symbol

            # Pass 2: parse RHS
            for line in lines:
                arrow = self._detect_arrow(line)
                lhs, rhs = line.split(arrow, 1)
                lhs = lhs.strip()
                alternatives = rhs.split('|')
                if lhs not in self.grammar:
                    self.grammar[lhs] = []
                for alt in alternatives:
                    alt = alt.strip()
                    if not alt:
                        self.grammar[lhs].append([])  # epsilon
                    else:
                        tokens = self._tokenize_rhs(alt)
                        self.grammar[lhs].append(tokens)

            # Collect terminals
            for nt, prods in self.grammar.items():
                for prod in prods:
                    for sym in prod:
                        if sym not in self.nt_set:
                            self.terminals.add(sym)

            self.debug_log.append(f"Non-terminals: {self.nt_set}")
            self.debug_log.append(f"Terminals: {self.terminals}")
            for nt, prods in self.grammar.items():
                for p in prods:
                    self.debug_log.append(f"  {nt} -> {' '.join(p) if p else 'ε'}")
            return True, "Grammar loaded successfully."
        except Exception as e:
            return False, f"Grammar parsing error: {str(e)}"

    def _detect_arrow(self, line: str) -> Optional[str]:
        for arrow in ('->', '→', '=>', '::='):
            if arrow in line:
                return arrow
        return None

    def _tokenize_rhs(self, s: str) -> List[str]:
        s = s.strip()
        if not s:
            return []
        if ' ' in s:
            parts = s.split()
            tokens = []
            for part in parts:
                tokens.extend(self._tokenize_part(part))
            return tokens
        else:
            return self._tokenize_part(s)

    def _tokenize_part(self, s: str) -> List[str]:
        """
        Tokenize an unspaced string fragment.
        CRITICAL FIX: When no non-terminal matches, check if a non-terminal
        appears ahead. If yes, consume only the current char as terminal.
        This prevents 'aSb' from being consumed as one token 'aSb'.
        """
        tokens = []
        i = 0
        n = len(s)
        nts = sorted(self.nt_set, key=len, reverse=True)
        while i < n:
            # 1. Try to match a known non-terminal (longest first)
            matched = False
            for nt in nts:
                if s.startswith(nt, i):
                    tokens.append(nt)
                    i += len(nt)
                    matched = True
                    break
            if matched:
                continue

            # 2. No non-terminal matched at position i.
            # Check if any non-terminal appears ahead in the string.
            found_nt_ahead = False
            for j in range(i + 1, n):
                for nt in nts:
                    if s.startswith(nt, j):
                        found_nt_ahead = True
                        break
                if found_nt_ahead:
                    break

            ch = s[i]
            if found_nt_ahead:
                # A non-terminal is coming up — consume just this char as terminal
                tokens.append(ch)
                i += 1
            else:
                # No non-terminal ahead — safe to consume alphanumeric word
                if ch.isalnum() or ch == '_':
                    j = i
                    while j < n and (s[j].isalnum() or s[j] == '_'):
                        j += 1
                    tokens.append(s[i:j])
                    i = j
                else:
                    tokens.append(ch)
                    i += 1
        return tokens

    # ------------------------------------------------------------------
    # Input Tokenization
    # ------------------------------------------------------------------
    def tokenize_input(self, input_str: str) -> Tuple[bool, List[str], str]:
        try:
            if not input_str or not input_str.strip():
                return False, [], "Input string is empty."
            if not self.terminals:
                return False, [], "No terminals found in grammar."

            s = re.sub(r'\s+', '', input_str)
            if not s:
                return False, [], "Input string is empty after removing spaces."

            terminal_list = sorted(self.terminals, key=len, reverse=True)
            self.debug_log.append(f"Tokenizing input '{s}' with terminals: {terminal_list}")

            tokens = []
            i = 0
            n = len(s)
            while i < n:
                matched = False
                for t in terminal_list:
                    if s.startswith(t, i):
                        tokens.append(t)
                        i += len(t)
                        matched = True
                        break
                if not matched:
                    ch = s[i]
                    # Defensive fallback: check if char exists in any production
                    found = False
                    for prods in self.grammar.values():
                        for prod in prods:
                            if ch in prod:
                                tokens.append(ch)
                                i += 1
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        return False, [], f"Invalid symbol at position {i}: '{s[i]}'"
            self.debug_log.append(f"Input tokens: {tokens}")
            return True, tokens, "Tokenization successful."
        except Exception as e:
            return False, [], f"Tokenization error: {str(e)}"

    # ------------------------------------------------------------------
    # Parse Tree Generation (recursive descent with left-recursion guard)
    # ------------------------------------------------------------------
    def find_all_parse_trees(self, tokens: List[str]) -> List[Node]:
        self.tokens = tokens
        self._memo = {}
        self.debug_log.append(f"Searching parse trees for tokens: {tokens}")
        results = self._parse_symbol_lr(self.start_symbol, 0, 0)
        trees = [node for end_pos, node in results if end_pos == len(tokens)]
        # Deduplicate by string representation
        seen = set()
        unique = []
        for t in trees:
            s = self._tree_str(t)
            if s not in seen:
                seen.add(s)
                unique.append(t)
        self.debug_log.append(f"Unique valid trees: {len(unique)}")
        return unique[:self.max_trees]

    def _tree_str(self, node: Node) -> str:
        if not node.children:
            return node.label
        return f"{node.label}({','.join(self._tree_str(c) for c in node.children)})"

    def _parse_symbol_lr(self, symbol: str, pos: int, lr_depth: int) -> List[Tuple[int, Node]]:
        """Parse symbol with left-recursion depth tracking."""
        if lr_depth > len(self.tokens) + 5 or pos > len(self.tokens):
            return []

        memo_key = (symbol, pos, lr_depth)
        if memo_key in self._memo:
            return self._memo[memo_key]

        if symbol not in self.nt_set:
            if pos < len(self.tokens) and self.tokens[pos] == symbol:
                return [(pos + 1, Node(symbol))]
            return []

        results = []
        self._memo[memo_key] = results

        for production in self.grammar.get(symbol, []):
            is_lr = len(production) > 0 and production[0] == symbol
            new_lr = lr_depth + 1 if is_lr else 0

            res = self._parse_sequence_lr(production, pos, new_lr)
            for end_pos, children in res:
                results.append((end_pos, Node(symbol, children)))
                if len(results) >= self.max_trees * 4:
                    break
            if len(results) >= self.max_trees * 4:
                break

        self._memo[memo_key] = results
        return results

    def _parse_sequence_lr(self, symbols: List[str], pos: int, lr_depth: int) -> List[Tuple[int, List[Node]]]:
        if not symbols:
            return [(pos, [])]
        first, rest = symbols[0], symbols[1:]
        results = []
        for end_pos, node in self._parse_symbol_lr(first, pos, lr_depth):
            for final_pos, rest_nodes in self._parse_sequence_lr(rest, end_pos, lr_depth):
                results.append((final_pos, [node] + rest_nodes))
                if len(results) >= self.max_trees * 4:
                    return results
        return results

    # ------------------------------------------------------------------
    # Derivation Extraction
    # ------------------------------------------------------------------
    def get_leftmost_derivation(self, tree: Node) -> List[str]:
        derivation = [tree.label]
        frontier = [tree]
        while True:
            idx = None
            for i, node in enumerate(frontier):
                if node.children:
                    idx = i
                    break
            if idx is None:
                break
            node = frontier[idx]
            frontier = frontier[:idx] + list(node.children) + frontier[idx + 1:]
            derivation.append(' '.join(n.label for n in frontier))
        return derivation

    def get_rightmost_derivation(self, tree: Node) -> List[str]:
        derivation = [tree.label]
        frontier = [tree]
        while True:
            idx = None
            for i in range(len(frontier) - 1, -1, -1):
                if frontier[i].children:
                    idx = i
                    break
            if idx is None:
                break
            node = frontier[idx]
            frontier = frontier[:idx] + list(node.children) + frontier[idx + 1:]
            derivation.append(' '.join(n.label for n in frontier))
        return derivation
