"""Safe evaluator for governance policy condition expressions.

Replaces ``eval()``: parses the expression with ``ast`` and walks an explicit
allow-list of node types. Anything else — attribute access, calls, subscripts,
comprehensions, lambdas — is rejected, so the object-graph escapes that defeat
``eval(expr, {"__builtins__": None}, ...)`` are impossible by construction.

Supported: ``and`` / ``or`` / ``not``, comparisons (``== != < <= > >= in not in``,
chained), unary minus, ``+ - * / %``, variable names from the context, and literal
numbers / strings / booleans / ``None`` / lists / tuples.
"""

import ast
import operator
from typing import Any, Mapping

MAX_EXPRESSION_LENGTH = 500
MAX_NODES = 200


class UnsafeExpressionError(ValueError):
    """Raised when an expression is malformed or uses a disallowed construct."""


_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_SAFE_CONSTANT_TYPES = (int, float, str, bool, type(None))


def _eval(node: ast.AST, ctx: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval(node.body, ctx)

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for value in node.values:
                result = _eval(value, ctx)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for value in node.values:
                result = _eval(value, ctx)
                if result:
                    return result
            return result

    if isinstance(node, ast.UnaryOp):
        operand = _eval(node.operand, ctx)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand

    if isinstance(node, ast.Compare):
        left = _eval(node.left, ctx)
        for op, comparator in zip(node.ops, node.comparators):
            fn = _COMPARE_OPS.get(type(op))
            if fn is None:
                break
            right = _eval(comparator, ctx)
            if not fn(left, right):
                return False
            left = right
        else:
            return True

    if isinstance(node, ast.BinOp):
        fn = _BIN_OPS.get(type(node.op))
        if fn is not None:
            return fn(_eval(node.left, ctx), _eval(node.right, ctx))

    if isinstance(node, ast.Name):
        if node.id not in ctx:
            raise UnsafeExpressionError(f"Unknown variable '{node.id}'")
        return ctx[node.id]

    if isinstance(node, ast.Constant) and isinstance(node.value, _SAFE_CONSTANT_TYPES):
        return node.value

    if isinstance(node, (ast.List, ast.Tuple)):
        return [_eval(elt, ctx) for elt in node.elts]

    raise UnsafeExpressionError(f"Disallowed expression element: {type(node).__name__}")


def evaluate_condition(expression: str, context: Mapping[str, Any]) -> bool:
    """Evaluate a policy condition against ``context`` without executing code."""
    if not isinstance(expression, str) or not expression.strip():
        raise UnsafeExpressionError("Expression must be a non-empty string")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpressionError(f"Expression exceeds {MAX_EXPRESSION_LENGTH} characters")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"Invalid syntax: {exc.msg}") from exc

    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise UnsafeExpressionError("Expression is too complex")

    safe_ctx = {k: v for k, v in context.items() if isinstance(k, str) and not k.startswith("_")}
    return bool(_eval(tree, safe_ctx))
