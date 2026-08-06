---
tags: [home, dataview]
created: {{DATE}}
purpose: Hub central del vault de {{PROJECT_NAME}}
---

# 🏠 {{PROJECT_NAME}} — Home

> **Hub central del workspace agéntico.** Todos los archivos taggeados tienen links de vuelta aquí.

---

## Estado del Ecosistema

<!-- ```dataview
TABLE type as Tipo, status as Estado, phase as Fase
FROM "repos" OR "components"
WHERE file.name = "overview"
``` -->

> ⚠️ CUSTOMIZE: Configura tus queries Dataview según la estructura de tu proyecto.

---

## Tareas Activas

<!-- ```dataview
TASK FROM "00_Global/AGENT_TASKS.md"
WHERE !completed
``` -->

---

## Agentes Activos

<!-- ```dataview
LIST FROM "00_Global/AGENT_REGISTRY.md"
WHERE contains(agent, "[status:: active]")
``` -->

---

## Mapas de Contenido (MOCs)

- [[00_Global/MOC-Agents.md|🤖 Agentes]] · [[00_Global/MOC-Rules.md|📜 Reglas]] · [[00_Global/MOC-Architecture.md|🏗 Arquitectura]]
- [[00_Global/MOC-Repos.md|📦 Componentes]] · [[00_Global/MOC-Operations.md|🔧 Operaciones]] · [[00_Global/MOC-Guides.md|📖 Guías]] · [[00_Global/MOC-Tasks.md|📋 Tareas]]

---

## Acceso Rápido

- [[00_Global/AGENT_TASKS.md|📋 Cola de tareas]] · [[00_Global/AGENT_REGISTRY.md|🤖 Registro de agentes]]
- [[00_Global/AGENT_COMMS.md|💬 Comunicación]] · [[00_Global/AGENT_SESSION_LOG.md|📜 Log de sesiones]]
- [[00_Global/STATE/WORKSPACE_STATE.md|📊 Estado del workspace]]
- [[00_Global/dashboards/task-dashboard.md|📊 Dashboard de tareas]]

---

## Tags

`#rules` `#agents` `#architecture` `#adr` `#iac` `#ci-cd` `#state` `#guide` `#reference` `#roadmap` `#runbook` `#risk` `#tasks` `#dataview`

---

> **Última actualización**: {{DATE}}
