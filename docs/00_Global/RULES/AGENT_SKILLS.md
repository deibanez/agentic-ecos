---
tags: [layer/l0, rules, agents, skills]
created: 2026-08-06
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

## Skills de Dominio (Específicas de agentic-ecos)

| Skill | Cuándo usarla | Pasos |
|-------|--------------|-------|
| `add-pattern` | Descubriste un patrón agéntico en una sesión | `add_custom_pattern` MCP → data/patterns-custom.json → disponible para todos |
| `promote-pattern` | El pattern custom se validó en ≥2 proyectos | Copiar de data/ → agentic_ecos/patterns.py → commiteo → borrar de custom |
| `add-preset` | Necesitas un tipo de proyecto nuevo | `add_custom_preset` MCP → data/presets-custom.json |
| `bootstrap-project` | Inicializar infra agéntica en un proyecto | `init_project` MCP → registrar en agentic.toml → connect |
| `ecosystem-onboard` | Integrar el ecosistema completo | `ecosystem_init` → `ecosystem_status` → gaps → init_project |
| `upgrade-from-agv` | Sincronizar patrones desde agv-docs | Extraer patterns del vault fuente → revisar → promover |
| `connect-mcp` | Disponibilizar agentic-ecos en un proyecto | `connect` MCP → agrega entrada al opencode.jsonc |

Para cada skill nueva descubierta en una sesión, agregarla aquí
(Learning Incorporation Reflex).

---

## Referencia

- **MCP tools**: ver `AGENTS.md` → sección MCP Tools
- **Patrones**: `agentic_ecos/patterns.py` (15 built-in) + `data/patterns-custom.json` (custom)
- **Reglas**: `RULES/AGENT_PROTOCOL.md` (deliberación, evidencia) · `RULES/MULTI_AGENT.md` (coordinación)

---

> **Última actualización**: 2026-08-06
