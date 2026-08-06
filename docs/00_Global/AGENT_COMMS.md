---
tags: [layer/l0, agents]
created: 2026-08-06
purpose: Tablero de mensajes entre agentes (append-only)
---

# AGENT_COMMS — Comunicación entre Agentes

> **Propósito**: Tablero de mensajes inter-agente. Append-only: nunca editar mensajes existentes.
> **Labels**: `handoff` (transferencia) · `blocked` (bloqueado) · `question` (pregunta) · `notice` (aviso) · `escalation` (escalado a admin/humano)
> **Protocolo**: Responder < 30 min · Archivar mensajes resueltos > 7 días

---

## Mensajes

| Timestamp | From | To | Label | Message |
|-----------|------|----|-------|---------|

<!-- CUSTOMIZE: Los mensajes se agregan aquí.
     Formato: | {ISO-timestamp} | {from-agent} | {to-agent o "all"} | {label} | {mensaje} |
     Señales estándar:
       [HANDOFF] Fase completada — {repo} — ✅/⏳/❌
       [BLOCKED] Esperando {recurso} de {repo} — {detalle}
       [NOTICE]  {workflow} falló en {branch} — {error}
       [ESCALATION] {problema} — requiere decisión humana
-->

---

[[00_Global/Home.md|🏠 Home]]

> **Última actualización**: 2026-08-06
