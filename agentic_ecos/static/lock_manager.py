#!/usr/bin/env python3
"""Lock Manager para escritura multi-agente (Python).

Uso como API:
    from lock_manager import LockManager
    lm = LockManager()
    lm.acquire("STATE/WORKSPACE_STATE.md", "opencode-alpha", "worker")
    lm.heartbeat("STATE/WORKSPACE_STATE.md", "opencode-alpha")
    lm.release("STATE/WORKSPACE_STATE.md", "opencode-alpha")

Uso como CLI:
    python lock_manager.py acquire <resource> <agent_id> <role> [ttl]
    python lock_manager.py release <resource> <agent_id>
    python lock_manager.py heartbeat <resource> <agent_id>
    python lock_manager.py status <resource>
    python lock_manager.py list-active
    python lock_manager.py force-unlock <resource> <agent_id> <caller_role>
"""

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class LockManager:
    LOCK_DIR = Path(__file__).resolve().parent.parent / ".locks"
    SESSION_LOG = Path(__file__).resolve().parent.parent / "00_Global" / "AGENT_SESSION_LOG.md"

    def __init__(self):
        self.LOCK_DIR.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, resource: str) -> Path:
        h = hashlib.sha256(resource.encode()).hexdigest()
        return self.LOCK_DIR / f"{h}.lock"

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _now_ts(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _read_lock(self, resource: str) -> Optional[dict]:
        path = self._lock_path(resource)
        if not path.exists():
            return None
        raw = path.read_text().strip()
        parts = [p.strip() for p in raw.split("|")]
        if len(parts) < 5:
            return None
        return {
            "agent_id": parts[0],
            "role": parts[1],
            "acquired_at": parts[2],
            "ttl": int(parts[3]),
            "heartbeat_at": parts[4],
        }

    def _write_lock(self, resource: str, agent_id: str, role: str, acquired_at: str, ttl: int, heartbeat_at: str):
        """Write lock atomically using temp file + rename."""
        path = self._lock_path(resource)
        content = f"{agent_id} | {role} | {acquired_at} | {ttl} | {heartbeat_at}\n"
        fd, tmp_path = tempfile.mkstemp(dir=str(self.LOCK_DIR), prefix=".lock_tmp_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _try_acquire_atomic(self, resource: str, agent_id: str, role: str, acquired_at: str, ttl: int, heartbeat_at: str) -> bool:
        """Try to atomically create the lock file. Returns True if acquired."""
        path = self._lock_path(resource)
        content = f"{agent_id} | {role} | {acquired_at} | {ttl} | {heartbeat_at}\n"
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(fd, "w") as f:
                f.write(content)
            return True
        except FileExistsError:
            return False
        except OSError:
            return False

    def _delete_lock(self, resource: str):
        path = self._lock_path(resource)
        if path.exists():
            path.unlink()

    def _log(self, agent_id: str, role: str, action: str, resource: str, status: str, details: str = ""):
        entry = {
            "timestamp": self._now(),
            "agent_id": agent_id,
            "role": role,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details,
        }
        with open(self.SESSION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def acquire(self, resource: str, agent_id: str, role: str = "explorer", ttl: int = 30) -> str:
        now = self._now()

        result = self._try_acquire_atomic(resource, agent_id, role, now, ttl, now)
        if result:
            self._log(agent_id, role, "lock_acquire", resource, "success", "acquired")
            return "ACQUIRED"

        lock = self._read_lock(resource)
        if lock is None:
            return "ACQUIRED"

        hb_ts = int(datetime.fromisoformat(lock["heartbeat_at"]).timestamp())
        age_min = (self._now_ts() - hb_ts) // 60

        if age_min > lock["ttl"]:
            old_agent = lock["agent_id"]
            self._write_lock(resource, agent_id, role, now, ttl, now)
            self._log(agent_id, role, "lock_acquire", resource, "success", f"reclaimed from {old_agent} (expired {age_min}min)")
            return f"RECLAIMED (was held by {old_agent}, expired {age_min} min ago)"

        if lock["agent_id"] == agent_id:
            self._write_lock(resource, agent_id, lock["role"], lock["acquired_at"], lock["ttl"], now)
            self._log(agent_id, role, "lock_acquire", resource, "success", "renewed")
            return "RENEWED"

        self._log(agent_id, role, "lock_acquire", resource, "failure", f"held by {lock['agent_id']}")
        return f"HELD_BY={lock['agent_id']}"

    def release(self, resource: str, agent_id: str) -> str:
        lock = self._read_lock(resource)
        if lock is None:
            return "NOT_LOCKED"
        if lock["agent_id"] == agent_id:
            self._delete_lock(resource)
            self._log(agent_id, lock["role"], "lock_release", resource, "success")
            return "RELEASED"
        self._log(agent_id, lock["role"], "lock_release", resource, "failure", f"not owner, held by {lock['agent_id']}")
        return f"NOT_OWNER (held by {lock['agent_id']})"

    def heartbeat(self, resource: str, agent_id: str) -> str:
        lock = self._read_lock(resource)
        if lock is None:
            return "NOT_LOCKED"
        if lock["agent_id"] == agent_id:
            now = self._now()
            self._write_lock(resource, agent_id, lock["role"], lock["acquired_at"], lock["ttl"], now)
            return "HEARTBEAT_OK"
        return f"NOT_OWNER (held by {lock['agent_id']})"

    def status(self, resource: str) -> dict:
        lock = self._read_lock(resource)
        if lock is None:
            return {"status": "FREE"}
        hb_ts = int(datetime.fromisoformat(lock["heartbeat_at"]).timestamp())
        age_min = (self._now_ts() - hb_ts) // 60
        return {
            "status": "LOCKED",
            "agent_id": lock["agent_id"],
            "role": lock["role"],
            "acquired_at": lock["acquired_at"],
            "ttl": lock["ttl"],
            "heartbeat_at": lock["heartbeat_at"],
            "elapsed_min": age_min,
            "expired": age_min > lock["ttl"],
        }

    def list_active(self) -> list[dict]:
        locks = []
        for f in sorted(self.LOCK_DIR.glob("*.lock")):
            resource_hash = f.stem
            raw = f.read_text().strip()
            parts = [p.strip() for p in raw.split("|")]
            if len(parts) < 5:
                continue
            hb_ts = int(datetime.fromisoformat(parts[4]).timestamp()) if "T" in parts[4] else 0
            age_min = (self._now_ts() - hb_ts) // 60 if hb_ts else 0
            locks.append({
                "resource_hash": resource_hash,
                "agent_id": parts[0],
                "role": parts[1],
                "acquired_at": parts[2],
                "ttl": int(parts[3]),
                "heartbeat_at": parts[4],
                "elapsed_min": age_min,
                "expired": age_min > int(parts[3]),
            })
        return locks

    def release_all_by_agent(self, agent_id: str) -> list[str]:
        """Release every lock owned by the given agent.

        Returns the list of resource hashes released. Useful for session close.
        """
        released = []
        for lock in self.list_active():
            if lock["agent_id"] == agent_id:
                self._delete_lock_from_hash(lock["resource_hash"])
                self._log(agent_id, lock["role"], "lock_release", f"hash:{lock['resource_hash'][:12]}", "success", "released on session close")
                released.append(lock["resource_hash"])
        return released

    def _delete_lock_from_hash(self, resource_hash: str):
        path = self.LOCK_DIR / f"{resource_hash}.lock"
        if path.exists():
            path.unlink()

    def force_unlock(self, resource: str, agent_id: str, caller_role: str) -> str:
        if caller_role not in ("admin", "supervisor"):
            return "FORCE_UNLOCK_DENIED"
        lock = self._read_lock(resource)
        if lock is None:
            return "NOT_LOCKED"
        old_agent = lock["agent_id"]
        self._delete_lock(resource)
        self._log(agent_id, caller_role, "force_unlock", resource, "success", f"force unlocked from {old_agent}")
        return f"FORCE_UNLOCKED (was held by {old_agent})"


def main():
    lm = LockManager()
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "list-active":
        locks = lm.list_active()
        if not locks:
            print("No active locks")
        else:
            for lk in locks:
                exp = "EXPIRED" if lk["expired"] else "ok"
                print(f"  {lk['resource_hash'][:12]} | {lk['agent_id']} | {lk['role']} | {lk['elapsed_min']}min | {exp}")
        return

    if len(sys.argv) < 3:
        print("Usage: lock_manager.py <command> <resource> [agent_id] [role] [ttl]")
        print("Commands: acquire | release | heartbeat | status | list-active | force-unlock")
        sys.exit(1)

    resource = sys.argv[2]
    agent_id = sys.argv[3] if len(sys.argv) > 3 else "unknown"
    role = sys.argv[4] if len(sys.argv) > 4 else "explorer"
    ttl = int(sys.argv[5]) if len(sys.argv) > 5 else 30

    if cmd == "acquire":
        print(lm.acquire(resource, agent_id, role, ttl))
    elif cmd == "release":
        print(lm.release(resource, agent_id))
    elif cmd == "heartbeat":
        print(lm.heartbeat(resource, agent_id))
    elif cmd == "status":
        s = lm.status(resource)
        if s["status"] == "FREE":
            print("FREE")
        else:
            print(f"agent={s['agent_id']} role={s['role']} elapsed={s['elapsed_min']}min expired={s['expired']}")
    elif cmd == "force-unlock":
        caller_role = sys.argv[4] if len(sys.argv) > 4 else "explorer"
        print(lm.force_unlock(resource, agent_id, caller_role))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
