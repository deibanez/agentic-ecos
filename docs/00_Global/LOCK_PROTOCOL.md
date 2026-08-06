---
tags: [layer/l0, agents]
---

# LOCK_PROTOCOL — Sistema de Locks para Escritura Multi-Agente

> **Propósito**: Prevenir race conditions cuando múltiples agentes modifican el mismo recurso.
> **Ubicación de locks**: `.locks/{resource_hash}.lock`
> **TTL default**: 30 minutos
> **Script auxiliar**: `scripts/lock_manager.sh`

---

## Formato del Lock

Cada archivo `.locks/{hash}.lock` contiene una línea con pipe-separated values:

```
agent_id | role | acquired_at | ttl_minutes | heartbeat_at
```

Ejemplo:
```
agent-a | worker | 2026-05-15T10:00:00Z | 30 | 2026-05-15T10:05:00Z
```

---

## Operaciones

### acquire_lock(resource, agent_id, role, ttl=30)
1. Calcular hash del resource path: `echo "$resource" | sha256sum | cut -d' ' -f1`
2. Leer `.locks/{hash}.lock`
3. Si **NO existe** → CREAR lock (atomic O_CREAT|O_EXCL), retornar `ACQUIRED`
4. Si **existe y heartbeat expirado** → RECLAMAR lock, retornar `RECLAIMED`
5. Si **existe y vigente y mismo agent_id** → RENOVAR heartbeat, retornar `RENEWED`
6. Si **existe y vigente y otro agent_id** → retornar `HELD_BY={agent_id}`

### release_lock(resource, agent_id)
1. Si `agent_id` coincide → BORRAR archivo, retornar `RELEASED`
2. Si otro `agent_id` → retornar `NOT_OWNER (held by {other})`
3. Si no existe → retornar `NOT_LOCKED`

### heartbeat_lock(resource, agent_id)
1. Si `agent_id` coincide → actualizar `heartbeat_at = now`, retornar `HEARTBEAT_OK`
2. Si no → retornar `NOT_OWNER`

### force_unlock(resource, agent_id, caller_role)
1. Solo `admin` o `supervisor` pueden hacer force-unlock
2. BORRAR archivo independientemente del owner
3. Registrar en `AGENT_SESSION_LOG.md` con action=`force_unlock`

---

## Reglas de Convivencia

1. **Siempre lock antes de escribir** cualquier recurso marcado como `WRITE (bajo lock)`
2. **Heartbeat cada 5 min** para mantener el lock vivo
3. **Liberar lock al terminar** (éxito o fracaso)
4. **Timeout automático**: lock expirado (> TTL sin heartbeat) es reclamable
5. **Force-unlock**: solo admin/supervisor, siempre registrado en el session log
6. **Si un agente muere**: lock expira solo después de TTL; supervisor puede force-unlock antes
7. **Locks anidados**: adquiérelos en orden alfabético para prevenir deadlocks
8. **Deadlock detection**: si un acquire falla 3 veces seguidas, libera todos, espera 30s, reintenta

---

## Git-based Distributed Locking (Multi-machine)

```
1. git pull --rebase                          ← Sync latest state
2. Check AGENT_REGISTRY.md for active locks
3. If resource locked by another agent → wait or pick another task
4. Add lock entry to your agent row: [lock:: resource] [locked_at:: ISO]
5. git commit -m "lock: resource [agent:: id]" && git push
   ↳ If push rejected → another agent pushed a lock → pull --rebase → retry
6. Do work
7. Remove [lock::] from your agent row
8. git commit -m "unlock: resource" && git push
```

---

## Resolución de Conflictos

| Situación | Acción Recomendada |
|-----------|-------------------|
| Lock ocupado por otro agente activo | Esperar 5 min, reintentar. Si persiste, preguntar en AGENT_COMMS.md |
| Lock ocupado por agente sin heartbeat reciente | Reclamar lock (expirado automáticamente) |
| Lock ocupado por agente caído | Supervisor hace force-unlock inmediato |
| Deadlock (A espera B, B espera A) | Ambos liberan locks, supervisor asigna orden |

---

> **Última actualización**: 2026-08-06
> **Versión**: 1.0.0
