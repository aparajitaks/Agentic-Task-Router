"""
app/tools/implementations/calculator.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    LLMs are notoriously bad at math because they predict the next token rather
    than executing arithmetic. A calculator tool forces the LLM to delegate
    mathematical operations to a deterministic Python engine.

WHAT IT DOES
    - Takes an arithmetic expression (e.g., "150 * 0.15").
    - Safely evaluates it using `numexpr` or a safe restricted `eval()`.
    - Returns the exact mathematical result.
"""

from langchain_core.tools import tool
import ast
import operator

from typing import Callable, Any
# Allowed safe operators
_ALLOWED_OPERATORS: dict[type[ast.operator] | type[ast.unaryop], Callable[..., Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _safe_eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        op = type(node.op)
        if op in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op](_safe_eval(node.left), _safe_eval(node.right))
        else:
            raise ValueError(f"Unsupported operator: {op}")
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        op_type = type(node.op)
        if op_type in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[op_type](_safe_eval(node.operand))
        else:
            raise ValueError(f"Unsupported operator: {op}")
    else:
        raise ValueError(f"Unsupported expression component: {type(node)}")

@tool
def calculator_tool(expression: str) -> str:
    """
    Evaluates a mathematical expression safely. 
    Use this tool whenever you need to perform calculations.
    Example expression: "450 * (1 - 0.20)"
    """
    try:
        # Parse the expression into an AST and safely evaluate it
        node = ast.parse(expression, mode='eval').body
        result = _safe_eval(node)
        return str(result)
    except Exception as e:
        return f"Error executing calculation '{expression}': {str(e)}"
