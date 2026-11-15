"""Compilador de reglas (formato anidado) a expresiones SQL.

- `to_sql(tree, threshold)`: umbrales exactos (repr de float, con exponente
  cuando hace falta para que DuckDB los lea como DOUBLE) -> equivalente a la
  evaluación en Python.
- `to_sql(tree, threshold, readable=True)`: umbrales redondeados para el
  informe (NO garantiza equivalencia).
"""
from __future__ import annotations

from evo.tree_eval import COMPARE, ThresholdFn, simplify, threshold_of


# Con hasta 15 dígitos significativos, DECIMAL -> DOUBLE es exacto (la mantisa
# cabe en los 53 bits de un double).
MAX_EXACT_DECIMAL_DIGITS = 15


def _fmt(v: float, readable: bool) -> str:
    if readable:
        # 4 cifras significativas; sin notación científica en valores grandes
        return f"{v:.0f}" if abs(v) >= 1e4 else f"{v:.4g}"
    s = repr(float(v))
    # DuckDB lee `45.333333333333336` como DECIMAL y, al convertirlo a DOUBLE
    # para comparar, puede cambiar el último bit: las filas que empatan con el
    # umbral dejarían de coincidir con Python. Con exponente lo lee como DOUBLE.
    if "e" not in s and len(s.lstrip("-").replace(".", "").lstrip("0")) > MAX_EXACT_DECIMAL_DIGITS:
        s += "e0"
    return s


def _emit(tree: tuple, threshold: ThresholdFn | None, readable: bool) -> str:
    op = tree[0]
    if op == "const":
        return "TRUE" if tree[1] else "FALSE"
    if op in COMPARE:
        sym = ">" if op == "gt" else "<"
        return f"{tree[1][1]} {sym} {_fmt(threshold_of(tree, threshold), readable)}"
    if op == "not_":
        return f"NOT ({_emit(tree[1], threshold, readable)})"
    if op in ("and_", "or_"):
        word = "AND" if op == "and_" else "OR"
        return f"({_emit(tree[1], threshold, readable)}) {word} ({_emit(tree[2], threshold, readable)})"
    raise ValueError(f"Nodo desconocido: {op}")


def to_sql(tree: tuple, threshold: ThresholdFn | None = None, *, readable: bool = False,
           do_simplify: bool = True) -> str:
    if do_simplify:
        tree = simplify(tree)
    return _emit(tree, threshold, readable)


def validate_sql(expr: str, dialect: str = "duckdb") -> bool:
    """Valida la sintaxis con sqlglot. Devuelve True si sqlglot no está instalado."""
    try:
        import sqlglot
    except ImportError:  # pragma: no cover
        return True
    sqlglot.parse_one(f"select * from t where {expr}", read=dialect)
    return True
