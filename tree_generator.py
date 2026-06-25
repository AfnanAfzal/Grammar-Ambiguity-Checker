"""
Parse tree visualization module.
"""
import os
from typing import Optional, List
from parser import Node

try:
    from nltk.tree import Tree
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


class TreeGenerator:
    """Handles conversion and rendering of parse trees."""

    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def node_to_nltk(self, node: Node) -> 'Tree':
        if not node.children:
            return node.label
        return Tree(node.label, [self.node_to_nltk(c) for c in node.children])

    def to_graphviz(self, node: Node) -> 'graphviz.Digraph':
        dot = graphviz.Digraph()
        dot.attr('node', shape='ellipse', style='filled', fillcolor='#e2e8f0',
                 fontname='Segoe UI', fontsize='12', color='#0f172a')
        dot.attr('edge', color='#64748b', arrowsize='0.8')
        dot.attr(bgcolor='#0b1120', margin='0')
        dot.attr(rankdir='TB')
        self._add_nodes(dot, node)
        return dot

    def _add_nodes(self, dot: 'graphviz.Digraph', node: Node, parent_id: str = None):
        node_id = f"{id(node)}_{node.label}"
        dot.node(node_id, node.label)
        if parent_id:
            dot.edge(parent_id, node_id)
        for child in node.children:
            if child.children:
                self._add_nodes(dot, child, node_id)
            else:
                child_id = f"{id(child)}_{child.label}"
                dot.node(child_id, child.label, shape='box', fillcolor='#38bdf8',
                         fontcolor='#0b1120', style='filled', fontsize='11')
                dot.edge(node_id, child_id)

    def render_tree(self, tree: Node, index: int = 0) -> Optional[str]:
        if not GRAPHVIZ_AVAILABLE:
            return None
        try:
            dot = self.to_graphviz(tree)
            path = os.path.join(self.output_dir, f"parse_tree_{index}")
            dot.render(path, format='png', cleanup=True)
            return f"{path}.png"
        except Exception as e:
            print(f"[TreeGenerator] Graphviz render error: {e}")
            return None

    def get_ascii_tree(self, tree: Node, prefix: str = "", is_last: bool = True) -> str:
        lines = []
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + tree.label)
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(tree.children):
            last = (i == len(tree.children) - 1)
            lines.append(self.get_ascii_tree(child, child_prefix, last))
        return "\n".join(lines)
