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
| `ecosystem_branch_create` | Creación de branch `ecosystem/{name}` |
| `ecosystem_sync_upstream` | Sync de una branch con upstream |
| `ecosystem_merge_main` | Merge de main a la branch de ecosistema |

---

<!-- CUSTOMIZE: Las entradas se agregan aquí (una por línea) por el lock_manager,
     orchestrator, cleanup_orphans y las tools MCP del ciclo de vida agéntico.
     No editar a mano excepto en emergencias. -->

---

[[00_Global/Home.md|🏠 Home]]

> **Última actualización**: 2026-08-06
{"timestamp": "2026-08-06T03:58:55Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Actualizar documentaci\u00f3n del vault):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Com"}
{"timestamp": "2026-08-06T03:58:55Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T03:59:00Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Actualizar documentaci\u00f3n del vault):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Com"}
{"timestamp": "2026-08-06T03:59:00Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T03:59:00Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Actualizar documentaci\u00f3n del vault):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Com"}
{"timestamp": "2026-08-06T03:59:00Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T03:59:06Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E2", "status": "success", "details": "type=feature, plan=Plan determin\u00edstico para E2 (Implementar feature cr\u00edtica):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + p"}
{"timestamp": "2026-08-06T03:59:06Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E2", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T03:59:36Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E2", "status": "success", "details": "type=feature, plan=Plan determin\u00edstico para E2 (Tarea feature):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + push con [agent"}
{"timestamp": "2026-08-06T03:59:36Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E2", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T03:59:36Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Tarea docs):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + push con [agent:: "}
{"timestamp": "2026-08-06T03:59:36Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T04:00:26Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E2", "status": "success", "details": "type=feature, plan=Plan determin\u00edstico para E2 (Tarea feature):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + push con [agent"}
{"timestamp": "2026-08-06T04:00:26Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E2", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T04:00:26Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Tarea docs):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + push con [agent:: "}
{"timestamp": "2026-08-06T04:00:26Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
{"timestamp": "2026-08-06T04:01:09Z", "agent_id": "bot-ci", "role": "worker", "action": "task_execute_dryrun", "resource": "E1", "status": "success", "details": "type=docs, plan=Plan determin\u00edstico para E1 (Tarea docs):\n1. Revisar el estado actual del ecosistema\n2. Implementar cambios at\u00f3micos con T-ID\n3. Verificar con validate_structure y tests\n4. Commit + push con [agent:: "}
{"timestamp": "2026-08-06T04:01:09Z", "agent_id": "bot-ci", "role": "worker", "action": "task_loop_done", "resource": "E1", "status": "success", "details": "iterations=1"}
