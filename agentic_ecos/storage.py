"""Almacenamiento de datos orgánicos de agentic-ecos.

El directorio `data/` (gitignored) guarda lo que crece con el uso del ecosistema:
patrones y presets custom descubiertos por agentes, snapshots históricos de
salud y estado interno del MCP. Vive DENTRO del repo para ser portable (se
migra copiando el repo), pero gitignored para no contaminar commits ni
conflictar con upgrades del paquete.

Ciclo de vida:
  - Los datos custom se escriben aquí (data/patterns-custom.json, ...)
  - Cuando un patrón madura, el humano lo promueve a agentic_ecos/patterns.py
    y se borra del JSON custom.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# data/ vive DENTRO del paquete (agentic_ecos/data/) — portable con el paquete,
# pero gitignored para no contaminar commits ni conflictar con upgrades.
DATA_DIR = Path(__file__).resolve().parent / "data"

# knowledge/ vive DENTRO del paquete (agentic_ecos/knowledge/) — commiteado,
# compartido vía PRs al repo upstream.
KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

# Variable de entorno para override (tests, máquinas con layout distinto)
ENV_DATA_DIR = "AGENTIC_ECOS_DATA_DIR"
ENV_WORKSPACE_DIR = "AGENTIC_ECOS_WORKSPACE_DIR"
ENV_KNOWLEDGE_DIR = "AGENTIC_ECOS_KNOWLEDGE_DIR"

# Nombres de archivos de datos
FILES = {
    "patterns_custom": "patterns-custom.json",
    "presets_custom": "presets-custom.json",
    "state": "state.json",
}


def get_data_dir() -> Path:
    env = os.environ.get(ENV_DATA_DIR)
    if env:
        return Path(env).expanduser().resolve()
    return DATA_DIR


def _atomic_write(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.rename(path)


def load_json(rel_path: str, default: Any = None) -> Any:
    """Carga un JSON desde data/ retornando `default` si no existe o está corrupto."""
    path = get_data_dir() / rel_path
    if not path.exists():
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(rel_path: str, data: Any) -> Path:
    """Guarda un JSON en data/ con escritura atómica."""
    path = get_data_dir() / rel_path
    _atomic_write(path, data)
    return path


# ─── Patterns custom ─────────────────────────────────────────────────────────

def load_custom_patterns() -> list[dict]:
    data = load_json(FILES["patterns_custom"], [])
    return data if isinstance(data, list) else []


def add_custom_pattern(pattern: dict) -> dict:
    """Agrega un patrón custom a data/patterns-custom.json.

    El patrón se valida mínimamente: requiere name y description.
    """
    if not pattern.get("name") or not pattern.get("description"):
        return {"ok": False, "error": "Pattern requires at least 'name' and 'description'"}
    patterns = load_custom_patterns()
    if any(p.get("name") == pattern["name"] for p in patterns):
        return {"ok": False, "error": f"Pattern '{pattern['name']}' already exists"}
    pattern.setdefault("custom", True)
    pattern.setdefault("domain", "custom")
    pattern.setdefault("source", "agent-discovery")
    patterns.append(pattern)
    path = save_json(FILES["patterns_custom"], patterns)
    # Hook: sincronizar Home.md del vault
    try:
        from .sync_home import hook_sync_home
        hook_sync_home()
    except Exception:
        pass
    return {"ok": True, "pattern": pattern, "path": str(path), "total_custom": len(patterns)}


def remove_custom_pattern(name: str) -> dict:
    patterns = load_custom_patterns()
    before = len(patterns)
    patterns = [p for p in patterns if p.get("name") != name]
    if len(patterns) == before:
        return {"ok": False, "error": f"Custom pattern '{name}' not found"}
    save_json(FILES["patterns_custom"], patterns)
    return {"ok": True, "removed": name}


# ─── Presets custom ──────────────────────────────────────────────────────────

def load_custom_presets() -> dict[str, dict]:
    data = load_json(FILES["presets_custom"], {})
    return data if isinstance(data, dict) else {}


def add_custom_preset(name: str, preset: dict) -> dict:
    if not name or not preset.get("label"):
        return {"ok": False, "error": "Preset requires a name and a 'label'"}
    presets = load_custom_presets()
    preset.setdefault("custom", True)
    presets[name] = preset
    path = save_json(FILES["presets_custom"], presets)
    return {"ok": True, "preset_name": name, "path": str(path), "total_custom": len(presets)}


def remove_custom_preset(name: str) -> dict:
    presets = load_custom_presets()
    if name not in presets:
        return {"ok": False, "error": f"Custom preset '{name}' not found"}
    del presets[name]
    save_json(FILES["presets_custom"], presets)
    return {"ok": True, "removed": name}


# ─── Snapshots ───────────────────────────────────────────────────────────────

def save_snapshot(payload: dict, label: str = "ecosystem-status") -> dict:
    """Guarda un snapshot histórico en data/ecosystem-snapshots/."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rel = f"ecosystem-snapshots/{label}-{ts}.json"
    path = save_json(rel, {"timestamp": ts, "label": label, **payload})
    return {"ok": True, "snapshot": str(path)}


def list_snapshots() -> list[str]:
    snap_dir = get_data_dir() / "ecosystem-snapshots"
    if not snap_dir.exists():
        return []
    return sorted(str(p.name) for p in snap_dir.glob("*.json"))


# ─── Estado interno ──────────────────────────────────────────────────────────

def get_state(key: str, default: Any = None) -> Any:
    state = load_json(FILES["state"], {}) or {}
    return state.get(key, default)


def set_state(key: str, value: Any) -> dict:
    state = load_json(FILES["state"], {}) or {}
    state[key] = value
    state["_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_json(FILES["state"], state)
    return {"ok": True, "key": key, "value": value}


def storage_status() -> dict:
    """Reporta el estado del almacenamiento orgánico."""
    d = get_data_dir()
    return {
        "data_dir": str(d),
        "exists": d.exists(),
        "custom_patterns": len(load_custom_patterns()),
        "custom_presets": len(load_custom_presets()),
        "snapshots": list_snapshots(),
        "state_keys": sorted((load_json(FILES["state"], {}) or {}).keys()),
        "knowledge_patterns": len(load_knowledge_patterns()),
        "knowledge_presets": len(load_knowledge_presets()),
        "knowledge_traps": len(load_knowledge_traps()),
        "workspace_patterns": len(load_workspace_patterns()),
        "note": "Conocimiento: built-in → knowledge/ (commiteado) → workspace/ "
                "(commiteado, fork privado) → data/ (patterns/presets commiteados). "
                "Solo snapshots/ y state.json son gitignored (runtime data).",
    }


# ─── Knowledge dir (tier 2, commiteado) ─────────────────────────────────────

def get_knowledge_dir() -> Path:
    """Directorio knowledge/ dentro del paquete (commiteado, tier 2).

    Override con AGENTIC_ECOS_KNOWLEDGE_DIR (tests, layouts distintos).
    """
    env = os.environ.get(ENV_KNOWLEDGE_DIR)
    if env:
        return Path(env).expanduser().resolve()
    return KNOWLEDGE_DIR


def _load_json_files(directory: Path, recursive: bool = False) -> list[dict]:
    """Carga todos los *.json de un directorio como lista de dicts.

    Si `recursive` es True, también carga los *.json de subdirectorios
    (ej: knowledge/traps/aws/*.json).
    """
    if not directory.exists():
        return []
    pattern = "**/*.json" if recursive else "*.json"
    items = []
    for f in sorted(directory.glob(pattern)):
        if ".gitkeep" in f.name or f.name.endswith(".tmp"):
            continue
        try:
            with open(f, "r") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                data.setdefault("source_file", str(f))
                items.append(data)
            elif isinstance(data, list):
                items.extend(data)
        except (json.JSONDecodeError, OSError):
            continue
    return items


def load_knowledge_patterns() -> list[dict]:
    """Carga patrones comunitarios de knowledge/patterns/*.json (tier 2)."""
    return _load_json_files(get_knowledge_dir() / "patterns")


def load_knowledge_presets() -> dict[str, dict]:
    """Carga presets comunitarios de knowledge/presets/*.json (tier 2)."""
    result = {}
    for item in _load_json_files(get_knowledge_dir() / "presets"):
        if item.get("name"):
            result[item["name"]] = {k: v for k, v in item.items() if k != "name"}
    return result


def load_knowledge_traps() -> list[dict]:
    """Carga traps comunitarios de knowledge/traps/** (tier 2).

    Recursivo: incluye traps de subdirectorios por nube (aws/, gcp/, azure/, do/).
    """
    return _load_json_files(get_knowledge_dir() / "traps", recursive=True)


def save_knowledge_pattern(pattern: dict) -> Path:
    """Escribe un patrón como archivo propio en knowledge/patterns/ (commiteable)."""
    name = pattern.get("name", "unnamed")
    slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    path = get_knowledge_dir() / "patterns" / f"{slug}.json"
    _atomic_write(path, pattern)
    return path


def save_knowledge_preset(name: str, preset: dict) -> Path:
    slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    path = get_knowledge_dir() / "presets" / f"{slug}.json"
    payload = {"name": name, **preset}
    _atomic_write(path, payload)
    return path


def save_knowledge_trap(trap: dict) -> Path:
    name = trap.get("name", "unnamed")
    slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    path = get_knowledge_dir() / "traps" / f"{slug}.json"
    _atomic_write(path, trap)
    return path


# ─── Workspace dir (tier 2.5, commiteado en branches de ecosistema) ─────────

def get_workspace_dir() -> Path:
    """Directorio workspace/ en la raíz del repo (branch de ecosistema).

    Override con AGENTIC_ECOS_WORKSPACE_DIR (tests, layouts distintos).
    """
    env = os.environ.get(ENV_WORKSPACE_DIR)
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "workspace"


def load_workspace_patterns() -> list[dict]:
    """Carga patrones específicos del ecosistema de workspace/patterns/*.json."""
    return _load_json_files(get_workspace_dir() / "patterns")


def save_workspace_pattern(pattern: dict) -> Path:
    name = pattern.get("name", "unnamed")
    slug = "".join(c if c.isalnum() else "_" for c in name.lower())
    path = get_workspace_dir() / "patterns" / f"{slug}.json"
    _atomic_write(path, pattern)
    return path


def workspace_tasks_path() -> Path:
    return get_workspace_dir() / "tasks.md"


def load_workspace_tasks() -> list[dict]:
    """Parsea workspace/tasks.md con el formato checkbox canónico."""
    path = workspace_tasks_path()
    if not path.exists():
        return []
    return parse_tasks_markdown(path.read_text())


def parse_tasks_markdown(content: str) -> list[dict]:
    """Parsea líneas checkbox con inline fields del formato AGENT_TASKS.

    Soporta IDs tipo T1 (proyecto) y E1 (ecosistema).
    """
    import re
    tasks = []
    for line in content.splitlines():
        m = re.match(r'^\s*- \[([ xX])\] ([TEN]?\d+):?\s*(.*)$', line)
        if not m:
            continue
        checked = m.group(1).strip().lower() == "x"
        text = m.group(3)
        fields = dict(re.findall(r'\[(\w+)::\s*(.+?)\s*\]', text))
        label = re.sub(r'\s*\[.*?\]', '', text).strip()
        tasks.append({"id": m.group(2), "label": label, "checked": checked,
                      "fields": fields, "raw": line})
    return tasks
