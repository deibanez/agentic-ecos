---
tags: [layer/l0, rules, agents]
---

# AGENTS.md — agentic-ecos Workspace Guide

> **Propósito**: Orientación compacta para agentes que operan en el desarrollo de agentic-ecos.
> **La IA debe leer este archivo al inicio de cada sesión**.

---

## Descripción del Proyecto

**agentic-ecos** es el plano de control del ecosistema: un MCP server que
inicializa, gestiona y opera infraestructura agéntica trazable en cualquier
conjunto de proyectos. Este vault (`docs/00_Global/`) es su autodocumentación,
generada con su propia infraestructura (demo viviente).

---

## Componentes del Repo

| Componente | Tipo | Descripción |
|-----------|------|-------------|
| `agentic_ecos/server.py` | código | MCP server (31 tools) |
| `agentic_ecos/generator.py` | código | init_project + generate_file + validate + CLI |
| `agentic_ecos/patterns.py` | código | tier 1: 15 patrones built-in |
| `agentic_ecos/protocols.py` | código | 5 plantillas de protocolos |
| `agentic_ecos/presets.py` | código | tier 1: 3 presets built-in |
| `agentic_ecos/ecosystem.py` | código | plano de control (agentic.toml, connect, tasks) |
| `agentic_ecos/storage.py` | código | data/ + knowledge/ + workspace/ carga/guardado |
| `agentic_ecos/knowledge.py` | código | promoción entre tiers |
| `agentic_ecos/knowledge/` | tier 2 | commiteado · comunidad (patterns/presets/traps) |
| `agentic_ecos/data/` | tier 3 | patterns/presets commiteados (fork privado) · snapshots/state gitignored |
| `agentic_ecos/static/` | código | scripts copiados a cada proyecto |
| `agentic_ecos/templates/` | código | plantillas markdown generables |
| `workspace/` | tier 2.5 | solo en branches de ecosistema (fork privado) · agentic.toml + tasks.md |
| `docs/` | docs | vault autodocumental |

---

## Cómo operar en este repo (agente)

Al igual que en cualquier proyecto agéntico, al iniciar sesión en agentic-ecos:

1. **Registrarse** en `AGENT_REGISTRY.md`
2. **Leer** `AGENT_PROTOCOL.md` §1 (deliberación) + `ACCESS_CONTROL.md`
3. **Revisar** `AGENT_TASKS.md` → claim de tarea (roadmap del proyecto)
4. **Leer** `STATE/WORKSPACE_STATE.md` (estado actual)
5. Si escribes código → **lock** sobre el recurso + heartbeat cada 5 min
6. Al terminar → `agent_close_session` + actualizar WORKSPACE_STATE

Los datos que descubras (patrones, presets) siguen el ciclo de 4 tiers:
1. **Descubrir** → `data/` (tier 3, commiteado en fork privado) vía `add_custom_pattern`
2. **Validar** (≥2 proyectos) → `workspace/` (tier 2.5) vía `promote_to_workspace`
3. **Compartir** (multi-ecosistema) → `knowledge/` (tier 2) vía `promote_to_knowledge`
4. **Madurar** → `agentic_ecos/patterns.py` (tier 1, built-in) + commitear

Todo se commitea en tu branch de ecosistema (`workspace/`, `knowledge/`,
`data/` patterns/presets). Solo el runtime data (`data/ecosystem-snapshots/`,
`data/state.json`) queda gitignored — no es conocimiento y genera conflictos.

---

## Reglas de Protección

| # | Regla | Ámbito |
|---|-------|--------|
| 1 | No promocionar patterns/presets a tier 1 sin validación en ≥2 proyectos | `patterns.py` / `presets.py` |
| 2 | No editar `data/*.json` a mano salvo emergencia (usar tools MCP) | `data/` |
| 3 | `data/patterns-custom.json` y `data/presets-custom.json` SÍ se commitean (fork privado, trazabilidad). `data/ecosystem-snapshots/` y `data/state.json` NO (runtime data). | `data/` |
| 4 | `workspace/` solo en branches de ecosistema (fork privado), nunca en main | `workspace/` |
| 5 | Todo cambio de API MCP (tools) debe actualizar README.md + ARCHITECTURE.md | `server.py` |
| 6 | **Solo `main` es público.** Fork **privado** obligatorio para cualquier ecosistema (`gh repo fork ... --private`). `workspace/` y `data/` nunca en repos públicos. | `workspace/` / `data/` |
| 7 | Nunca crear PR desde un branch con `workspace/` — contribuir desde un branch limpio de main (cherry-pick de `knowledge/`). Ver CONTRIBUTING.md §10 | PRs |

---

## Índice de Documentación

| Archivo | Propósito | Leer cuando... |
|---------|-----------|----------------|
| `AGENTS.md` | **Este archivo** — guía del workspace | Siempre primero |
| `AGENT_PROTOCOL.md` | Código de conducta + deliberación | Cada sesión (§1) |
| `AGENT_REGISTRY.md` | Identidad y sesiones de agentes | Al registrarse |
| `MULTI_AGENT.md` | Protocolos multi-agente, handoff | Trabajo multi-agente |
| `IAC_TRAPS.md` | Traps del desarrollo de agentic-ecos | Debugging del código |
| `ACCESS_CONTROL.md` | Matriz de permisos por rol | Antes de modificar recursos |
| `LOCK_PROTOCOL.md` | Sistema de locks | Antes de adquirir lock |
| `AGENT_COMMS.md` | Comunicación entre agentes | Handoff, bloqueos |
| `AGENT_SESSION_LOG.md` | Log de auditoría | Después de cada acción |
| `AGENT_TASKS.md` | Cola de tareas (canónica) | Al buscar qué hacer |
| `STATE/WORKSPACE_STATE.md` | Estado del proyecto | Al inicio de sesión |
| `../../ARCHITECTURE.md` | Arquitectura del sistema | Para entender el diseño |
| `../../README.md` | Uso e instalación | Para usar agentic-ecos |
| `../../CONTRIBUTING.md` | Uso, forking, ciclo del conocimiento, privacidad | Para forkear/contribuir/privacidad |

---

> **Última actualización**: 2026-08-06
> **Versión**: 1.0.0
