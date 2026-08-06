# agentic-ecos — Arquitectura

> **Propósito**: Explica la arquitectura de agentic-ecos: el plano de control del
> ecosistema, los patrones agénticos que porta, y el pipeline de generación.
> **Audiencia**: Agentes y humanos que quieran usar, extender o mantener el sistema.

---

## 1. Visión

`agentic-ecos` es el **plano de control** del ecosistema: un MCP server que
inicializa, gestiona y opera infraestructura agéntica trazable en cualquier
conjunto de proyectos. No es un generador de archivos aislado — es la capa que
sabe *qué proyectos existen*, *cuáles tienen infra agéntica*, *cómo están de
salud* y *cómo inicializar los que faltan*.

```
┌───────────────────────────────────────────────────────────────┐
│                  agentic.toml (plano de control)               │
│  [ecosystem] name · workspace_root · defaults                  │
│  [[projects]] path · type · preset · agentic_infra · status    │
└──────────────────────────────┬────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │  agentic-ecos MCP Server (31 tools) │
              └────────────────┬────────────────┘
                               │ MCP (stdio)
              ┌────────────────┴────────────────┐
              │        AI Agent (OpenCode, etc.)    │
              └────────────────────────────────────┘
```

---

## 2. Capas de la infraestructura agéntica

Cada proyecto que agentic-ecos genera contiene 3 capas, heredadas del patrón
validado en el ecosistema AGViewer:

| Capa | Qué vive ahí | Archivos |
|------|-------------|----------|
| **L0 — Framework agéntico** | Locks, tasks, comms, session log, access control, lifecycle | `AGENT_REGISTRY.md`, `AGENT_TASKS.md`, `AGENT_COMMS.md`, `AGENT_SESSION_LOG.md`, `LOCK_PROTOCOL.md`, `ACCESS_CONTROL.md`, `scripts/lock_manager.*`, `scripts/sync_kanban.py`, `scripts/orchestrator.py`, `scripts/cleanup_orphans.py` |
| **L1 — MCP server del proyecto** | Tools de lifecycle + vault para que el agente opere el proyecto | `scripts/mcp_server.py`, `scripts/{project}_tools.py` (stubs de dominio) |
| **L2 — Documentación y protocolos** | Reglas de operación, skills, traps, estado | `RULES/AGENT_PROTOCOL.md`, `RULES/MULTI_AGENT.md`, `RULES/AGENT_SKILLS.md`, `RULES/IAC_TRAPS.md`, `STATE/WORKSPACE_STATE.md` |
| **L3 — Vault de conocimiento** | Navegación Obsidian: wiki links, tags, dashboards, MOCs | `Home.md`, `MOC-*.md`, `dashboards/*`, `kanban/*` |

---

## 3. Los 15 patrones agénticos

`agentic-ecos` codifica patrones validados en producción como datos (`patterns.py`).
Cada patrón tiene: `name`, `domain`, `description`, `when_to_use`, `implementation_guide`
y texto bilingüe EN/ES.

| Dominio | Patrones |
|---------|----------|
| **coordination** | `lock_system`, `task_system`, `comms_system`, `distributed_coordination` |
| **identity** | `agent_lifecycle` |
| **security** | `access_control` |
| **observability** | `session_audit`, `heartbeat_daemon`, `zombie_cleanup` |
| **workflow** | `kanban_sync` |
| **interface** | `mcp_tool_design`, `domain_tool_pattern` |
| **knowledge** | `vault_structure`, `protocol_writing`, `trap_documentation` |

**Decisiones clave de diseño** (heredadas del ecosistema fuente):

1. **File-based everything**: todo el estado vive en markdown bajo git. Sin DB ni servidor.
2. **Git como bus de coordinación**: los agentes coordinan vía `git push`; la resolución
   de races es determinista (first-push-wins).
3. **MCP como interfaz**: cualquier agente MCP-compatible puede operar.
4. **Canónico + vistas derivadas**: `AGENT_TASKS.md` es canónico; `kanban/` se regenera
   con `sync_kanban.py`. La automatización supera la disciplina.
5. **Auto-mejora**: cada error se codifica como regla, trap o skill (Learning Reflex).

---

## 4. Plano de control (`agentic.toml`)

### 4.1 Ubicación

El registro canónico se busca en orden:
1. `AGENTIC_ECOS_CONFIG` (env var)
2. Primer `agentic.toml` subiendo desde CWD
3. `~/.config/agentic-ecos/agentic.toml`

### 4.2 Esquema

```toml
[ecosystem]
name = "mi-ecosistema"
description = ""
workspace_root = "/abs/path"
created = "2026-08-05T00:00:00Z"
updated = "2026-08-05T00:00:00Z"

[defaults]
cloud = "aws"
ci_cd = "github-actions"
language = "es"
vault_path = "docs"

[[projects]]
name = "app1"
path = "app1"
type = "backend"
preset = "monorepo"
agentic_infra = true
status = "operational"
notes = ""
```

### 4.3 Semántica de `agentic_infra`

- **En `ecosystem_init`/`project_add`**: señales de infra (existe `00_Global/AGENTS.md`
  o similar). Es una heurística rápida de detección.
- **En `ecosystem_status`**: se recalcula con `validate_structure` — el valor real es
  la cobertura de los 16 archivos requeridos. Un proyecto con solo `AGENTS.md` tendrá
  `agentic_infra=true` en el registro pero `coverage_pct≈6%` en el status.

---

## 5. Pipeline de generación (`generator.init_project`)

`init_project` genera ~42 archivos en 9 pasos:

```
1. Crear estructura de directorios (.locks, DATA, 00_Global/STATE, kanban, ...)
2. Copiar scripts static (lock_manager.py/sh, sync_kanban, orchestrator, ...)
3. Renderizar protocolos (AGENT_PROTOCOL, MULTI_AGENT, LOCK_PROTOCOL, ...)
4. Renderizar archivos de estado (registry, tasks, comms, session_log, ...)
5. Generar MOCs del vault (7 Maps of Content interlinkeados)
6. Generar tools de dominio + MCP server skeleton
7. Generar instructions.md (prompt del agente)
8. Inicializar boards kanban vacíos
9. Registrar en agentic.toml (si hay config)
```

Los templates viven en `templates/` y usan placeholders `{{PLACEHOLDER}}` reemplazados
por `render_template()`. Los scripts static se copian tal cual (son agnósticos de path:
usan `Path(__file__).resolve().parent.parent` para ubicar `00_Global/`).

### Presets

| Preset | Estructura | Domain tools generadas |
|--------|-----------|----------------------|
| `monorepo` | Múltiples servicios, CI/CD compartido, IaC centralizada | `project_health`, `repo_details`, `deploy_service`, `branch_health` |
| `single_service` | Un servicio con componentes en subdirectorios | `build_status`, `test_report`, `deploy_status` |
| `data_pipeline` | Lambdas, batch, pipelines de datos | `pipeline_status`, `data_freshness`, `run_metrics` |

---

## 6. El MCP server del proyecto generado

Cada proyecto generado tiene su propio `scripts/mcp_server.py` con:
- Tools de **lifecycle agéntico**: `agent_register`, `agent_heartbeat`, `agent_lock`,
  `agent_add_task`, `agent_status`, `agent_close_session`
- Tools de **vault**: `vault_build_graph`, `vault_query_graph`, `vault_audit_coverage`
- Tools de **dominio** (desde `{project}_tools.py`): stubs que el equipo implementa

El patrón de dispatch (`HANDLERS` dict + `@server.call_tool()`) mantiene el core
portable y la lógica de dominio aislada en un módulo plugin.

---

## 7. Tools del MCP server de agentic-ecos (31)

### Generación y patrones
| Tool | Rol |
|------|-----|
| `init_project` | Genera el esqueleto agéntico completo en un proyecto + lo registra |
| `list_patterns` / `get_pattern` | Catálogo de 15 patrones built-in + knowledge + workspace + custom |
| `protocol_template` / `list_protocols` | Plantillas de protocolos |
| `generate_file` | Genera un archivo individual |
| `list_presets` | Presets built-in + knowledge + custom |

### Validación y guía
| Tool | Rol |
|------|-----|
| `validate_structure` | Checklist de 16 archivos requeridos |
| `suggest_next_steps` | Próximos pasos priorizados |
| `agentic_health` | Coverage + gaps + sugerencias |

### Plano de control del ecosistema
| Tool | Rol |
|------|-----|
| `ecosystem_init` | Crea `agentic.toml`, auto-detecta proyectos |
| `ecosystem_status` | Salud del ecosistema completo (cobertura por proyecto) |
| `ecosystem_config` | Devuelve el registro completo |
| `project_add` / `project_remove` | Registrar/eliminar proyectos |
| `connect` | Configura agentic-ecos para uno o más agentes (opencode/claude/cursor/auto/snippet) |
| `connect_status` | Detecta qué agentes tienen config y si agentic-ecos está conectado |
| `scan_opencode` | Qué proyectos tienen agentic-ecos conectado |

### Tareas cross-cutting
| Tool | Rol |
|------|-----|
| `ecosystem_tasks` | Agregado: tareas del workspace/tasks.md + conteo por proyecto |
| `ecosystem_task_add` | Agrega tarea cross-cutting al workspace/tasks.md |

### Storage orgánico (data/) y conocimiento
| Tool | Rol |
|------|-----|
| `add_custom_pattern` / `remove_custom_pattern` | Patrones tier 3 (personal, gitignored) |
| `add_custom_preset` / `remove_custom_preset` | Presets tier 3 |
| `save_snapshot` | Histórico de salud |
| `storage_status` | Estado del almacenamiento orgánico |
| `set_state` | Estado interno del MCP |
| `promote_to_workspace` | Mueve pattern de data/ → workspace/ (tier 2.5, tu branch) |
| `promote_to_knowledge` | Copia pattern de workspace/ → knowledge/ (tier 2, PR a upstream) |
| `knowledge_status` | Estado del conocimiento por tier |

### Otros
| Tool | Rol |
|------|-----|
| `rag_status` | RAG es opt-in (YAGNI por defecto) |

---

## 8. Decisiones técnicas relevantes

- **mcp>=1.27,<2**: la API con decoradores (`@server.list_tools()`,
  `@server.call_tool()`) cambió en mcp 2.0. Fijada la 1.x.
- **tomllib**: lectura de `agentic.toml` (Python 3.11+). Escritura manual con
  serializador propio + escritura atómica (temp + rename).
- **Escritura atómica**: aplicada en `save_config` y en `lock_manager.py`
  (IAC_TRAPS #10 del ecosistema fuente).
- **JSONC tolerant**: `connect` preserva comentarios del `opencode.jsonc` existente
  (inserta la entrada MCP sin re-serializar el archivo).

---

## 9. Estructura del repo

```
agentic-ecos/                               ← repo git (peer de los demás repos del workspace)
├── pyproject.toml
├── agentic_ecos/                           ← paquete Python
│   ├── server.py          # MCP server (31 tools)
│   ├── generator.py       # init_project + generate_file + validate + CLI
│   ├── patterns.py        # tier 1: 15 patrones agénticos (built-in)
│   ├── protocols.py       # 5 plantillas de protocolos
│   ├── presets.py         # tier 1: 3 presets de proyecto (built-in)
│   ├── ecosystem.py       # plano de control (agentic.toml, connect, tasks)
│   ├── storage.py         # data/ + knowledge/ + workspace/ carga/guardado
│   ├── knowledge.py       # promoción entre tiers (workspace/knowledge)
│   ├── knowledge/         # tier 2: COMMITEADO (comunidad)
│   │   ├── patterns/*.json
│   │   ├── presets/*.json
│   │   └── traps/*.json
│   ├── data/              # tier 3: patterns/presets commiteados (fork privado)
│   │   ├── .gitkeep       # commiteado
│   │   ├── patterns-custom.json      # ✅ commiteado (trazabilidad)
│   │   ├── presets-custom.json       # ✅ commiteado (trazabilidad)
│   │   ├── ecosystem-snapshots/      # ❌ gitignored (runtime)
│   │   └── state.json                # ❌ gitignored (runtime)
│   ├── static/            # scripts copiados tal cual a cada proyecto
│   └── templates/         # plantillas markdown generables
├── workspace/             # tier 2.5: SOLO en branches de ecosistema (commiteado)
│   ├── .gitkeep           # en main (si existe) solo hay .gitkeep
│   ├── agentic.toml       # registro de proyectos de ESTE ecosistema
│   ├── tasks.md           # tareas cross-cutting
│   └── patterns/*.json    # patrones específicos de tu ecosistema
├── docs/                  # vault autodocumental (Obsidian)
│   └── 00_Global/         # Home, MOCs, AGENTS, AGENT_TASKS, RULES, STATE, kanban
├── instructions.md        # prompt del agente
├── README.md
├── ARCHITECTURE.md        # este archivo
├── CONTRIBUTING.md        # uso, forking, ciclo de vida del conocimiento
└── tests/
```

---

## 10. Conocimiento orgánico (4 tiers)

El conocimiento del ecosistema se organiza en 4 tiers de madurez, todos dentro
del repo (portable) y todos **commiteados** en el fork privado (trazabilidad):

| Tier | Ubicación | Git | Ámbito | MCP tool |
|------|-----------|:---:|--------|----------|
| **1 · Built-in** | `agentic_ecos/patterns.py` | ✅ commiteado | Todos los ecosistemas | — |
| **2 · Comunitario** | `agentic_ecos/knowledge/*.json` | ✅ commiteado | Compartido vía PR a main | `promote_to_knowledge` |
| **2.5 · Ecosistema** | `workspace/*.json` | ✅ commiteado (branch, fork privado) | Tu ecosistema específico | `promote_to_workspace` |
| **3 · Personal** | `agentic_ecos/data/*.json` (patterns/presets) | ✅ commiteado (fork privado) | Experimentos personales | `add_custom_pattern` |
| **— · Runtime** | `agentic_ecos/data/` (snapshots, state.json) | ❌ gitignored | No es conocimiento | — |

**Fusión 4-tier en `list_patterns`**:
```python
built-in (patterns.py) → knowledge/ → workspace/ → data/ (custom)
```

**Ciclo de vida**:
1. Descubrir → `data/` (tier 3, commiteado en fork privado — trazabilidad del hallazgo)
2. Validar (≥2 proyectos) → `workspace/` (tier 2.5, commiteado en tu branch)
3. Compartir (multi-ecosistema) → `knowledge/` (tier 2, commiteado, PR a main)
4. Madurar → `patterns.py` (tier 1, built-in)

**Solo runtime data es gitignored**: los snapshots de `ecosystem_status`
(`data/ecosystem-snapshots/`) y el estado interno del MCP (`data/state.json`)
no contienen conocimiento estructurado, son voluminosos y generan conflictos de
merge entre agentes concurrentes. Se excluyen del versionado por diseño.

**Overrides de ruta**: `AGENTIC_ECOS_DATA_DIR`, `AGENTIC_ECOS_WORKSPACE_DIR`,
`AGENTIC_ECOS_KNOWLEDGE_DIR` para tests y layouts distintos.

---

## 11. Modelo de branches

El repo es autocontenido. La separación entre lo **oficial** (público) y lo
**específico de cada ecosistema** (privado) se hace con branches + forks. El
upstream tiene dos ramas públicas: `main` (estable) y `dev` (integración):

```
UPSTREAM (público)                    TU FORK (privado)
─────────────────────                ─────────────────────
main (estable, releases)              main (sync desde upstream/main)
  ↑                                   │
  └── dev (integración)               ├── ecosystem/mi-eco  ← base main (estable)
        ↑                             │   └── workspace/
        ├── feature/* PRs             │
        └── knowledge/* PRs           └── (opcional: base dev para bleeding edge)
```

**Reglas**:
- **`main` (estable) y `dev` (integración) son las branches públicas.** Contienen
  código + knowledge/ + docs/. Los PRs de feature/knowledge van a `dev`; el merge
  `dev → main` es periódico y testeado.
- **`ecosystem/*` solo existen en forks privados.** Contienen `workspace/`
  (siempre privado).
- **Tools MCP de git** (trazables, registran en AGENT_SESSION_LOG):
  - `ecosystem_branch_create(name, base)` — crea tu branch de ecosistema
    (`base=main` estable | `base=dev` bleeding edge).
  - `ecosystem_sync_upstream(branch)` — sync de main/dev con upstream.
  - `ecosystem_merge_main(target)` — merge de main a tu branch, reporta conflictos.
- `git merge main` en tu branch de ecosistema trae nuevo código + knowledge/
  sin tocar tu workspace/ (0 conflictos).
- `data/` patterns/presets se commitean (fork privado, trazabilidad). Solo
  `data/ecosystem-snapshots/` y `data/state.json` son gitignored (runtime data).
- Contribuciones al upstream: patrón validado en ≥2 ecosistemas, PR desde un
  branch limpio (sin workspace/) a `dev`.

### Por qué fork privado siempre

`workspace/` (proyectos, tareas, patrones) y `data/` (experimentos) se commitean.
Si vivieran en un repo público, serían visibles. El diseño fuerza:

- **Público** = `main` + `dev` (código + knowledge/ + docs/)
- **Privado** = todo tu ecosistema (`ecosystem/*` + `workspace/` + `data/`)

Esto da **privacidad total + trazabilidad completa** sin fricción: todo se
commitea en tu fork privado, `git log` de cada cambio.

Ver `CONTRIBUTING.md` §9 para el flujo completo.

---

## 12. Vault autodocumental (`docs/`)

`agentic-ecos` se documenta con su propia infraestructura (demo viviente). El
vault `docs/00_Global/` contiene: Home.md, 7 MOCs, AGENTS.md (guía de operación
del repo), AGENT_TASKS.md (roadmap real), RULES/ (protocolos aplicados al propio
desarrollo), STATE/ (estado del proyecto) y kanban/ (auto-generado).

Los archivos raíz (`ARCHITECTURE.md`, `README.md`, `CONTRIBUTING.md`) se
referencian desde el vault con `[[../ARCHITECTURE]]`. Abrir `docs/` en Obsidian
da navegabilidad completa.

---

> **Última actualización**: 2026-08-06
