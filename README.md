# agentic-ecos

MCP server que inicializa, gestiona y opera **infraestructura agéntica trazable**
en todo tu ecosistema digital. Un plano de control: sabe qué proyectos existen,
cuáles tienen infra agéntica, cómo están de salud y cómo inicializar los que faltan.

Instalar una vez, conectar desde todos tus proyectos.

## Qué es

`agentic-ecos` es el **plano de control** de tu ecosistema:

- **Inicializa** — genera la infraestructura agéntica completa (locks multi-agente,
  cola de tareas con kanban, comunicación entre agentes, auditoría de sesiones,
  control de acceso, protocolos de operación, vault de Obsidian, MCP server del
  proyecto) en cualquier proyecto nuevo.
- **Gestiona** — mantiene un registro canónico (`agentic.toml`) de todos los
  proyectos y su estado agéntico; conecta el MCP server al `opencode.jsonc`.
- **Provee lógicas agénticas trazables** — 15 patrones codificados, plantillas de
  protocolos, validación de estructura y próximos pasos priorizados.

## Instalación

```bash
cd agentic-ecos
uv add --dev mcp
```

## Quickstart

> **Fork privado obligatorio.** Solo `main` del upstream es público (código +
> knowledge/ + docs/). Tu ecosistema (`workspace/` + `data/`) vive en un fork
> privado — con trazabilidad completa (`git log` de cada cambio).
> Detalle en `CONTRIBUTING.md` §9.

```bash
# 0. Crear el fork privado (una vez)
gh repo fork usuario/agentic-ecos --clone --private
cd agentic-ecos
git remote add upstream https://github.com/usuario/agentic-ecos.git
git checkout -b ecosystem/mi-eco main

# 1. Inicializar el plano de control (una vez por ecosistema)
agentic-ecos ecosystem init --name mi-ecosistema --workspace ~/repos

# 2. Conectar el MCP server al workspace (multi-agente)
agentic-ecos connect --target ~/repos --agent auto

# 3. Desde el agente: generar infra agéntica para un proyecto
#    → init_project("mi-proyecto", preset="monorepo", target_path=".../docs")
```

> **Privacidad**: tu `workspace/` (proyectos, tareas) y `data/` (patterns en
> experimentación) se commitean en tu fork **privado** — nadie más los ve.
> Solo compartís lo que querés vía PR de `knowledge/` al `main` público.

## Uso con el agente (MCP)

Conecta el server a cualquier proyecto (en su `opencode.jsonc`):

```jsonc
"mcp": {
  "agentic-ecos": {
    "type": "local",
    "command": ["uv", "run", "--directory", "/abs/path/to/agentic-ecos", "agentic_ecos/server.py"]
  }
}
```

La tool `connect` hace esto automáticamente para uno o más agentes (OpenCode,
Claude Code, Cursor) — preserva tus comentarios y configs existentes:

```bash
agentic-ecos connect --target ~/repos --agent auto   # detecta agentes presentes
agentic-ecos connect --agent claude                  # solo Claude Code
agentic-ecos connect --agent snippet                 # snippets para pegar manual
```

### Tools (31)

**Generación y patrones**
| Tool | Función |
|------|---------|
| `init_project` | Genera el esqueleto agéntico completo en un proyecto + lo registra |
| `list_patterns` / `get_pattern` | Catálogo de 15 patrones + knowledge + workspace + custom |
| `protocol_template` / `list_protocols` | Plantillas de protocolos |
| `generate_file` | Genera un archivo individual |
| `list_presets` | Presets de tipos de proyecto (built-in + knowledge + custom) |

**Validación y guía**
| Tool | Función |
|------|---------|
| `validate_structure` | Checklist de piezas existentes/faltantes (16 archivos) |
| `suggest_next_steps` / `agentic_health` | Próximos pasos y salud agéntica |

**Plano de control del ecosistema**
| Tool | Función |
|------|---------|
| `ecosystem_init` | Crea `agentic.toml`, auto-detecta proyectos |
| `ecosystem_status` | Salud del ecosistema completo (cobertura por proyecto) |
| `ecosystem_config` | Devuelve el registro completo |
| `project_add` / `project_remove` | Registrar/eliminar proyectos del registro |
| `connect` / `connect_status` | Configura agentic-ecos para múltiples agentes y verifica conexión |
| `scan_opencode` | Qué proyectos tienen agentic-ecos conectado |

**Tareas cross-cutting**
| Tool | Función |
|------|---------|
| `ecosystem_tasks` | Agregado: tareas del workspace/tasks.md + por proyecto |
| `ecosystem_task_add` | Agrega tarea cross-cutting al workspace/tasks.md |

**Conocimiento (4 tiers)**
| Tool | Función |
|------|---------|
| `add_custom_pattern` / `remove_custom_pattern` | Tier 3: patrones personales (data/, commiteado en fork privado) |
| `promote_to_workspace` | Tier 2.5: data/ → workspace/ (commiteado en tu branch) |
| `promote_to_knowledge` | Tier 2: workspace/ → knowledge/ (commiteado, PR a main) |
| `knowledge_status` | Estado del conocimiento por tier |
| `add_custom_preset` / `remove_custom_preset` | Presets custom |
| `save_snapshot` / `storage_status` / `set_state` | Históricos y estado |

**Otros**
| Tool | Función |
|------|---------|
| `rag_status` | Estado RAG (opt-in) |

## Uso CLI (sin agente)

```bash
# Generar un proyecto nuevo
agentic-ecos init mi-proyecto --preset monorepo --repos api,frontend,workers

# Validar estructura existente
agentic-ecos validate ./ruta/al/vault

# Plano de control
agentic-ecos ecosystem init --name eco --workspace ~/repos
agentic-ecos ecosystem status
agentic-ecos ecosystem add otro-svc --type frontend
agentic-ecos ecosystem tasks
agentic-ecos ecosystem add-task "Migrar satet" --priority high --type iac

# Conectar MCP (multi-agente)
agentic-ecos connect --target ~/repos --agent auto
agentic-ecos connect --agent claude

# Conocimiento
agentic-ecos promote mi-pattern --to workspace
agentic-ecos promote mi-pattern --to knowledge --source workspace

# Listar patrones / protocolos
agentic-ecos patterns --domain coordination
agentic-ecos protocols
```

## Presets

- `monorepo` — múltiples servicios con CI/CD compartido e IaC centralizada
- `single_service` — un servicio con componentes en subdirectorios
- `data_pipeline` — lambdas, jobs batch, pipeline de ingesta/procesamiento

## RAG

YAGNI por defecto. El vault de proyectos pequeños se consulta con wiki links
(`vault_query_graph`). Si un proyecto necesita búsqueda semántica:

```bash
pip install 'agentic-ecos[rag]'
```

## Conocimiento (4 tiers)

El conocimiento del ecosistema sigue 4 tiers de madurez, todos dentro del repo
(portable, actualizable con `git pull`) y todos **commiteados** en tu fork
privado (trazabilidad completa):

| Tier | Ubicación | Git | Ciclo |
|------|-----------|:---:|-------|
| 3 · Personal | `agentic_ecos/data/` (patterns/presets) | ✅ commiteado (fork privado) | `add_custom_pattern` → experimento |
| 2.5 · Ecosistema | `workspace/` | ✅ (tu branch) | `promote_to_workspace` → validado |
| 2 · Comunitario | `agentic_ecos/knowledge/` | ✅ commiteado | `promote_to_knowledge` → PR a main |
| 1 · Built-in | `agentic_ecos/patterns.py` | ✅ commiteado | mover a código → todos |

Solo el **runtime data** (`data/ecosystem-snapshots/`, `data/state.json`) queda
gitignored — no es conocimiento y genera conflictos de merge.

```bash
# MCP:
#   add_custom_pattern(...)      → data/ (tier 3)
#   promote_to_workspace(...)    → workspace/ (tier 2.5)
#   promote_to_knowledge(...)    → knowledge/ (tier 2)
#   knowledge_status()           → estado por tier
```

Ciclo de vida completo: **descubrir** → `data/` → **validar** (≥2 proyectos) →
`workspace/` → **compartir** (multi-ecosistema) → `knowledge/` → **madurar** →
`patterns.py`.

Override de ruta: `AGENTIC_ECOS_DATA_DIR=/path/to/data`.

## Vault autodocumental (`docs/`)

`agentic-ecos` se documenta con su propia infraestructura (demo viviente).
Abre `docs/` en Obsidian: Home.md, MOCs, AGENT_TASKS.md (roadmap), RULES/,
STATE/ y kanban/ — todo interlinkeado con wiki links y tags.

## Estructura del repo

```
agentic_ecos/
├── server.py        # MCP server (31 tools)
├── generator.py     # init_project + generate_file + validate + CLI
├── patterns.py      # 15 patrones agénticos codificados (tier 1)
├── protocols.py     # plantillas de protocolos (5)
├── presets.py       # monorepo / single_service / data_pipeline (tier 1)
├── ecosystem.py     # plano de control (agentic.toml, connect, tasks)
├── storage.py       # data/ + knowledge/ + workspace/ carga/guardado
├── knowledge.py     # promoción entre tiers
├── knowledge/       # tier 2 · commiteado · comunidad (patterns/presets/traps)
├── data/            # tier 3 · patterns/presets commiteados (fork privado) · snapshots/state gitignored
├── static/          # scripts copiados tal cual (lock_manager, sync_kanban, ...)
└── templates/       # plantillas markdown generables

workspace/           # tier 2.5 · solo en branches de ecosistema (fork privado) · agentic.toml + tasks.md
docs/00_Global/      # vault autodocumental (Obsidian)
```

## Documentación

- [ARCHITECTURE.md](ARCHITECTURE.md) — arquitectura de capas, patrones, plano de control, pipeline de generación

## Roadmap

- [ ] Extracción de patrones desde agv-docs (upgrade unidireccional)
- [ ] Skill de OpenCode para orquestar la inicialización
- [ ] RAG opt-in para vaults grandes
