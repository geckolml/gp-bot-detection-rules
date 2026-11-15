## Why

El valor diferencial del proyecto es que las reglas evolucionadas no se quedan
en un notebook: se compilan a SQL y se ejecutan como modelos de dbt sobre el
mismo warehouse que calcula las features. Para que esto sea confiable, la regla
en SQL debe marcar exactamente las mismas filas que la regla evaluada en Python.

Fase del curso: IV (análisis de la solución óptima en el contexto real).

## What Changes

- Compilador árbol → expresión SQL con umbrales reales (no cuantiles).
- Simplificación de constantes (`True AND x → x`, `NOT NOT x → x`, etc.).
- Generación de modelos dbt en `dbt_project/models/moderation/`.
- Validación de sintaxis con sqlglot y prueba de equivalencia Python ↔ DuckDB.

## Capabilities

### New Capabilities
- `sql-rule-compiler`: traducción fiel y desplegable de reglas a SQL / dbt.

### Modified Capabilities
- Ninguna.

## Impact

- Código nuevo: `evo/to_sql.py`, `evo/export_dbt.py`.
- Modelos generados en `dbt_project/models/moderation/` (se versionan solo los elegidos como finales).
