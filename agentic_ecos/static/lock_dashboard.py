#!/usr/bin/env python3
"""Dashboard de locks activos y estado de agentes.

Uso:
    python scripts/lock_dashboard.py          # Todos los locks activos
    python scripts/lock_dashboard.py --agents # Solo agentes registrados
    python scripts/lock_dashboard.py --watch  # Watch mode (actualiza cada 10s)
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from lock_manager import LockManager

REGISTRY = BASE_DIR / "00_Global" / "AGENT_REGISTRY.md"


def fmt_time(iso_str: str) -> str:
    """Format ISO timestamp to relative time."""
    if not iso_str or iso_str == "—":
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        delta = now - dt
        mins = int(delta.total_seconds() // 60)
        if mins < 1:
            return "just now"
        if mins < 60:
            return f"{mins}min ago"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h {mins % 60}min ago"
        return f"{hours // 24}d ago"
    except (ValueError, TypeError):
        return iso_str[:19]


def colorize(text: str, status: str) -> str:
    """Simple ANSI coloring."""
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    if not sys.stdout.isatty():
        return text
    c = colors.get(status, colors["reset"])
    return f"{c}{text}{colors['reset']}"


def show_locks():
    lm = LockManager()
    locks = lm.list_active()

    print("\n=== 🔒 Active Locks ===\n")
    if not locks:
        print("  No active locks.")
        return

    # Header
    print(f"  {'Resource':<30} {'Agent':<20} {'Role':<12} {'Elapsed':<10} {'Status':<10}")
    print(f"  {'-'*30} {'-'*20} {'-'*12} {'-'*10} {'-'*10}")

    for lk in locks:
        expired = lk["expired"]
        status_str = colorize("⚠️ EXPIRED", "red") if expired else colorize("✅ OK", "green")
        elapsed = f"{lk['elapsed_min']}min"
        resource_short = lk["resource_hash"][:16]
        agent_colored = colorize(lk["agent_id"], "yellow") if expired else lk["agent_id"]
        elapsed_colored = colorize(elapsed, "red") if expired else elapsed
        print(f"  {resource_short:<30} {agent_colored:<20} {lk['role']:<12} {elapsed_colored:<10} {status_str:<10}")

    print(f"\n  Total: {len(locks)} lock(s)")


def show_agents():
    if not REGISTRY.exists():
        print("  Registry not found.")
        return

    text = REGISTRY.read_text()
    agents = []

    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "Agent ID" in line or line.startswith("|---"):
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

    print("\n=== 👤 Registered Agents ===\n")
    if not agents:
        print("  No agents registered.")
        return

    print(f"  {'Agent':<20} {'Role':<12} {'Status':<10} {'Last HB':<16} {'Task':<30}")
    print(f"  {'-'*20} {'-'*12} {'-'*10} {'-'*16} {'-'*30}")

    for a in agents:
        if a["id"] in ("—", ""):
            continue
        status_colored = {
            "active": colorize("🟢 active", "green"),
            "inactive": colorize("⚪ inactive", "cyan"),
            "zombie": colorize("🧟 zombie", "red"),
        }.get(a["status"], a["status"])
        hb = fmt_time(a["heartbeat"])
        task_short = a["task"][:28] if len(a["task"]) > 28 else a["task"]
        print(f"  {a['id']:<20} {a['role']:<12} {status_colored:<10} {hb:<16} {task_short:<30}")

    active = sum(1 for a in agents if a["status"] == "active")
    zombie = sum(1 for a in agents if a["status"] == "zombie")
    print(f"\n  Active: {active} | Zombie: {zombie} | Total: {len(agents)}")


def show_all():
    show_locks()
    show_agents()


def watch_mode(interval: int = 10):
    """Refresh dashboard every N seconds."""
    try:
        while True:
            os.system("clear" if sys.platform != "win32" else "cls")
            print(f"🔍 Agent Dashboard — refreshing every {interval}s (Ctrl+C to stop)")
            print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            show_all()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    import os

    if "--watch" in sys.argv:
        interval = 10
        for i, arg in enumerate(sys.argv):
            if arg == "--watch" and i + 1 < len(sys.argv):
                try:
                    interval = int(sys.argv[i + 1])
                except ValueError:
                    pass
        watch_mode(interval)
    elif "--agents" in sys.argv:
        show_agents()
    elif "--locks" in sys.argv:
        show_locks()
    else:
        show_all()
