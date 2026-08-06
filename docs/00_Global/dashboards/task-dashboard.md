---
tags: [dashboard, dataview]
created: 2026-08-06
purpose: Dashboard de tareas + agentes activos
---

# 📊 Task & Agent Dashboard

> Consultas Dataview sobre AGENT_TASKS.md y AGENT_REGISTRY.md.

---

## Tareas por Prioridad

<!-- ```dataview
TASK FROM "00_Global/AGENT_TASKS.md"
WHERE contains(file.name, "AGENT_TASKS") AND contains(priority, "high")
``` -->

## Tareas Backlog

<!-- ```dataview
TASK FROM "00_Global/AGENT_TASKS.md"
WHERE contains(status, "backlog")
``` -->

## Agentes Activos

<!-- ```dataview
LIST FROM "00_Global/AGENT_REGISTRY.md"
WHERE contains(agent_role, "worker") OR contains(agent_role, "supervisor")
``` -->

---

[[00_Global/Home.md|🏠 Home]] · [[00_Global/AGENT_TASKS.md|📋 Cola canónica]] · [[00_Global/kanban/tasks.md|💼 Kanban]]

> **Última actualización**: 2026-08-06
