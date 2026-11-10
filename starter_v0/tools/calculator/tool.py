from __future__ import annotations

import ast
import math
import operator
from typing import Any

# Supported binary operators
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Supported unary operators
_SAFE_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Safe built-in functions
_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log10": math.log10,
    "pow": pow,
}


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _SAFE_OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_UNARY_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return _SAFE_UNARY_OPERATORS[op_type](operand)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are supported")
        func_name = node.func.id
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(f"Forbidden or unsupported function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        return _SAFE_FUNCTIONS[func_name](*args)

    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def calculate(expression: str = "") -> dict[str, Any]:
    """Safely evaluates a basic mathematical expression."""
    expr = (expression or "").strip()
    if not expr:
        return {
            "tool": "calculator",
            "expression": expr,
            "result": None,
            "status": "error",
            "error": "Empty expression",
        }

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _eval_node(parsed.body)
        # Format whole numbers as int or float
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return {
            "tool": "calculator",
            "expression": expr,
            "result": result,
            "status": "success",
        }
    except ZeroDivisionError:
        return {
            "tool": "calculator",
            "expression": expr,
            "result": None,
            "status": "error",
            "error": "Division by zero",
        }
    except Exception as exc:
        return {
            "tool": "calculator",
            "expression": expr,
            "result": None,
            "status": "error",
            "error": f"Invalid expression: {exc}",
        }

