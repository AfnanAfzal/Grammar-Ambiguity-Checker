"""
LL(1) Determinism Checker Module
Computes FIRST sets, FOLLOW sets, builds the LL(1) parsing table,
and determines whether the grammar is Deterministic (LL(1)) or not.
"""
from typing import Dict, List, Set, Tuple, Optional
from parser import CFGParser


class DeterminismChecker:
    """
    Checks if a Context-Free Grammar is LL(1) (Deterministic).

    Algorithm:
      1. Compute FIRST sets for all non-terminals.
      2. Compute FOLLOW sets for all non-terminals.
      3. Build the predictive parsing table M[A, a].
      4. If any table cell has > 1 entry → NOT LL(1).
    """

    EPSILON = 'ε'
    EOF = '$'

    def __init__(self, parser: CFGParser):
        self.parser = parser
        self.grammar = parser.grammar
        self.nt_set = parser.nt_set
        self.terminals = parser.terminals
        self.start = parser.start_symbol

        self._first: Dict[str, Set[str]] = {}
        self._follow: Dict[str, Set[str]] = {}
        self._table: Dict[Tuple[str, str], List[str]] = {}
        self._conflicts: List[str] = []

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    def analyze(self) -> Dict:
        """Run the full LL(1) analysis and return a structured result."""
        self._compute_first()
        self._compute_follow()
        self._build_table()

        is_ll1 = len(self._conflicts) == 0

        return {
            'is_ll1': is_ll1,
            'verdict': 'LL(1) — DETERMINISTIC' if is_ll1 else 'NOT LL(1) — NON-DETERMINISTIC',
            'first': {nt: sorted(s) for nt, s in self._first.items()},
            'follow': {nt: sorted(s) for nt, s in self._follow.items()},
            'table': {
                f"M[{nt}, {t}]": f"{nt} -> {' '.join(p) if p else 'ε'}"
                for (nt, t), p in sorted(self._table.items())
            },
            'conflicts': self._conflicts,
            'explanation': self._make_explanation(is_ll1),
        }

    # ------------------------------------------------------------------
    # FIRST Sets
    # ------------------------------------------------------------------

    def _sym_first(self, sym: str) -> Set[str]:
        """FIRST of a single symbol (terminal or non-terminal)."""
        if sym not in self.nt_set:
            return {sym}
        return self._first.get(sym, set())

    def _seq_first(self, seq: List[str]) -> Set[str]:
        """FIRST of a sequence of symbols (production RHS)."""
        result: Set[str] = set()
        for sym in seq:
            sf = self._sym_first(sym)
            result |= sf - {self.EPSILON}
            if self.EPSILON not in sf:
                return result
        result.add(self.EPSILON)
        return result

    def _compute_first(self):
        """Fixed-point iteration to compute FIRST sets."""
        for nt in self.nt_set:
            self._first[nt] = set()

        changed = True
        while changed:
            changed = False
            for nt, prods in self.grammar.items():
                for prod in prods:
                    if not prod:                        # epsilon production
                        if self.EPSILON not in self._first[nt]:
                            self._first[nt].add(self.EPSILON)
                            changed = True
                        continue
                    all_derive_eps = True
                    for sym in prod:
                        if sym not in self.nt_set:      # terminal
                            if sym not in self._first[nt]:
                                self._first[nt].add(sym)
                                changed = True
                            all_derive_eps = False
                            break
                        else:                           # non-terminal
                            new = self._first[sym] - {self.EPSILON}
                            if not new.issubset(self._first[nt]):
                                self._first[nt] |= new
                                changed = True
                            if self.EPSILON not in self._first[sym]:
                                all_derive_eps = False
                                break
                    if all_derive_eps:
                        if self.EPSILON not in self._first[nt]:
                            self._first[nt].add(self.EPSILON)
                            changed = True

    # ------------------------------------------------------------------
    # FOLLOW Sets
    # ------------------------------------------------------------------

    def _compute_follow(self):
        """Fixed-point iteration to compute FOLLOW sets."""
        for nt in self.nt_set:
            self._follow[nt] = set()
        if self.start:
            self._follow[self.start].add(self.EOF)

        changed = True
        while changed:
            changed = False
            for nt, prods in self.grammar.items():
                for prod in prods:
                    for i, sym in enumerate(prod):
                        if sym not in self.nt_set:
                            continue
                        rest = prod[i + 1:]
                        first_rest = self._seq_first(rest)

                        # Add FIRST(rest) - {ε} to FOLLOW(sym)
                        add = first_rest - {self.EPSILON}
                        if not add.issubset(self._follow[sym]):
                            self._follow[sym] |= add
                            changed = True

                        # If rest can derive ε, add FOLLOW(nt) to FOLLOW(sym)
                        if self.EPSILON in first_rest:
                            if not self._follow[nt].issubset(self._follow[sym]):
                                self._follow[sym] |= self._follow[nt]
                                changed = True

    # ------------------------------------------------------------------
    # LL(1) Parsing Table
    # ------------------------------------------------------------------

    def _build_table(self):
        """Build M[A, a] and collect any conflicts."""
        self._table = {}
        self._conflicts = []

        for nt, prods in self.grammar.items():
            for prod in prods:
                prod_first = self._seq_first(prod)
                prod_str = ' '.join(prod) if prod else 'ε'

                for terminal in prod_first - {self.EPSILON}:
                    self._add_entry(nt, terminal, prod, prod_str)

                if self.EPSILON in prod_first:
                    for terminal in self._follow.get(nt, set()):
                        self._add_entry(nt, terminal, prod, 'ε (via FOLLOW)')

    def _add_entry(self, nt: str, terminal: str,
                   prod: List[str], prod_str: str):
        key = (nt, terminal)
        if key in self._table:
            existing = ' '.join(self._table[key]) if self._table[key] else 'ε'
            if existing != prod_str:
                msg = (f"CONFLICT  M[{nt}, {terminal}]:"
                       f"  '{nt} -> {existing}'  vs  '{nt} -> {prod_str}'")
                if msg not in self._conflicts:
                    self._conflicts.append(msg)
        else:
            self._table[key] = prod

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def _make_explanation(self, is_ll1: bool) -> List[str]:
        if is_ll1:
            return [
                "Grammar IS LL(1) — Deterministic Parsing possible.",
                "",
                "An LL(1) grammar satisfies all three conditions:",
                "  1. No left recursion (direct or indirect)",
                "  2. For any A -> α | β:  FIRST(α) ∩ FIRST(β) = ∅",
                "  3. If ε ∈ FIRST(α):  FIRST(β) ∩ FOLLOW(A) = ∅",
                "",
                "Benefits of LL(1):",
                "  • Parsed by a simple predictive (recursive-descent) parser",
                "  • No backtracking required",
                "  • Single lookahead token is enough to decide the rule",
                "  • Used in hand-written compilers (GCC frontend, etc.)",
            ]
        else:
            return [
                "Grammar is NOT LL(1) — Non-Deterministic.",
                "",
                "A conflict in the parsing table means the parser cannot",
                "decide which production to apply with 1 token of lookahead.",
                "",
                "Common causes of non-determinism:",
                "  • Left recursion:       E -> E + T",
                "  • Common prefixes:      A -> a B | a C",
                "  • Ambiguous grammar (always non-LL(1))",
                "  • FIRST/FOLLOW overlap for nullable non-terminals",
                "",
                "Possible fixes:",
                "  1. Use 'Convert Grammar' to eliminate left recursion",
                "     and apply left factoring automatically.",
                "  2. Use a more powerful parser: LR(1), LALR(1), GLR.",
                "  3. Rewrite the grammar manually to remove conflicts.",
            ]
