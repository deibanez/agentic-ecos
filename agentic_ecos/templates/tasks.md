---
tags: [layer/l0, tasks, agent-framework, dataview]
created: {{DATE}}
updated: {{DATE}}
purpose: Fuente canónica única de tareas del ecosistema. Los boards Kanban son vistas derivadas.
canonical: true
---

# AGENT_TASKS — Cola de Tareas Multi-Agente (Canónica)

> ⚠️ **Fuente de verdad única.** Los boards Kanban en `kanban/` son vistas derivadas.
> Editar solo aquí. Ejecutar `python scripts/sync_kanban.py` para regenerar los boards.

---

<!-- TASKS_START -->

<!-- Agrega tus tareas aquí con líneas de checkbox. Reglas:
     • NO pongas ejemplos con formato de checkbox DENTRO de comentarios HTML:
       el parser los tomaría como tareas reales.
     • Formato de una línea de tarea (el parser detecta líneas que empiezan
       con guion + corchete + espacio):
       `- [ ] T1: Descripción de la tarea [priority:: high] [status:: backlog] [type:: feature] [repo:: backend]`
     • Campos:
       [priority::] high | medium | low
       [status::]   backlog | doing | review | done | blocked
       [type::]     ci-cd | infra | docs | monitoring | bug | feature | security | ops | agents | iac
       [repo::]     nombre del componente
       [depends::]  T-id (opcional)
       [due::]      YYYY-MM-DD (opcional, solo milestones)
       [agent::]    id del agente asignado (opcional)
-->

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
| `[due::]` | YYYY-MM-DD | Deadline (opcional) |
| `[agent::]` | id del agente | Asignado (opcional) |

## Protocolo

1. **Asignar tarea**: supervisor escribe `[status:: doing]` + `[agent:: id]`
2. **Bloquear**: cambiar `[status:: blocked]` + agregar razón en el texto
3. **Completar**: cambiar `[status:: done]` + evidencia verificable
4. **Sincronizar Kanban**: ejecutar `python scripts/sync_kanban.py`

---

[[00_Global/kanban/tasks.md|💼 Tasks Board]] · [[00_Global/kanban/roadmap.md|🗺 Roadmap]] · [[00_Global/Home.md|🏠 Home]]

> **Última actualización**: {{DATE}}
