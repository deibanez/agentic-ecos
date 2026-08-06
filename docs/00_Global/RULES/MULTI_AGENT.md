---
tags: [layer/l0, rules, agents]
---

# MULTI_AGENT — Protocolos de Orquestación Multi-Agente

> **Propósito**: Definir cómo múltiples agentes coordinan, comunican y hacen handoff en **agentic-ecos**.

---

## I. Agente Registry y Sesiones

- Un agente no registrado = solo lectura (explorer)
- Usar `agent_register()` para aparecer en los dashboards
- Sesiones expiran después de 1h sin heartbeat
- Al cerrar sesión, liberar todos los locks y actualizar SESSION_LOG

## II. Lock Protocol

Ver `LOCK_PROTOCOL.md` para el protocolo completo.

- Adquirir lock antes de escribir cualquier recurso marcado como `WRITE (bajo lock)`
- Heartbeat cada 5 min
- TTL default: 30 min
- Force-unlock solo para admin/supervisor

## III. Handoff Protocol

> **Cuando terminas una tarea y otro agente/humano continúa:**

```
1. Asegurar que todos los cambios están commiteados y pusheados
2. Liberar locks adquiridos
3. Escribir handoff en AGENT_COMMS.md con label `handoff`
4. Actualizar MEMORY_BANK.md local (estado, hecho, falta, decisiones, próximos)
5. Si aplica: actualizar STATE/WORKSPACE_STATE.md
6. Dejar resumen ejecutivo en AGENT_SESSION_LOG.md
```

## IV. Git Workflow Multi-Agente

<!-- CUSTOMIZE: Define tu esquema de branches multi-agente aquí.
     Ejemplo:
     develop                                  ← Main integration branch
     ├── feature/{agente}/{desc}              ← Agente A
     ├── feature/{agente}/{desc}              ← Agente B (en paralelo)
-->

**Reglas:**
- Cada agente trabaja en su branch con naming descriptivo
- PR apunta siempre a la branch de integración
- Si dos agentes modifican el mismo módulo compartido → PR sequential, no paralelo

### Task Ownership

| Rol | Responsabilidad |
|-----|----------------|
| **Agente de Fase** | Implementa el componente asignado |
| **Agente Core** | Modifica módulos compartidos |
| **Agente Integrador** | Mergea PRs, resuelve conflictos, verifica gates |
| **Humano** | Aprueba PRs, decide cortes, resuelve bloqueantes |

## V. Cross-Repo Communication Protocol

| Señal | Medio | Cuándo | Contenido mínimo |
|-------|-------|--------|------------------|
| **Fase completada** | AGENT_COMMS.md + PR mergeado | Fin de fase | `[HANDOFF] Fase N completa — {repo}` |
| **Bloqueante** | AGENT_COMMS.md + label `blocked` | Necesitas algo de otro repo | `[BLOCKED] Esperando {recurso}` |
| **Error en CI/CD** | AGENT_COMMS.md + label `notice` | Falla de workflow | `[NOTICE] {workflow} falló` |
| **Status periódico** | STATE/WORKSPACE_STATE.md | Semanal / post-fase | Tabla de fases actualizada |

## VI. Distributed Coordination via Git

### Task Claiming (Race-Condition-Free)

```
Agent A:                                  Agent B:
git pull                                  git pull
→ task T is unclaimed                     → task T is unclaimed
[agent:: A] [claimed:: T1]                 [agent:: B] [claimed:: T2]
git commit && git push → ✅ OK            git commit && git push → ❌ REJECTED
                                           git pull --rebase → task T shows [agent:: A]
                                           → pick different task
```

### Lock Protocol for Multi-Machine

- On shared filesystem: use `LOCK_PROTOCOL.md` (locks/ directory, local).
- On different machines: use git-based locks via `AGENT_REGISTRY.md`.

## VII. Error Recovery Protocol

| Síntoma | Acción del agente |
|---------|------------------|
| CI/CD workflow falla post-merge | Rollback commit, fix, re-deploy |
| Lock de agente expirado sin heartbeat | Reclamar lock automáticamente |
| Deadlock detectado | Liberar todos los locks, esperar 30s, reintentar en orden |
| Dependencia bloqueante | AGENT_COMMS.md con label `blocked` |

---

<!-- CUSTOMIZE: Agrega protocolos multi-agente específicos de tu proyecto:
     - Fases y gates de migración
     - Señales de comunicación de tu dominio
     - Ownership de tareas por componente -->

> **Última actualización**: 2026-08-06
> **Versión**: 1.0.0
