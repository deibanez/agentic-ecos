"""Generador de infraestructura agéntica para proyectos.

Orquesta el bootstrap completo de un proyecto: crea la estructura de
directorios, copia los scripts static, renderiza las plantillas markdown,
genera protocolos personalizados, el vault de Obsidian y el MCP server
skeleton con stubs de tools de dominio.
"""

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import __version__
from .presets import get_preset
from .protocols import PROTOCOLS

# Directorio del paquete (contiene static/ y templates/)
PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"
TEMPLATES_DIR = PACKAGE_DIR / "templates"

# Archivos estáticos que se copian tal cual.
STATIC_FILES = [
    "lock_manager.py",
    "lock_manager.sh",
    "agent_daemon.sh",
    "lock_dashboard.py",
    "signature.py",
    "sync_kanban.py",
    "cleanup_orphans.py",
    "orchestrator.py",
]

# Archivos template → destino relativo al vault.
TEMPLATE_FILES = {
    "registry.md": "00_Global/AGENT_REGISTRY.md",
    "tasks.md": "00_Global/AGENT_TASKS.md",
    "comms.md": "00_Global/AGENT_COMMS.md",
    "session_log.md": "00_Global/AGENT_SESSION_LOG.md",
    "onboarding.md": "00_Global/AGENT_ONBOARDING.md",
    "skills.md": "00_Global/RULES/AGENT_SKILLS.md",
    "traps.md": "00_Global/RULES/IAC_TRAPS.md",
    "home.md": "00_Global/Home.md",
    "workspace_state.md": "00_Global/STATE/WORKSPACE_STATE.md",
    "dashboard_tasks.md": "00_Global/dashboards/task-dashboard.md",
    "opencode.jsonc": "00_Global/opencode.jsonc",
}

# Protocolos → destino relativo al vault.
PROTOCOL_FILES = {
    "agent_protocol": "00_Global/RULES/AGENT_PROTOCOL.md",
    "multi_agent": "00_Global/RULES/MULTI_AGENT.md",
    "lock_protocol": "00_Global/LOCK_PROTOCOL.md",
    "access_control": "00_Global/ACCESS_CONTROL.md",
    "agents_guide": "00_Global/AGENTS.md",
}

# MOCs: (nombre_archivo, título, emoji, tag)
MOCS = [
    ("MOC-Agents.md", "Agentes", "🤖", "agents"),
    ("MOC-Rules.md", "Reglas", "📜", "rules"),
    ("MOC-Architecture.md", "Arquitectura", "🏗", "architecture"),
    ("MOC-Repos.md", "Componentes", "📦", "state"),
    ("MOC-Operations.md", "Operaciones", "🔧", "runbook"),
    ("MOC-Guides.md", "Guías", "📖", "guide"),
    ("MOC-Tasks.md", "Tareas", "📋", "tasks"),
]

# Directorios que se crean vacíos (con .gitkeep).
EMPTY_DIRS = [".locks", "DATA", "00_Global/STATE", "00_Global/dashboards", "00_Global/kanban", "repos"]


def render_template(content: str, context: dict) -> str:
    """Reemplaza {{PLACEHOLDER}} en el contenido con los valores del context."""
    for key, value in context.items():
        content = content.replace("{{" + key + "}}", str(value))
    return content


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def to_slug(name: str) -> str:
    """Convierte un nombre de proyecto a slug de python (lowercase, _, no guiones)."""
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


def build_context(project_name: str, description: str, preset: dict,
                  repos: list[dict], cloud: str, ci_cd: str, language: str) -> dict:
    """Construye el context de renderizado común a todas las plantillas."""
    slug = to_slug(project_name)
    repo_rows = "\n".join(
        f"| {r['name']} | {r['type']} | {r.get('iac', 'none')} | {ci_cd} | |" for r in repos
    )
    component_rows = "\n".join(
        f"| {r['name']} | {r['type']} | ⏳ | — | |" for r in repos
    )
    protection_rules = "\n".join(preset.get("protection_rules", []))
    traps_sections = "\n".join(
        f"     - **{s}**: traps de {s} del proyecto" for s in preset.get("traps_sections", [])
    )
    return {
        "PROJECT_NAME": project_name,
        "PROJECT_SLUG": slug,
        "PROJECT_DESCRIPTION": description,
        "DATE": utc_now(),
        "VERSION": __version__,
        "REPO_ROWS": repo_rows,
        "COMPONENT_ROWS": component_rows,
        "PROTECTION_RULES": protection_rules or "_Definir reglas de protección (ver CUSTOMIZE)_",
        "TRAPS_SECTIONS": traps_sections,
        "CLOUD": cloud,
        "CI_CD": ci_cd,
        "LANGUAGE": language,
        "DOMAIN_TOOLS_SECTION": "",
    }


def _make_moc_links(project_name: str) -> str:
    """Genera los links de cada MOC apuntando a los archivos canónicos relevantes."""
    return "\n".join(
        f"- [[00_Global/{f}|{t}]]" for f, t in [
            ("AGENTS.md", "AGENTS.md — Guía del workspace"),
            ("AGENT_PROTOCOL.md", "AGENT_PROTOCOL.md — Código de conducta"),
            ("AGENT_REGISTRY.md", "AGENT_REGISTRY.md — Identidad de agentes"),
            ("AGENT_TASKS.md", "AGENT_TASKS.md — Cola de tareas"),
            ("AGENT_COMMS.md", "AGENT_COMMS.md — Comunicación"),
            ("AGENT_SESSION_LOG.md", "AGENT_SESSION_LOG.md — Auditoría"),
            ("LOCK_PROTOCOL.md", "LOCK_PROTOCOL.md — Locks"),
            ("ACCESS_CONTROL.md", "ACCESS_CONTROL.md — Permisos"),
            ("RULES/MULTI_AGENT.md", "MULTI_AGENT.md — Coordinación multi-agente"),
            ("RULES/AGENT_SKILLS.md", "AGENT_SKILLS.md — Catálogo de skills"),
            ("RULES/IAC_TRAPS.md", "IAC_TRAPS.md — Traps técnicos"),
            ("STATE/WORKSPACE_STATE.md", "WORKSPACE_STATE.md — Estado del proyecto"),
            ("dashboards/task-dashboard.md", "Dashboard de tareas"),
        ]
    )


def generate_domain_tools(project_name: str, preset: dict) -> str:
    """Genera el módulo de tools de dominio con stubs."""
    slug = to_slug(project_name)
    template = (TEMPLATES_DIR / "domain_tools.py").read_text()
    tool_stubs = []
    for tool in preset.get("domain_tools", []):
        tname = tool["name"]
        tdesc = tool["description"]
        returns = tool.get("returns", "{}")
        tool_stubs.append(
            f"""    async def _{tname}(args):
        \"\"\"{tdesc}

        CUSTOMIZE: implementa la lógica real de esta tool.
        \"\"\"
        # TODO: implementar — consulta tu CI/CD, healthchecks o pipelines
        return {returns}

    HANDLERS["{tname}"] = _{tname}
    TOOL_DEFINITIONS.append(make_tool(
        "{tname}",
        "{tdesc}",
        {{}},
    ))"""
        )
    context = {
        "PROJECT_NAME": project_name,
        "TOOL_STUBS": "\n\n".join(tool_stubs),
    }
    return render_template(template, context)


def generate_mcp_server(project_name: str, preset: dict) -> str:
    """Genera el MCP server skeleton con placeholders resueltos."""
    template = (TEMPLATES_DIR / "mcp_server.py").read_text()
    context = {
        "PROJECT_NAME": project_name,
        "PROJECT_SLUG": to_slug(project_name),
        "DOMAIN_TOOLS_IMPORT": "",
    }
    return render_template(template, context)


def init_project(
    project_name: str,
    preset_name: str = "monorepo",
    target_path: Optional[str] = None,
    repos: Optional[list[str]] = None,
    cloud: str = "none",
    ci_cd: str = "github-actions",
    language: str = "en",
    description: str = "",
    register: bool = True,
    project_type: str = "backend",
) -> dict:
    """Workflow principal: genera el esqueleto agéntico completo.

    Args:
        project_name: Nombre del proyecto (ej: 'satet-ng').
        preset_name: 'monorepo' | 'single_service' | 'data_pipeline'.
        target_path: Ruta donde generar (default: ./<slug>/docs).
        repos: Lista de componentes (default: los del preset).
        cloud: 'aws' | 'gcp' | 'azure' | 'none'.
        ci_cd: 'github-actions' | 'gitlab-ci' | 'none'.
        language: 'en' | 'es' (idioma de los comentarios CUSTOMIZE).
        description: Descripción breve del proyecto.
        register: Registrar el proyecto en agentic.toml tras generar (si hay config).
        project_type: Tipo del proyecto para el registro (backend | frontend | data | docs | infra).

    Returns:
        dict con summary, archivos generados y next steps.
    """
    preset = get_preset(preset_name)
    slug = to_slug(project_name)

    if repos is None:
        repos = preset["default_repos"]
    else:
        # Normalizar: lista de strings → dicts con type desconocido
        repos = [{"name": r, "type": "component", "language": "unknown", "iac": "unknown"}
                 if isinstance(r, str) else r for r in repos]

    if target_path is None:
        target_path = str(Path.cwd() / slug / "docs")

    vault = Path(target_path)
    scripts_dir = vault / "scripts"

    # 1. Crear estructura de directorios
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for d in EMPTY_DIRS:
        (vault / d).mkdir(parents=True, exist_ok=True)
        gitkeep = vault / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    # 2. Copiar scripts static
    for fname in STATIC_FILES:
        src = STATIC_DIR / fname
        dst = scripts_dir / fname
        if src.exists():
            shutil.copy2(src, dst)

    # 3. Renderizar protocolos
    context = build_context(project_name, description, preset, repos, cloud, ci_cd, language)
    for proto_name, rel_path in PROTOCOL_FILES.items():
        dst = vault / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(render_template(PROTOCOLS[proto_name], context))

    # 4. Renderizar archivos de estado
    for tpl_name, rel_path in TEMPLATE_FILES.items():
        dst = vault / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        template = (TEMPLATES_DIR / tpl_name).read_text()
        dst.write_text(render_template(template, context))

    # 5. Generar MOCs
    moc_template = (TEMPLATES_DIR / "moc.md").read_text()
    for fname, title, emoji, tag in MOCS:
        ctx = {
            "MOC_TITLE": title,
            "MOC_EMOJI": emoji,
            "MOC_TAG": tag,
            "MOC_LOWER": title.lower(),
            "MOC_LINKS": _make_moc_links(project_name),
            "DATE": utc_now(),
        }
        (vault / "00_Global" / fname).write_text(render_template(moc_template, ctx))

    # 6. Generar tools de dominio + MCP server skeleton
    domain_tools = generate_domain_tools(project_name, preset)
    (scripts_dir / f"{slug}_tools.py").write_text(domain_tools)
    (scripts_dir / "mcp_server.py").write_text(generate_mcp_server(project_name, preset))

    # 7. Generar instructions.md (prompt del agente) en la raíz del vault
    (vault / "instructions.md").write_text(
        render_template(INSTRUCTIONS_TEMPLATE, {"PROJECT_NAME": project_name,
                                                 "PROJECT_SLUG": slug,
                                                 "VERSION": __version__,
                                                 "DATE": utc_now()})
    )

    # 8. Inicializar boards kanban
    kanban = "\n".join([
        "---",
        "tags: [kanban, tasks, ecosystem]",
        "kanban-plugin: board",
        "purpose: Auto-generado desde AGENT_TASKS.md. NO EDITAR A MANO.",
        "---",
        "",
        "# Task Kanban",
        "",
        "> ⚠️ **Auto-generado desde [[../AGENT_TASKS.md]]**. Editar AGENT_TASKS.md y ejecutar `python scripts/sync_kanban.py`.",
        "",
        "## 📋 Backlog",
        "",
        "_Sin tareas — ver AGENT_TASKS.md_",
        "",
        "## ⏳ In Progress",
        "",
        "_Sin tareas_",
        "",
        "## ✅ Done",
        "",
        "_Sin tareas_",
        "",
    ])
    (vault / "00_Global" / "kanban" / "tasks.md").write_text(kanban)
    (vault / "00_Global" / "kanban" / "roadmap.md").write_text(
        "# Roadmap\n\n> Auto-generado desde AGENT_TASKS.md (items con `[due::]`).\n\n_Sin milestones con fecha._\n"
    )

    generated = sorted(str(p.relative_to(vault)) for p in vault.rglob("*") if p.is_file())

    # 9. Registrar en el ecosistema (agentic.toml) si aplica
    registration = None
    if register:
        try:
            from .ecosystem import project_add, find_config
            if find_config():
                registration = project_add(
                    name=project_name,
                    project_type=project_type,
                    path=str(Path(vault).parent),
                    preset=preset_name,
                    status="operational",
                    notes=f"Bootstrapped by agentic-ecos ({preset_name} preset)",
                )
        except Exception as exc:  # pragma: no cover
            registration = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "project": project_name,
        "preset": preset_name,
        "target_path": str(vault),
        "files_generated": len(generated),
        "structure": generated,
        "registered": bool(registration and registration.get("ok")),
        "registration": registration,
        "next_steps": next_steps(project_name, str(vault)),
    }


def generate_file(file_name: str, target_path: str, context: dict | None = None) -> dict:
    """Genera un archivo individual desde el template correspondiente.

    Args:
        file_name: nombre del template (ej: 'registry.md', 'home.md') o 'protocol:agent_protocol'.
        target_path: directorio destino donde escribir.
        context: placeholders a resolver (default: básicos).

    Returns:
        dict con ok, destino, y archivos generados.
    """
    context = context or {}
    ctx_defaults = {"PROJECT_NAME": context.get("PROJECT_NAME", "project"),
                    "PROJECT_SLUG": to_slug(context.get("PROJECT_NAME", "project")),
                    "DATE": utc_now(),
                    "VERSION": __version__}
    ctx_defaults.update(context)

    dst_dir = Path(target_path)
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Protocolo por nombre: protocol:<name>
    if file_name.startswith("protocol:"):
        proto_name = file_name.split(":", 1)[1]
        if proto_name not in PROTOCOLS:
            return {"ok": False, "error": f"Protocol '{proto_name}' not found. "
                                          f"Available: {', '.join(sorted(PROTOCOLS))}"}
        dst = dst_dir / f"{proto_name}.md"
        dst.write_text(render_template(PROTOCOLS[proto_name], ctx_defaults))
        return {"ok": True, "target": str(dst), "template": file_name}

    # Template por nombre de archivo
    tpl_path = TEMPLATES_DIR / file_name
    if not tpl_path.exists():
        return {"ok": False, "error": f"Template '{file_name}' not found. "
                                      f"Available: {', '.join(sorted(p.name for p in TEMPLATES_DIR.glob('*')))}"}
    dst = dst_dir / file_name
    dst.write_text(render_template(tpl_path.read_text(), ctx_defaults))
    return {"ok": True, "target": str(dst), "template": file_name}


# ─── Validación y guía ────────────────────────────────────────────────────────

REQUIRED_STRUCTURE = [
    "00_Global/AGENTS.md",
    "00_Global/AGENT_REGISTRY.md",
    "00_Global/AGENT_TASKS.md",
    "00_Global/AGENT_COMMS.md",
    "00_Global/AGENT_SESSION_LOG.md",
    "00_Global/AGENT_ONBOARDING.md",
    "00_Global/LOCK_PROTOCOL.md",
    "00_Global/ACCESS_CONTROL.md",
    "00_Global/RULES/AGENT_PROTOCOL.md",
    "00_Global/RULES/MULTI_AGENT.md",
    "00_Global/RULES/AGENT_SKILLS.md",
    "00_Global/RULES/IAC_TRAPS.md",
    "00_Global/STATE/WORKSPACE_STATE.md",
    "00_Global/Home.md",
    "scripts/lock_manager.py",
    "scripts/sync_kanban.py",
]


def validate_structure(project_path: str) -> dict:
    """Escanea un proyecto y reporta qué piezas de infraestructura agéntica existen.

    Returns:
        dict con checklist de gaps, present_missing y score de cobertura.
    """
    root = Path(project_path)
    missing = []
    present = []
    for rel in REQUIRED_STRUCTURE:
        if (root / rel).exists():
            present.append(rel)
        else:
            missing.append(rel)

    coverage = round(100 * len(present) / len(REQUIRED_STRUCTURE), 1)
    return {
        "ok": len(missing) == 0,
        "coverage_pct": coverage,
        "present": present,
        "missing": missing,
        "total_required": len(REQUIRED_STRUCTURE),
    }


def next_steps(project_name: str, target_path: str) -> list[str]:
    """Sugiere próximos pasos tras el bootstrap o para un proyecto existente."""
    slug = to_slug(project_name)
    return [
        f"1. Editar {target_path}/00_Global/AGENTS.md → completar mapa de componentes y reglas de protección",
        f"2. Editar {target_path}/scripts/{slug}_tools.py → implementar las tools de dominio",
        f"3. Editar {target_path}/00_Global/RULES/IAC_TRAPS.md → documentar traps específicos",
        f"4. Agregar el backlog inicial en {target_path}/00_Global/AGENT_TASKS.md",
        f"5. Conectar el MCP: agregar el server a tu opencode.jsonc apuntando a {target_path}/scripts/mcp_server.py",
        f"6. Registrar tu primer agente en {target_path}/00_Global/AGENT_REGISTRY.md",
    ]


def suggest_next_steps(project_path: str) -> list[str]:
    """Analiza el estado actual de un proyecto y sugiere próximos pasos priorizados."""
    v = validate_structure(project_path)
    steps = []
    if v["missing"]:
        steps.append(f"Faltan {len(v['missing'])} piezas de infraestructura agéntica:")
        steps.extend(f"  - Crear {m}" for m in v["missing"][:8])
        steps.append("  → Ejecuta init_project() con este target_path para regenerar todo el esqueleto.")
    else:
        steps.append("Estructura agéntica completa. Siguientes pasos:")
        steps.extend(next_steps(Path(project_path).parent.name, project_path))
    return steps


# ─── Instructions.md (prompt del agente) ──────────────────────────────────────

INSTRUCTIONS_TEMPLATE = """# {{PROJECT_NAME}} — Agent Instructions

You are operating in **{{PROJECT_NAME}}**, a project with multi-agent
coordination infrastructure. This document tells you how to operate.

## Before acting (session start)

1. Register in `00_Global/AGENT_REGISTRY.md` (agent_register tool)
2. Read `00_Global/AGENT_PROTOCOL.md` §1 (deliberation framework, risk tiers)
3. Check `00_Global/AGENT_COMMS.md` for messages directed at you
4. Check `00_Global/STATE/WORKSPACE_STATE.md` for current state
5. If writing: acquire a lock (LOCK_PROTOCOL.md) on the resource

## Coordination rules

- Claim tasks from `00_Global/AGENT_TASKS.md` (canonical queue).
- Never edit `kanban/` boards directly — edit AGENT_TASKS.md and run `python scripts/sync_kanban.py`.
- Every action must reference a T-ID (task ID).
- Log actions to `00_Global/AGENT_SESSION_LOG.md`.
- Use `agent_close_session` when finished (releases your locks).

## Access control

Roles: explorer (read-only) · worker (write under lock) · supervisor (assign) · admin (full).
See `00_Global/ACCESS_CONTROL.md` for the permission matrix.

## Customizing

Files marked `CUSTOMIZE:` are project-specific. Fill them with your domain:
- `00_Global/AGENTS.md` — repo map, protection rules
- `scripts/{{PROJECT_SLUG}}_tools.py` — domain MCP tools
- `00_Global/RULES/IAC_TRAPS.md` — tribal knowledge

## Language

This infrastructure supports English and Spanish. Generated files include
bilingual comments where relevant. Respond in the user's language.

---
_Generated by agentic-ecos v{{VERSION}} on {{DATE}}_
"""


def main():
    """CLI básica para uso sin agente (agentic-ecos init ...)."""
    import argparse

    parser = argparse.ArgumentParser(prog="agentic-ecos",
                                     description="Porta infraestructura agéntica a un proyecto.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Genera el esqueleto agéntico en un proyecto.")
    p_init.add_argument("project_name")
    p_init.add_argument("--preset", default="monorepo", choices=["monorepo", "single_service", "data_pipeline"])
    p_init.add_argument("--target", default=None, help="Ruta destino (default: ./<slug>/docs)")
    p_init.add_argument("--repos", default=None, help="Lista de componentes separados por coma")
    p_init.add_argument("--cloud", default="none")
    p_init.add_argument("--ci-cd", default="github-actions")
    p_init.add_argument("--description", default="")

    p_validate = sub.add_parser("validate", help="Valida la estructura agéntica de un proyecto.")
    p_validate.add_argument("path")
    p_validate.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_patterns = sub.add_parser("patterns", help="Lista los patrones agénticos disponibles.")
    p_patterns.add_argument("--domain", default=None)
    p_patterns.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_protocols = sub.add_parser("protocols", help="Lista los protocolos disponibles.")
    p_protocols.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_knowledge = sub.add_parser("knowledge", help="Estado del conocimiento por tier.")
    p_knowledge_sub = p_knowledge.add_subparsers(dest="knowledge_command", required=True)
    p_knowledge_status = p_knowledge_sub.add_parser("status", help="Estado por tier.")
    p_knowledge_status.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_llm = sub.add_parser("llm-test", help="Verifica la conexión con el LLM configurado.")
    p_llm.add_argument("--prompt", default="Responde con OK si me lees.",
                       help="Prompt de prueba")
    p_llm.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_loop = sub.add_parser("task-loop", help="Ejecuta el desarrollo continuo de tareas (Task Loop).")
    p_loop.add_argument("--task-id", default=None, help="T-ID específica (E1, T5) o vacío para la primera disponible")
    p_loop.add_argument("--type-filter", default="docs,ops",
                        help="Tipos permitidos cuando no se da task-id (ej: docs,ops)")
    p_loop.add_argument("--max-iterations", type=int, default=3, help="Máx iteraciones por tarea")
    p_loop.add_argument("--confirm", action="store_true",
                        help="Permite tipos riesgosos (feature/bug/iac)")
    p_loop.add_argument("--execute", action="store_true",
                        help="Ejecuta cambios reales (sin este flag, solo dry-run)")
    p_loop.add_argument("--tasks-file", default=None, help="Archivo de tareas (default: workspace/tasks.md)")
    p_loop.add_argument("--json", action="store_true", help="Salida JSON para scripts")

    p_eco = sub.add_parser("ecosystem", help="Gestiona el plano de control (agentic.toml).")
    p_eco_sub = p_eco.add_subparsers(dest="eco_command", required=True)
    p_eco_init = p_eco_sub.add_parser("init", help="Inicializa agentic.toml.")
    p_eco_init.add_argument("--name", default="mi-ecosistema")
    p_eco_init.add_argument("--workspace", required=True, help="Raíz del workspace")
    p_eco_init.add_argument("--cloud", default="aws")
    p_eco_init.add_argument("--ci-cd", default="github-actions")
    p_eco_init.add_argument("--language", default="es")
    p_eco_init.add_argument("--config", default=None, help="Ruta del agentic.toml")
    p_eco_status = p_eco_sub.add_parser("status", help="Reporte de salud del ecosistema.")
    p_eco_status.add_argument("--config", default=None)
    p_eco_status.add_argument("--json", action="store_true", help="Salida JSON para scripts")
    p_eco_add = p_eco_sub.add_parser("add", help="Registra un proyecto.")
    p_eco_add.add_argument("name")
    p_eco_add.add_argument("--type", default="backend")
    p_eco_add.add_argument("--path", default=None)
    p_eco_add.add_argument("--preset", default="monorepo")
    p_eco_add.add_argument("--config", default=None)
    p_eco_tasks = p_eco_sub.add_parser("tasks", help="Muestra las tareas del ecosistema.")
    p_eco_tasks.add_argument("--config", default=None)
    p_eco_tasks.add_argument("--json", action="store_true", help="Salida JSON para scripts")
    p_eco_addtask = p_eco_sub.add_parser("add-task", help="Agrega una tarea cross-cutting.")
    p_eco_addtask.add_argument("description")
    p_eco_addtask.add_argument("--priority", default="medium")
    p_eco_addtask.add_argument("--type", default="ops")
    p_eco_addtask.add_argument("--scope", default="ecosystem")
    p_eco_addtask.add_argument("--config", default=None)
    p_eco_branch = p_eco_sub.add_parser("branch-create", help="Crea tu branch de ecosistema.")
    p_eco_branch.add_argument("name")
    p_eco_branch.add_argument("--base", default="main",
                              help="main (estable) | dev (bleeding edge)")
    p_eco_sync = p_eco_sub.add_parser("sync", help="Sincroniza una branch con upstream.")
    p_eco_sync.add_argument("--branch", default="main", help="main | dev")
    p_eco_merge = p_eco_sub.add_parser("merge-main",
                                       help="Mergea main a la branch de ecosistema.")
    p_eco_merge.add_argument("--target", default=None)

    p_connect = sub.add_parser("connect", help="Conecta agentic-ecos a uno o más agentes.")
    p_connect.add_argument("--target", default=None)
    p_connect.add_argument("--agent", default="auto",
                           help="opencode | claude | cursor | auto | snippet")
    p_connect.add_argument("--config", default=None)

    p_promote = sub.add_parser("promote", help="Promueve conocimiento entre tiers.")
    p_promote.add_argument("name")
    p_promote.add_argument("--to", default="knowledge", choices=["workspace", "knowledge"])
    p_promote.add_argument("--source", default="workspace", help="workspace | data")
    p_promote.add_argument("--kind", default="pattern", help="pattern | preset | trap")

    args = parser.parse_args()

    def _out(data, json_flag=False):
        """Imprime output humano o JSON según el flag --json."""
        if json_flag:
            import json as _json
            print(_json.dumps(data, indent=2, ensure_ascii=False, default=str))
            return True
        return False

    if args.command == "ecosystem":
        from .ecosystem import ecosystem_init, ecosystem_status, project_add
        if args.eco_command == "init":
            r = ecosystem_init(args.name, args.workspace, cloud=args.cloud, ci_cd=args.ci_cd,
                               language=args.language, config_path=args.config)
            print(f"✅ Ecosistema '{r['ecosystem']['name']}' inicializado")
            print(f"   config: {r['config_path']}")
            print(f"   proyectos detectados: {r['projects_count']} "
                  f"({r['detected_with_infra']} con infra agéntica)")
            return 0
        if args.eco_command == "status":
            s = ecosystem_status(args.config)
            if _out(s, args.json):
                return 0
            print(f"Ecosistema: {s['ecosystem'].get('name', '—')}")
            print(f"  proyectos: {s['projects_count']} "
                  f"({s['with_agentic_infra']} con infra, {s['without_agentic_infra']} sin)")
            for p in s["projects"]:
                cov = p.get("coverage_pct", "?")
                mark = "✅" if p.get("agentic_infra") else "❌"
                print(f"  {mark} {p['name']:<20} cov={cov}% status={p.get('status','')}")
            return 0
        if args.eco_command == "add":
            r = project_add(args.name, project_type=args.type, path=args.path,
                            preset=args.preset, config_path=args.config)
            print(f"{'✅' if r['ok'] else '❌'} project {r.get('action', 'error')}: "
                  f"{args.name} (infra={r.get('project', {}).get('agentic_infra')})")
            return 0 if r["ok"] else 1
        if args.eco_command == "tasks":
            from .ecosystem import ecosystem_tasks
            t = ecosystem_tasks(args.config)
            if _out(t, args.json):
                return 0
            print(f"Cross-cutting: {t['cross_cutting_count']} "
                  f"(backlog {t['cross_cutting_backlog']}) · backlog total ecosistema: {t['ecosystem_backlog']}")
            for task in t["cross_cutting"]:
                mark = "✅" if task["checked"] else "⬜"
                print(f"  {mark} {task['id']}: {task['label']}")
            for name, counts in t["per_project"].items():
                print(f"  {name:<20} total={counts['total']} "
                      f"backlog={counts['backlog']} doing={counts['doing']} done={counts['done']}")
            return 0
        if args.eco_command == "add-task":
            from .ecosystem import ecosystem_task_add
            r = ecosystem_task_add(args.description, priority=args.priority,
                                   type=args.type, scope=args.scope, config_path=args.config)
            print(f"✅ {r.get('task_id', '?')} agregada en {r.get('path', '?')}")
            return 0
        if args.eco_command == "branch-create":
            from .ecosystem import ecosystem_branch_create
            r = ecosystem_branch_create(args.name, base=args.base)
            if not r["ok"]:
                print(f"❌ {r['error']}")
                return 1
            print(f"✅ Branch {r['branch']} creada (base={r['base']})")
            print(f"   workspace: {r['workspace']}")
            return 0
        if args.eco_command == "sync":
            from .ecosystem import ecosystem_sync_upstream
            r = ecosystem_sync_upstream(branch=args.branch)
            if not r["ok"]:
                print(f"❌ {r['error']}")
                return 1
            print(f"✅ {r['branch']} → {r['status']} ({r['detail']})")
            return 0
        if args.eco_command == "merge-main":
            from .ecosystem import ecosystem_merge_main
            r = ecosystem_merge_main(args.target)
            if not r["ok"]:
                print(f"❌ Conflicto en {r.get('conflicted_files', [])}")
                return 1
            print(f"✅ main mergeado a {r['target_branch']}")
            return 0

    if args.command == "connect":
        from .ecosystem import connect
        r = connect(target=args.target, agent=args.agent, config_path=args.config)
        if not r["ok"]:
            print(f"❌ {r.get('error', 'error')}")
            return 1
        if r.get("mode") == "snippet":
            import json as _json
            for name, snippet in r["snippets"].items():
                print(f"--- {name} ---")
                print(_json.dumps(snippet, indent=2, ensure_ascii=False))
            return 0
        for name, res in r.get("results", {}).items():
            print(f"✅ {name}: {res['status']} → {res['path']}")
        return 0

    if args.command == "promote":
        from . import knowledge
        if args.to == "workspace":
            r = knowledge.promote_to_workspace(args.name)
        else:
            r = knowledge.promote_to_knowledge(args.name, source=args.source, kind=args.kind)
        if not r["ok"]:
            print(f"❌ {r['error']}")
            return 1
        print(f"✅ {r['action']}: {args.name}")
        print(f"   → {r['path']}")
        print(f"   {r.get('note', '')}")
        return 0

    if args.command == "init":
        repos = args.repos.split(",") if args.repos else None
        result = init_project(
            args.project_name, preset_name=args.preset, target_path=args.target,
            repos=repos, cloud=args.cloud, ci_cd=args.ci_cd, description=args.description,
        )
        print(f"✅ {result['project']} — {result['files_generated']} archivos generados en {result['target_path']}")
        print("\n📁 Estructura:")
        for f in result["structure"]:
            print(f"  {f}")
        print("\n🔧 Next steps:")
        for s in result["next_steps"]:
            print(f"  {s}")
        return 0

    if args.command == "validate":
        v = validate_structure(args.path)
        if _out(v, args.json):
            return 0
        print(f"Cobertura: {v['coverage_pct']}% ({len(v['present'])}/{v['total_required']})")
        if v["missing"]:
            print("❌ Faltan:")
            for m in v["missing"]:
                print(f"  - {m}")
        else:
            print("✅ Estructura agéntica completa.")
        return 0 if v["ok"] else 1

    if args.command == "patterns":
        from .patterns import list_patterns
        patterns = list_patterns(args.domain)
        if _out(patterns, args.json):
            return 0
        for p in patterns:
            print(f"- {p['name']} [{p['domain']}] — {p['description']}")
        return 0

    if args.command == "protocols":
        if _out(sorted(PROTOCOLS), args.json):
            return 0
        for name in sorted(PROTOCOLS):
            print(f"- {name}")
        return 0

    if args.command == "knowledge":
        from .knowledge import knowledge_status
        k = knowledge_status()
        if _out(k, args.json):
            return 0
        for key, val in k.items():
            print(f"  {key}: {val}")
        return 0

    if args.command == "llm-test":
        from .llm import synthesize, DEFAULT_PROMPTS
        import os
        r = synthesize({"test": True}, role="echo",
                       prompt=args.prompt, model=os.environ.get("LLM_MODEL"),
                       api_key=os.environ.get("LLM_API_KEY"),
                       base_url=os.environ.get("LLM_BASE_URL"))
        if _out(r, args.json):
            return 0 if r.get("ok") else 1
        if not r.get("ok"):
            print(f"❌ {r.get('error', 'error')}")
            return 1
        print(f"✅ LLM OK ({r.get('model', '?')}):")
        print(r.get("text", ""))
        return 0

    if args.command == "task-loop":
        from .task_loop import run_loop
        from pathlib import Path
        tasks_file = Path(args.tasks_file) if args.tasks_file else None
        r = run_loop(task_id=args.task_id,
                     type_filter=args.type_filter,
                     max_iterations=args.max_iterations,
                     confirm=args.confirm,
                     dry_run=not args.execute,
                     tasks_file=tasks_file)
        if _out(r, args.json):
            return 0 if r.get("ok") else 1
        if not r.get("ok"):
            print(f"❌ {r.get('error', 'error')}")
            return 1
        mode = "DRY-RUN" if r.get("dry_run") else "EXECUTE"
        print(f"🔁 Task Loop [{mode}] — agente: {r.get('agent_id')}")
        print(f"   archivo: {r.get('tasks_file')}")
        for res in r.get("results", []):
            mark = "✅" if res.get("status") == "done" else "⛔"
            print(f"  {mark} {res['task_id']}: {res.get('label', '')} → {res.get('status')}")
            if res.get("risk"):
                print(f"     riesgo: {res['risk']} | plan: {res.get('plan_source', '?')}")
            if res.get("error"):
                print(f"     error: {res['error']}")
        if not r.get("results") and r.get("note"):
            print(f"   {r['note']}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
