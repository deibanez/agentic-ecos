#!/bin/bash
# Lock Manager para escritura multi-agente
# Usage: ./scripts/lock_manager.sh <command> <resource> <agent_id> [role] [ttl]
# Commands: acquire | release | heartbeat | status | force-unlock

LOCK_DIR="$(dirname "$0")/../.locks"
mkdir -p "$LOCK_DIR"

RESOURCE_HASH=$(echo "$2" | sha256sum | cut -d' ' -f1)
LOCK_FILE="$LOCK_DIR/$RESOURCE_HASH.lock"

case "$1" in
  acquire)
    ROLE="${4:-explorer}"
    TTL="${5:-30}"
    NOW=$(date -u -Iseconds)

    if [ -f "$LOCK_FILE" ]; then
      IFS='|' read -r LOCK_AGENT LOCK_ROLE LOCK_ACQUIRED LOCK_TTL LOCK_HEARTBEAT < "$LOCK_FILE"
      HEARTBEAT_TS=$(date -d "$LOCK_HEARTBEAT" +%s 2>/dev/null || echo 0)
      NOW_TS=$(date -u +%s)
      AGE_MIN=$(( (NOW_TS - HEARTBEAT_TS) / 60 ))

      if [ "$AGE_MIN" -gt "$LOCK_TTL" ]; then
        echo "$3 | $ROLE | $NOW | $TTL | $NOW" > "$LOCK_FILE"
        echo "RECLAIMED (was held by $LOCK_AGENT, expired $AGE_MIN min ago)"
        exit 0
      elif [ "$LOCK_AGENT" = "$3" ]; then
        echo "$LOCK_AGENT | $LOCK_ROLE | $LOCK_ACQUIRED | $LOCK_TTL | $NOW" > "$LOCK_FILE"
        echo "RENEWED"
        exit 0
      else
        echo "HELD_BY=$LOCK_AGENT"
        exit 1
      fi
    else
      echo "$3 | $ROLE | $NOW | $TTL | $NOW" > "$LOCK_FILE"
      echo "ACQUIRED"
      exit 0
    fi
    ;;

  release)
    if [ ! -f "$LOCK_FILE" ]; then
      echo "NOT_LOCKED"
      exit 0
    fi
    IFS='|' read -r LOCK_AGENT _ _ _ _ < "$LOCK_FILE"
    if [ "$LOCK_AGENT" = "$3" ]; then
      rm "$LOCK_FILE"
      echo "RELEASED"
      exit 0
    else
      echo "NOT_OWNER (held by $LOCK_AGENT)"
      exit 1
    fi
    ;;

  heartbeat)
    if [ ! -f "$LOCK_FILE" ]; then
      echo "NOT_LOCKED"
      exit 1
    fi
    IFS='|' read -r LOCK_AGENT LOCK_ROLE LOCK_ACQUIRED LOCK_TTL _ < "$LOCK_FILE"
    if [ "$LOCK_AGENT" = "$3" ]; then
      NOW=$(date -u -Iseconds)
      echo "$LOCK_AGENT | $LOCK_ROLE | $LOCK_ACQUIRED | $LOCK_TTL | $NOW" > "$LOCK_FILE"
      echo "HEARTBEAT_OK"
      exit 0
    else
      echo "NOT_OWNER"
      exit 1
    fi
    ;;

  status)
    if [ -f "$LOCK_FILE" ]; then
      IFS='|' read -r LOCK_AGENT LOCK_ROLE LOCK_ACQUIRED LOCK_TTL LOCK_HEARTBEAT < "$LOCK_FILE"
      echo "agent=$LOCK_AGENT role=$LOCK_ROLE acquired=$LOCK_ACQUIRED ttl=$LOCK_TTL heartbeat=$LOCK_HEARTBEAT"
    else
      echo "FREE"
    fi
    exit 0
    ;;

  force-unlock)
    CALLER_ROLE="${4:-explorer}"
    if [ "$CALLER_ROLE" != "admin" ] && [ "$CALLER_ROLE" != "supervisor" ]; then
      echo "FORCE_UNLOCK_DENIED (role $CALLER_ROLE not authorized)"
      exit 1
    fi
    if [ -f "$LOCK_FILE" ]; then
      IFS='|' read -r LOCK_AGENT _ _ _ _ < "$LOCK_FILE"
      rm "$LOCK_FILE"
      echo "FORCE_UNLOCKED (was held by $LOCK_AGENT)"
      LOG_ENTRY="{\"timestamp\":\"$(date -u -Iseconds)\",\"agent_id\":\"$3\",\"role\":\"$CALLER_ROLE\",\"action\":\"force_unlock\",\"resource\":\"$2\",\"status\":\"success\",\"details\":\"force unlocked from $LOCK_AGENT\"}"
      SESSION_LOG="$(dirname "$0")/../00_Global/AGENT_SESSION_LOG.md"
      echo "$LOG_ENTRY" >> "$SESSION_LOG"
      exit 0
    else
      echo "NOT_LOCKED"
      exit 0
    fi
    ;;

  *)
    echo "Usage: $0 {acquire|release|heartbeat|status|force-unlock} <resource> <agent_id> [role] [ttl]"
    exit 1
    ;;
esac
