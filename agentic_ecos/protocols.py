"""Plantillas de protocolos agénticos para proyectos generados.

Cada protocolo es un template markdown con placeholders `{{PLACEHOLDER}}`
que el generador reemplaza según el config del proyecto. Los protocolos
son genéricos — no contienen referencias a AGViewer — y usan comentarios
`<!-- CUSTOMIZE: ... -->` para guiar la personalización.
"""

# ─── AGENT_PROTOCOL.md ────────────────────────────────────────────────────────

AGENT_PROTOCOL = """---
tags: [layer/l0, rules, agents]
---

# AGENT_PROTOCOL — Código de Conducta y Protocolos de Operación

> **Propósito**: Código de conducta agéntico para IAs que operan en **{{PROJECT_NAME}}**.
> **La IA debe leer este archivo al inicio de cada sesión** antes de ejecutar cualquier acción.

---

## I. Core Operating Principles

### 1.1 Memory Bank First Protocol

> **Siempre leer el memory bank antes de actuar.**

```
Orden de lectura al inicio de sesión:
1.  AGENT_REGISTRY.md                ← Registrarse
2.  ACCESS_CONTROL.md                ← Conocer permisos
3.  RULES/AGENT_PROTOCOL.md          ← Este archivo
4.  STATE/WORKSPACE_STATE.md         ← Estado del proyecto
5.  RULES/MULTI_AGENT.md             ← Protocolos multi-agente
6.  {repo}/MEMORY_BANK.md            ← Estado local del repo
7.  ARCHITECTURE.md                  ← Arquitectura del sistema
```

**Reglas:**
- Si el memory bank dice que algo está roto, **no asumas que está arreglado** — verifícalo.
- Si encuentras información que contradice el memory bank, **actualízalo**.
- Al finalizar cada sesión, **actualiza MEMORY_BANK.md** con lo que hiciste.

### 1.2 Risk Tiers

| Tier | Tareas | Lifecycle requerido |
|------|--------|---------------------|
| READ | Leer, analizar, planificar, explorar | Register + Session log (mínimo) |
| DOCS | Editar `.md` de docs/skills/rules | Register + Lock + Session log + Memory bank |
| CODE | Editar código | **Full**: Register + Lock + Heartbeat + Session log + Memory bank + Tests |
| INFRA | Deploy, escala, cambios de infraestructura | **Full** + Snapshot + Verify + Handoff |

### 1.3 Deliberation Framework

```
Fase 0: CLASIFICAR
├── Determinar el MODO OPERATIVO ANTES de leer nada:
│   DATA (datos runtime) / CODE / INFRA / CI/CD / DOCS
├── GATE: COMPLIANCE CHECK (obligatorio)
│   ├── [ ] ¿Hay sesiones zombie? → agent_close_session(stale_sweep=true)
│   ├── [ ] ¿Estoy registrado? → agent_register()
│   ├── [ ] ¿Voy a ESCRIBIR archivos? → agent_lock("acquire", <resource>)
│   ├── [ ] ¿Heartbeat activo? → agent_heartbeat() (tier CODE/INFRA)
│   └── Si algún check falla → NO PROCEDER. Resolver el gap primero.

Fase 1: ANALIZAR        ← ¿Cuál es el problema? ¿Qué leer primero? ¿Qué falta?
Fase 2: PLANIFICAR      ← ¿Enfoque más seguro/rápido/mantenible? Documentar el plan.
Fase 3: VALIDAR         ← ¿Rompe algo existente? ¿Rollback? ¿Aprobación humana?
Fase 4: EJECUTAR        ← Cambios atómicos, verificar cada paso.
Fase 5: VERIFICAR       ← ¿Funciona? ¿Efectos secundarios? ¿Memory bank actualizado?
```

### 1.4 Ask vs Act Thresholds

| Escenario | Acción |
|-----------|--------|
| El cambio es reversible y de bajo riesgo | ✅ Ejecutar directamente |
| El cambio modifica infraestructura en producción | ❌ Preguntar primero |
| No estás seguro del impacto | ❌ Preguntar primero |
| La información en memory bank está desactualizada | ⚠️ Investigar más, luego preguntar |
| Es un bugfix obvio (typo, import faltante) | ✅ Ejecutar directamente |
| Es un cambio arquitectónico | ❌ Proponer ADR, preguntar |

### 1.5 Verify Before Merge

> Cuando consolides, mergees o deduplicques información de múltiples fuentes de
> texto, SIEMPRE cruzar contra al menos una fuente de datos vivos antes de actuar.

```
1. Identificar las fuentes de texto a consolidar
2. Consultar datos vivos (estado real de CI/CD, deploys, healthchecks)
3. Contrastar punto por punto
4. Los datos vivos tienen prioridad — documentar discrepancias
```

---

## II. Change Execution Framework

### Safe Change Protocol

```
[REGISTER]  → [LOCK] → [READ] → [PLAN] → [VALIDATE] → [EXECUTE]
→ [VERIFY] → [COMMIT] → [LOG] → [DOCUMENT] → [UNLOCK]
```

### Rollback-First Mindset

```
□ ¿Puedo revertir este cambio con git revert?
□ ¿El cambio modifica datos persistentes?
□ ¿Tengo un plan de rollback documentado?
□ ¿El rollback toma menos tiempo que el fix?
Si respondiste NO a alguna: pausa y replantea.
```

### Learning Incorporation Reflex

> Cuando cometas un error que las reglas existentes no cubrían, codifica la regla
> que debió prevenirlo.

```
1. Identifica la regla que faltaba (no el síntoma)
2. Determina dónde va: AGENT_PROTOCOL.md / IAC_TRAPS.md / AGENTS.md
3. Redacta la regla de forma accionable
4. Commitea la regla + el fix juntos
```

---

## III. Evidence & Diagnosis Discipline

- **Cross-verification rule**: afirmaciones del ecosistema verificadas contra mínimo 2 fuentes.
- **Confidence levels**: ALTA (leí el código/error explícito), MEDIA (probable), BAJA (hipótesis).
- **No chain unverified hypotheses**: una hipótesis [BAJA] no puede ser premisa de otra.
- **Distinguir "archivo existe" de "infra operativa"**: runs > 0, no file exists.
- **Self-correction as protocol**: cada error → nueva regla.

---

## IV. Agent Session Checklist

| # | Paso | Comando / Acción |
|---|------|------------------|
| 1 | **Pull** | `git pull --rebase` |
| 2 | **Task** | Abrir AGENT_TASKS.md → elegir task sin `[agent::]` → claim |
| 3 | **Lock** | Acquire si el recurso lo requiere (ACCESS_CONTROL.md) |
| 4 | **Work** | Cambios atómicos según §II |
| 5 | **Heartbeat** | Cada 5 min |
| 6 | **Document** | Registrar en AGENT_SESSION_LOG.md |
| 7 | **Unlock** | Liberar locks |
| 8 | **Task Done** | `[status:: done]` + sync-kanban |
| 9 | **Reflect** | §VIII Session Retrospective |
| 10 | **Push** | `git add -A && git commit && git push` |

---

## VIII. Session Retrospective — Learning Integration

> Toda sesión debe concluir con una reflexión que codifique patrones emergentes.

```
1. ¿Qué patrones nuevos emergieron? (skills, reglas, traps)
2. ¿Qué descubriste que debería codificarse? ¿Dónde?
3. ¿El plan se verificó contra datos vivos?
4. ¿Hay algo que genere un falso positivo más adelante?
```

---

<!-- CUSTOMIZE: Agrega aquí reglas específicas de tu proyecto:
     - Traps y patrones propios de {{PROJECT_NAME}}
     - Casos reales de sesiones con lecciones aprendidas
     - Modos DATA/CODE específicos de tu dominio -->

> **Última actualización**: {{DATE}}
> **Versión**: 1.0.0
"""

# ─── MULTI_AGENT.md ───────────────────────────────────────────────────────────

MULTI_AGENT = """---
tags: [layer/l0, rules, agents]
---

# MULTI_AGENT — Protocolos de Orquestación Multi-Agente

> **Propósito**: Definir cómo múltiples agentes coordinan, comunican y hacen handoff en **{{PROJECT_NAME}}**.

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

> **Última actualización**: {{DATE}}
> **Versión**: 1.0.0
"""

# ─── LOCK_PROTOCOL.md ─────────────────────────────────────────────────────────

LOCK_PROTOCOL = """---
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

> **Última actualización**: {{DATE}}
> **Versión**: 1.0.0
"""

# ─── ACCESS_CONTROL.md ────────────────────────────────────────────────────────

ACCESS_CONTROL = """---
tags: [layer/l0, agents]
---

# ACCESS_CONTROL — Matriz de Permisos por Recurso

> **Propósito**: Definir qué roles pueden leer/modificar cada recurso del proyecto **{{PROJECT_NAME}}**.

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
| **kanban/\\*** | N/A (auto-generado) | N/A (no editar a mano) | N/A | FULL |
| **ACCESS_CONTROL.md** | READ | READ | READ | FULL |
| **LOCK_PROTOCOL.md** | READ | READ | READ | FULL |
| **AGENT_COMMS.md** | READ | APPEND | APPEND | FULL |
| **AGENT_SESSION_LOG.md** | READ | APPEND (acciones propias) | APPEND | FULL |
| **RULES/\\*** | READ | READ | READ | FULL |
| **STATE/\\*** | READ | WRITE (bajo lock) | WRITE | FULL |
| **{repo}/MEMORY_BANK.md** | READ | WRITE (bajo lock) | WRITE | FULL |
| **.locks/\\*** | — | RW (propios) | RW (cualquiera) | FULL |

<!-- CUSTOMIZE: Agrega recursos específicos de {{PROJECT_NAME}} a la matriz -->

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

> **Última actualización**: {{DATE}}
> **Versión**: 1.0.0
"""

# ─── AGENTS.md (workspace guide) ──────────────────────────────────────────────

AGENTS_GUIDE = """---
tags: [layer/l0, rules, agents]
---

# AGENTS.md — {{PROJECT_NAME}} Workspace Guide

> **Propósito**: Orientación compacta para agentes que operan en {{PROJECT_NAME}}.
> **La IA debe leer este archivo al inicio de cada sesión**.

---

## Descripción del Proyecto

<!-- CUSTOMIZE: Describe tu proyecto aquí -->

> {{PROJECT_DESCRIPTION}}

---

## Mapa de Repositorios / Componentes

| Componente | Tipo | IaC | CI/CD | Notas |
|-----------|------|-----|-------|-------|
{{REPO_ROWS}}

<!-- CUSTOMIZE: Ajusta el mapa de componentes según tu proyecto -->

---

## MCP Tools del Ecosistema

El MCP server `{{PROJECT_NAME}}` expone tools para los agentes. Tools principales:

| Tool | Para qué |
|------|----------|
| `agent_register` | Registrar agente en AGENT_REGISTRY.md |
| `agent_heartbeat` | Refrescar heartbeat (cada 5 min) |
| `agent_lock` | Gestionar locks multi-agente |
| `agent_add_task` | Crear tarea en la cola canónica |
| `agent_status` | Ver sistema multi-agente completo |
| `agent_close_session` | Cerrar sesión + liberar locks |
| `vault_build_graph` | Construir grafo de wiki links del vault |

{{DOMAIN_TOOLS_SECTION}}

---

## 🚫 Reglas de Protección

<!-- CUSTOMIZE: Define las reglas no-negociables de tu proyecto.
     Ejemplo:
     | # | Regla | Ámbito |
     |---|-------|--------|
     | 1 | Nunca hacer push/commit directo a `main` | Todos los repos |
     | 2 | Nunca modificar la DB de producción | Sin excepción |
     | 3 | Solo feature branches → PR → develop | Todos los cambios |
-->

{{PROTECTION_RULES}}

---

## Índice de Documentación

| Archivo | Propósito | Leer cuando... |
|---------|-----------|----------------|
| `AGENTS.md` | **Este archivo** — guía del workspace | Siempre primero |
| `AGENT_PROTOCOL.md` | Código de conducta + deliberación | Cada sesión (§1) |
| `AGENT_REGISTRY.md` | Identidad y sesiones de agentes | Al registrarse |
| `MULTI_AGENT.md` | Protocolos multi-agente, handoff | Trabajo multi-agente |
| `IAC_TRAPS.md` | Conocimiento tribal (traps técnicos) | Debugging de infraestructura |
| `ACCESS_CONTROL.md` | Matriz de permisos por rol | Antes de modificar recursos |
| `LOCK_PROTOCOL.md` | Sistema de locks | Antes de adquirir lock |
| `AGENT_COMMS.md` | Comunicación entre agentes | Handoff, bloqueos |
| `AGENT_SESSION_LOG.md` | Log de auditoría | Después de cada acción |
| `AGENT_TASKS.md` | Cola de tareas (canónica) | Al buscar qué hacer |
| `STATE/WORKSPACE_STATE.md` | Estado del proyecto | Al inicio de sesión |

---

> **Última actualización**: {{DATE}}
> **Versión**: 1.0.0
"""

# Diccionario para lookup por nombre.
PROTOCOLS = {
    "agent_protocol": AGENT_PROTOCOL,
    "multi_agent": MULTI_AGENT,
    "lock_protocol": LOCK_PROTOCOL,
    "access_control": ACCESS_CONTROL,
    "agents_guide": AGENTS_GUIDE,
}


def get_protocol(name: str) -> str:
    """Return a protocol template by name, or raise KeyError."""
    if name not in PROTOCOLS:
        raise KeyError(
            f"Protocol '{name}' not found. Available: {', '.join(sorted(PROTOCOLS))}"
        )
    return PROTOCOLS[name]
