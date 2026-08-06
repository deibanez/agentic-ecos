---
tags: [home, dataview]
created: 2026-08-06
purpose: Hub central del vault autodocumental de agentic-ecos
---

# agentic-ecos — Home

> Hub central del vault autodocumental. agentic-ecos se documenta con su propia
> infraestructura agéntica — este vault es la demo viviente.

---

## El Proyecto

**agentic-ecos** es el plano de control del ecosistema: un MCP server que
inicializa, gestiona y opera infraestructura agéntica trazable en cualquier
conjunto de proyectos digitales.

- Documentación arquitectónica: [[../ARCHITECTURE]]
- Guía de uso: [[../README]]

---

## Pulso del Ecosistema

> Sincronizado automáticamente por `sync_home_md` — se actualiza cuando el
> ecosistema crece (nuevo proyecto, patrón o trap).

<!-- AUTO_START: pulse -->
| Metrica | Valor |
|---------|-------|
| Proyectos registrados | 0 |
| Con infra agencia | 0 |
| Sin infra agencia | 0 |
| Tareas en backlog | 0 |
| Patrones built-in | 17 |
| Traps curados | 0 |
| Patrones en experimentacion | 0 |

_Actualizado: 2026-08-06 06:43 UTC_
<!-- AUTO_END: pulse -->

---

## Conocimiento por Tier

<!-- AUTO_START: knowledge-table -->
| Tier | Patrones | Traps |
|------|:---:|:---:|
| 1 · Built-in | 17 | — |
| 2 · Knowledge | 1 | 0 |
| 3 · Custom | 0 | — |
<!-- AUTO_END: knowledge-table -->

---

## Tareas Activas

```dataview
TASK FROM "00_Global/AGENT_TASKS.md"
WHERE !completed
```

## Agentes Activos

```dataview
TABLE agent_id as Agente, role as Rol, status as Estado
FROM "00_Global/AGENT_REGISTRY.md"
WHERE contains(status, "active")
```

## Estado del Desarrollo

```dataview
TABLE status as Estado
FROM "00_Global/STATE/WORKSPACE_STATE.md"
```

---

## Mapas de Contenido (MOCs)

- [[00_Global/MOC-Agents.md|Agentes]] · [[00_Global/MOC-Rules.md|Reglas]] · [[00_Global/MOC-Architecture.md|Arquitectura]]
- [[00_Global/MOC-Repos.md|Componentes]] · [[00_Global/MOC-Operations.md|Operaciones]] · [[00_Global/MOC-Guides.md|Guías]] · [[00_Global/MOC-Tasks.md|Tareas]]

---

## Acceso Rápido

- [[00_Global/AGENT_TASKS.md|Cola de tareas]] · [[00_Global/AGENT_REGISTRY.md|Registro de agentes]]
- [[00_Global/AGENT_COMMS.md|Comunicación]] · [[00_Global/AGENT_SESSION_LOG.md|Log de sesiones]]
- [[00_Global/STATE/WORKSPACE_STATE.md|Estado del desarrollo]]
- [[00_Global/dashboards/task-dashboard.md|Dashboard de tareas]]
- [[00_Global/RULES/AGENT_SKILLS.md|Skills para extender agentic-ecos]]
- [[00_Global/RULES/AGENT_PROTOCOL.md|Protocolo de operación]]

---

## Tags

`#rules` `#agents` `#architecture` `#adr` `#iac` `#ci-cd` `#state` `#guide` `#reference` `#roadmap` `#runbook` `#risk` `#tasks` `#dataview`

---

> Ultima actualizacion: 2026-08-06
