---
tags: [layer/l0, rules, agents, skills]
created: {{DATE}}
purpose: Catálogo de capacidades del agente (skills por dominio)
---

# AGENT_SKILLS — Catálogo de Capacidades del Agente

> **Propósito**: Catálogo de skills que un agente puede ejecutar, organizado por dominio.
> Cada skill tiene: cuándo usarla, pasos, y verificación.

---

## Skills de Ciclo de Vida (Genéricas)

| Skill | Cuándo usarla | Pasos |
|-------|--------------|-------|
| `agent-register` | Al iniciar sesión | Registrar en AGENT_REGISTRY.md, definir rol |
| `agent-heartbeat` | Cada 5 min de operación | Refrescar heartbeat en registry |
| `agent-lock` | Antes de escribir recursos | Acquire → trabajar → release |
| `agent-close-session` | Al terminar | Liberar locks + marcar inactive + log |
| `agent-claim-task` | Al buscar trabajo | Elegir task sin owner, claim, sync-kanban |
| `task-traceability` | Antes de cualquier acción | Verificar T-ID, registrar en session log |

## Skills de Coordinación (Genéricas)

| Skill | Cuándo usarla | Pasos |
|-------|--------------|-------|
| `handoff` | Transferir trabajo | Commit+push, liberar locks, mensaje en COMMS, actualizar MEMORY_BANK |
| `blocked-escalation` | Dependencia bloqueante | Mensaje `blocked` en COMMS con detalle |
| `zombie-sweep` | Al iniciar sesión | Cerrar sesiones stale (heartbeat > 30min) |

## Skills de Dominio (Específicas del Proyecto)

<!-- CUSTOMIZE: Documenta aquí las skills específicas de {{PROJECT_NAME}}.
     Organízalas por dominio (ej: IaC, Data, CI/CD, Docs) con el formato:

     | Skill | Cuándo usarla | Pasos |
     |-------|--------------|-------|
     | `deploy-service` | Al desplegar un servicio | Build → plan → apply → verify |

     Para cada skill nueva descubierta en una sesión, agregarla aquí
     (Learning Incorporation Reflex).
-->

---

## Referencia

- **MCP tools**: ver `AGENTS.md` → sección MCP Tools
- **Scripts locales**: `scripts/` (lock_manager, sync_kanban, orchestrator, cleanup_orphans, lock_dashboard)
- **Reglas**: `RULES/AGENT_PROTOCOL.md` (deliberación, evidencia) · `RULES/MULTI_AGENT.md` (coordinación)

---

> **Última actualización**: {{DATE}}
