# Flujo de trabajo: desarrollo guiado por specs (OpenSpec)

Este repositorio usa [OpenSpec](https://openspec.dev). Ningún cambio de
comportamiento se implementa sin una especificación previa.

## Estructura

```
openspec/
├── config.yaml        # contexto del proyecto y reglas para los artefactos
├── specs/             # verdad vigente: cómo se comporta el sistema hoy
└── changes/           # cambios propuestos (uno por carpeta)
    └── <cambio>/
        ├── proposal.md   # por qué y qué cambia
        ├── design.md     # cómo (decisiones técnicas)
        ├── tasks.md      # checklist de implementación
        └── specs/<capacidad>/spec.md   # requisitos (ADDED/MODIFIED/REMOVED)
```

## Ciclo de un cambio

1. **Proponer**: crear `openspec/changes/<cambio>/` con propuesta, diseño,
   specs y tareas (`/opsx:propose <cambio>` en Claude Code tras `openspec init`).
2. **Revisar**: la propuesta y las specs se aprueban antes de escribir código.
3. **Implementar**: seguir `tasks.md` en orden y marcar `[x]` cada tarea terminada
   (`/opsx:apply`). Cada requisito con escenario verificable tiene su test en `tests/`.
4. **Verificar**: `make test` dentro del contenedor; `openspec validate --all`.
5. **Archivar**: `openspec archive <cambio>` fusiona las specs del cambio en
   `openspec/specs/` cuando todas las tareas están completas.

## Reglas para agentes y colaboradores

- Leer `openspec/config.yaml` antes de proponer un cambio.
- Specs en español, conservando `SHALL`/`MUST`, `### Requirement:`,
  `#### Scenario:` y `**WHEN**`/`**THEN**` (formato que valida OpenSpec).
- Código e identificadores en inglés; docstrings y comentarios en español.
- Privacidad: nunca nombrar la plataforma real ni describir su tipo más allá de
  "plataforma social con chat y geolocalización". Nunca usar datos reales de usuarios.
- Todo se ejecuta en Docker (`make ...`); no asumir dependencias en el host.
- No versionar datos (`data/`), la base DuckDB ni `results/runs/`.
