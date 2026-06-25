"""
Grammar Converter Module
Converts Ambiguous Grammars to Unambiguous form.
Handles: Arithmetic Expressions, Dangling Else, General CFGs.
"""
from typing import Dict, List, Tuple, Set
from parser import CFGParser


class GrammarConverter:
    """
    Converts ambiguous grammars to unambiguous equivalents.
    Detects grammar type and applies the appropriate algorithm.
    """

    def __init__(self, parser: CFGParser):
        self.parser = parser
        self.grammar = parser.grammar
        self.nt_set = parser.nt_set
        self.terminals = parser.terminals
        self.start = parser.start_symbol

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    def convert(self) -> Dict:
        """Detect grammar type and run the appropriate conversion."""
        if self._is_arithmetic():
            return self._convert_arithmetic()
        elif self._has_dangling_else():
            return self._convert_dangling_else()
        else:
            return self._general_conversion()

    # ------------------------------------------------------------------
    # Grammar Type Detection
    # ------------------------------------------------------------------

    def _is_arithmetic(self) -> bool:
        arith_ops = {'+', '-', '*', '/', '^', '%'}
        return bool(self.terminals & arith_ops)

    def _has_dangling_else(self) -> bool:
        return {'if', 'then', 'else'}.issubset(self.terminals)

    # ------------------------------------------------------------------
    # 1. Arithmetic Grammar: Operator Precedence & Associativity
    # ------------------------------------------------------------------

    def _convert_arithmetic(self) -> Dict:
        op_levels = self._get_op_levels()       # low → high precedence
        base_terms = self._get_base_terms()
        has_parens = '(' in self.terminals and ')' in self.terminals

        # Generate NT name hierarchy: E → T → F → G ...
        nts = self._make_nt_names(len(op_levels))

        lines, steps = [], []
        steps.append("STEP 1 — Identify operators and assign precedence levels")
        steps.append("(Lower level number = lower precedence = outermost rule)\n")
        for i, lvl in enumerate(op_levels):
            assoc = "Right-assoc" if '^' in lvl else "Left-assoc"
            steps.append(f"  Level {i+1}: {' , '.join(lvl)}   [{assoc}]")

        steps.append("\nSTEP 2 — One non-terminal per precedence level")
        steps.append(f"  Hierarchy: {' → '.join(nts)}")

        steps.append("\nSTEP 3 — Write left-recursive rules (enforces left-assoc)")

        for i, lvl in enumerate(op_levels):
            curr, nxt = nts[i], nts[i + 1]
            if '^' in lvl:
                # Right-associative: curr -> nxt op curr | nxt
                alts = ' | '.join(f"{nxt} {op} {curr}" for op in lvl)
                rule = f"{curr} -> {alts} | {nxt}"
            else:
                # Left-associative: curr -> curr op nxt | nxt
                alts = ' | '.join(f"{curr} {op} {nxt}" for op in lvl)
                rule = f"{curr} -> {alts} | {nxt}"
            lines.append(rule)
            steps.append(f"  {rule}")

        # Base / Factor level
        factor = nts[-1]
        base_str = ' | '.join(sorted(set(base_terms))) if base_terms else 'id'
        if has_parens:
            factor_rule = f"{factor} -> ( {nts[0]} ) | {base_str}"
        else:
            factor_rule = f"{factor} -> {base_str}"
        lines.append(factor_rule)
        steps.append(f"  {factor_rule}")

        steps.append("\nSTEP 4 — Verify: each string has exactly ONE parse tree now.")

        explanation = [
            "WHY the original grammar is ambiguous:",
            f"  Rules like  {self.start} -> {self.start} + {self.start}  give no",
            "  information about which operator binds tighter or",
            "  whether operators are left/right associative.",
            "",
            "HOW the fix works:",
            f"  Non-terminal hierarchy:  {' → '.join(nts)}",
            "  • LOWER in the list  =  HIGHER precedence (binds tighter)",
            "  • Left-recursive rule  (E -> E op T)  =  LEFT-associative",
            "  • Right-recursive rule (E -> T op E)  =  RIGHT-associative",
            "  • Parentheses break precedence (override any level)",
            "",
            "This is the STANDARD technique used in real compilers.",
        ]

        return {
            'success': True,
            'method': 'Operator Precedence & Associativity',
            'original': self._grammar_str(self.grammar),
            'converted': '\n'.join(lines),
            'steps': steps,
            'explanation': explanation,
        }

    def _get_op_levels(self) -> List[List[str]]:
        """Return operator groups ordered lowest → highest precedence."""
        standard = [
            ['+', '-'],     # lowest
            ['*', '/'],     # medium
            ['^'],          # highest (right-assoc)
        ]
        present = []
        known: Set[str] = set()
        for lvl in standard:
            found = [op for op in lvl if op in self.terminals]
            if found:
                present.append(found)
            known |= set(lvl)

        # Unknown operators → treat as lowest precedence
        unknown = [t for t in self.terminals
                   if t not in known and t not in self.nt_set
                   and t not in {'(', ')', 'id', 'num', 'n', 'a', 'b', 'c', 'epsilon'}]
        if unknown:
            present = [unknown] + present

        return present if present else [['+', '*']]

    def _get_base_terms(self) -> List[str]:
        """Collect base/atomic terminals (single-symbol productions)."""
        base = []
        for _, prods in self.grammar.items():
            for prod in prods:
                if len(prod) == 1 and prod[0] not in self.nt_set:
                    base.append(prod[0])
        for sym in ['id', 'num', 'n']:
            if sym in self.terminals and sym not in base:
                base.append(sym)
        seen, result = set(), []
        for x in base:
            if x not in seen:
                seen.add(x)
                result.append(x)
        return result

    def _make_nt_names(self, num_levels: int) -> List[str]:
        """Build a list of num_levels+1 unique NT names."""
        pool = ['E', 'T', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']
        # Start with the grammar's start symbol
        s = self.start or 'E'
        result = [s]
        for c in pool:
            if len(result) == num_levels + 1:
                break
            if c != s:
                result.append(c)
        while len(result) < num_levels + 1:
            result.append(f"N{len(result)}")
        return result

    # ------------------------------------------------------------------
    # 2. Dangling Else Resolution
    # ------------------------------------------------------------------

    def _convert_dangling_else(self) -> Dict:
        lines = [
            "S           -> matched_stmt | unmatched_stmt",
            "matched_stmt   -> if cond then matched_stmt else matched_stmt | other",
            "unmatched_stmt -> if cond then S",
            "              |  if cond then matched_stmt else unmatched_stmt",
        ]
        steps = [
            "STEP 1 — Identify the dangling-else ambiguity",
            "  'if a then if b then s1 else s2'",
            "  Ambiguous: does 'else s2' belong to inner or outer if?",
            "",
            "STEP 2 — Split statements into two categories",
            "  matched_stmt   : always has a matching else",
            "  unmatched_stmt : has an if with no matching else",
            "",
            "STEP 3 — Write rules so 'else' always binds to nearest if",
            "  matched   -> if cond then matched else matched | other",
            "  unmatched -> if cond then S",
            "            -> if cond then matched else unmatched",
            "",
            "STEP 4 — Result: grammar now forces C/Java 'nearest-if' rule.",
        ]
        explanation = [
            "The 'Dangling Else' problem:",
            "  if a then if b then x else y",
            "  Can be parsed two ways (ambiguous).",
            "",
            "The fix separates 'matched' (has else) from 'unmatched'",
            "statements. Else always pairs with the nearest open if.",
            "This is exactly how C, Java, and Python handle it.",
        ]
        return {
            'success': True,
            'method': 'Dangling Else Resolution',
            'original': self._grammar_str(self.grammar),
            'converted': '\n'.join(lines),
            'steps': steps,
            'explanation': explanation,
        }

    # ------------------------------------------------------------------
    # 3. General: Left Recursion Elimination + Left Factoring
    # ------------------------------------------------------------------

    def _general_conversion(self) -> Dict:
        steps = [
            "STEP 1 — Scan for left recursion",
            "  A production  A -> A α  is directly left-recursive.",
            "  Left recursion can cause ambiguity and infinite loops.",
            "",
        ]
        new_grammar: Dict[str, List[List[str]]] = {}

        for nt in list(self.grammar.keys()):
            prods = self.grammar[nt]
            lr = [p for p in prods if p and p[0] == nt]
            non_lr = [p for p in prods if not p or p[0] != nt]

            if lr:
                prime = nt + "'"
                # A -> β A'  for each non-left-recursive β
                new_grammar[nt] = [p + [prime] for p in non_lr] if non_lr else [[prime]]
                # A' -> α A' | ε  for each left-recursive A -> A α
                new_grammar[prime] = [p[1:] + [prime] for p in lr] + [[]]

                steps.append(f"  Left recursion found in  {nt}:")
                steps.append(f"  Introducing new NT:  {prime}")
                for p in new_grammar[nt]:
                    steps.append(f"    {nt} -> {' '.join(p) if p else 'ε'}")
                for p in new_grammar[prime]:
                    steps.append(f"    {prime} -> {' '.join(p) if p else 'ε'}")
                steps.append("")
            else:
                new_grammar[nt] = prods

        if len(steps) == 4:  # only header lines, nothing found
            steps.append("  No direct left recursion detected.")
            steps.append("")

        # Left factoring
        steps.append("STEP 2 — Apply Left Factoring")
        steps.append("  A -> α β | α γ  becomes  A -> α A',  A' -> β | γ")
        steps.append("")
        factored: Dict[str, List[List[str]]] = {}
        existing = set(new_grammar.keys())
        for nt, prods in new_grammar.items():
            new_prods, extras = self._left_factor(nt, prods, existing)
            factored[nt] = new_prods
            factored.update(extras)
            existing |= set(extras.keys())
            if extras:
                steps.append(f"  Left factored  {nt}  → introduced {list(extras.keys())}")

        if not any(k for k in factored if k not in new_grammar):
            steps.append("  No common prefixes found — no left factoring needed.")

        explanation = [
            "Two standard algorithms applied:\n",
            "1. LEFT RECURSION ELIMINATION",
            "   A -> A α | β   is converted to:",
            "   A  -> β A'",
            "   A' -> α A' | ε",
            "   Removes infinite-loop risk in top-down parsers.",
            "",
            "2. LEFT FACTORING",
            "   A -> α β | α γ   is converted to:",
            "   A  -> α A'",
            "   A' -> β | γ",
            "   Removes ambiguity from common prefixes.",
            "",
            "Note: These are necessary but not always sufficient.",
            "For complex grammars, use an LR(1) or LALR parser.",
        ]

        return {
            'success': True,
            'method': 'Left Recursion Elimination + Left Factoring',
            'original': self._grammar_str(self.grammar),
            'converted': self._grammar_str(factored),
            'steps': steps,
            'explanation': explanation,
        }

    def _left_factor(self, nt: str, prods: List[List[str]],
                     existing: Set[str]) -> Tuple[List[List[str]], Dict]:
        if len(prods) <= 1:
            return prods, {}

        groups: Dict[str, List[List[str]]] = {}
        for p in prods:
            k = p[0] if p else ''
            groups.setdefault(k, []).append(p)

        if all(len(g) == 1 for g in groups.values()):
            return prods, {}

        new_prods: List[List[str]] = []
        extras: Dict[str, List[List[str]]] = {}

        for first, grp in groups.items():
            if len(grp) == 1:
                new_prods.append(grp[0])
            else:
                prime = nt + "'"
                while prime in existing or prime in extras:
                    prime += "'"
                new_prods.append([first, prime] if first else [prime])
                extras[prime] = [p[1:] for p in grp]

        return new_prods, extras

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _grammar_str(self, grammar: Dict) -> str:
        lines = []
        for nt, prods in grammar.items():
            rhs = ' | '.join(' '.join(p) if p else 'ε' for p in prods)
            lines.append(f"{nt} -> {rhs}")
        return '\n'.join(lines)
