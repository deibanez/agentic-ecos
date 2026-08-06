#!/bin/bash
# agent_daemon.sh — Heartbeat automático para agentes multi-agente
#
# Mantiene vivo el heartbeat de un agente mientras opera.
# Corre en background y refresca el heartbeat cada 5 minutos.
#
# Uso:
#   ./agent_daemon.sh start <agent_id> <role> [ttl]
#   ./agent_daemon.sh stop <agent_id>
#   ./agent_daemon.sh status [agent_id]

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCK_MANAGER="$BASE_DIR/scripts/lock_manager.py"
REGISTRY="$BASE_DIR/00_Global/AGENT_REGISTRY.md"
SESSION_LOG="$BASE_DIR/00_Global/AGENT_SESSION_LOG.md"
PID_DIR="/tmp/agv-agent-daemons"
mkdir -p "$PID_DIR"

case "$1" in
  start)
    AGENT_ID="$2"
    ROLE="${3:-worker}"
    TTL="${4:-30}"

    if [ -z "$AGENT_ID" ]; then
      echo "Usage: $0 start <agent_id> <role> [ttl]"
      exit 1
    fi

    # Check if already running — handle zombie PIDs
    PID_FILE="$PID_DIR/$AGENT_ID.pid"
    if [ -f "$PID_FILE" ]; then
      OLD_PID=$(cat "$PID_FILE")
      if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Daemon already running for $AGENT_ID (PID $OLD_PID)"
        exit 0
      else
        echo "Cleaning up stale PID file for $AGENT_ID (PID $OLD_PID was zombie)"
        rm -f "$PID_FILE"
      fi
    fi

    # Fork daemon
    (
      # Trap signals to clean up
      cleanup() {
        python3 "$LOCK_MANAGER" release "agent:$AGENT_ID" "$AGENT_ID" 2>/dev/null || true
        rm -f "$PID_FILE"
        LOG_ENTRY="{\"timestamp\":\"$(date -u -Iseconds)\",\"agent_id\":\"$AGENT_ID\",\"role\":\"$ROLE\",\"action\":\"daemon_stop\",\"resource\":\"agent:$AGENT_ID\",\"status\":\"success\",\"details\":\"daemon stopped\"}"
        echo "$LOG_ENTRY" >> "$SESSION_LOG"
        exit 0
      }
      trap cleanup SIGTERM SIGINT EXIT

      # Initial heartbeat
      python3 "$LOCK_MANAGER" acquire "agent:$AGENT_ID" "$AGENT_ID" "$ROLE" "$TTL" > /dev/null 2>&1 || true

      # Heartbeat loop
      while true; do
        sleep 300  # 5 minutes
        python3 "$LOCK_MANAGER" heartbeat "agent:$AGENT_ID" "$AGENT_ID" > /dev/null 2>&1 || true
      done
    ) &

    PID=$!
    echo "$PID" > "$PID_FILE"
    echo "Daemon started for $AGENT_ID (PID $PID, role=$ROLE, ttl=${TTL}min)"
    LOG_ENTRY="{\"timestamp\":\"$(date -u -Iseconds)\",\"agent_id\":\"$AGENT_ID\",\"role\":\"$ROLE\",\"action\":\"daemon_start\",\"resource\":\"agent:$AGENT_ID\",\"status\":\"success\",\"details\":\"daemon started PID $PID\"}"
    echo "$LOG_ENTRY" >> "$SESSION_LOG"
    ;;

  stop)
    AGENT_ID="$2"
    if [ -z "$AGENT_ID" ]; then
      echo "Usage: $0 stop <agent_id>"
      exit 1
    fi

    PID_FILE="$PID_DIR/$AGENT_ID.pid"
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      kill "$PID" 2>/dev/null && echo "Daemon stopped for $AGENT_ID (PID $PID)" || echo "Daemon not running for $AGENT_ID"
      rm -f "$PID_FILE"
      # Release all locks held by this agent
      python3 "$LOCK_MANAGER" release "agent:$AGENT_ID" "$AGENT_ID" > /dev/null 2>&1 || true
    else
      echo "No daemon found for $AGENT_ID"
    fi
    ;;

  status)
    echo "=== Agent Daemons ==="
    if [ -n "$2" ]; then
      PID_FILE="$PID_DIR/$2.pid"
      if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "  $2: running (PID $(cat "$PID_FILE"))"
      else
        [ -f "$PID_FILE" ] && rm -f "$PID_FILE" && echo "  $2: cleaned up zombie PID file"
        echo "  $2: not running"
      fi
    else
      for pid_file in "$PID_DIR"/*.pid; do
        [ -f "$pid_file" ] || continue
        agent=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
          echo "  $agent: running (PID $pid)"
        else
          echo "  $agent: cleaned up zombie (was PID $pid)"
          rm -f "$pid_file"
        fi
      done
      echo ""
      echo "Active locks:"
      python3 "$LOCK_MANAGER" list-active 2>/dev/null || echo "  (none)"
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|status} [agent_id] [role] [ttl]"
    exit 1
    ;;
esac
