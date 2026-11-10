from __future__ import annotations

import ast
import operator
from typing import Any

from tools._shared import err

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _evaluate_ast(node.left)
        right = _evaluate_ast(node.right)
        op_type = type(node.op)
        if op_type in _OPERATORS:
            if op_type == ast.Div and right == 0:
                raise ZeroDivisionError("division by zero")
            return _OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _evaluate_ast(node.operand)
        op_type = type(node.op)
        if op_type in _OPERATORS:
            return _OPERATORS[op_type](operand)
    raise ValueError(f"Unsupported math syntax: {ast.dump(node)}")


def calculate(expression: str = "") -> dict[str, Any]:
    try:
        raw_expr = (expression or "").strip()
        if not raw_expr:
            return {"tool": "calculate", "error": "ValueError", "message": "Expression cannot be empty"}
        tree = ast.parse(raw_expr, mode="eval")
        result = _evaluate_ast(tree.body)
        return {
            "tool": "calculate",
            "expression": raw_expr,
            "result": result,
            "status": "success",
        }
    except Exception as exc:
        return err("calculate", exc)

