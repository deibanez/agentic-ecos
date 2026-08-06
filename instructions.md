# agentic-ecos — Agent Instructions

You are connected to the `agentic-ecos` MCP server, the control plane of the
ecosystem. It initializes, manages and operates traceable agentic infrastructure
across ALL projects — not just one.

## What this server does

**Control plane (ecosystem-wide)**
- `ecosystem_init(name, workspace_root)` — creates the canonical registry
  `agentic.toml`, auto-detecting existing projects and their agentic infra.
- `ecosystem_status()` — health of the whole ecosystem: per-project coverage
  of the 16 required agentic files, gaps, counts with/without infra.
- `ecosystem_config()` — returns the full registry (projects + defaults).
- `project_add(name, type, path, preset)` / `project_remove(name)` — register
  or unregister a project.
- `connect(target, agent)` — configures agentic-ecos for OpenCode, Claude Code
  or Cursor (`agent="auto"` detects present; `"snippet"` returns snippets).
- `connect_status(target)` — which agents are configured and connected.
- `scan_opencode()` — which projects in the workspace have agentic-ecos connected.

**Tasks cross-cutting (full lifecycle)**
- `ecosystem_tasks()` — aggregates workspace/tasks.md + per-project task counts.
- `ecosystem_task_add(description, priority, type, scope)` — adds a task to
  workspace/tasks.md (committed on your ecosystem branch).
- `ecosystem_task_claim(task_id, agent_id)` — claims a task: `[agent::]`
  `[status:: doing]` + commit + push. Race-free via git push rejection.
- `ecosystem_task_done(task_id, agent_id)` — marks a task done (verifies the
  agent completing is the one that claimed it).
- `ecosystem_task_status(filter_agent)` — filter tasks: unclaimed | claimed |
  done | backlog | <agent-id>.

> **Local-first**: these tools work in any agent session — they commit and push
> via git to your branch. GitHub Actions task-automation is OPTIONAL (see
> CONTRIBUTING.md §9); it runs the same cycle for docs/ops tasks automatically.

**Generation**
- `init_project(name, preset, target_path, repos)` — generates the full agentic
  skeleton in a project (locks, tasks, comms, session audit, protocols, vault,
  MCP server skeleton) AND registers it in the registry.
- `protocol_template(name)` / `generate_file(name, target_path, context)` — individual templates.
- `list_presets()` — monorepo / single_service / data_pipeline.

**Patterns & validation**
- `list_patterns(domain)` / `get_pattern(name)` — catalog across 4 tiers:
  built-in + knowledge (committed) + workspace (ecosystem) + custom (personal).
- `validate_structure(path)` — checklist of the 16 required pieces.
- `suggest_next_steps(path)` / `agentic_health(path)` — prioritized next actions
  and health report.
- `rag_status()` — RAG is opt-in; small vaults use wiki-link queries instead.

**Knowledge lifecycle (4 tiers)**
- `add_custom_pattern(pattern)` → `data/` (tier 3, personal, committed in private fork)
- `promote_to_workspace(name)` → `workspace/` (tier 2.5, committed on your branch)
- `promote_to_knowledge(name, source, kind)` → `knowledge/` (tier 2, committed, PR to main)
- `knowledge_status()` — state of knowledge per tier.

## Two modes of operation

agentic-ecos has two levels of use:

**Mode 1 — MCP tools (no ecosystem needed).** Works immediately after the
server is connected. No private fork, no registry required:
- `init_project(...)` — bootstrap agentic infra in a project.
- `validate_structure(...)` / `agentic_health(...)` — check coverage.
- `list_patterns()` / `get_pattern()` / `list_protocols()` — consult knowledge.
- `generate_file(...)` — generate a single template.

**Mode 2 — Ecosystem management (requires private fork).** For multi-project
coordination with canonical registry, cross-cutting tasks, and traceable
branch/fork operations. Setup is documented in CONTRIBUTING.md §10.

## When to use

1. **Bootstrap a single project (no ecosystem)** → `init_project(...)`
2. **Bootstrap the ecosystem** → `ecosystem_init(name, workspace_root)`
3. **Starting a new project** → `init_project(name, preset, target_path)`
4. **Registering an existing project** → `project_add(...)`
5. **Checking ecosystem health** → `ecosystem_status()`
6. **Connecting the MCP server** → `connect(target, agent="auto")`
7. **Managing cross-cutting tasks** → `ecosystem_tasks()` / `ecosystem_task_add()`
8. **Documenting a discovered pattern** → `add_custom_pattern(...)` then promote.
9. **Branch/fork management (traceable)** → `ecosystem_branch_create(name, base)`,
   `ecosystem_sync_upstream(branch)`, `ecosystem_merge_main(target)`.

## Recommended flow for a NEW project

1. Ask: project name, type (preset), components, cloud, CI/CD.
2. Call `init_project(...)`.
3. Show the generated structure and `next_steps`.
4. Guide customization: AGENTS.md (repo map), `{slug}_tools.py` (domain
   tools), IAC_TRAPS.md (tribal knowledge), AGENT_TASKS.md (initial backlog).
5. If the project needs the MCP connected: `connect(target=<project_dir>)`.

## Recommended flow for onboarding the ECOSYSTEM

1. **Private fork is REQUIRED** for using agentic-ecos with your own ecosystem.
   Only `main` (stable) and `dev` (integration) are public. Guide the user to
   create a private fork on GitHub (`gh repo fork ... --clone --fork-name
   agentic-ecos-priv` + `gh repo edit --visibility private`) BEFORE
   proceeding. The `workspace/` and `data/` patterns will be committed there —
   not in any public repo.
   See CONTRIBUTING.md §10 for the full flow.
2. **Create the ecosystem branch** → `ecosystem_branch_create(name, base)`.
   Ask the user: `base="main"` (stable, default, recommended) or `base="dev"`
   (bleeding edge, follows upstream development closely).
3. `ecosystem_init(name, workspace_root)` — detect existing projects.
4. `ecosystem_status()` — see which projects lack agentic infra.
5. For each gap: `init_project(...)` or `project_add(...)`.
6. `connect()` on the workspace to make agentic-ecos available everywhere.

### Branch/fork guidance for agents

- **Upstream**: `main` = stable releases, `dev` = integration. Feature and
  knowledge PRs go to `dev`, not `main`. `dev → main` merge is periodic/tested.
- **Ecosystem branches** (`ecosystem/*`) live ONLY in the private fork. Create
  them with `ecosystem_branch_create(name, base)` — traceable (logged with T-ID).
- **Keeping up to date**: `ecosystem_sync_upstream(branch="main"|"dev")` syncs
  your local branch from upstream. `ecosystem_merge_main(target)` merges main
  into your ecosystem branch and reports conflicts.
- **Contributions to upstream**: always from a clean branch off `dev` (never
  from a branch containing `workspace/`).

### Privacy guidance for agents

- **Only `main` and `dev` are public.** Code, `knowledge/` and docs live there.
  Your ecosystem (`workspace/`, `data/` patterns/presets) lives in a **private
  fork**.
- `workspace/` (projects registry, tasks.md, patterns) is committed in the
  ecosystem branch → **private** because the fork is private.
- `agentic_ecos/data/patterns-custom.json` and `data/presets-custom.json` are
  COMMITTED (in the private fork) for discovery traceability. The agent should
  `git add` them after `add_custom_pattern` and commit alongside session work.
- `agentic_ecos/data/ecosystem-snapshots/` and `data/state.json` are NEVER
  committed (runtime data, merge conflicts).
- `agentic_ecos/knowledge/` is what you WANT to share via PR.
- Never create a PR from a branch containing `workspace/`. Contribute from a
  clean branch off `main` (cherry-pick `knowledge/` if needed).

## Patterns to reach for

| Situation | Pattern |
|-----------|---------|
| Agents writing shared files | `lock_system` + `access_control` |
| Coordinating who does what | `task_system` + `kanban_sync` |
| Agents on different machines | `distributed_coordination` |
| Crash recovery | `zombie_cleanup` + `heartbeat_daemon` |
| Accountability | `session_audit` + `agent_lifecycle` |
| Exposing to AI agents | `mcp_tool_design` + `domain_tool_pattern` |

## Language

English by default; Spanish is fully supported. Generated files include
bilingual `CUSTOMIZE:` comments. Respond in the user's language.
