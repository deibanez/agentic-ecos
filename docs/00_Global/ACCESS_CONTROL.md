---
tags: [layer/l0, agents]
---

# ACCESS_CONTROL — Matriz de Permisos por Recurso

> **Propósito**: Definir qué roles pueden leer/modificar cada recurso del proyecto **agentic-ecos**.

---

## Roles

| Rol | Nivel | Quién lo obtiene |
|-----|-------|------------------|
| `explorer` | Solo lectura | Agentes de consulta, agentes nuevos sin tarea asignada |
| `worker` | READ + WRITE bajo lock | Agentes con tarea asignada |
| `supervisor` | READ + WRITE sin lock + assign tasks | Agentes coordinadores |
| `admin` | FULL + force-unlock | Humano o agente de confianza explícita |

---

## Matriz de Acceso

| Recurso | explorer | worker | supervisor | admin |
|---------|----------|--------|------------|-------|
| **AGENT_REGISTRY.md** | READ | WRITE (propia fila) | WRITE (agentes asignados) | FULL |
| **AGENT_TASKS.md** | READ | WRITE (bajo lock) | WRITE | FULL |
| **kanban/\*** | N/A (auto-generado) | N/A (no editar a mano) | N/A | FULL |
| **ACCESS_CONTROL.md** | READ | READ | READ | FULL |
| **LOCK_PROTOCOL.md** | READ | READ | READ | FULL |
| **AGENT_COMMS.md** | READ | APPEND | APPEND | FULL |
| **AGENT_SESSION_LOG.md** | READ | APPEND (acciones propias) | APPEND | FULL |
| **RULES/\*** | READ | READ | READ | FULL |
| **STATE/\*** | READ | WRITE (bajo lock) | WRITE | FULL |
| **{repo}/MEMORY_BANK.md** | READ | WRITE (bajo lock) | WRITE | FULL |
| **.locks/\*** | — | RW (propios) | RW (cualquiera) | FULL |

<!-- CUSTOMIZE: Agrega recursos específicos de agentic-ecos a la matriz -->

**Leyenda:**
- `READ` = puede leer el archivo
- `WRITE` = puede modificar el archivo
- `WRITE (bajo lock)` = debe adquirir lock antes de escribir
- `APPEND` = solo puede agregar contenido al final
- `WRITE (propia fila)` = solo puede modificar su propia entrada
- `FULL` = READ + WRITE + DELETE + force-unlock

---

## Penalties por Violación

| Violación | Consecuencia |
|-----------|-------------|
| Escritura sin lock en recurso lockeable | Advertencia pública en AGENT_COMMS.md |
| 3 violaciones de lock | Downgrade a `explorer` por 24h |
| Force-unlock sin autorización | Escalado a admin + suspensión temporal |
| Modificar sección READ-only | Reversión del cambio + advertencia |
| Borrar entrada de AGENT_REGISTRY.md | Violación grave — escalado a admin |

---

> **Última actualización**: 2026-08-06
> **Versión**: 1.0.0
