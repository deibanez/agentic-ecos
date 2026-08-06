"""Plano de control del ecosistema: registro canónico de proyectos (agentic.toml).

agentic-ecos gestiona UN registro TOML (`agentic.toml`) que es la fuente de
verdad de qué proyectos forman el ecosistema y su estado agéntico.

Ubicación del config (en orden de prioridad):
  1. Variable de entorno AGENTIC_ECOS_CONFIG
  2. Primer archivo `agentic.toml` subiendo desde CWD
  3. ~/.config/agentic-ecos/agentic.toml
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CONFIG_FILENAME = "agentic.toml"
ENV_CONFIG = "AGENTIC_ECOS_CONFIG"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "agentic-ecos"

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_config_path() -> Path:
    """Ruta por defecto del config (env override, luego ~/.config)."""
    env = os.environ.get(ENV_CONFIG)
    if env:
        return Path(env)
    return DEFAULT_CONFIG_DIR / CONFIG_FILENAME


def find_config(start: Optional[Path] = None) -> Optional[Path]:
    """Busca el agentic.toml subiendo desde `start` (default: CWD).

    Prioridad: env var → búsqueda ascendente → workspace/agentic.toml del repo
    agentic-ecos → ~/.config.
    """
    env = os.environ.get(ENV_CONFIG)
    if env and Path(env).exists():
        return Path(env)

    cursor = (start or Path.cwd()).resolve()
    for parent in [cursor, *cursor.parents]:
        candidate = parent / CONFIG_FILENAME
        if candidate.exists():
            return candidate

    # workspace/agentic.toml dentro del repo agentic-ecos (branch de ecosistema)
    repo_ws = Path(__file__).resolve().parent.parent / "workspace" / CONFIG_FILENAME
    if repo_ws.exists():
        return repo_ws

    default = default_config_path()
    if default.exists():
        return default
    return None


def repo_workspace_dir() -> Path:
    """Directorio workspace/ en la raíz del repo agentic-ecos (branch de ecosistema)."""
    return Path(__file__).resolve().parent.parent / "workspace"


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v))


def save_config(data: dict, path: Optional[Path] = None) -> Path:
    """Escribe el registro agentic.toml desde un dict."""
    path = Path(path) if path else default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    eco = data.get("ecosystem", {})
    lines.append("[ecosystem]")
    for k, v in eco.items():
        lines.append(f"{k} = {_toml_value(v)}")
    lines.append("")

    defaults = data.get("defaults", {})
    if defaults:
        lines.append("[defaults]")
        for k, v in defaults.items():
            lines.append(f"{k} = {_toml_value(v)}")
        lines.append("")

    for proj in data.get("projects", []):
        lines.append("[[projects]]")
        for k, v in proj.items():
            lines.append(f"{k} = {_toml_value(v)}")
        lines.append("")

    # Escritura atómica (IAC_TRAPS #10): temp + rename
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines))
    tmp.rename(path)
    return path


def load_config(path: Optional[Path] = None) -> dict:
    """Carga el registro agentic.toml. Devuelve dict vacío si no existe."""
    if tomllib is None:
        raise RuntimeError("tomllib no disponible (Python 3.11+)")
    resolved = Path(path) if path else find_config()
    if not resolved or not resolved.exists():
        return {"ecosystem": {}, "defaults": {}, "projects": []}
    with open(resolved, "rb") as f:
        data = tomllib.load(f)
    data.setdefault("ecosystem", {})
    data.setdefault("defaults", {})
    data.setdefault("projects", [])
    return data


# ─── ecosystem_init ───────────────────────────────────────────────────────────

DEFAULT_SCAN_SUBDIRS = ["00_Global", "docs/00_Global", "docs/AGENTS.md", "AGENTS.md"]


def _has_agentic_infra(project_dir: Path) -> bool:
    """Detecta si un directorio ya tiene infraestructura agéntica."""
    for rel in ["00_Global/AGENTS.md", "00_Global/AGENT_REGISTRY.md",
                "docs/00_Global/AGENTS.md", "00_Global/AGENT_TASKS.md"]:
        if (project_dir / rel).exists():
            return True
    return False


def _scan_projects(workspace_root: Path, vault_path: str = "docs") -> list[dict]:
    """Auto-detecta proyectos en el workspace que ya tienen infra agéntica."""
    found = []
    if not workspace_root.exists():
        return found
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        # Solo directorios con señales de proyecto (git, package, docs)
        has_git = (child / ".git").exists()
        has_code = any((child / f).exists() for f in ["package.json", "pyproject.toml",
                                                      "requirements.txt", "go.mod", "Cargo.toml"])
        if not (has_git or has_code):
            continue
        agentic = _has_agentic_infra(child)
        found.append({
            "name": child.name,
            "path": child.name,
            "type": "unknown",
            "preset": "monorepo",
            "agentic_infra": agentic,
            "status": "operational" if agentic else "pending",
            "notes": "",
        })
    return found


def ecosystem_init(
    name: str,
    workspace_root: str,
    cloud: str = "aws",
    ci_cd: str = "github-actions",
    language: str = "es",
    vault_path: str = "docs",
    description: str = "",
    scan: bool = True,
    config_path: Optional[str] = None,
) -> dict:
    """Inicializa el plano de control: crea agentic.toml con los proyectos detectados.

    El config por defecto se escribe en `workspace/agentic.toml` dentro del repo
    (branch de ecosistema), autocontenido y commiteable. Si `config_path` se
    pasa, se escribe allí.
    """
    root = Path(workspace_root).expanduser().resolve()
    projects = _scan_projects(root) if scan else []
    data = {
        "ecosystem": {
            "name": name,
            "description": description,
            "workspace_root": str(root),
            "created": utc_now(),
            "updated": utc_now(),
        },
        "defaults": {
            "cloud": cloud,
            "ci_cd": ci_cd,
            "language": language,
            "vault_path": vault_path,
        },
        "projects": projects,
    }
    # Default: workspace/agentic.toml dentro del repo (branch de ecosistema)
    if config_path is None:
        ws_dir = repo_workspace_dir()
        ws_dir.mkdir(parents=True, exist_ok=True)
        config_path = str(ws_dir / CONFIG_FILENAME)
    path = save_config(data, Path(config_path))
    return {
        "ok": True,
        "config_path": str(path),
        "ecosystem": data["ecosystem"],
        "projects_found": projects,
        "projects_count": len(projects),
        "detected_with_infra": sum(1 for p in projects if p["agentic_infra"]),
    }


# ─── project_add / project_update ────────────────────────────────────────────

def project_add(
    name: str,
    project_type: str = "backend",
    path: Optional[str] = None,
    preset: str = "monorepo",
    status: str = "pending",
    notes: str = "",
    config_path: Optional[str] = None,
) -> dict:
    """Registra un proyecto en agentic.toml (no genera infra, solo registra)."""
    data = load_config(config_path)
    if not data.get("ecosystem"):
        return {"ok": False, "error": "No ecosystem config found. Run ecosystem_init first."}

    proj_path = path or name
    # Detectar infra agéntica real si workspace_root existe
    ws = data["ecosystem"].get("workspace_root", "")
    agentic = False
    if ws:
        vault = data.get("defaults", {}).get("vault_path", "docs")
        agentic = _has_agentic_infra(Path(ws) / proj_path / vault) or \
            _has_agentic_infra(Path(ws) / proj_path)

    existing = next((p for p in data["projects"] if p.get("name") == name), None)
    entry = {
        "name": name,
        "path": proj_path,
        "type": project_type,
        "preset": preset,
        "agentic_infra": agentic,
        "status": status,
        "notes": notes,
    }
    if existing:
        existing.update(entry)
        action = "updated"
    else:
        data["projects"].append(entry)
        action = "added"

    data.setdefault("ecosystem", {}).setdefault("updated", utc_now())
    data["ecosystem"]["updated"] = utc_now()
    path_saved = save_config(data, Path(config_path) if config_path else None)
    return {"ok": True, "action": action, "project": entry, "config_path": str(path_saved)}


def project_remove(name: str, config_path: Optional[str] = None) -> dict:
    """Elimina un proyecto del registro agentic.toml."""
    data = load_config(config_path)
    before = len(data.get("projects", []))
    data["projects"] = [p for p in data.get("projects", []) if p.get("name") != name]
    if len(data["projects"]) == before:
        return {"ok": False, "error": f"Project '{name}' not found in registry"}
    data.setdefault("ecosystem", {}).setdefault("updated", utc_now())
    data["ecosystem"]["updated"] = utc_now()
    save_config(data, Path(config_path) if config_path else None)
    return {"ok": True, "action": "removed", "project": name}


# ─── ecosystem_status ────────────────────────────────────────────────────────

def ecosystem_status(config_path: Optional[str] = None) -> dict:
    """Reporte de salud del ecosistema: proyectos, cobertura agéntica, gaps."""
    data = load_config(config_path)
    projects = data.get("projects", [])
    ws = data["ecosystem"].get("workspace_root", "")
    vault = data.get("defaults", {}).get("vault_path", "docs")

    # Validar cobertura agéntica de cada proyecto con validate_structure
    from .generator import validate_structure

    enriched = []
    for p in projects:
        p = dict(p)
        coverage = None
        if ws and p.get("path"):
            base = Path(ws) / p["path"] / vault
            if not base.exists():
                base = Path(ws) / p["path"]
            v = validate_structure(str(base))
            coverage = v["coverage_pct"]
            p["agentic_infra"] = v["ok"] or v["coverage_pct"] >= 80
            p["coverage_pct"] = coverage
            p["missing_count"] = len(v["missing"])
        enriched.append(p)

    with_infra = sum(1 for p in enriched if p.get("agentic_infra"))
    return {
        "ok": True,
        "ecosystem": data["ecosystem"],
        "defaults": data["defaults"],
        "projects_count": len(enriched),
        "with_agentic_infra": with_infra,
        "without_agentic_infra": len(enriched) - with_infra,
        "projects": enriched,
        "config_path": str(Path(config_path) if config_path else (find_config() or "")),
    }


# ─── Tasks cross-cutting (workspace/tasks.md) ────────────────────────────────

TASKS_MARKER_START = "<!-- TASKS_START -->"
TASKS_MARKER_END = "<!-- TASKS_END -->"


def ecosystem_tasks(config_path: Optional[str] = None) -> dict:
    """Agregado de tareas: cross-cutting (workspace/tasks.md) + por proyecto.

    Devuelve las tareas cross-cutting del ecosistema y el conteo por proyecto
    (leyendo el AGENT_TASKS.md de cada proyecto registrado).
    """
    data = load_config(config_path)
    ws = data["ecosystem"].get("workspace_root", "")
    vault = data.get("defaults", {}).get("vault_path", "docs")
    projects = data.get("projects", [])

    from . import storage
    cross = storage.load_workspace_tasks()

    # Tareas por proyecto (AGENT_TASKS.md de cada vault)
    per_project = {}
    for p in projects:
        name = p.get("name", "?")
        if ws and p.get("path"):
            base = Path(ws) / p["path"] / vault
            if not base.exists():
                base = Path(ws) / p["path"]
            tasks_file = base / "00_Global" / "AGENT_TASKS.md"
            if tasks_file.exists():
                parsed = storage.parse_tasks_markdown(tasks_file.read_text())
            else:
                parsed = []
            counts = {"total": len(parsed),
                      "backlog": sum(1 for t in parsed if t["fields"].get("status", "backlog") == "backlog" and not t["checked"]),
                      "doing": sum(1 for t in parsed if t["fields"].get("status") == "doing" or t["checked"]),
                      "done": sum(1 for t in parsed if t["checked"] or t["fields"].get("status") == "done")}
            per_project[name] = {"total": counts["total"], "backlog": counts["backlog"],
                                 "doing": counts["doing"], "done": counts["done"]}
        else:
            per_project[name] = {"total": 0, "backlog": 0, "doing": 0, "done": 0}

    backlog = [t for t in cross if not t["checked"] and t["fields"].get("status", "backlog") == "backlog"]
    return {
        "ok": True,
        "cross_cutting": cross,
        "cross_cutting_count": len(cross),
        "cross_cutting_backlog": len(backlog),
        "per_project": per_project,
        "ecosystem_backlog": sum(v["backlog"] for v in per_project.values()) + len(backlog),
        "tasks_file": str(storage.workspace_tasks_path()),
    }


def ecosystem_task_add(
    description: str,
    priority: str = "medium",
    type: str = "ops",
    scope: str = "ecosystem",
    config_path: Optional[str] = None,
) -> dict:
    """Agrega una tarea cross-cutting al workspace/tasks.md.

    Formato canónico: `- [ ] E{n}: {desc} [priority:: {p}] [status:: backlog] [type:: {t}] [scope:: {s}]`
    """
    from . import storage
    from .generator import to_slug

    path = storage.workspace_tasks_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    content = ""
    if path.exists():
        content = path.read_text()

    # Generar ID E{n}
    existing = storage.load_workspace_tasks()
    ids = [int(t["id"][1:]) for t in existing if t["id"].startswith("E")]
    next_id = max(ids) + 1 if ids else 1
    task_id = f"E{next_id}"

    line = (f"- [ ] {task_id}: {description} [priority:: {priority}] "
            f"[status:: backlog] [type:: {type}] [scope:: {scope}]")

    if TASKS_MARKER_START not in content:
        header = "---\ntags: [layer/l0, tasks, ecosystem]\npurpose: Tareas cross-cutting del ecosistema\n---\n\n# ECOSYSTEM_TASKS — Tareas Cross-Cutting\n\n"
        content = header + "\n" + TASKS_MARKER_START + "\n" + line + "\n" + TASKS_MARKER_END + "\n"
    else:
        content = content.replace(TASKS_MARKER_END, line + "\n" + TASKS_MARKER_END)

    # Escritura atómica
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content)
    tmp.rename(path)

    return {"ok": True, "task_id": task_id, "line": line, "path": str(path),
            "note": "Commitea workspace/tasks.md en tu branch de ecosistema."}


# ─── connect (opencode.jsonc) ────────────────────────────────────────────────

def _strip_jsonc_comments(text: str) -> str:
    """Elimina comentarios // y /* */ respetando strings."""
    out = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_string:
            out.append(c)
            if c == "\\":
                out.append(nxt)
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and nxt == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _insert_mcp_entry(jsonc: str, server_name: str, payload: dict) -> str:
    """Inserta o actualiza una entrada MCP en un opencode.jsonc preservando comentarios."""
    # Buscar la sección "mcp" en texto limpio (sin comentarios) para ubicar
    clean = _strip_jsonc_comments(jsonc)
    entry_text = json.dumps({server_name: payload}, indent=2, ensure_ascii=False)
    # Quitar llaves externas para incrustar
    inner = entry_text.strip()
    if inner.startswith("{"):
        inner = inner[1:]
    if inner.endswith("}"):
        inner = inner[:-1]
    inner = inner.strip().rstrip(",")

    mcp_idx = clean.find('"mcp"')
    if mcp_idx == -1:
        # No hay sección mcp → insertar antes del cierre de la raíz
        brace = jsonc.rfind("}")
        if brace == -1:
            return jsonc.rstrip() + "\n{\n  \"mcp\": {\n" + inner + "\n  }\n}"
        # Insertar tras la última llave que abre la raíz (antes del último })
        tail = jsonc[:brace].rstrip()
        if tail.endswith(",") or tail.endswith("{"):
            sep = ""
        else:
            sep = ","
        return tail + sep + "\n  \"mcp\": {\n" + inner + "\n  }\n" + jsonc[brace:]

    # Ya existe "mcp" → insertar entrada dentro de sus llaves
    brace_open = clean.find("{", mcp_idx)
    if brace_open == -1:
        return jsonc
    # Buscar la llave de cierre balanceada del objeto mcp
    depth = 0
    j = brace_open
    for j in range(brace_open, len(clean)):
        if clean[j] == "{":
            depth += 1
        elif clean[j] == "}":
            depth -= 1
            if depth == 0:
                break
    # Insertar entrada justo antes del cierre del objeto mcp en el texto ORIGINAL
    # Usar posición relativa aproximada: localizar en el original el mismo offset
    # Mapear offset limpio→original es complejo; hacer inserción textual simple:
    if '"' + server_name + '"' in jsonc:
        return jsonc  # ya está conectado
    # Encontrar la posición original del '}' que cierra mcp buscando en el texto original
    # desde brace_open es frágil → usar última ocurrencia balanceada en original
    orig_mcp = jsonc.find('"mcp"')
    if orig_mcp == -1:
        return jsonc
    orig_brace = jsonc.find("{", orig_mcp)
    depth = 0
    k = orig_brace
    for k in range(orig_brace, len(jsonc)):
        # ignorar strings simples
        ch = jsonc[k]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
    insert_at = jsonc.rfind("}", 0, k)
    prefix = jsonc[:k].rstrip()
    if not prefix.endswith("{"):
        prefix += ","
    return prefix + "\n    " + inner + "\n  " + jsonc[k:]


# Configuración MCP por agente (dónde vive el config y su formato de entrada)
AGENT_MCP_CONFIGS = {
    "opencode": {
        "path": "opencode.jsonc",
        "key": "mcp",
        "make_entry": lambda ap: {"agentic-ecos": {
            "type": "local",
            "command": ["uv", "run", "--directory", ap, "agentic_ecos/server.py"],
        }},
        "jsonc": True,
    },
    "claude": {
        "path": ".mcp.json",
        "key": "mcpServers",
        "make_entry": lambda ap: {"agentic-ecos": {
            "command": "uv",
            "args": ["run", "--directory", ap, "agentic_ecos/server.py"],
        }},
        "jsonc": False,
    },
    "cursor": {
        "path": ".cursor/mcp.json",
        "key": "mcpServers",
        "make_entry": lambda ap: {"agentic-ecos": {
            "command": "uv",
            "args": ["run", "--directory", ap, "agentic_ecos/server.py"],
        }},
        "jsonc": False,
    },
}


def connect(
    target: Optional[str] = None,
    agent: str = "auto",
    agentic_path: Optional[str] = None,
    create_if_missing: bool = True,
    config_path: Optional[str] = None,
) -> dict:
    """Configura agentic-ecos como MCP server para uno o más agentes.

    Args:
        target: Directorio donde escribir el/los config (default: workspace_root
                del agentic.toml, o CWD si no hay config).
        agent: 'opencode' | 'claude' | 'cursor' | 'auto' (detecta presentes)
               | 'snippet' (solo devuelve los fragmentos, no escribe archivos).
        agentic_path: Ruta absoluta al repo agentic-ecos (default: este repo).
        create_if_missing: Crear el archivo de config si no existe.
        config_path: Ruta al agentic.toml.
    """
    if agentic_path is None:
        agentic_path = str(Path(__file__).resolve().parent.parent)

    if target is None:
        data = load_config(config_path)
        ws = data.get("ecosystem", {}).get("workspace_root")
        target = ws if ws else str(Path.cwd())
    target = Path(target).expanduser().resolve()

    # Resolver qué agentes configurar
    if agent == "snippet":
        snippets = {}
        for name, cfg in AGENT_MCP_CONFIGS.items():
            snippets[name] = {cfg["key"]: cfg["make_entry"](agentic_path)}
        return {"ok": True, "mode": "snippet", "snippets": snippets,
                "note": "Pega el fragmento correspondiente en tu archivo de config del agente."}

    if agent == "auto":
        agents_to_do = [name for name in AGENT_MCP_CONFIGS
                        if (target / AGENT_MCP_CONFIGS[name]["path"]).exists()]
        # Si no hay ningún config presente, default a opencode (el más común)
        if not agents_to_do:
            agents_to_do = ["opencode"]
    else:
        if agent not in AGENT_MCP_CONFIGS:
            return {"ok": False, "error": f"Agent '{agent}' not supported. "
                                          f"Available: {', '.join(AGENT_MCP_CONFIGS)} + auto/snippet"}
        agents_to_do = [agent]

    results = {}
    all_done = True
    for name in agents_to_do:
        cfg = AGENT_MCP_CONFIGS[name]
        path = target / cfg["path"]
        payload = cfg["make_entry"](agentic_path)

        if path.exists():
            original = path.read_text()
            if '"agentic-ecos"' in original:
                results[name] = {"status": "already_connected", "path": str(path)}
                continue
            if cfg["jsonc"]:
                updated = _insert_mcp_entry(original, "agentic-ecos", payload)
                path.write_text(updated)
            else:
                # JSON puro (claude/cursor): parsear, agregar, re-serializar
                import json as _json
                try:
                    data = _json.loads(_strip_jsonc_comments(original))
                except _json.JSONDecodeError:
                    data = {}
                data.setdefault(cfg["key"], {})["agentic-ecos"] = payload[list(payload)[0]]
                path.write_text(_json.dumps(data, indent=2, ensure_ascii=False))
            results[name] = {"status": "connected", "path": str(path)}
        elif create_if_missing:
            if cfg["jsonc"]:
                content = json.dumps({
                    "instructions": ["00_Global/AGENTS.md"],
                    "mcp": {"agentic-ecos": payload["agentic-ecos"]},
                }, indent=2, ensure_ascii=False)
            else:
                content = json.dumps({cfg["key"]: payload}, indent=2, ensure_ascii=False)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            results[name] = {"status": "created", "path": str(path)}
        else:
            results[name] = {"status": "skipped_missing", "path": str(path)}
            all_done = False

    return {
        "ok": all_done,
        "agent": agent,
        "agents_configured": agents_to_do,
        "results": results,
        "target": str(target),
        "agentic_path": agentic_path,
    }


def connect_status(target: Optional[str] = None, config_path: Optional[str] = None) -> dict:
    """Detecta qué agentes tienen config en target y si agentic-ecos está conectado."""
    data = load_config(config_path)
    ws = data.get("ecosystem", {}).get("workspace_root")
    if target is None:
        target = ws if ws else str(Path.cwd())
    target = Path(target).expanduser().resolve()

    detected = {}
    for name, cfg in AGENT_MCP_CONFIGS.items():
        path = target / cfg["path"]
        if path.exists():
            connected = '"agentic-ecos"' in path.read_text()
            detected[name] = {"config_exists": True, "connected": connected, "path": str(path)}
        else:
            detected[name] = {"config_exists": False, "connected": False, "path": str(path)}

    return {
        "ok": True,
        "target": str(target),
        "agents": detected,
        "connected_any": any(v["connected"] for v in detected.values()),
    }


def scan_opencode(workspace_root: Optional[str] = None) -> dict:
    """Escanea el workspace y reporta qué proyectos tienen agentic-ecos conectado.

    Incluye todo subdirectorio que parezca un proyecto (git/code marker), tenga
    o no opencode.jsonc. Los sin opencode.jsonc se reportan como not_connected.
    """
    data = load_config()
    ws = workspace_root or data.get("ecosystem", {}).get("workspace_root") or str(Path.cwd())
    root = Path(ws).expanduser().resolve()
    results = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        has_git = (child / ".git").exists()
        has_code = any((child / f).exists() for f in ["package.json", "pyproject.toml",
                                                      "requirements.txt", "go.mod", "Cargo.toml"])
        if not (has_git or has_code):
            continue
        jsonc = child / "opencode.jsonc"
        if jsonc.exists():
            connected = '"agentic-ecos"' in jsonc.read_text()
            results.append({"project": child.name, "opencode_jsonc": str(jsonc),
                            "connected": connected})
        else:
            results.append({"project": child.name, "opencode_jsonc": None,
                            "connected": False})
    return {"workspace_root": str(root), "projects": results,
            "connected": sum(1 for r in results if r["connected"]),
            "not_connected": sum(1 for r in results if not r["connected"])}
