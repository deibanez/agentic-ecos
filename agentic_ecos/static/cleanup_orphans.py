#!/usr/bin/env python3
"""Cleanup de sesiones huérfanas y locks expirados.

Correr como cron cada 15 minutos:
    python scripts/cleanup_orphans.py

Escanea:
1. AGENT_REGISTRY.md → busca agents "active" sin heartbeat > 30 min → marca "zombie"
2. .locks/ → busca locks cuyo owner es zombie → force-unlock
3. AGENT_SESSION_LOG.md → registra todas las acciones
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOCK_DIR = BASE_DIR / ".locks"
REGISTRY = BASE_DIR / "00_Global" / "AGENT_REGISTRY.md"
SESSION_LOG = BASE_DIR / "00_Global" / "AGENT_SESSION_LOG.md"
LOCK_MANAGER_PATH = BASE_DIR / "scripts" / "lock_manager.py"

sys.path.insert(0, str(BASE_DIR / "scripts"))
from lock_manager import LockManager


def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def log(agent_id: str, action: str, resource: str, details: str = ""):
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent_id": agent_id,
        "role": "system",
        "action": action,
        "resource": resource,
        "status": "success",
        "details": details,
    }
    with open(SESSION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def scan_registry() -> list[dict]:
    """Scan AGENT_REGISTRY.md for active agents with stale heartbeats."""
    if not REGISTRY.exists():
        return []

    text = REGISTRY.read_text()
    zombies = []

    # Find table rows (lines with | pipes and agent IDs)
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Agent ID" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 8:
            continue

        agent_id = parts[1]
        role = parts[2]
        heartbeat_str = parts[5]
        status = parts[6]

        if status != "active":
            continue
        if not heartbeat_str or heartbeat_str == "—":
            continue

        try:
            hb_dt = datetime.fromisoformat(heartbeat_str)
            hb_ts = int(hb_dt.timestamp())
            age_min = (now_ts() - hb_ts) // 60
        except (ValueError, TypeError):
            continue

        if age_min > 30:
            zombies.append({"agent_id": agent_id, "role": role, "age_min": age_min})

    return zombies


def mark_zombie(agent_id: str, age_min: int):
    """Mark an agent as zombie in the registry."""
    if not REGISTRY.exists():
        return
    text = REGISTRY.read_text()
    # Find the line with this agent_id and replace "active" with "zombie"
    new_lines = []
    found = False
    for line in text.split("\n"):
        if f"| {agent_id} |" in line and "| active |" in line:
            line = line.replace("| active |", "| zombie |")
            found = True
        new_lines.append(line)

    if found:
        REGISTRY.write_text("\n".join(new_lines))
        log("system-cleanup", "mark_zombie", f"agent:{agent_id}", f"no heartbeat for {age_min}min")
        print(f"  🧟 Marked {agent_id} as zombie (no heartbeat for {age_min}min)")


def cleanup_locks(zombie_ids: set):
    """Force-unlock all locks held by zombie agents."""
    lm = LockManager()
    for lock_file in LOCK_DIR.glob("*.lock"):
        raw = lock_file.read_text().strip()
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 1:
            continue
        agent_id = parts[0]
        # Find resource from lock files
        resource_hash = lock_file.stem

        if agent_id in zombie_ids:
            lock_file.unlink()
            log("system-cleanup", "force_unlock", f".locks/{resource_hash}.lock", f"zombie agent {agent_id}")
            print(f"  🔓 Force-unlocked .locks/{resource_hash}.lock (owned by zombie {agent_id})")


def cleanup_expired_locks():
    """Force-unlock expired locks (heartbeat > TTL, owner not in zombie list)."""
    lm = LockManager()
    for lock_file in LOCK_DIR.glob("*.lock"):
        raw = lock_file.read_text().strip()
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 5:
            continue
        agent_id = parts[0]
        resource_hash = lock_file.stem

        try:
            hb_dt = datetime.fromisoformat(parts[4])
            hb_ts = int(hb_dt.timestamp())
            ttl = int(parts[3])
            age_min = (now_ts() - hb_ts) // 60
        except (ValueError, TypeError):
            continue

        if age_min > ttl:
            lock_file.unlink()
            log("system-cleanup", "lock_expired", f".locks/{resource_hash}.lock", f"owner {agent_id}, expired {age_min}min (ttl={ttl})")
            print(f"  ⏰ Removed expired lock .locks/{resource_hash}.lock (owner {agent_id}, {age_min}min > ttl={ttl})")


def main():
    print("=== Orphan Cleanup ===")

    # Phase 1: Find zombie agents
    print("\n🔍 Scanning registry for zombie agents...")
    zombies = scan_registry()
    zombie_ids = set()
    if not zombies:
        print("  No zombie agents found.")
    else:
        for z in zombies:
            mark_zombie(z["agent_id"], z["age_min"])
            zombie_ids.add(z["agent_id"])

    # Phase 2: Cleanup locks from zombies
    print("\n🔍 Scanning locks for zombie owners...")
    cleanup_locks(zombie_ids)

    # Phase 3: Cleanup expired locks
    print("\n🔍 Scanning for expired locks...")
    cleanup_expired_locks()

    print("\n✅ Cleanup complete.")


if __name__ == "__main__":
    main()
