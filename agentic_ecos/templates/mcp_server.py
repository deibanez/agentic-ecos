#!/usr/bin/env python3
"""MCP Server skeleton generado por agentic-ecos.

Este server expone:
  - Tools de ciclo de vida agéntico (register, heartbeat, lock, tasks, comms)
  - Tools de vault (build_graph, query_graph, execute_dataview)
  - Tools de dominio (desde {project}_tools.py → register_tools)

CUSTOMIZE: Ajusta el nombre del server y las rutas si tu estructura difiere.
Requiere: mcp>=1.27.0 (pip install 'mcp>=1.27.0,<2.0')
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # raíz del vault (docs/)
sys.path.insert(0, str(BASE_DIR / "scripts"))

try:
    from lock_manager import LockManager
except ImportError:
    LockManager = None

# ─── MCP Server ──────────────────────────────────────────────────────────────
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ MCP package not installed. Run: pip install 'mcp>=1.27.0,<2.0'", file=sys.stderr)
    sys.exit(1)

server = Server("{{PROJECT_NAME}}")
lm = LockManager() if LockManager else None


def _make_tool(name: str, description: str, properties: dict, required: list | None = None) -> Tool:
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return Tool(name=name, description=description, inputSchema=schema)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _context() -> dict:
    """CUSTOMIZE: inyecta contexto del sistema en cada respuesta."""
    return {"system_health": "unknown", "anomaly_score": 0, "critical_warnings": []}


# ─── Handlers de ciclo de vida agéntico ──────────────────────────────────────

async def _agent_register(args: dict):
    """CUSTOMIZE: implementa la escritura de la fila en AGENT_REGISTRY.md"""
    return {"agent_id": args.get("agent_id"), "role": args.get("role"),
            "status": "registered", "_context": _context()}


async def _agent_heartbeat(args: dict):
    """CUSTOMIZE: implementa el refresh del heartbeat en AGENT_REGISTRY.md"""
    return {"agent_id": args.get("agent_id"), "status": "heartbeat_ok", "timestamp": _now()}


async def _agent_lock(args: dict):
    if lm is None:
        return {"error": "lock_manager not importable"}
    command = args.get("command")
    resource = args.get("resource")
    agent_id = args.get("agent_id")
    role = args.get("role", "explorer")
    if command == "status":
        return lm.status(resource)
    if command == "acquire":
        return {"result": lm.acquire(resource, agent_id, role, args.get("ttl", 30))}
    if command == "release":
        return {"result": lm.release(resource, agent_id)}
    if command == "heartbeat":
        return {"result": lm.heartbeat(resource, agent_id)}
    if command == "force-unlock":
        return {"result": lm.force_unlock(resource, agent_id, role)}
    return {"error": f"Unknown command: {command}"}


async def _agent_add_task(args: dict):
    """CUSTOMIZE: implementa el append de una línea checkbox a AGENT_TASKS.md
    Formato: - [ ] T{n}: {description} [priority:: {p}] [status:: backlog] [type:: {t}] [repo:: {r}]
    """
    return {"agent_id": args.get("agent_id"), "status": "task_added",
            "description": args.get("description")}


async def _agent_status(args: dict):
    return {
        "agents": [],           # CUSTOMIZE: parsea AGENT_REGISTRY.md
        "locks": lm.list_active() if lm else [],
        "tasks": [],            # CUSTOMIZE: parsea AGENT_TASKS.md
        "_context": _context(),
    }


async def _agent_close_session(args: dict):
    released = lm.release_all_by_agent(args.get("agent_id")) if lm else []
    # CUSTOMIZE: marca el agente como inactive en AGENT_REGISTRY.md
    return {"agent_id": args.get("agent_id"), "released_locks": len(released),
            "summary": args.get("summary", "")}


# ─── Handlers de vault ────────────────────────────────────────────────────────

async def _vault_build_graph(args: dict):
    """CUSTOMIZE: parsea [[wiki links]] y frontmatter tags de los .md del vault"""
    return {"nodes": 0, "edges": 0, "rebuild": args.get("force_rebuild", False)}


async def _vault_query_graph(args: dict):
    return {"query": args.get("query"), "params": args.get("params", "{}"), "results": []}


async def _vault_audit_coverage(args: dict):
    return {"tagged_pct": 0, "linked_pct": 0, "orphans": []}


# ─── Dispatch ─────────────────────────────────────────────────────────────────

HANDLERS = {
    "agent_register": _agent_register,
    "agent_heartbeat": _agent_heartbeat,
    "agent_lock": _agent_lock,
    "agent_add_task": _agent_add_task,
    "agent_status": _agent_status,
    "agent_close_session": _agent_close_session,
    "vault_build_graph": _vault_build_graph,
    "vault_query_graph": _vault_query_graph,
    "vault_audit_coverage": _vault_audit_coverage,
}

TOOL_DEFINITIONS = [
    _make_tool("agent_register", "Registrar un agente en AGENT_REGISTRY.md",
               {"agent_id": {"type": "string"}, "role": {"type": "string"},
                "task": {"type": "string", "default": ""}},
               required=["agent_id", "role"]),
    _make_tool("agent_heartbeat", "Refrescar heartbeat de un agente",
               {"agent_id": {"type": "string"}}, required=["agent_id"]),
    _make_tool("agent_lock", "Gestionar locks multi-agente",
               {"command": {"type": "string"}, "resource": {"type": "string"},
                "agent_id": {"type": "string"}, "role": {"type": "string", "default": "explorer"},
                "ttl": {"type": "number", "default": 30}},
               required=["command", "resource", "agent_id"]),
    _make_tool("agent_add_task", "Crear tarea en AGENT_TASKS.md",
               {"agent_id": {"type": "string"}, "description": {"type": "string"},
                "priority": {"type": "string", "default": "medium"},
                "type": {"type": "string", "default": "task"},
                "repo": {"type": "string", "default": ""}},
               required=["agent_id", "description"]),
    _make_tool("agent_status", "Ver el sistema multi-agente completo", {}),
    _make_tool("agent_close_session", "Cerrar sesión de agente",
               {"agent_id": {"type": "string"}, "role": {"type": "string", "default": "explorer"},
                "summary": {"type": "string", "default": ""}},
               required=["agent_id"]),
    _make_tool("vault_build_graph", "Construir grafo de wiki links del vault",
               {"force_rebuild": {"type": "boolean", "default": False}}),
    _make_tool("vault_query_graph", "Consultar el grafo del vault",
               {"query": {"type": "string"}, "params": {"type": "string", "default": "{}"}},
               required=["query"]),
    _make_tool("vault_audit_coverage", "Auditar cobertura del vault", {}),
]

# Tools de dominio (implementadas en {project}_tools.py)
try:
    from {{PROJECT_SLUG}}_tools import register_tools as _register_domain_tools
    _register_domain_tools(server, HANDLERS, TOOL_DEFINITIONS, _make_tool)
except ImportError:
    # CUSTOMIZE: implementa scripts/{project}_tools.py y este import funcionará
    pass


@server.list_tools()
async def handle_list_tools():
    return TOOL_DEFINITIONS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    handler = HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"ok": False, "error": f"Unknown tool: {name}"}))]
    try:
        result = await handler(arguments or {})
        return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False, default=str))]
    except Exception as exc:  # pragma: no cover
        return [TextContent(type="text", text=json.dumps({"ok": False, "error": str(exc)}, indent=2))]


async def _run():
    import asyncio
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="{{PROJECT_NAME}}",
                server_version="0.1.0",
                capabilities={"tools": {}},
            ),
        )


def main():
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
