---
tags: [layer/l0, agents, guide]
created: {{DATE}}
purpose: Quickstart token-optimizado para agentes nuevos
---

# AGENT_ONBOARDING — Quickstart para Agentes Nuevos

> **Propósito**: Iniciar una sesión en **{{PROJECT_NAME}}** con el mínimo de lecturas obligatorias.
> Primera sesión: leer este archivo + las secciones MUST. Sesiones subsecuentes: consultar AGENT_SESSION_CACHE.md.

---

## MUST — Obligatorio al iniciar sesión

1. **Registrarse**: agregar fila en `AGENT_REGISTRY.md` (o tool `agent_register`)
2. **Leer** `AGENT_PROTOCOL.md` §1 (principios operativos) + §1.3 (deliberation framework)
3. **Consultar** `ACCESS_CONTROL.md` (conocer permisos)
4. **Leer** `STATE/WORKSPACE_STATE.md` (estado del proyecto)

## SHOULD — Recomendado

5. **Adquirir lock** (`LOCK_PROTOCOL.md`) si vas a escribir
6. **Heartbeat** cada 5 min si vas a operar por > 10 min
7. **Leer** `RULES/IAC_TRAPS.md` si vas a tocar infraestructura/CI-CD

## COULD — Opcional

8. **Leer** `RULES/AGENT_SKILLS.md` para encontrar skills específicas
9. **Revisar** `AGENT_COMMS.md` para mensajes dirigidos a ti

---

## Flujo de Sesión Estándar

```
1. git pull --rebase
2. Abrir AGENT_TASKS.md → elegir task sin [agent::]
3. Claim: [agent:: {id}] [status:: doing]
4. python scripts/sync_kanban.py
5. Trabajar (cambios atómicos, referenciando el T-ID)
6. Documentar en AGENT_SESSION_LOG.md
7. [status:: done] + sync_kanban.py
8. git commit + push
```

---

> **Última actualización**: {{DATE}}
