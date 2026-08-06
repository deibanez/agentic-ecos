"""Gestión del conocimiento compartido (tier 2) y del ecosistema (tier 2.5).

Ciclo de vida del conocimiento:
  1. Descubrir   → data/patterns-custom.json          (tier 3, gitignored, personal)
  2. Validar     → workspace/patterns/*.json          (tier 2.5, commiteado en tu branch de ecosistema)
  3. Compartir   → knowledge/patterns/*.json          (tier 2, commiteado, PR a upstream)
  4. Madurar     → agentic_ecos/patterns.py           (tier 1, built-in)
"""

from pathlib import Path

from . import storage
from .patterns import PATTERNS


def list_patterns(domain=None) -> list[dict]:
    """Todos los patrones: built-in + knowledge + workspace + custom."""
    patterns = list(PATTERNS)
    patterns.extend(storage.load_knowledge_patterns())       # tier 2
    patterns.extend(storage.load_workspace_patterns())        # tier 2.5
    patterns.extend(storage.load_custom_patterns())           # tier 3
    if domain and domain != "all":
        patterns = [p for p in patterns if p.get("domain") == domain]
    return patterns


def get_pattern(name: str):
    """Busca un patrón en todos los tiers."""
    for p in list_patterns():
        if p.get("name") == name:
            return p
    return None


def promote_to_workspace(name: str, config_path=None) -> dict:
    """Mueve un pattern de data/ (personal) a workspace/patterns/ (commiteable).

    El workspace/ vive en el branch de ecosistema, así que este patrón queda
    commiteado en tu branch, no en main.
    """
    custom = storage.load_custom_patterns()
    pattern = next((p for p in custom if p.get("name") == name), None)
    if pattern is None:
        return {"ok": False, "error": f"Pattern '{name}' not found in data/ (custom). "
                                      f"Agrega con add_custom_pattern primero."}
    path = storage.save_workspace_pattern(pattern)
    storage.remove_custom_pattern(name)
    return {"ok": True, "action": "promoted_to_workspace", "pattern": pattern,
            "path": str(path), "note": "Commitea en tu branch de ecosistema."}


def promote_to_knowledge(name: str, source: str = "workspace", kind: str = "pattern") -> dict:
    """Copia un pattern de workspace/ o data/ a knowledge/ (para PR a upstream).

    Args:
        name: nombre del pattern.
        source: 'workspace' (default) o 'data'.
        kind: 'pattern' | 'preset' | 'trap'.
    """
    if source == "data":
        pool = storage.load_custom_patterns()
        match = next((p for p in pool if p.get("name") == name), None)
    else:
        pool = storage.load_workspace_patterns()
        match = next((p for p in pool if p.get("name") == name), None)
    if match is None:
        return {"ok": False, "error": f"Pattern '{name}' not found in {source}/."}

    match.setdefault("source", "community")
    match.setdefault("promoted_at", storage.get_state("now", ""))
    if kind == "preset":
        path = storage.save_knowledge_preset(name, match)
    elif kind == "trap":
        path = storage.save_knowledge_trap(match)
    else:
        path = storage.save_knowledge_pattern(match)
    return {"ok": True, "action": f"promoted_to_knowledge[{kind}]",
            "pattern": match, "path": str(path),
            "note": "Commitea knowledge/ y crea PR a upstream/main."}


def knowledge_status() -> dict:
    """Reporta el estado del conocimiento por tier."""
    return {
        "tier1_builtin_patterns": len(PATTERNS),
        "tier2_knowledge_patterns": len(storage.load_knowledge_patterns()),
        "tier2_knowledge_presets": len(storage.load_knowledge_presets()),
        "tier2_knowledge_traps": len(storage.load_knowledge_traps()),
        "tier25_workspace_patterns": len(storage.load_workspace_patterns()),
        "tier3_custom_patterns": len(storage.load_custom_patterns()),
    }
