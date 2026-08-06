---
tags: [layer/l0, tasks, agent-framework, dataview]
created: 2026-08-06
updated: 2026-08-06
purpose: Fuente canónica de tareas del desarrollo de agentic-ecos. Los boards Kanban son vistas derivadas.
canonical: true
---

# AGENT_TASKS — Cola de Tareas (Canónica) de agentic-ecos

> ⚠️ **Fuente de verdad única.** Los boards Kanban en `kanban/` son vistas derivadas.
> Editar solo aquí. Ejecutar `python agentic_ecos/generator.py` para regenerar los boards
> (o `scripts/sync_kanban.py` si el scripts/ local existe).

---

<!-- TASKS_START -->

- [ ] T1: Extracción de patrones desde agv-docs (upgrade unidireccional) [priority:: high] [status:: backlog] [type:: feature] [repo:: agentic-ecos]
- [ ] T2: Skill de OpenCode para orquestar la inicialización [priority:: medium] [status:: backlog] [type:: feature] [repo:: agentic-ecos]
- [ ] T3: RAG opt-in para vaults grandes [priority:: low] [status:: backlog] [type:: feature] [repo:: agentic-ecos]
- [ ] T4: Test de promoción de pattern custom → patterns.py [priority:: medium] [status:: backlog] [type:: bug] [repo:: agentic-ecos]
- [ ] T5: Documentar flujo de migración de data/ entre máquinas [priority:: medium] [status:: backlog] [type:: docs] [repo:: agentic-ecos]
- [x] T6: Implementar conocimiento 4-tier + branches + tasks cross-cutting + connect multi-agente [priority:: high] [status:: done] [type:: feature] [repo:: agentic-ecos]
- [x] T7: Escribir CONTRIBUTING.md (flujo de forking, upgrade, ciclo del conocimiento) [priority:: medium] [status:: done] [type:: docs] [repo:: agentic-ecos]
- [x] T8: Documentar flujo de fork privado para privacidad (CONTRIBUTING §9, README, ARCHITECTURE, instructions, AGENTS) [priority:: medium] [status:: done] [type:: docs] [repo:: agentic-ecos]
- [x] T9: Refinar modelo: solo main público, ecosystem/* en forks privados, data/ patterns/presets commiteados [priority:: medium] [status:: done] [type:: docs] [repo:: agentic-ecos]

<!-- TASKS_END -->

---

## Campos Dataview

| Campo | Valores | Descripción |
|-------|---------|-------------|
| `[priority::]` | high / medium / low | Prioridad |
| `[status::]` | backlog / doing / review / done / blocked | Estado actual |
| `[type::]` | ci-cd / infra / docs / monitoring / bug / feature / security / ops / agents / iac | Categoría |
| `[repo::]` | nombre del componente | Componente afectado |
| `[depends::]` | T-id | Dependencia (opcional) |
| `[agent::]` | id del agente | Asignado (opcional) |

---

[[00_Global/Home.md|🏠 Home]] · [[00_Global/kanban/tasks.md|💼 Tasks Board]]

> **Última actualización**: 2026-08-06
