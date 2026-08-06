#!/usr/bin/env python3
"""HMAC Signature Verification para acciones de agentes.

Cada acción en AGENT_SESSION_LOG.md puede incluir una firma HMAC
que verifica que la acción fue ejecutada por el agente que dice serlo.

Uso:
    python scripts/signature.py sign <agent_id> <session_token> <action> <resource>
    python scripts/signature.py verify <agent_id> <session_token> <action> <resource> <signature>
    python scripts/signature.py verify-log <log_entry_json>
"""

import hashlib
import hmac
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def sign(agent_id: str, session_token: str, action: str, resource: str) -> str:
    """Create HMAC-SHA256 signature for an agent action."""
    message = f"{agent_id}|{action}|{resource}|{session_token}"
    return hmac.new(
        session_token.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify(agent_id: str, session_token: str, action: str, resource: str, signature: str) -> bool:
    """Verify HMAC-SHA256 signature matches."""
    expected = sign(agent_id, session_token, action, resource)
    return hmac.compare_digest(expected, signature)


def verify_log_entry(entry_json: str) -> dict:
    """Verify a session log entry's signature."""
    try:
        entry = json.loads(entry_json)
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Invalid JSON: {e}"}

    if "signature" not in entry:
        return {"valid": False, "error": "No signature field in entry"}

    agent_id = entry.get("agent_id", "")
    action = entry.get("action", "")
    resource = entry.get("resource", "")
    signature = entry.get("signature", "")

    # Session token is NOT stored in the log entry (security)
    # Token must be provided separately or looked up from AGENT_REGISTRY.md
    # For now, we verify with a provided token or return partial verification
    if "session_token" not in entry:
        return {
            "valid": None,
            "warning": "Session token not in entry — cannot verify",
            "entry": entry,
        }

    token = entry["session_token"]
    is_valid = verify(agent_id, token, action, resource, signature)
    return {"valid": is_valid, "entry": entry}


def main():
    if len(sys.argv) < 2:
        print("Usage: signature.py {sign | verify | verify-log} ...")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "sign":
        if len(sys.argv) < 6:
            print("Usage: signature.py sign <agent_id> <session_token> <action> <resource>")
            sys.exit(1)
        sig = sign(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        print(sig)

    elif cmd == "verify":
        if len(sys.argv) < 7:
            print("Usage: signature.py verify <agent_id> <session_token> <action> <resource> <signature>")
            sys.exit(1)
        result = verify(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        print("VALID" if result else "INVALID")
        sys.exit(0 if result else 1)

    elif cmd == "verify-log":
        if len(sys.argv) < 3:
            print("Usage: signature.py verify-log '<json_entry>'")
            sys.exit(1)
        result = verify_log_entry(sys.argv[2])
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
