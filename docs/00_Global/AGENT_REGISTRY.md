---
tags: [layer/l0, agents, identity, dataview]
created: 2026-08-06
updated: 2026-08-06
purpose: Identidad y sesiones de agentes, registro de operación
---

# AGENT_REGISTRY — Identidad y Sesiones de Agentes

> **Propósito**: Registrar qué agentes están operando, su rol, y su sesión activa.
> **Formato**: Append-only. Nunca borrar entradas, solo marcar como `inactive`.
> **Lectura obligatoria**: Cualquier agente debe leer este archivo al inicio y registrarse antes de ejecutar acciones.

---

## Agentes Registrados

| Agent ID | Role | Session Token | Started | Last Heartbeat | Status | Current Task |
|----------|------|---------------|---------|----------------|--------|--------------|

<!-- CUSTOMIZE: Los agentes se agregan aquí al registrarse.
     Formato: | {agent-id} | {role} | {token} | {ISO-start} | {ISO-heartbeat} | active | {task} | -->

---

## Roles Disponibles

| Rol | Nivel | Descripción |
|-----|-------|-------------|
| `explorer` | Solo lectura | Agente de consulta, no modifica nada |
| `worker` | READ + WRITE bajo lock | Agente con tarea asignada |
| `supervisor` | READ + WRITE + assign tasks | Agente coordinador |
| `admin` | FULL + force-unlock | Humano o agente de confianza |

Ver `ACCESS_CONTROL.md` para la matriz detallada de permisos.

---

## Protocolo de Registro

### 1. Generar Agent ID
```
Formato: {tipo}-{identificador}
Ejemplos: opencode-agentic_ecos, cline-frontend, copilot-backend
```

### 2. Determinar Rol
- Por defecto: `explorer` (solo lectura)
- Si se asigna una tarea explícita: `worker`
- Si se coordina una fase: `supervisor`
- Solo admin puede crear admin

### 3. Registrar Entrada
Agregar una fila a la tabla con: Agent ID, Role, Session Token, Started (ISO UTC), Last Heartbeat, Status=`active`, Current Task.

### 4. Heartbeat
Refrescar `Last Heartbeat` cada 5 minutos mientras se esté operando.

### 5. Cierre de Sesión
Al finalizar: marcar `Status = inactive`, liberar locks activos, escribir resumen en `AGENT_SESSION_LOG.md`.

---

## Active Agent Fields for Dataview

<!-- CUSTOMIZE: Al registrar un agente activo, agregar una línea aquí:
     - [agent:: {id}] [agent_role:: {role}] [agent_task:: {desc}] -->

_(0 agentes activos)_

---

> **Última actualización**: 2026-08-06
