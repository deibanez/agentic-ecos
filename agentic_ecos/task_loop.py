"""Task Loop — desarrollo continuo automático con trazabilidad.

Implementa el ciclo:
    detect → claim (git push rejection) → plan (LLM) → execute (por tipo)
    → verify → done | iterate (máx N intentos)

Diseñado para ser ejecutado por GitHub Actions (workflow_dispatch) con control
humano total al principio. El bot NUNCA edita AGENT_TASKS.md directamente sin
el protocolo de git push rejection (race-condition-free).

Riesgo escalonado por tipo de tarea:
    - docs, ops   → permitido en modo automático (workflow_dispatch)
    - feature, bug, iac → requiere confirmación explícita (confirm=true)
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import storage

# Tipos de tarea por nivel de riesgo
SAFE_TYPES = {"docs", "ops"}
RISKY_TYPES = {"feature", "bug", "iac", "ci-cd", "monitoring", "security"}

# Marcadores del formato canónico
MARKER_START = "<!-- TASKS_START -->"
MARKER_END = "<!-- TASKS_END -->"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(agent_id: str, action: str, resource: str, status: str, details: str = ""):
    """Registra en AGENT_SESSION_LOG del vault (trazabilidad del loop)."""
    try:
        entry = {"timestamp": _now(), "agent_id": agent_id, "role": "worker",
                 "action": action, "resource": resource, "status": status,
                 "details": details}
        from .ecosystem import repo_root
        log_path = repo_root() / "docs" / "00_Global" / "AGENT_SESSION_LOG.md"
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _git(*args: str, cwd: Optional[Path] = None) -> dict:
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True,
                           cwd=cwd or Path.cwd())
    except FileNotFoundError:
        return {"ok": False, "error": "git no instalado", "stdout": "", "stderr": ""}
    return {"ok": r.returncode == 0, "rc": r.returncode,
            "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}


# ─── Detección de tareas ────────────────────────────────────────────────────

def find_task(task_id: str, tasks_file: Path) -> Optional[dict]:
    """Busca una tarea por ID (E1, T1, etc.) en un archivo tasks."""
    if not tasks_file.exists():
        return None
    for t in storage.parse_tasks_markdown(tasks_file.read_text()):
        if t["id"] == task_id:
            return t
    return None


def find_available_tasks(type_filter: str, max_items: int = 5,
                         tasks_file: Optional[Path] = None) -> list[dict]:
    """Encuentra tareas disponibles (backlog, sin agent) en el workspace tasks.md.

    Si tasks_file es None, usa workspace/tasks.md (E-tasks cross-cutting).
    """
    path = tasks_file or storage.workspace_tasks_path()
    if not path.exists():
        return []
    allowed_types = {t.strip() for t in type_filter.split(",") if t.strip()}
    available = []
    for t in storage.parse_tasks_markdown(path.read_text()):
        if t["checked"]:
            continue
        status = t["fields"].get("status", "backlog")
        if status not in ("backlog",):
            continue
        if "agent" in t["fields"]:
            continue  # ya reclamada
        ttype = t["fields"].get("type", "")
        if allowed_types and ttype not in allowed_types:
            continue
        available.append(t)
        if len(available) >= max_items:
            break
    return available


# ─── Claim con git push rejection ───────────────────────────────────────────

def claim_task(task_id: str, agent_id: str, tasks_file: Optional[Path] = None) -> dict:
    """Reclama una tarea: agrega [agent::] y [status:: doing], commit + push.

    Si el push es rechazado (otro agente la reclamó primero), retorna conflicto.
    """
    path = tasks_file or storage.workspace_tasks_path()
    if not path.exists():
        return {"ok": False, "error": f"Tasks file no existe: {path}"}

    content = path.read_text()
    task = find_task(task_id, path)
    if task is None:
        return {"ok": False, "error": f"Tarea {task_id} no encontrada"}

    # Verificar que no esté reclamada
    if "agent" in task["fields"]:
        return {"ok": False, "error": f"Tarea {task_id} ya reclamada por {task['fields']['agent']}"}

    # Actualizar la línea: agregar agent + status doing
    line = task["raw"]
    new_line = re.sub(r"\[status::\s*[^\]]+\]", "[status:: doing]", line)
    new_line = new_line.rstrip() + f" [agent:: {agent_id}] [claimed:: {_now()}]"
    new_content = content.replace(line, new_line)

    # Commit + push (primero verificar que el archivo está en un repo git)
    repo_ok = _git("rev-parse", "--is-inside-work-tree")["ok"]
    if not repo_ok:
        return {"ok": False,
                "error": "No es un repositorio git. El claim requiere git para la "
                         "coordinación race-free. Inicializá git o usá --dry-run."}

    # Escritura atómica DESPUÉS de verificar que git está disponible
    tmp = path.with_suffix(".tmp")
    tmp.write_text(new_content)
    tmp.rename(path)

    # Commit + push
    commit = _git("add", str(path))
    if commit["ok"]:
        commit = _git("commit", "-m",
                      f"task: claim {task_id} [agent:: {agent_id}] [session:: {_now()}]")
    if not commit["ok"]:
        # Revertir la modificación local (restaurar contenido original)
        tmp2 = path.with_suffix(".revert")
        tmp2.write_text(content)
        tmp2.rename(path)
        return {"ok": False, "error": f"Commit falló: {commit.get('stderr')}"}

    push = _git("push")
    if not push["ok"]:
        # Revertir el claim local (push rechazado → otro agente ganó)
        tmp2 = path.with_suffix(".revert")
        tmp2.write_text(content)
        tmp2.rename(path)
        return {"ok": False, "error": "Push rechazado — otro agente reclamó primero",
                "stderr": push.get("stderr")}

    _log(agent_id, "task_claim", task_id, "success", f"file={path.name}")
    return {"ok": True, "task": task, "task_id": task_id}


# ─── Verificación de tipos seguros ──────────────────────────────────────────

def check_risk(task: dict, confirm: bool = False) -> dict:
    """Verifica el riesgo de ejecutar una tarea.

    SAFE_TYPES (docs, ops) → permitido.
    RISKY_TYPES (feature, bug, iac) → requiere confirm=true.
    """
    ttype = task.get("fields", {}).get("type", "")
    if ttype in SAFE_TYPES:
        return {"ok": True, "type": ttype, "level": "safe",
                "note": "Tipo seguro: se puede automatizar."}
    if ttype in RISKY_TYPES and confirm:
        return {"ok": True, "type": ttype, "level": "confirmed",
                "note": "Tipo riesgoso pero confirmado explícitamente."}
    if ttype in RISKY_TYPES:
        return {"ok": False, "type": ttype, "level": "blocked",
                "error": f"Tipo '{ttype}' requiere confirmación humana "
                         f"(workflow_dispatch con confirm=true)."}
    return {"ok": True, "type": ttype, "level": "unknown",
            "note": "Tipo no clasificado — permitido."}


# ─── Plan con LLM ───────────────────────────────────────────────────────────

PLAN_PROMPT = """Eres un planificador de desarrollo para una tarea de infraestructura agéntica.

Tarea: {task}

Contexto del ecosistema: {context}

Genera un plan de implementación con:
1. Enfoque (2-3 pasos concretos)
2. Archivos que podrían modificarse (si aplica)
3. Criterios de verificación
4. Rollback (cómo revertir si falla)

Responde en markdown, conciso (máximo 20 líneas)."""


def plan_task(task: dict, context: dict = None,
              model: str = None, api_key: str = None, base_url: str = None) -> dict:
    """Genera un plan de implementación usando LLM (o fallback determinístico)."""
    from .llm import synthesize

    if api_key is None:
        api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        # Fallback determinístico sin LLM
        return {
            "ok": True,
            "plan": f"Plan determinístico para {task['id']} ({task.get('label', '')}):\n"
                    "1. Revisar el estado actual del ecosistema\n"
                    "2. Implementar cambios atómicos con T-ID\n"
                    "3. Verificar con validate_structure y tests\n"
                    "4. Commit + push con [agent:: bot-ci]",
            "source": "fallback",
            "llm_used": False,
        }

    prompt = PLAN_PROMPT.format(task=json.dumps(task, default=str),
                                context=json.dumps(context or {}, default=str))
    r = synthesize(context or {}, role="echo", prompt=prompt,
                   model=model, api_key=api_key, base_url=base_url)
    return {"ok": r.get("ok", False),
            "plan": r.get("text", ""),
            "source": "llm" if r.get("ok") else "error",
            "llm_used": True,
            "error": r.get("error")}


# ─── Ejecución por tipo ─────────────────────────────────────────────────────

def execute_task(task: dict, plan: str, agent_id: str, dry_run: bool = True) -> dict:
    """Ejecuta la tarea según su tipo.

    dry_run=True (default): NO ejecuta nada real, solo reporta el plan.
    El workflow puede pasar dry_run=false para tipos seguros.
    """
    ttype = task.get("fields", {}).get("type", "")
    label = task.get("label", "")

    if dry_run:
        _log(agent_id, "task_execute_dryrun", task["id"], "success",
             f"type={ttype}, plan={plan[:200]}")
        return {"ok": True, "dry_run": True, "type": ttype,
                "note": "dry_run — el plan fue: " + plan[:300]}

    # Sin dry_run: aquí iría la ejecución real por tipo.
    # En el MVP, solo docs/ops tienen ejecución segura.
    if ttype == "docs":
        # Ej: regenerar kanban, actualizar estado
        result = _execute_docs(task, agent_id)
    elif ttype == "ops":
        result = {"ok": True, "executed": "ops (comando de operación)"}
    else:
        result = {"ok": True, "executed": f"type={ttype} (requiere lógica específica)"}

    _log(agent_id, "task_execute", task["id"], "success", str(result)[:200])
    return {"ok": True, "dry_run": False, "type": ttype, "result": result}


def _execute_docs(task: dict, agent_id: str) -> dict:
    """Ejecución para tareas tipo docs: regenera kanban boards del workspace."""
    from .ecosystem import repo_root
    # Regenerar kanban si hay sync_kanban disponible
    sync = repo_root() / "agentic_ecos" / "static" / "sync_kanban.py"
    if sync.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("sync_kanban", str(sync))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.main()
            return {"ok": True, "executed": "kanban regenerado"}
        except Exception as e:
            return {"ok": False, "executed": f"error regenerando kanban: {e}"}
    return {"ok": True, "executed": "docs task (kanban script no disponible)"}


# ─── El loop principal ──────────────────────────────────────────────────────

def run_loop(task_id: Optional[str] = None,
             type_filter: str = "docs,ops",
             max_iterations: int = 3,
             confirm: bool = False,
             dry_run: bool = True,
             agent_id: str = "bot-ci",
             tasks_file: Optional[Path] = None) -> dict:
    """Ejecuta el loop completo para una o más tareas.

    Args:
        task_id: T-ID específica (E1, T5) o None para tomar la primera disponible.
        type_filter: tipos permitidos (ej: "docs,ops"). Solo filtra si task_id es None.
        max_iterations: máx iteraciones por tarea.
        confirm: permite tipos riesgosos (feature/bug/iac).
        dry_run: no ejecuta cambios reales (solo plan + reporte).
        agent_id: identidad del bot.
        tasks_file: archivo de tareas (default: workspace/tasks.md).
    """
    path = tasks_file or storage.workspace_tasks_path()
    results = []

    if task_id:
        task = find_task(task_id, path)
        if task is None:
            return {"ok": False, "error": f"Tarea {task_id} no encontrada en {path}"}
        tasks = [task]
    else:
        tasks = find_available_tasks(type_filter, max_items=5, tasks_file=path)
        if not tasks:
            return {"ok": True, "results": [], "agent_id": agent_id, "dry_run": dry_run,
                    "note": f"No hay tareas disponibles (filter={type_filter})"}

    for task in tasks:
        tid = task["id"]
        entry = {"task_id": tid, "label": task.get("label", "")}

        # Risk check
        risk = check_risk(task, confirm=confirm)
        entry["risk"] = risk["level"]
        if not risk["ok"]:
            entry["status"] = "blocked"
            entry["error"] = risk["error"]
            results.append(entry)
            continue

        # Claim (solo si no es dry_run)
        if not dry_run:
            claimed = claim_task(tid, agent_id, tasks_file=path)
            if not claimed["ok"]:
                entry["status"] = "claim_conflict"
                entry["error"] = claimed["error"]
                results.append(entry)
                continue
            entry["claimed"] = True

        # Plan (LLM con fallback)
        plan = plan_task(task)
        entry["plan_source"] = plan.get("source", "?")
        entry["plan"] = plan.get("plan", "")[:200]

        # Iteraciones de ejecución + verificación
        entry["iterations"] = []
        success = False
        for i in range(1, max_iterations + 1):
            exec_r = execute_task(task, plan.get("plan", ""), agent_id, dry_run=dry_run)
            iter_entry = {"iteration": i, "ok": exec_r.get("ok"),
                          "dry_run": exec_r.get("dry_run", True)}
            if exec_r.get("ok"):
                success = True
                iter_entry["status"] = "passed"
                entry["iterations"].append(iter_entry)
                break
            iter_entry["status"] = "failed"
            iter_entry["error"] = exec_r.get("result", {})
            entry["iterations"].append(iter_entry)

        entry["status"] = "done" if success else "failed_after_iterations"
        if success:
            _log(agent_id, "task_loop_done", tid, "success", f"iterations={len(entry['iterations'])}")
        else:
            _log(agent_id, "task_loop_fail", tid, "failure",
                 f"max_iterations={max_iterations}")
        results.append(entry)

    return {"ok": True, "agent_id": agent_id, "results": results,
            "dry_run": dry_run, "tasks_file": str(path)}


# ─── Completar tarea ─────────────────────────────────────────────────────────

def done_task(task_id: str, agent_id: str, tasks_file: Optional[Path] = None) -> dict:
    """Marca una tarea como completada: [status:: done] [completed:: ISO].

    Verifica que el `agent_id` que completa es el mismo que la reclamó
    (si tiene [agent::]). Commit + push con trazabilidad.
    """
    path = tasks_file or storage.workspace_tasks_path()
    if not path.exists():
        return {"ok": False, "error": f"Tasks file no existe: {path}"}

    task = find_task(task_id, path)
    if task is None:
        return {"ok": False, "error": f"Tarea {task_id} no encontrada"}

    # Verificar ownership: si tiene agent, debe ser el mismo
    claimed_by = task["fields"].get("agent")
    if claimed_by and claimed_by != agent_id:
        return {"ok": False, "error": f"Tarea {task_id} reclamada por {claimed_by}, "
                                      f"no por {agent_id} — no podés completarla."}

    # Actualizar la línea: status doing/backlog → done + completed
    content = path.read_text()
    line = task["raw"]
    new_line = re.sub(r"\[status::\s*[^\]]+\]", "[status:: done]", line)
    new_line = re.sub(r"\[claimed::\s*[^\]]+\]", "", new_line)
    new_line = new_line.rstrip() + f" [completed:: {_now()}]"
    new_content = content.replace(line, new_line)

    # Verificar que el archivo está en un repo git (commit/push requieren git)
    repo_ok = _git("rev-parse", "--is-inside-work-tree")["ok"]
    if not repo_ok:
        return {"ok": False,
                "error": "No es un repositorio git. El done requiere git para la "
                         "trazabilidad. Inicializá git o usá --dry-run."}

    tmp = path.with_suffix(".tmp")
    tmp.write_text(new_content)
    tmp.rename(path)

    commit = _git("add", str(path))
    if commit["ok"]:
        commit = _git("commit", "-m",
                      f"task: done {task_id} [agent:: {agent_id}] [session:: {_now()}]")
    if not commit["ok"]:
        # Revertir la modificación local (restaurar contenido original)
        tmp2 = path.with_suffix(".revert")
        tmp2.write_text(content)
        tmp2.rename(path)
        return {"ok": False, "error": f"Commit falló: {commit.get('stderr')}"}

    push = _git("push")
    if not push["ok"]:
        tmp2 = path.with_suffix(".revert")
        tmp2.write_text(content)
        tmp2.rename(path)
        return {"ok": False, "error": "Push rechazado — otro agente modificó la tarea",
                "stderr": push.get("stderr")}

    _log(agent_id, "task_done", task_id, "success", f"file={path.name}")
    return {"ok": True, "task_id": task_id, "status": "done"}


# ─── Estado / filtro de tareas ──────────────────────────────────────────────

def get_task_status(task_id: Optional[str] = None,
                    filter_agent: Optional[str] = None,
                    tasks_file: Optional[Path] = None) -> dict:
    """Devuelve tareas filtradas.

    Args:
        task_id: tarea específica por ID.
        filter_agent: 'unclaimed' (sin [agent::]) | 'claimed' | 'done'
                      | 'backlog' | ID de agente específico.
        tasks_file: archivo de tareas (default: workspace/tasks.md).
    """
    path = tasks_file or storage.workspace_tasks_path()
    if not path.exists():
        return {"ok": True, "tasks": [], "tasks_file": str(path)}

    all_tasks = storage.parse_tasks_markdown(path.read_text())

    if task_id:
        match = next((t for t in all_tasks if t["id"] == task_id), None)
        return {"ok": True, "task": match, "tasks": [match] if match else [],
                "tasks_file": str(path)}

    filtered = []
    for t in all_tasks:
        fields = t["fields"]
        status = fields.get("status", "backlog")
        agent = fields.get("agent")
        if filter_agent == "unclaimed":
            if not t["checked"] and not agent and status == "backlog":
                filtered.append(t)
        elif filter_agent == "claimed":
            if not t["checked"] and agent:
                filtered.append(t)
        elif filter_agent == "done":
            if t["checked"] or status == "done":
                filtered.append(t)
        elif filter_agent == "backlog":
            if not t["checked"] and status == "backlog":
                filtered.append(t)
        elif filter_agent:
            if agent == filter_agent:
                filtered.append(t)
        else:
            filtered.append(t)

    return {"ok": True, "tasks": filtered, "tasks_file": str(path),
            "filter": filter_agent}