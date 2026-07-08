"""A couple of small, dependency-free built-in tools."""

from __future__ import annotations

import ast
import operator as op

from agentmesh.tools.base import Tool

_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluate a basic arithmetic expression, e.g. '(3 + 4) * 2'."

    def run(self, expression: str) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            result = _eval_node(tree.body)
            return str(result)
        except Exception as exc:
            return f"error: could not evaluate '{expression}' ({exc})"


class WordCountTool(Tool):
    name = "word_count"
    description = "Count words in a piece of text."

    def run(self, text: str) -> str:
        return str(len(text.split()))
