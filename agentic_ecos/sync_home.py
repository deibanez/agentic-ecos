"""Sincronización del Home.md del vault con el estado vivo del ecosistema.

Regenera los bloques `<!-- AUTO_START: X -->` ... `<!-- AUTO_END: X -->` del
Home.md con las métricas actuales, preservando el contenido estático
(descripción, MOCs, tags, Dataview queries).

Bloques gestionados:
  - pulse:          tabla de métricas del ecosistema (proyectos, tareas, conocimiento)
  - knowledge-table: estado del conocimiento por tier
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import storage

MARKER_START = "<!-- AUTO_START: {name} -->"
MARKER_END = "<!-- AUTO_END: {name} -->"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def find_home_md(target_path: Optional[Path] = None) -> Path:
    """Localiza el Home.md del vault. Default: vault autodocumental de agentic-ecos."""
    if target_path is not None:
        candidate = Path(target_path) / "00_Global" / "Home.md"
        if candidate.exists():
            return candidate
        candidate2 = Path(target_path) / "Home.md"
        if candidate2.exists():
            return candidate2
        return candidate  # no existe aún, se creará en target
    # vault autodocumental del repo agentic-ecos
    return Path(__file__).resolve().parent.parent / "docs" / "00_Global" / "Home.md"


def _norm_knowledge(knowledge: dict) -> dict:
    """Normaliza las keys de knowledge_status a las usadas por los bloques."""
    return {
        "tier1_builtin": knowledge.get("tier1_builtin_patterns",
                                        knowledge.get("tier1_builtin", 0)),
        "tier2_patterns": knowledge.get("tier2_knowledge_patterns",
                                         knowledge.get("tier2_patterns", 0)),
        "tier2_traps": knowledge.get("tier2_knowledge_traps",
                                      knowledge.get("tier2_traps", 0)),
        "tier3_custom": knowledge.get("tier3_custom_patterns",
                                      knowledge.get("tier3_custom", 0)),
    }


def _get_pulse_block(ecosystem: dict, tasks: dict, knowledge: dict) -> str:
    """Genera el contenido del bloque pulse."""
    k = _norm_knowledge(knowledge)
    projects = ecosystem.get("projects_count", ecosystem.get("projects", 0))
    with_infra = ecosystem.get("with_agentic_infra", ecosystem.get("with_infra", 0))
    without_infra = ecosystem.get("without_agentic_infra", ecosystem.get("without_infra", 0))
    lines = [
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Proyectos registrados | {projects} |",
        f"| Con infra agencia | {with_infra} |",
        f"| Sin infra agencia | {without_infra} |",
        f"| Tareas en backlog | {tasks.get('ecosystem_backlog', 0)} |",
        f"| Patrones built-in | {k['tier1_builtin']} |",
        f"| Traps curados | {k['tier2_traps']} |",
        f"| Patrones en experimentacion | {k['tier3_custom']} |",
        "",
        f"_Actualizado: {utc_now()}_",
    ]
    return "\n".join(lines)


def _get_knowledge_table(knowledge: dict) -> str:
    """Genera el contenido del bloque knowledge-table."""
    k = _norm_knowledge(knowledge)
    lines = [
        "| Tier | Patrones | Traps |",
        "|------|:---:|:---:|",
        f"| 1 · Built-in | {k['tier1_builtin']} | — |",
        f"| 2 · Knowledge | {k['tier2_patterns']} | {k['tier2_traps']} |",
        f"| 3 · Custom | {k['tier3_custom']} | — |",
    ]
    return "\n".join(lines)


def _replace_block(content: str, name: str, new_block: str) -> str:
    """Reemplaza o inserta un bloque AUTO_START/AUTO_END en el contenido."""
    start_marker = MARKER_START.format(name=name)
    end_marker = MARKER_END.format(name=name)

    if start_marker in content and end_marker in content:
        # Reemplazar el contenido entre marcadores
        start_idx = content.index(start_marker) + len(start_marker)
        end_idx = content.index(end_marker)
        return content[:start_idx] + "\n" + new_block + "\n" + content[end_idx:]

    # Insertar antes de "## Mapas de Contenido" o al final
    section = f"{start_marker}\n{new_block}\n{end_marker}"
    insert_after = "## Mapas de Contenido (MOCs)"
    if insert_after in content:
        idx = content.index(insert_after)
        # Insertar justo antes de la sección de MOCs
        return content[:idx] + section + "\n\n" + content[idx:]
    return content.rstrip() + "\n\n" + section + "\n"


def sync_home_md(target_path: Optional[Path] = None) -> dict:
    """Regenera los bloques dinámicos del Home.md del vault.

    Args:
        target_path: raíz del vault (default: vault autodocumental de agentic-ecos).

    Returns:
        dict con ok, path, y bloques actualizados.
    """
    try:
        from .ecosystem import ecosystem_status, ecosystem_tasks
        from .knowledge import knowledge_status
    except Exception:
        pass

    home = find_home_md(target_path)
    home.parent.mkdir(parents=True, exist_ok=True)

    # Recolectar estado vivo (con fallbacks para no bloquear)
    ecosystem = {}
    tasks = {}
    knowledge = {}
    try:
        ecosystem = ecosystem_status()
    except Exception:
        ecosystem = {}
    try:
        tasks = ecosystem_tasks()
    except Exception:
        tasks = {}
    try:
        knowledge = knowledge_status()
    except Exception:
        knowledge = {}

    if not home.exists():
        home.write_text("# agentic-ecos\n\n> Vault autodocumental del ecosistema agéntico.\n\n")

    content = home.read_text()

    # Generar bloques
    pulse = _get_pulse_block(ecosystem, tasks, knowledge)
    ktable = _get_knowledge_table(knowledge)

    updated = _replace_block(content, "pulse", pulse)
    updated = _replace_block(updated, "knowledge-table", ktable)

    # Escritura atómica
    tmp = home.with_suffix(".tmp")
    tmp.write_text(updated)
    tmp.rename(home)

    return {
        "ok": True,
        "path": str(home),
        "blocks_updated": ["pulse", "knowledge-table"],
        "pulse": pulse.splitlines()[0],
    }


def hook_sync_home(target_path: Optional[Path] = None) -> None:
    """Hook seguro para llamar desde otras tools — nunca rompe el flujo principal."""
    try:
        sync_home_md(target_path)
    except Exception:
        pass

