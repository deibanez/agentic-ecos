#!/usr/bin/env python3
"""Agent Orchestrator — Supervisor automático multi-agente.

Monitorea el estado de todos los agentes, detecta bloqueos, asigna tareas
de la cola a agentes disponibles, y escala a humano cuando es necesario.

Uso:
    python scripts/orchestrator.py status          # Estado actual del sistema
    python scripts/orchestrator.py assign          # Asignar tareas pendientes
    python scripts/orchestrator.py monitor         # Loop de monitoreo continuo
    python scripts/orchestrator.py report          # Generar reporte de健康
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

REGISTRY = BASE_DIR / "00_Global" / "AGENT_REGISTRY.md"
TASKS = BASE_DIR / "00_Global" / "AGENT_TASKS.md"
COMMS = BASE_DIR / "00_Global" / "AGENT_COMMS.md"
SESSION_LOG = BASE_DIR / "00_Global" / "AGENT_SESSION_LOG.md"
TASKS_MARKER = "<!-- TASKS_START -->"


def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def log(agent_id: str, action: str, resource: str, details: str = ""):
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent_id": agent_id,
        "role": "orchestrator",
        "action": action,
        "resource": resource,
        "status": "success",
        "details": details,
    }
    with open(SESSION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_active_agents() -> list[dict]:
    """Get list of active agents from registry."""
    if not REGISTRY.exists():
        return []
    agents = []
    for line in REGISTRY.read_text().split("\n"):
        line = line.strip()
        if not line.startswith("|") or "Agent ID" in line or "---" in line or line.startswith("| — |"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 8:
            continue
        agents.append({
            "id": parts[1],
            "role": parts[2],
            "heartbeat": parts[5],
            "status": parts[6],
            "task": parts[7],
        })
    return agents


def get_stale_agents(agents: list[dict], max_age_min: int = 30) -> list[dict]:
    """Find agents with heartbeat older than max_age_min."""
    stale = []
    for a in agents:
        if a["status"] != "active":
            continue
        try:
            hb = datetime.fromisoformat(a["heartbeat"])
            age_min = (now_ts() - int(hb.timestamp())) // 60
        except (ValueError, TypeError):
            continue
        if age_min > max_age_min:
            stale.append({**a, "age_min": age_min})
    return stale


def sync_kanban() -> dict:
    """Regenerate kanban boards from AGENT_TASKS.md (same as scripts/sync-kanban.py)."""
    import importlib.util
    script_path = BASE_DIR / "scripts" / "sync-kanban.py"
    if not script_path.exists():
        log("orchestrator", "sync_kanban", "AGENT_TASKS.md", "sync-kanban.py not found")
        return {"ok": False, "error": "sync-kanban.py not found"}
    try:
        spec = importlib.util.spec_from_file_location("sync_kanban", str(script_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rc = mod.main()
        return {"ok": rc == 0, "exit_code": rc}
    except Exception as e:
        log("orchestrator", "sync_kanban", "AGENT_TASKS.md", f"failed: {e}")
        return {"ok": False, "error": str(e)}


def parse_tasks() -> list[dict]:
    """Parse AGENT_TASKS.md checkbox tasks (canonical format) into structured list."""
    if not TASKS.exists():
        return []
    tasks = []
    in_tasks = False
    for line in TASKS.read_text().split("\n"):
        line = line.strip()
        if TASKS_MARKER in line:
            in_tasks = True
            continue
        if not in_tasks:
            continue
        m = re.match(r"^\s*(- \[([ xX])\]) (.+)$", line)
        if not m:
            continue
        text = m.group(3)
        checked = m.group(2).strip().lower() == "x"
        fields = dict(re.findall(r"\[(\w+)::\s*(.+?)\s*\]", text))
        label = re.sub(r"\s*\[.*?\]", "", text).strip()
        if not label:
            continue
        mid = re.match(r"\s*(T\d+)\b", label)
        tasks.append({
            "id": mid.group(1) if mid else "",
            "task": label,
            "repo": fields.get("repo", ""),
            "priority": fields.get("priority", "low"),
            "status": fields.get("status", "backlog"),
            "assigned": fields.get("agent", ""),
            "depends": fields.get("depends", ""),
            "fields": fields,
            "checked": checked,
            "raw": line,
        })
    return tasks


def get_pending_tasks(tasks: list[dict]) -> list[dict]:
    """Get tasks ready for assignment (backlog + dependencies met)."""
    pending = []
    for t in tasks:
        if t["checked"] or t["status"] not in ("backlog", "pending"):
            continue
        # Check dependencies
        deps_met = True
        if t["depends"]:
            for dep_id in t["depends"].split(","):
                dep_id = dep_id.strip()
                dep_task = next((x for x in tasks if x["id"] == dep_id), None)
                if dep_task and not dep_task["checked"] and dep_task["status"] != "done":
                    deps_met = False
                    break
        if deps_met:
            pending.append(t)
    return pending


def available_workers(agents: list[dict]) -> list[dict]:
    """Find agents that can take new tasks (active, not currently assigned)."""
    return [a for a in agents if a["status"] == "active" and a["role"] in ("worker", "supervisor", "admin")]


def assign_tasks(dry_run: bool = False) -> list[dict]:
    """Assign pending tasks to available workers. Writes in checkbox format,
    acquires lock on AGENT_TASKS.md, and regenerates kanban boards after."""
    agents = get_active_agents()
    tasks = parse_tasks()
    pending = get_pending_tasks(tasks)
    workers = available_workers(agents)
    assignments = []

    if not pending:
        log("orchestrator", "assign_check", "AGENT_TASKS.md", "No pending tasks to assign")
        return []

    if not workers:
        log("orchestrator", "assign_check", "AGENT_TASKS.md", "No available workers")
        return []

    for i, task in enumerate(pending):
        if i >= len(workers):
            break
        worker = workers[i]
        if dry_run:
            print(f"  Would assign {task['id']} ({task['task']}) → {worker['id']}")
            continue

        lock_res = _acquire_task_lock()
        if lock_res != "OK":
            log("orchestrator", "assign_task", "AGENT_TASKS.md", f"Cannot acquire lock: {lock_res}")
            print(f"  ⚠️ Cannot acquire lock on AGENT_TASKS.md: {lock_res}")
            return assignments
        try:
            text = TASKS.read_text()
            old_raw = task["raw"].rstrip()
            new_raw = old_raw.replace("[status:: backlog]", "[status:: doing]")
            if f"[agent:: {worker['id']}]" not in new_raw:
                new_raw += f" [agent:: {worker['id']}]"
            if old_raw in text:
                text = text.replace(old_raw, new_raw, 1)
                TASKS.write_text(text)
                assignments.append({"task_id": task["id"], "worker": worker["id"]})
                log("orchestrator", "assign_task", f"AGENT_TASKS.md#{task['id']}", f"Assigned to {worker['id']}")
            else:
                log("orchestrator", "assign_task", f"AGENT_TASKS.md#{task['id']}", "Task line changed since parse, skipped")
        finally:
            _release_task_lock()

    if assignments:
        sync_kanban()

    return assignments


def _acquire_task_lock() -> str:
    """Acquire lock on AGENT_TASKS.md. Returns 'OK' or the lock result."""
    from lock_manager import LockManager
    lm = LockManager()
    res = lm.acquire("00_Global/AGENT_TASKS.md", "orchestrator", "supervisor", 30)
    return "OK" if not res.startswith("HELD_BY=") else res


def _release_task_lock():
    from lock_manager import LockManager
    lm = LockManager()
    lm.release("00_Global/AGENT_TASKS.md", "orchestrator")


def check_agent_health() -> list[dict]:
    """Check all agents and return health issues."""
    agents = get_active_agents()
    issues = []

    # Check for stale agents
    stale = get_stale_agents(agents)
    for s in stale:
        issues.append({
            "severity": "high",
            "agent_id": s["id"],
            "issue": f"No heartbeat for {s['age_min']}min (max 30)",
            "action": "Mark as zombie, release locks, reassign tasks",
        })
        log("orchestrator", "stale_agent", f"agent:{s['id']}", f"No heartbeat for {s['age_min']}min")

    # Check for zombie agents
    zombies = [a for a in agents if a["status"] == "zombie"]
    for z in zombies:
        issues.append({
            "severity": "medium",
            "agent_id": z["id"],
            "issue": "Agent is zombie",
            "action": "Clean up locks, remove from registry after 24h",
        })

    # Check for blocked tasks
    tasks = parse_tasks()
    blocked = [t for t in tasks if t["status"] == "blocked"]
    for b in blocked:
        issues.append({
            "severity": "medium",
            "task_id": b["id"],
            "issue": f"Task blocked: {b['task']}",
            "action": "Check dependencies or escalate",
        })

    return issues


def escalate(issues: list[dict]):
    """Escalate unresolved issues to admin via AGENT_COMMS.md."""
    high_issues = [i for i in issues if i["severity"] == "high"]
    if not high_issues:
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    msg_lines = "\n".join(f"  - @{i['agent_id']}: {i['issue']} → {i['action']}" for i in high_issues)

    comms_entry = f"\n| {now} | orchestrator | admin | escalation | ⚠️ Issues requiring attention:\n{msg_lines} |"

    if COMMS.exists():
        with open(COMMS, "a") as f:
            f.write(comms_entry)


def show_status():
    """Display current orchestrator state."""
    agents = get_active_agents()
    tasks = parse_tasks()
    issues = check_agent_health()
    pending = get_pending_tasks(tasks)

    print(f"\n{'='*60}")
    print(f"  ORCHESTRATOR STATUS — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    # Agents
    active_count = sum(1 for a in agents if a["status"] == "active")
    zombie_count = sum(1 for a in agents if a["status"] == "zombie")
    print(f"\n  👤 Agents: {active_count} active, {zombie_count} zombie, {len(agents)} total")
    for a in agents:
        status_icon = "🟢" if a["status"] == "active" else "🧟" if a["status"] == "zombie" else "⚪"
        print(f"    {status_icon} {a['id']:<20} {a['role']:<12} {a['status']:<10} {a['task'][:30]}")

    # Tasks
    done = sum(1 for t in tasks if t["checked"] or t["status"] == "done")
    in_prog = sum(1 for t in tasks if t["status"] == "doing")
    backlog = sum(1 for t in tasks if t["status"] in ("backlog", "pending"))
    blocked = sum(1 for t in tasks if t["status"] == "blocked")
    print(f"\n  📋 Tasks: {done} done, {in_prog} in progress, {blocked} blocked, {backlog} backlog, {len(tasks)} total")
    for t in tasks:
        if not (t["checked"] or t["status"] == "done"):
            print(f"    [{t['status']}] {t['id']:<5} {t['task'][:40]:<42} → {t['assigned'] or 'unassigned'}")

    # Pending assignments
    if pending:
        print(f"\n  🔄 Ready to assign: {len(pending)} task(s)")
        for t in pending:
            print(f"    {t['id']:<5} {t['task'][:40]:<42} deps: {t['depends'] or '—'}")

    # Issues
    if issues:
        print(f"\n  ⚠️  Health issues: {len(issues)}")
        for i in issues:
            severity_icon = "🔴" if i["severity"] == "high" else "🟡"
            print(f"    {severity_icon} {i.get('agent_id', i.get('task_id',''))}: {i['issue']}")
            print(f"       → {i['action']}")
    else:
        print(f"\n  ✅ System healthy — no issues detected")

    print()


def monitor_loop(interval_sec: int = 60):
    """Continuous monitoring loop."""
    print(f"🤖 Orchestrator monitoring started (interval: {interval_sec}s)")
    print("  Press Ctrl+C to stop\n")
    try:
        while True:
            issues = check_agent_health()
            if issues:
                high = [i for i in issues if i["severity"] == "high"]
                if high:
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] ⚠️ {len(high)} high-severity issue(s)")
                    escalate(high)
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\nOrchestrator stopped.")


def generate_report() -> str:
    """Generate a health report as markdown."""
    agents = get_active_agents()
    tasks = parse_tasks()
    issues = check_agent_health()

    lines = [
        f"# Agent Orchestrator Report — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Agents",
        f"- Active: {sum(1 for a in agents if a['status'] == 'active')}",
        f"- Zombie: {sum(1 for a in agents if a['status'] == 'zombie')}",
        f"- Total: {len(agents)}",
        "",
        "## Tasks",
        f"- Done: {sum(1 for t in tasks if t['checked'] or t['status'] == 'done')}",
        f"- In progress: {sum(1 for t in tasks if t['status'] == 'doing')}",
        f"- Blocked: {sum(1 for t in tasks if t['status'] == 'blocked')}",
        f"- Backlog: {sum(1 for t in tasks if t['status'] in ('backlog', 'pending'))}",
        f"- Total: {len(tasks)}",
        "",
    ]
    if issues:
        lines.append("## Issues")
        for i in issues:
            lines.append(f"- [{i['severity']}] {i.get('agent_id', i.get('task_id',''))}: {i['issue']}")
            lines.append(f"  - Action: {i['action']}")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrator.py {status | assign | monitor | report}")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        show_status()
    elif cmd == "assign":
        assignments = assign_tasks(dry_run="--dry-run" in sys.argv)
        if assignments:
            print(f"✅ Assigned {len(assignments)} task(s)")
            for a in assignments:
                print(f"  {a['task_id']} → {a['worker']}")
        else:
            print("No tasks to assign")
    elif cmd == "monitor":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor_loop(interval)
    elif cmd == "report":
        print(generate_report())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
