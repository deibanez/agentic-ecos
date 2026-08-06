#!/usr/bin/env python3
"""agentic-ecos MCP Server — portador de patrones agénticos.

Expone tools para que un agente pueda:
  - Inicializar infraestructura agéntica en cualquier proyecto (init_project)
  - Consultar patrones agénticos (get_pattern, list_patterns)
  - Obtener plantillas de protocolos (protocol_template)
  - Generar archivos individuales (generate_file)
  - Validar estructura agéntica existente (validate_structure)
  - Obtener próximos pasos priorizados (suggest_next_steps)

Instalación (una vez, para todo el ecosistema):
    uv add --dev mcp   (en el repo agentic-ecos)

Conexión desde cualquier proyecto (opencode.jsonc):
    "mcp": {
      "agentic-ecos": {
        "type": "local",
        "command": ["uv", "run", "--directory", "/abs/path/to/agentic-ecos",
                    "agentic_ecos/server.py"]
      }
    }
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .generator import (init_project, generate_file, validate_structure,
                        suggest_next_steps, next_steps)
from .patterns import list_patterns, get_pattern, get_domains
from .protocols import PROTOCOLS, get_protocol
from .presets import all_presets, PRESETS
from .ecosystem import (ecosystem_init, ecosystem_status, project_add,
                        project_remove, connect, connect_status, scan_opencode,
                        load_config, find_config, ecosystem_tasks, ecosystem_task_add,
                        ecosystem_branch_create, ecosystem_sync_upstream,
                        ecosystem_merge_main)
from .task_loop import claim_task, done_task, get_task_status

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import Tool
except ImportError:
    print("❌ MCP package not installed. Run: uv add mcp", file=sys.stderr)
    sys.exit(1)

server = Server("agentic-ecos")


# Instrucciones del servidor — se inyectan automáticamente al agente al conectar
# (campo `instructions` del handshake MCP). Agnóstico: funciona con cualquier
# cliente MCP (OpenCode, Claude Code, Cursor, etc.). Mismo contenido que
# instructions.md, que connect() agrega al opencode.jsonc del workspace.
SERVER_INSTRUCTIONS = """agentic-ecos is the control plane for your digital ecosystem.
It bootstraps, manages and operates traceable agentic infrastructure.

TWO MODES — both work immediately after connecting the server.

MODE 1 · SIMPLE (no ecosystem needed):
  init_project(name, preset, target_path) — bootstrap agentic infra in a project
  list_patterns() / get_pattern(name) — catalog of 15 agentic patterns
  validate_structure(path) — check agentic infrastructure coverage
  protocol_template(name) — get a protocol template
  generate_file(name, target_path) — generate a single template file

MODE 2 · ECOSYSTEM (multi-project coordination, requires private fork):
  ecosystem_init(name, workspace_root) — bootstrap the ecosystem registry
  ecosystem_status() — health of all projects
  ecosystem_tasks() — cross-cutting + per-project task counts
  ecosystem_task_claim(task_id, agent_id) — claim a task (race-free via git)
  ecosystem_task_done(task_id, agent_id) — mark a task done (verifies ownership)
  ecosystem_task_status(filter_agent) — filter tasks (unclaimed/claimed/done/agent)
  ecosystem_branch_create(name) — create your ecosystem branch (traceable)
  ecosystem_sync_upstream(branch) — sync main/dev with upstream
  → See CONTRIBUTING.md §10 for the private-fork setup.

TASK LIFECYCLE (local-first): ecosystem_task_add/claim/done/status work in any
agent session — they commit and push via git to your branch (git push rejection
handles multi-agent races). GitHub Actions task-automation is OPTIONAL: it runs
the same cycle for docs/ops tasks automatically. Not required for local work.

QUICK HELP:
  knowledge_status() — knowledge state per tier
  list_protocols() — protocol templates
  list_patterns("coordination|knowledge|interface|...") — patterns by domain

EVERY tool response includes a `_context` field with live ecosystem state:
  ecosystem_summary — project counts and infra coverage
  task_backlog — pending task counts
  knowledge_state — patterns/traps per tier
  → You don't need to call ecosystem_status/tasks separately for a quick pulse.

LLM is OPTIONAL: set LLM_API_KEY env var for AI-synthesized summaries,
task proposals and PR reviews. Without it, everything works normally.

Full docs: ARCHITECTURE.md, CONTRIBUTING.md, README.md"""


def _make_tool(name: str, description: str, properties: dict, required: list | None = None) -> Tool:
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return Tool(name=name, description=description, inputSchema=schema)


# ─── Handlers ─────────────────────────────────────────────────────────────────

def _json_context(context: Optional[str]) -> dict:
    if not context:
        return {}
    try:
        parsed = json.loads(context)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


async def handle_init_project(args: dict):
    presets_all = all_presets()
    preset = args.get("preset", "monorepo")
    if preset not in presets_all:
        return {"ok": False, "error": f"Preset '{preset}' not found. "
                                      f"Available: {', '.join(sorted(presets_all))}"}
    repo_str = args.get("repos")
    repos = repo_str.split(",") if repo_str else None
    try:
        return init_project(
            args["project_name"],
            preset_name=preset,
            target_path=args.get("target_path"),
            repos=repos,
            cloud=args.get("cloud", "none"),
            ci_cd=args.get("ci_cd", "github-actions"),
            language=args.get("language", "en"),
            description=args.get("description", ""),
        )
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}


async def handle_list_patterns(args: dict):
    return {"patterns": list_patterns(args.get("domain")), "domains": get_domains()}


async def handle_get_pattern(args: dict):
    p = get_pattern(args["name"])
    if p is None:
        available = sorted(x["name"] for x in list_patterns())
        return {"ok": False, "error": f"Pattern '{args['name']}' not found. "
                                      f"Available: {', '.join(available)}"}
    return p


async def handle_protocol_template(args: dict):
    name = args["name"]
    if name not in PROTOCOLS:
        return {"ok": False, "error": f"Protocol '{name}' not found. "
                                      f"Available: {', '.join(sorted(PROTOCOLS))}"}
    return {"name": name, "template": get_protocol(name), "context_applied": _json_context(args.get("context"))}


async def handle_list_protocols(args: dict):
    return {"protocols": sorted(PROTOCOLS)}


async def handle_list_presets(args: dict):
    return {
        "presets": {
            name: {"label": p["label"], "description": p["description"],
                   "default_repos": p["default_repos"], "custom": p.get("custom", False)}
            for name, p in all_presets().items()
        }
    }


async def handle_generate_file(args: dict):
    return generate_file(args["file_name"], args["target_path"],
                         _json_context(args.get("context")))


async def handle_validate_structure(args: dict):
    return validate_structure(args["project_path"])


async def handle_suggest_next_steps(args: dict):
    return {"next_steps": suggest_next_steps(args["project_path"])}


async def handle_agentic_health(args: dict):
    v = validate_structure(args["project_path"])
    return {
        "ok": v["ok"],
        "coverage_pct": v["coverage_pct"],
        "present": v["present"],
        "missing": v["missing"],
        "next_steps": suggest_next_steps(args["project_path"]) if not v["ok"]
        else next_steps("", args["project_path"]),
        "version": __version__,
    }


async def handle_rag_status(args: dict):
    return {
        "enabled": False,
        "reason": "RAG es opt-in. El vault de proyectos pequeños se consulta con "
                  "vault_query_graph (wiki links) sin necesidad de embeddings.",
        "how_to_enable": "pip install 'agentic-ecos[rag]' → ejecutar vector_index.py "
                         "sobre el vault → habilitar tool de búsqueda semántica.",
    }


# ─── Plano de control del ecosistema ─────────────────────────────────────────

async def handle_ecosystem_init(args: dict):
    return ecosystem_init(
        name=args.get("name", "mi-ecosistema"),
        workspace_root=args.get("workspace_root", str(Path.cwd())),
        cloud=args.get("cloud", "aws"),
        ci_cd=args.get("ci_cd", "github-actions"),
        language=args.get("language", "es"),
        vault_path=args.get("vault_path", "docs"),
        description=args.get("description", ""),
        scan=args.get("scan", True),
        config_path=args.get("config_path"),
    )


async def handle_ecosystem_status(args: dict):
    return ecosystem_status(args.get("config_path"))


async def handle_project_add(args: dict):
    return project_add(
        name=args.get("name"),
        project_type=args.get("type", "backend"),
        path=args.get("path"),
        preset=args.get("preset", "monorepo"),
        status=args.get("status", "pending"),
        notes=args.get("notes", ""),
        config_path=args.get("config_path"),
    )


async def handle_project_remove(args: dict):
    return project_remove(args.get("name"), args.get("config_path"))


async def handle_connect(args: dict):
    return connect(
        target=args.get("target"),
        agent=args.get("agent", "auto"),
        agentic_path=args.get("agentic_path"),
        create_if_missing=args.get("create_if_missing", True),
        config_path=args.get("config_path"),
    )


async def handle_connect_status(args: dict):
    return connect_status(args.get("target"), args.get("config_path"))


async def handle_scan_opencode(args: dict):
    return scan_opencode(args.get("workspace_root"))


async def handle_ecosystem_config(args: dict):
    return {"ok": True, "config_path": str(find_config() or ""),
            "data": load_config(args.get("config_path"))}


async def handle_ecosystem_tasks(args: dict):
    return ecosystem_tasks(args.get("config_path"))


async def handle_ecosystem_task_add(args: dict):
    return ecosystem_task_add(
        description=args.get("description"),
        priority=args.get("priority", "medium"),
        type=args.get("type", "ops"),
        scope=args.get("scope", "ecosystem"),
        config_path=args.get("config_path"),
    )


async def handle_ecosystem_task_claim(args: dict):
    from pathlib import Path as _P
    tasks_file = _P(args["tasks_file"]) if args.get("tasks_file") else None
    return claim_task(args["task_id"], args["agent_id"], tasks_file=tasks_file)


async def handle_ecosystem_task_done(args: dict):
    from pathlib import Path as _P
    tasks_file = _P(args["tasks_file"]) if args.get("tasks_file") else None
    return done_task(args["task_id"], args["agent_id"], tasks_file=tasks_file)


async def handle_ecosystem_task_status(args: dict):
    from pathlib import Path as _P
    tasks_file = _P(args["tasks_file"]) if args.get("tasks_file") else None
    return get_task_status(task_id=args.get("task_id"),
                           filter_agent=args.get("filter_agent"),
                           tasks_file=tasks_file)


async def handle_ecosystem_branch_create(args: dict):
    return ecosystem_branch_create(args["name"], base=args.get("base", "main"))


async def handle_ecosystem_sync_upstream(args: dict):
    return ecosystem_sync_upstream(branch=args.get("branch", "main"))


async def handle_ecosystem_merge_main(args: dict):
    return ecosystem_merge_main(args.get("target_branch"))


# ─── Storage orgánico (data/) ────────────────────────────────────────────────

async def handle_add_custom_pattern(args: dict):
    from . import storage
    return storage.add_custom_pattern(args.get("pattern") or {})


async def handle_remove_custom_pattern(args: dict):
    from . import storage
    return storage.remove_custom_pattern(args["name"])


async def handle_add_custom_preset(args: dict):
    from . import storage
    return storage.add_custom_preset(args["name"], args.get("preset") or {})


async def handle_remove_custom_preset(args: dict):
    from . import storage
    return storage.remove_custom_preset(args["name"])


async def handle_save_snapshot(args: dict):
    from . import storage
    return storage.save_snapshot(args.get("payload") or {},
                                 label=args.get("label", "ecosystem-status"))


async def handle_storage_status(args: dict):
    from . import storage
    return storage.storage_status()


async def handle_set_state(args: dict):
    from . import storage
    return storage.set_state(args["key"], args.get("value"))


# ─── Conocimiento (knowledge/ + workspace/ + promote) ───────────────────────

async def handle_promote_to_workspace(args: dict):
    from . import knowledge
    return knowledge.promote_to_workspace(args["name"], args.get("config_path"))


async def handle_promote_to_knowledge(args: dict):
    from . import knowledge
    return knowledge.promote_to_knowledge(
        args["name"],
        source=args.get("source", "workspace"),
        kind=args.get("kind", "pattern"),
    )


async def handle_knowledge_status(args: dict):
    from . import knowledge
    return knowledge.knowledge_status()


# Dispatch: name → handler
HANDLERS = {
    "init_project": handle_init_project,
    "list_patterns": handle_list_patterns,
    "get_pattern": handle_get_pattern,
    "protocol_template": handle_protocol_template,
    "list_protocols": handle_list_protocols,
    "list_presets": handle_list_presets,
    "generate_file": handle_generate_file,
    "validate_structure": handle_validate_structure,
    "suggest_next_steps": handle_suggest_next_steps,
    "agentic_health": handle_agentic_health,
    "rag_status": handle_rag_status,
    # Plano de control
    "ecosystem_init": handle_ecosystem_init,
    "ecosystem_status": handle_ecosystem_status,
    "ecosystem_config": handle_ecosystem_config,
    "project_add": handle_project_add,
    "project_remove": handle_project_remove,
    "connect": handle_connect,
    "connect_status": handle_connect_status,
    "scan_opencode": handle_scan_opencode,
    # Tareas cross-cutting
    "ecosystem_tasks": handle_ecosystem_tasks,
    "ecosystem_task_add": handle_ecosystem_task_add,
    "ecosystem_task_claim": handle_ecosystem_task_claim,
    "ecosystem_task_done": handle_ecosystem_task_done,
    "ecosystem_task_status": handle_ecosystem_task_status,
    # Operaciones git del ecosistema
    "ecosystem_branch_create": handle_ecosystem_branch_create,
    "ecosystem_sync_upstream": handle_ecosystem_sync_upstream,
    "ecosystem_merge_main": handle_ecosystem_merge_main,
    # Storage orgánico
    "add_custom_pattern": handle_add_custom_pattern,
    "remove_custom_pattern": handle_remove_custom_pattern,
    "add_custom_preset": handle_add_custom_preset,
    "remove_custom_preset": handle_remove_custom_preset,
    "save_snapshot": handle_save_snapshot,
    "storage_status": handle_storage_status,
    "set_state": handle_set_state,
    # Conocimiento
    "promote_to_workspace": handle_promote_to_workspace,
    "promote_to_knowledge": handle_promote_to_knowledge,
    "knowledge_status": handle_knowledge_status,
}


# ─── Contexto sistémico (inyectado en CADA respuesta MCP) ───────────────────

_ctx_cache = {"ts": 0.0, "data": None}
_CTX_TTL = 10.0  # segundos — refresco barato para no bloquear cada llamada


def _ecosystem_summary_compact() -> dict:
    """Resumen del ecosistema en formato mínimo (no bloquea)."""
    try:
        s = ecosystem_status()
        return {
            "projects": s.get("projects_count", 0),
            "with_infra": s.get("with_agentic_infra", 0),
            "without_infra": s.get("without_agentic_infra", 0),
        }
    except Exception:
        return {"error": "no ecosystem configured"}


def _task_backlog_compact() -> dict:
    """Estado de tareas en formato mínimo."""
    try:
        t = ecosystem_tasks()
        return {
            "cross_cutting_backlog": t.get("cross_cutting_backlog", 0),
            "ecosystem_backlog": t.get("ecosystem_backlog", 0),
        }
    except Exception:
        return {"error": "no tasks"}


def _knowledge_compact() -> dict:
    """Estado del conocimiento por tier en formato mínimo."""
    try:
        from .knowledge import knowledge_status
        k = knowledge_status()
        return {
            "tier1_builtin": k.get("tier1_builtin_patterns", 0),
            "tier2_patterns": k.get("tier2_knowledge_patterns", 0),
            "tier2_traps": k.get("tier2_knowledge_traps", 0),
            "tier3_custom": k.get("tier3_custom_patterns", 0),
        }
    except Exception:
        return {}


def _suggestions() -> list[str]:
    """Recomendaciones accionables basadas en heurísticas del estado actual."""
    items = []
    eco = _ecosystem_summary_compact()
    tasks = _task_backlog_compact()
    know = _knowledge_compact()

    if eco.get("error"):
        items.append("No ecosystem configured. Use ecosystem_init() to bootstrap.")
    elif eco.get("without_infra", 0) > 0:
        items.append(f"{eco['without_infra']} project(s) lack agentic infra. "
                     f"Use ecosystem_status() to identify gaps, then init_project().")
    if tasks.get("ecosystem_backlog", 0) > 0:
        items.append(f"{tasks['ecosystem_backlog']} task(s) in backlog. "
                     f"Use ecosystem_task_status(filter='unclaimed') to see available.")
    if know.get("tier3_custom", 0) > 0:
        items.append(f"{know['tier3_custom']} pattern(s) in tier3 (personal). "
                     f"Consider promote_to_workspace() if validated in 2+ projects.")
    if know.get("tier2_patterns", 0) > 0 or know.get("tier2_traps", 0) > 0:
        items.append("Knowledge in tier2 (community). "
                     "Use get_pattern() to consult, or promote_to_knowledge() for new ones.")

    if not items:
        items.append("Ecosystem is healthy. Explore patterns (list_patterns) or "
                     "bootstrap a project (init_project).")
    return items


def _context() -> dict:
    """Contexto sistémico inyectado en cada respuesta MCP (cacheado 10s)."""
    import time
    now = time.time()
    if _ctx_cache["data"] is not None and (now - _ctx_cache["ts"]) < _CTX_TTL:
        return _ctx_cache["data"]
    ctx = {
        "system_health": "unknown",
        "ecosystem_summary": _ecosystem_summary_compact(),
        "task_backlog": _task_backlog_compact(),
        "knowledge_state": _knowledge_compact(),
        "suggestions": _suggestions(),
    }
    _ctx_cache["ts"] = now
    _ctx_cache["data"] = ctx
    return ctx


def _inject_context(result: dict) -> dict:
    """Agrega _context a una respuesta MCP si es dict y no lo tiene ya."""
    if isinstance(result, dict) and "_context" not in result:
        result["_context"] = _context()
    return result


# ─── Tool registration (list) ─────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    _make_tool(
        "init_project",
        "Genera el esqueleto completo de infraestructura agéntica en un proyecto "
        "(locks, tasks, comms, session audit, protocols, vault, MCP skeleton).",
        {
            "project_name": {"type": "string"},
            "preset": {"type": "string", "default": "monorepo",
                       "description": "monorepo | single_service | data_pipeline"},
            "target_path": {"type": "string", "default": None,
                            "description": "Ruta destino (default: ./<slug>/docs)"},
            "repos": {"type": "string", "default": None,
                      "description": "Componentes separados por coma"},
            "cloud": {"type": "string", "default": "none"},
            "ci_cd": {"type": "string", "default": "github-actions"},
            "language": {"type": "string", "default": "en"},
            "description": {"type": "string", "default": ""},
        },
        required=["project_name"],
    ),
    _make_tool(
        "list_patterns",
        "Lista los patrones agénticos disponibles, opcionalmente por dominio.",
        {"domain": {"type": "string", "default": None}},
    ),
    _make_tool(
        "get_pattern",
        "Devuelve un patrón agéntico específico con guía de implementación.",
        {"name": {"type": "string"}},
        required=["name"],
    ),
    _make_tool(
        "protocol_template",
        "Devuelve una plantilla de protocolo con placeholders reemplazados.",
        {"name": {"type": "string"},
         "context": {"type": "string", "default": None, "description": "JSON opcional"}},
        required=["name"],
    ),
    _make_tool("list_protocols", "Lista las plantillas de protocolos disponibles.", {}),
    _make_tool("list_presets", "Lista los presets de tipos de proyecto disponibles.", {}),
    _make_tool(
        "generate_file",
        "Genera un archivo individual desde un template.",
        {"file_name": {"type": "string"},
         "target_path": {"type": "string"},
         "context": {"type": "string", "default": None, "description": "JSON opcional"}},
        required=["file_name", "target_path"],
    ),
    _make_tool(
        "validate_structure",
        "Valida qué piezas de infraestructura agéntica existen en un proyecto.",
        {"project_path": {"type": "string"}},
        required=["project_path"],
    ),
    _make_tool(
        "suggest_next_steps",
        "Sugiere próximos pasos priorizados para un proyecto.",
        {"project_path": {"type": "string"}},
        required=["project_path"],
    ),
    _make_tool(
        "agentic_health",
        "Reporte de salud agéntica de un proyecto (coverage + gaps + sugerencias).",
        {"project_path": {"type": "string"}},
        required=["project_path"],
    ),
    _make_tool(
        "rag_status",
        "Verifica si el vault del proyecto está indexado para RAG (opt-in).",
        {"target_path": {"type": "string", "default": None}},
    ),
    # ─── Plano de control del ecosistema ───
    _make_tool(
        "ecosystem_init",
        "Inicializa el plano de control: crea agentic.toml en el workspace con "
        "registro canónico de proyectos y sus defaults.",
        {
            "name": {"type": "string", "default": "mi-ecosistema"},
            "workspace_root": {"type": "string",
                               "description": "Raíz del workspace con los proyectos"},
            "cloud": {"type": "string", "default": "aws"},
            "ci_cd": {"type": "string", "default": "github-actions"},
            "language": {"type": "string", "default": "es"},
            "vault_path": {"type": "string", "default": "docs"},
            "description": {"type": "string", "default": ""},
            "scan": {"type": "boolean", "default": True,
                     "description": "Auto-detectar proyectos existentes"},
            "config_path": {"type": "string", "default": None},
        },
        required=["workspace_root"],
    ),
    _make_tool(
        "ecosystem_status",
        "Reporte de salud del ecosistema completo: proyectos, cobertura agéntica, gaps.",
        {"config_path": {"type": "string", "default": None}},
    ),
    _make_tool(
        "ecosystem_config",
        "Devuelve el registro agentic.toml completo (proyectos + defaults).",
        {"config_path": {"type": "string", "default": None}},
    ),
    _make_tool(
        "project_add",
        "Registra un proyecto en agentic.toml (detecta si ya tiene infra agéntica).",
        {
            "name": {"type": "string"},
            "type": {"type": "string", "default": "backend"},
            "path": {"type": "string", "default": None},
            "preset": {"type": "string", "default": "monorepo"},
            "status": {"type": "string", "default": "pending"},
            "notes": {"type": "string", "default": ""},
            "config_path": {"type": "string", "default": None},
        },
        required=["name"],
    ),
    _make_tool(
        "project_remove",
        "Elimina un proyecto del registro agentic.toml.",
        {"name": {"type": "string"}, "config_path": {"type": "string", "default": None}},
        required=["name"],
    ),
    _make_tool(
        "connect",
        "Configura agentic-ecos como MCP server para uno o más agentes (opencode, claude, "
        "cursor, auto, snippet). No modifica configs existentes de otros servers.",
        {
            "target": {"type": "string", "default": None,
                       "description": "Directorio donde escribir los configs"},
            "agent": {"type": "string", "default": "auto",
                      "description": "opencode | claude | cursor | auto (detecta) | snippet"},
            "agentic_path": {"type": "string", "default": None},
            "create_if_missing": {"type": "boolean", "default": True},
            "config_path": {"type": "string", "default": None},
        },
    ),
    _make_tool(
        "connect_status",
        "Detecta qué agentes tienen config en target y si agentic-ecos está conectado.",
        {"target": {"type": "string", "default": None},
         "config_path": {"type": "string", "default": None}},
    ),
    _make_tool(
        "scan_opencode",
        "Escanea el workspace y reporta qué proyectos tienen agentic-ecos conectado.",
        {"workspace_root": {"type": "string", "default": None}},
    ),
    # ─── Storage orgánico (data/) ───
    _make_tool(
        "add_custom_pattern",
        "Agrega un patrón agéntico descubierto por un agente a data/patterns-custom.json "
        "(disponible para todos los proyectos; promocionar a patterns.py cuando madure).",
        {"pattern": {"type": "object"}},
        required=["pattern"],
    ),
    _make_tool(
        "remove_custom_pattern",
        "Elimina un patrón custom de data/patterns-custom.json.",
        {"name": {"type": "string"}},
        required=["name"],
    ),
    _make_tool(
        "add_custom_preset",
        "Agrega un preset custom a data/presets-custom.json.",
        {"name": {"type": "string"}, "preset": {"type": "object"}},
        required=["name", "preset"],
    ),
    _make_tool(
        "remove_custom_preset",
        "Elimina un preset custom de data/presets-custom.json.",
        {"name": {"type": "string"}},
        required=["name"],
    ),
    _make_tool(
        "save_snapshot",
        "Guarda un snapshot histórico (ej: de ecosystem_status) en data/ecosystem-snapshots/.",
        {"payload": {"type": "object"}, "label": {"type": "string", "default": "ecosystem-status"}},
    ),
    _make_tool(
        "storage_status",
        "Reporta el estado del almacenamiento orgánico (data/): custom patterns/presets, snapshots, state.",
        {},
    ),
    _make_tool(
        "set_state",
        "Guarda una clave/valor en el estado interno del MCP (data/state.json).",
        {"key": {"type": "string"}, "value": {"type": "object"}},
        required=["key"],
    ),
    # ─── Tareas cross-cutting ───
    _make_tool(
        "ecosystem_tasks",
        "Agregado de tareas del ecosistema: cross-cutting (workspace/tasks.md) + conteo por proyecto.",
        {"config_path": {"type": "string", "default": None}},
    ),
    _make_tool(
        "ecosystem_task_add",
        "Agrega una tarea cross-cutting al workspace/tasks.md (commiteable en tu branch).",
        {"description": {"type": "string"},
         "priority": {"type": "string", "default": "medium"},
         "type": {"type": "string", "default": "ops"},
         "scope": {"type": "string", "default": "ecosystem"},
         "config_path": {"type": "string", "default": None}},
        required=["description"],
    ),
    _make_tool(
        "ecosystem_task_claim",
        "Reclama una tarea: agrega [agent::] + [status:: doing] + commit + push. "
        "Race-free con git push rejection (si otro agente reclamó primero, falla). Trazable con T-ID.",
        {"task_id": {"type": "string"}, "agent_id": {"type": "string"},
         "tasks_file": {"type": "string", "default": None}},
        required=["task_id", "agent_id"],
    ),
    _make_tool(
        "ecosystem_task_done",
        "Marca una tarea como completada: [status:: done] + commit + push. "
        "Verifica que el agent_id que completa es el que la reclamó.",
        {"task_id": {"type": "string"}, "agent_id": {"type": "string"},
         "tasks_file": {"type": "string", "default": None}},
        required=["task_id", "agent_id"],
    ),
    _make_tool(
        "ecosystem_task_status",
        "Consulta el estado de tareas: por ID, o filtradas por agente/estado "
        "(unclaimed | claimed | done | backlog | agent-id).",
        {"task_id": {"type": "string", "default": None},
         "filter_agent": {"type": "string", "default": None,
                          "description": "unclaimed | claimed | done | backlog | <agent-id>"},
         "tasks_file": {"type": "string", "default": None}},
    ),
    # ─── Conocimiento (knowledge/ + promote) ───
    _make_tool(
        "promote_to_workspace",
        "Mueve un pattern de data/ (personal) a workspace/patterns/ (commiteable en tu branch de ecosistema).",
        {"name": {"type": "string"}, "config_path": {"type": "string", "default": None}},
        required=["name"],
    ),
    _make_tool(
        "promote_to_knowledge",
        "Copia un pattern de workspace/ o data/ a knowledge/ (commiteable, para PR a upstream).",
        {"name": {"type": "string"},
         "source": {"type": "string", "default": "workspace", "description": "workspace | data"},
         "kind": {"type": "string", "default": "pattern", "description": "pattern | preset | trap"}},
        required=["name"],
    ),
    _make_tool(
        "knowledge_status",
        "Reporta el estado del conocimiento por tier (built-in / knowledge / workspace / custom).",
        {},
    ),
    # ─── Operaciones git del ecosistema ───
    _make_tool(
        "ecosystem_branch_create",
        "Crea la branch `ecosystem/{name}` desde `base` (default: main). Trazable: "
        "registra la operación en AGENT_SESSION_LOG.",
        {"name": {"type": "string"},
         "base": {"type": "string", "default": "main",
                  "description": "main (estable) | dev (bleeding edge)"}},
        required=["name"],
    ),
    _make_tool(
        "ecosystem_sync_upstream",
        "Sincroniza una branch local con upstream (git fetch + merge). "
        "branch='main' actualiza estable; branch='dev' actualiza bleeding edge.",
        {"branch": {"type": "string", "default": "main", "description": "main | dev"}},
    ),
    _make_tool(
        "ecosystem_merge_main",
        "Mergea main a la branch de ecosistema (target_branch o branch actual). "
        "Reporta archivos en conflicto si los hay.",
        {"target_branch": {"type": "string", "default": None}},
    ),
]


@server.list_tools()
async def handle_list_tools():
    return TOOL_DEFINITIONS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    from mcp.types import TextContent

    handler = HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"ok": False, "error": f"Unknown tool: {name}"}))]
    try:
        result = await handler(arguments or {})
        result = _inject_context(result)
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, default=str))]
    except Exception as exc:  # pragma: no cover
        return [TextContent(type="text", text=json.dumps({"ok": False, "error": str(exc)}, indent=2))]


async def _run():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agentic-ecos",
                server_version=__version__,
                instructions=SERVER_INSTRUCTIONS,
                capabilities={
                    "tools": {},  # Tools are listed via list_tools()
                },
            ),
        )


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
