---
tags: [layer/l0, agents, audit]
created: 2026-08-06
purpose: Log de auditoría append-only de acciones de agentes (JSONL)
---

# AGENT_SESSION_LOG — Registro de Auditoría de Agentes

> **Propósito**: Trazabilidad completa de acciones de agentes (register, lock, unlock, heartbeat, session_close).
> **Formato**: JSON Lines (JSONL) — un objeto JSON por línea. Append-only, nunca editar entradas existentes.

---

## Esquema de Entrada

```json
{
  "timestamp": "2026-05-15T10:00:00Z",
  "agent_id": "opencode-alpha",
  "role": "worker",
  "action": "lock_acquire",
  "resource": "STATE/WORKSPACE_STATE.md",
  "status": "success",
  "details": "acquired"
}
```

### Acciones registradas

| action | Cuándo |
|--------|--------|
| `register` | Al registrarse un agente |
| `lock_acquire` / `lock_release` | Operaciones de lock |
| `force_unlock` | Force-unlock por admin/supervisor |
| `agent_heartbeat` | Refresco de heartbeat |
| `session_close` | Cierre de sesión |
| `task_add` | Alta de tarea |
| `mark_zombie` | Sesión marcada como zombie por cleanup |

---

<!-- CUSTOMIZE: Las entradas se agregan aquí (una por línea) por el lock_manager,
     orchestrator, cleanup_orphans y las tools MCP del ciclo de vida agéntico.
     No editar a mano excepto en emergencias. -->

---

[[00_Global/Home.md|🏠 Home]]

> **Última actualización**: 2026-08-06
