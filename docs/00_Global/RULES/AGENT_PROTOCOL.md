---
tags: [layer/l0, rules, agents]
---

# AGENT_PROTOCOL — Código de Conducta y Protocolos de Operación

> **Propósito**: Código de conducta agéntico para IAs que operan en **agentic-ecos**.
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
     - Traps y patrones propios de agentic-ecos
     - Casos reales de sesiones con lecciones aprendidas
     - Modos DATA/CODE específicos de tu dominio -->

> **Última actualización**: 2026-08-06
> **Versión**: 1.0.0
