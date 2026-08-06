---
tags: [home, dataview]
created: 2026-08-06
purpose: Hub central del vault autodocumental de agentic-ecos
---

# 🏠 agentic-ecos — Home

> **Hub central del vault autodocumental.** agentic-ecos se documenta con su
> propia infraestructura agéntica. Este vault es la demo viviente.

---

## El Proyecto

**agentic-ecos** es el plano de control del ecosistema: un MCP server que
inicializa, gestiona y opera infraestructura agéntica trazable en cualquier
conjunto de proyectos digitales.

- **Documentación arquitectónica**: [[../ARCHITECTURE]]
- **Guía de uso**: [[../README]]

---

## Tareas Activas

```dataview
TASK FROM "00_Global/AGENT_TASKS.md"
WHERE !completed
```

---

## Estado del Desarrollo

```dataview
TABLE status as Estado, version as Versión
FROM "00_Global/STATE/WORKSPACE_STATE.md"
```

---

## Mapas de Contenido (MOCs)

- [[00_Global/MOC-Agents.md|🤖 Agentes]] · [[00_Global/MOC-Rules.md|📜 Reglas]] · [[00_Global/MOC-Architecture.md|🏗 Arquitectura]]
- [[00_Global/MOC-Repos.md|📦 Componentes]] · [[00_Global/MOC-Operations.md|🔧 Operaciones]] · [[00_Global/MOC-Guides.md|📖 Guías]] · [[00_Global/MOC-Tasks.md|📋 Tareas]]

---

## Acceso Rápido

- [[00_Global/AGENT_TASKS.md|📋 Cola de tareas]] · [[00_Global/AGENT_REGISTRY.md|🤖 Registro de agentes]]
- [[00_Global/AGENT_COMMS.md|💬 Comunicación]] · [[00_Global/AGENT_SESSION_LOG.md|📜 Log de sesiones]]
- [[00_Global/STATE/WORKSPACE_STATE.md|📊 Estado del desarrollo]]
- [[00_Global/dashboards/task-dashboard.md|📊 Dashboard de tareas]]
- [[00_Global/RULES/AGENT_SKILLS.md|🛠 Skills para extender agentic-ecos]]
- [[00_Global/RULES/AGENT_PROTOCOL.md|📜 Protocolo de operación]]

---

## Tags

`#rules` `#agents` `#architecture` `#adr` `#iac` `#ci-cd` `#state` `#guide` `#reference` `#roadmap` `#runbook` `#risk` `#tasks` `#dataview`

---

> **Última actualización**: 2026-08-06
