# CONTRIBUTING — Uso, Forking y Ciclo de Vida del Conocimiento

> **Propósito**: Cómo usar agentic-ecos en tu propio ecosistema, cómo mantenerlo
> actualizado, cómo contribuir conocimiento al repo matriz, y cómo preservar la
> privacidad de tus datos con un fork privado.

---

## 1. Modelo de branches

`agentic-ecos` separa lo **oficial** (público) de lo **específico de cada
ecosistema** (privado) con branches y forks. El upstream usa **dos ramas
públicas**: `main` (estable) y `dev` (integración):

```
UPSTREAM (público)                    TU FORK (privado)
─────────────────────                ─────────────────────
main (estable, releases)              main (sync desde upstream/main)
  ↑                                   │
  └── dev (integración)               ├── ecosystem/mi-eco   ← basado en main (estable)
        ↑                             │   └── workspace/
        ├── feature/* PRs             │
        └── knowledge/* PRs           └── (opcional: ecosistema basado en dev
  (NO tiene workspace/,                        para bleeding edge)
   NO tiene branches ecosystem/)
```

**Flujo de PRs**: `feature/* → dev` (integración) → `main` (estable, testeado).
Los PRs de `knowledge/*` también van a `dev`. Solo se mergea `dev → main` cuando
el estado está testeado y estable.

**Reglas de visibilidad**:
- **`main` (estable) y `dev` (integración) son las branches públicas.**
  Contienen código + knowledge/ + docs/.
- **Las branches `ecosystem/*` solo existen en forks privados.** Contienen
  tu `workspace/` (proyectos, tareas, patrones) — siempre privado.
- **Para usar agentic-ecos con tu propio ecosistema**: fork privado obligatorio.
  Tu branch de ecosistema se crea desde `main` (estable, recomendado) o `dev`
  (bleeding edge) — ver `ecosystem_branch_create(base=...)`.
- **Para contribuir al código/knowledge del upstream**: clon público separado,
  branch `feature/*` desde `dev`, PR a `dev`. Sin `workspace/`.
- `git merge main` en tu branch de ecosistema nunca toca `workspace/` ni `data/`.

**Separación garantizada**: `main` y `dev` NO tienen `workspace/`. Cada branch
de ecosistema (en fork privado) crea el suyo.

---

## 2. Primer uso — crear tu ecosistema

> **El fork privado es obligatorio** para usar agentic-ecos con tu propio
> ecosistema. Tu `workspace/` (proyectos, tareas, patrones) se commitea ahí —
> nunca en un repo público. Solo `main` (estable) y `dev` (integración) del
> upstream son públicos.

```bash
# 1. Crear el fork privado (una vez)
gh repo fork deibanez/agentic-ecos --clone --private
cd agentic-ecos

# 2. Agregar upstream para sincronizar (una vez)
git remote add upstream https://github.com/deibanez/agentic-ecos.git

# 3. Crear tu branch de ecosistema (una vez) — vía tool MCP (trazable)
agentic-ecos ecosystem branch-create mi-eco --base main
#   base=main (estable, recomendado) | base=dev (bleeding edge)
#   → equivalente a: git checkout -b ecosystem/mi-eco main
#   → registrado en AGENT_SESSION_LOG con T-ID

# 4. Inicializar el plano de control
agentic-ecos ecosystem init --name "mi-ecosistema" --workspace ~/repos
#   → crea workspace/agentic.toml con tus proyectos detectados

# 5. Conectar el MCP al workspace (para todos los agentes que uses)
agentic-ecos connect --target ~/repos --agent auto
#   → escribe opencode.jsonc / .mcp.json / .cursor/mcp.json según detecte

# 6. Desde el agente, bootstrapear proyectos
#   → init_project("mi-api", preset="monorepo", target_path="~/repos/mi-api/docs")
```

> **¿Main o dev como base?**
> - **`main`** (default): estable, testeado. Recomendado para ecosistemas en
>   producción.
> - **`dev`** (opcional): bleeding edge, con las últimas features y knowledge.
>   Elegilo si querés seguir de cerca el desarrollo del upstream.
> Cambiá la base con `agentic-ecos ecosystem branch-create mi-eco --base dev`.

---

## 3. Día a día

```bash
# Siempre en tu branch de ecosistema
git checkout ecosystem/mi-eco

# Desde el agente (MCP):
#   ecosystem_status()      → salud de todo el ecosistema
#   ecosystem_tasks()       → tareas cross-cutting + por proyecto
#   ecosystem_task_add()    → nueva tarea cross-cutting
#   init_project(...)       → bootstrap de un proyecto nuevo
#   add_custom_pattern(...) → documenta un patrón descubierto
#   ecosystem_sync_upstream()  → sync de main/dev con upstream (trazable)
#   ecosystem_merge_main()     → merge de main a tu branch (trazable)
```

---

## 4. Actualizar desde upstream

Usá las tools MCP (trazables, registran en AGENT_SESSION_LOG) o git directo:

```bash
# Opción A — tools MCP (recomendado, trazable)
agentic-ecos ecosystem sync --branch main     # sync tu main estable desde upstream
agentic-ecos ecosystem merge-main --target ecosystem/mi-eco  # merge main → tu ecosistema

# Opción B — git directo (fork privado)
git fetch upstream
git checkout main && git merge upstream/main
git checkout ecosystem/mi-eco && git merge main
git push origin ecosystem/mi-eco   # ← a tu repo privado

# Opcional — seguir dev (bleeding edge) en vez de main
agentic-ecos ecosystem sync --branch dev       # sync tu dev desde upstream
agentic-ecos ecosystem merge-main --target ecosystem/mi-eco
```

> **Nota**: en un fork privado, `origin` = tu repo privado, `upstream` = el repo
> público matriz. Todo el `git push` de tu `workspace/` va a `origin` (privado).
> Si tu ecosistema está basado en `dev`, sincronizá `dev` en vez de `main`.

---

## 5. Ciclo de vida del conocimiento

Todo conocimiento sigue 4 tiers de madurez (todos commiteados en tu fork
privado — solo los snapshots/state de runtime son gitignored):

```
TIER 3  Personal (commiteado)          → data/patterns-custom.json
         Descubriste un patrón en sesión → add_custom_pattern()
         Se commitea en tu fork privado (trazabilidad del descubrimiento).

TIER 2.5 Ecosistema (commiteado)       → workspace/patterns/*.json
         Validado en ≥2 proyectos tuyos → promote_to_workspace()
         Se commitea en tu branch de ecosistema.

TIER 2  Comunitario (commiteado)       → agentic_ecos/knowledge/patterns/*.json
         Validado en múltiples ecosistemas → promote_to_knowledge()
         Se commitea y se abre PR a main.

TIER 1  Built-in (código)              → agentic_ecos/patterns.py
         Estable, aplica a todos → mover a patterns.py + PR a main.
```

> **Trazabilidad**: como todo se commitea en tu fork privado, `git log
> data/patterns-custom.json` muestra quién descubrió cada patrón y cuándo,
> con la descripción original del hallazgo.

### Comandos

```bash
# Tier 3 → Tier 2.5 (personal → tu ecosistema)
agentic-ecos promote mi-pattern --to workspace

# Tier 2.5 → Tier 2 (tu ecosistema → comunitario)
agentic-ecos promote mi-pattern --to knowledge --source workspace

# Ver el estado del conocimiento por tier
agentic-ecos ecosystem status   # o knowledge_status vía MCP
```

---

## 6. Contribuir al repo matriz

Los PRs van a **`dev`** (integración), no directo a `main`. Solo se mergea
`dev → main` cuando el estado está testeado y estable.

```bash
# Desde un clon público separado (sin workspace/)
git checkout -b feature/add-cold-start-pattern dev

# Opción A: desde el MCP, promote_to_knowledge(...)
# Opción B: editar agentic_ecos/knowledge/patterns/aws-lambda-cold-start.json

git add agentic_ecos/knowledge/
git commit -m "knowledge: add lambda cold start pattern"
git push && crear PR → dev
```

**Reglas para contribuir a `dev`**:
- Patrón validado en ≥2 ecosistemas independientes.
- Documentado con `description`, `when_to_use`, `implementation_guide`.
- Un archivo por item en `agentic_ecos/knowledge/`.
- El merge `dev → main` es periódico, solo cuando `dev` está estable.

---

## 7. Migrar entre máquinas

```bash
# Todo el conocimiento vive en el repo:
cp -r agentic-ecos/ /backup/            # lleva código + knowledge/ + data/ + workspace/
# En la otra máquina: clonar + checkout de tu branch de ecosistema
git clone https://github.com/deibanez/agentic-ecos.git
git checkout ecosystem/mi-eco
```

El `workspace/` (tus proyectos) está commiteado en tu branch, al igual que
`data/patterns-custom.json` y `data/presets-custom.json` (trazabilidad). Solo
los snapshots y `data/state.json` (runtime data) no viajan por git — pero sí
con el `cp -r`.

---

## 8. Multi-agente

`connect` soporta OpenCode, Claude Code y Cursor:

```bash
# Detectar agentes presentes y conectar a todos
agentic-ecos connect --agent auto

# Conectar solo a Claude Code
agentic-ecos connect --agent claude

# Obtener snippets para pegar manualmente
agentic-ecos connect --agent snippet
```

---

## 9. Automatización CI/CD con LLMs (opcional)

### Qué es

agentic-ecos puede automatizar flujos periódicos con GitHub Actions usando
síntesis LLM: resúmenes semanales, propuestas de tareas, verificación de PRs
y revisión de conocimiento. **Es opt-in** — la infraestructura base funciona
sin LLM. Se activa configurando secrets.

### Requisitos (GitHub secrets)

Configurá en `Settings → Secrets and variables → Actions`:

| Secret | Requerido | Descripción |
|--------|:---:|-----------|
| `LLM_API_KEY` | ✅ | API key del provider (DeepSeek, OpenAI, Anthropic, etc.) |
| `LLM_MODEL` | ⏸️ | Modelo. Default: `deepseek-chat`. Ej: `gpt-4o`, `claude-3-5-sonnet` |
| `LLM_BASE_URL` | ⏸️ | Solo para providers custom/self-hosted. Default por provider |

### Proveedores soportados

El motor es agnóstico. Detecta el provider por el prefijo del modelo:

| Modelo | Provider | Endpoint |
|--------|----------|----------|
| `deepseek-*` | DeepSeek (default) | `https://api.deepseek.com/v1` |
| `gpt-*`, `o3-*` | OpenAI | `https://api.openai.com/v1` |
| `claude-*` | Anthropic | `https://api.anthropic.com/v1` |
| cualquier otro | OpenAI-compatible (Groq, Ollama, local) | `LLM_BASE_URL` |

### Degradación elegante

Sin `LLM_API_KEY` configurado:
- El CLI, MCP y 34 tools funcionan normalmente.
- `agentic-ecos llm-test` → error claro: "LLM_API_KEY no configurado".
- Los workflows commitean los datos crudos (JSON) sin síntesis y crean issues mínimos.

### Verificar la conexión

```bash
# Local (requiere LLM_API_KEY exportado)
LLM_API_KEY=sk-... agentic-ecos llm-test --prompt "Hola, ¿funciona?"

# En CI: el workflow weekly-summary ya incluye la verificación implícita
```

### Workflows disponibles

| Workflow | Schedule | Qué hace |
|----------|----------|---------|
| `ecosystem-snapshot.yml` | Daily 8am | Commitea snapshot JSON de salud |
| `weekly-summary.yml` | Lunes 9am | Resumen + 3-5 tareas propuestas (issue) |
| `pre-dev-verification.yml` | On PR → dev | LLM revisa el PR y comenta |
| `knowledge-review.yml` | 1er día del mes | Detecta patterns listos para promover |
| `task-automation.yml` | `workflow_dispatch` | Task loops (desarrollo continuo) |

**Regla de no-edición**: los workflows NUNCA modifican `AGENT_TASKS.md`,
`agentic.toml`, `knowledge/` ni `workspace/tasks.md`. Solo escriben archivos
nuevos en `proposals/` o `data/ecosystem-snapshots/` y crean issues.

---

## 10. Privacidad — main público, todo lo demás privado

### El modelo

**Solo `main` es público.** El código del upstream, el `knowledge/` comunitario
y la documentación viven ahí. Tu ecosistema — `workspace/` (proyectos, tareas,
patrones) y `data/` (experimentos personales) — vive en un **fork privado**.

```
github.com/deibanez/agentic-ecos      ← PÚBLICO (solo main)
  └── main                           ← código + knowledge/ + docs/
                                       NO workspace/, NO branches ecosystem/

github.com/tu-usuario/agentic-ecos   ← PRIVADO (fork)
  ├── main (sync desde upstream)
  ├── ecosystem/mi-eco               ← tu workspace/
  └── ecosystem/otro-cliente         ← otros ecosistemas (colaboración)
```

### Por qué es obligatorio

Tu `workspace/` se commitea en tu branch de ecosistema. Contiene:

- Qué proyectos componen tu ecosistema (`agentic.toml`)
- Qué tareas tenés pendientes (`tasks.md`)
- Patrones en validación (`workspace/patterns/`)
- Patrones personales (`data/patterns-custom.json`)

Si esa branch viviera en un repo **público**, todo eso sería visible. Por eso
**cualquier ecosistema propio usa un fork privado** — no es una opción solo para
datos "sensibles", es la regla. Solo `main` es público por diseño.

### Setup

```bash
# 1. Crear el fork privado (una vez)
gh repo fork deibanez/agentic-ecos --clone --private
cd agentic-ecos

# 2. Agregar upstream para sincronizar (una vez)
git remote add upstream https://github.com/deibanez/agentic-ecos.git

# 3. Crear tu branch de ecosistema
git checkout -b ecosystem/mi-eco main

# 4. Inicializar el plano de control
agentic-ecos ecosystem init --name "mi-ecosistema" --workspace ~/repos
#   → workspace/agentic.toml se crea y se commitea EN TU REPO PRIVADO

# 5. Conectar el MCP
agentic-ecos connect --target ~/repos --agent auto
```

### Trazabilidad + privacidad

Con el fork privado tenés **ambas cosas**: privacidad total (nadie más ve tu
ecosistema) y trazabilidad completa (todo se commitea, `git log` de cada cambio).

| Directorio | Git | ¿Dónde? |
|-----------|:---:|---------|
| `workspace/` (tu branch) | ✅ commiteado | Solo en tu fork privado |
| `data/patterns-custom.json` | ✅ commiteado | Solo en tu fork privado (trazabilidad del descubrimiento) |
| `data/presets-custom.json` | ✅ commiteado | Solo en tu fork privado |
| `data/ecosystem-snapshots/` | ❌ gitignored | Nunca (runtime voluminoso) |
| `data/state.json` | ❌ gitignored | Nunca (conflictos de merge) |
| `agentic_ecos/knowledge/` | ✅ commiteado | Público (main) — es lo que compartís |
| `agentic.toml` dentro de workspace/ | ✅ | Solo en tu fork privado |

> **Qué se commitea vs qué no**: todo el conocimiento estructurado (patterns,
> presets, workspace/) se commitea. Solo el runtime data (snapshots de estado,
> estado interno del MCP) queda gitignored — no es conocimiento y genera
> conflictos de merge entre agentes concurrentes.

### Sincronizar desde upstream

```bash
git fetch upstream
git checkout main
git merge upstream/main          # trae código + knowledge/ nuevos
git checkout ecosystem/mi-eco
git merge main                    # 0 conflictos: workspace/ no existe en main
git push origin ecosystem/mi-eco  # queda solo en tu repo privado
```

### Contribuir al upstream sin exponer tu ecosistema

Tu fork privado contiene tu `workspace/`. No hagas PRs desde ahí. Contribuí
desde un **clon público separado** o un branch limpio de `upstream/main`:

```bash
# Opción A — cherry-pick al repo público
# (clona el repo público por separado y cherry-pick el commit)
git clone https://github.com/deibanez/agentic-ecos.git /tmp/agentic-public
cd /tmp/agentic-public
git checkout -b feature/add-pattern main
# copiar el patrón validado de tu fork privado (knowledge/ o workspace/)
git cherry-pick <sha-del-commit>   # o copiar el archivo
git push origin feature/add-pattern
# → PR desde /tmp/agentic-public (limpio, sin workspace/)

# Opción B — push directo de un branch limpio al upstream
cd ~/tu-fork-privado
git checkout -b contribution/knowledge-pattern upstream/main
git add agentic_ecos/knowledge/
git commit -m "knowledge: add <pattern>"
git push upstream contribution/knowledge-pattern
# → PR desde ese branch (no contiene workspace/)
```

**Regla de oro**: nunca hagas PR desde un branch que contenga `workspace/`.
Siempre contribuí desde un branch limpio de `main`.

---

> **Última actualización**: 2026-08-06
