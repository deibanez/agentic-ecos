import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic_ecos.generator import (init_project, validate_structure,
                                     suggest_next_steps, generate_file, to_slug)
from agentic_ecos.patterns import list_patterns, get_pattern, get_domains
from agentic_ecos.protocols import PROTOCOLS, get_protocol
from agentic_ecos.presets import PRESETS, get_preset, all_presets
from agentic_ecos.ecosystem import (ecosystem_init, ecosystem_status, project_add,
                                     project_remove, connect, connect_status, scan_opencode,
                                     find_config, load_config)
from agentic_ecos import __version__


def test_patterns_count():
    assert len(list_patterns()) == 15
    assert len(get_domains()) >= 6


def test_pattern_lookup():
    p = get_pattern("lock_system")
    assert p is not None
    assert "implementation_guide" in p
    assert get_pattern("does_not_exist") is None


def test_protocols():
    for name in PROTOCOLS:
        content = get_protocol(name)
        assert "{{" not in content.replace("{{PROJECT_NAME}}", "x").replace(
            "{{DATE}}", "x").replace("{{REPO_ROWS}}", "x").replace(
            "{{PROTECTION_RULES}}", "x").replace("{{TRAPS_SECTIONS}}", "x").replace(
            "{{COMPONENT_ROWS}}", "x").replace("{{PROJECT_DESCRIPTION}}", "x").replace(
            "{{DOMAIN_TOOLS_SECTION}}", "x")


def test_presets():
    assert set(PRESETS) == {"monorepo", "single_service", "data_pipeline"}
    for p in PRESETS.values():
        assert p["default_repos"]
        assert p["domain_tools"]


def test_init_project(tmp_path):
    result = init_project(
        "test-project",
        preset_name="data_pipeline",
        target_path=str(tmp_path),
        repos=["ingestor", "processor"],
        cloud="aws",
        ci_cd="github-actions",
        description="Pipeline de prueba",
    )
    assert result["ok"] is True
    assert result["files_generated"] > 20

    # Archivos críticos generados
    for rel in [
        "00_Global/AGENTS.md",
        "00_Global/AGENT_REGISTRY.md",
        "00_Global/AGENT_TASKS.md",
        "00_Global/AGENT_COMMS.md",
        "00_Global/AGENT_SESSION_LOG.md",
        "00_Global/LOCK_PROTOCOL.md",
        "00_Global/ACCESS_CONTROL.md",
        "00_Global/RULES/AGENT_PROTOCOL.md",
        "00_Global/RULES/MULTI_AGENT.md",
        "00_Global/RULES/AGENT_SKILLS.md",
        "00_Global/RULES/IAC_TRAPS.md",
        "00_Global/STATE/WORKSPACE_STATE.md",
        "00_Global/Home.md",
        "scripts/lock_manager.py",
        "scripts/sync_kanban.py",
        "scripts/test_project_tools.py",
        "scripts/mcp_server.py",
        "instructions.md",
        "00_Global/opencode.jsonc",
        "00_Global/kanban/tasks.md",
        "00_Global/MOC-Agents.md",
    ]:
        assert (tmp_path / rel).exists(), f"Missing: {rel}"

    # Validar placeholders resueltos
    agents = (tmp_path / "00_Global/AGENTS.md").read_text()
    assert "test-project" in agents
    assert "{{" not in agents


def test_init_preset_names_injected(tmp_path):
    result = init_project("preset-check", preset_name="single_service",
                          target_path=str(tmp_path))
    traps = (tmp_path / "00_Global/RULES/IAC_TRAPS.md").read_text()
    assert "Docker" in traps  # sección del preset single_service


def test_domain_tools_are_presets_specific(tmp_path):
    result = init_project("mono", preset_name="monorepo", target_path=str(tmp_path))
    tools = (tmp_path / "scripts/mono_tools.py").read_text()
    assert "project_health" in tools
    assert "deploy_service" in tools


def test_validate_structure(tmp_path):
    init_project("val", preset_name="single_service", target_path=str(tmp_path))
    v = validate_structure(str(tmp_path))
    assert v["ok"] is True
    assert v["coverage_pct"] == 100.0

    # Proyecto vacío → coverage bajo
    empty = tmp_path / "empty"
    empty.mkdir()
    v2 = validate_structure(str(empty))
    assert v2["ok"] is False
    assert len(v2["missing"]) > 0


def test_suggest_next_steps(tmp_path):
    init_project("sug", preset_name="data_pipeline", target_path=str(tmp_path))
    steps = suggest_next_steps(str(tmp_path))
    assert len(steps) > 0


def test_generate_file_single(tmp_path):
    r = generate_file("registry.md", str(tmp_path),
                      {"PROJECT_NAME": "my-app"})
    assert r["ok"] is True
    content = (tmp_path / "registry.md").read_text()
    assert "Agentes Registrados" in content

    r2 = generate_file("protocol:lock_protocol", str(tmp_path),
                       {"PROJECT_NAME": "my-app"})
    assert r2["ok"] is True
    assert (tmp_path / "lock_protocol.md").exists()


def test_generate_file_bad_template(tmp_path):
    r = generate_file("nope.md", str(tmp_path))
    assert r["ok"] is False


def test_to_slug():
    assert to_slug("Satet NG") == "satet_ng"
    assert to_slug("mi-proyecto") == "mi_proyecto"
    assert to_slug("Proyecto") == "proyecto"


def test_version():
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2


# ─── Plano de control del ecosistema ─────────────────────────────────────────

def test_ecosystem_init_creates_config(tmp_path):
    r = ecosystem_init("test-eco", str(tmp_path), cloud="aws", ci_cd="github-actions",
                       config_path=str(tmp_path / "agentic.toml"))
    assert r["ok"] is True
    assert (tmp_path / "agentic.toml").exists()
    data = load_config(str(tmp_path / "agentic.toml"))
    assert data["ecosystem"]["name"] == "test-eco"
    assert data["defaults"]["cloud"] == "aws"


def test_ecosystem_init_detects_projects_with_infra(tmp_path):
    # Proyecto 1 con infra agéntica
    proj_a = tmp_path / "alpha"
    (proj_a / "00_Global").mkdir(parents=True)
    (proj_a / "00_Global" / "AGENTS.md").write_text("# AGENTS")
    (proj_a / ".git").mkdir()
    # Proyecto 2 sin infra
    proj_b = tmp_path / "beta"
    proj_b.mkdir()
    (proj_b / ".git").mkdir()
    (proj_b / "README.md").write_text("readme")

    r = ecosystem_init("eco", str(tmp_path), scan=True,
                       config_path=str(tmp_path / "agentic.toml"))
    names = {p["name"] for p in r["projects_found"]}
    assert "alpha" in names
    assert "beta" in names
    alpha = next(p for p in r["projects_found"] if p["name"] == "alpha")
    beta = next(p for p in r["projects_found"] if p["name"] == "beta")
    assert alpha["agentic_infra"] is True
    assert beta["agentic_infra"] is False


def test_project_add_and_status(tmp_path):
    r = ecosystem_init("eco", str(tmp_path), config_path=str(tmp_path / "agentic.toml"))
    assert r["ok"]

    add = project_add("svc", project_type="backend", path="svc", preset="single_service",
                      config_path=str(tmp_path / "agentic.toml"))
    assert add["ok"] is True
    assert add["action"] == "added"

    # status sin infra detectada → cov 0%
    st = ecosystem_status(str(tmp_path / "agentic.toml"))
    assert st["projects_count"] == 1
    assert st["projects"][0]["coverage_pct"] == 0.0

    # update (misma acción idempotente)
    add2 = project_add("svc", project_type="backend", path="svc", preset="single_service",
                       config_path=str(tmp_path / "agentic.toml"))
    assert add2["action"] == "updated"

    # remove
    rm = project_remove("svc", str(tmp_path / "agentic.toml"))
    assert rm["ok"] is True
    st2 = ecosystem_status(str(tmp_path / "agentic.toml"))
    assert st2["projects_count"] == 0


def test_project_add_with_real_infra(tmp_path):
    # Proyecto con infra agéntica real
    proj = tmp_path / "app"
    init_project("app", preset_name="single_service", target_path=str(proj / "docs"),
                 register=False)
    eco = tmp_path / "agentic.toml"
    ecosystem_init("eco", str(tmp_path), scan=False, config_path=str(eco))
    add = project_add("app", project_type="backend", path="app",
                      config_path=str(eco))
    assert add["ok"] is True
    assert add["project"]["agentic_infra"] is True


def test_connect_creates_opencode(tmp_path):
    r = connect(target=str(tmp_path), create_if_missing=True)
    assert r["ok"] is True
    jsonc = tmp_path / "opencode.jsonc"
    assert jsonc.exists()
    content = jsonc.read_text()
    assert '"agentic-ecos"' in content
    assert "agentic_ecos/server.py" in content
    assert "opencode" in r["results"]  # default a opencode si no hay otros configs


def test_connect_preserves_existing_mcp(tmp_path):
    # opencode.jsonc existente con otro server
    jsonc = tmp_path / "opencode.jsonc"
    jsonc.write_text('{\n  "mcp": {\n    "other": {\n      "type": "local",\n      "command": ["x"]\n    }\n  }\n}\n')
    r = connect(target=str(tmp_path))
    assert r["ok"] is True
    content = jsonc.read_text()
    assert '"agentic-ecos"' in content
    assert '"other"' in content  # se preservó el existente


def test_connect_idempotent(tmp_path):
    connect(target=str(tmp_path))
    r2 = connect(target=str(tmp_path))
    assert r2["ok"] is True
    # el segundo connect detecta already_connected en los results
    assert r2["results"]["opencode"]["status"] == "already_connected"
    content = (tmp_path / "opencode.jsonc").read_text()
    assert content.count('"agentic-ecos"') == 1


def test_scan_opencode(tmp_path):
    (tmp_path / "a" / ".git").mkdir(parents=True)
    (tmp_path / "b" / ".git").mkdir(parents=True)
    connect(target=str(tmp_path / "a"))
    r = scan_opencode(str(tmp_path))
    assert r["connected"] == 1
    assert r["not_connected"] == 1


def test_connect_with_comments_preserved(tmp_path):
    jsonc = tmp_path / "opencode.jsonc"
    jsonc.write_text('{\n  "instructions": ["00_Global/AGENTS.md"],  // workspace guide\n  "agent": {}\n}\n')
    r = connect(target=str(tmp_path))
    assert r["ok"] is True
    content = jsonc.read_text()
    assert '"agentic-ecos"' in content
    assert "workspace guide" in content  # comentario preservado


# ─── Storage orgánico (data/) y fusión de patterns/presets ──────────────────

def _storage_env(tmp_path, monkeypatch):
    """Apunta storage a data/, workspace/ y knowledge/ temporales y limpia caché."""
    d = tmp_path / "data"
    d.mkdir()
    w = tmp_path / "workspace"
    w.mkdir()
    k = tmp_path / "knowledge"
    (k / "patterns").mkdir(parents=True)
    (k / "presets").mkdir(parents=True)
    (k / "traps").mkdir(parents=True)
    monkeypatch.setenv("AGENTIC_ECOS_DATA_DIR", str(d))
    monkeypatch.setenv("AGENTIC_ECOS_WORKSPACE_DIR", str(w))
    monkeypatch.setenv("AGENTIC_ECOS_KNOWLEDGE_DIR", str(k))
    import agentic_ecos.storage as storage
    return storage, d


def test_add_and_remove_custom_pattern(tmp_path, monkeypatch):
    storage, d = _storage_env(tmp_path, monkeypatch)
    r = storage.add_custom_pattern({"name": "custom_p", "domain": "knowledge",
                                    "description": "desc"})
    assert r["ok"] is True
    assert (d / "patterns-custom.json").exists()
    assert any(p["name"] == "custom_p" for p in storage.load_custom_patterns())

    # duplicado → error
    r2 = storage.add_custom_pattern({"name": "custom_p", "domain": "knowledge",
                                     "description": "desc"})
    assert r2["ok"] is False

    rm = storage.remove_custom_pattern("custom_p")
    assert rm["ok"] is True
    assert storage.load_custom_patterns() == []


def test_custom_pattern_fusion(tmp_path, monkeypatch):
    from agentic_ecos import patterns
    storage, _ = _storage_env(tmp_path, monkeypatch)
    storage.add_custom_pattern({"name": "my_new_p", "domain": "coordination",
                                "description": "custom pattern"})
    names = [p["name"] for p in patterns.list_patterns()]
    assert "my_new_p" in names  # fusionado con built-in
    assert patterns.get_pattern("my_new_p") is not None


def test_custom_preset_fusion(tmp_path, monkeypatch):
    storage, _ = _storage_env(tmp_path, monkeypatch)
    storage.add_custom_preset("batch_etl", {"label": "Batch ETL", "description": "d",
                                            "default_repos": [{"name": "etl", "type": "data"}],
                                            "domain_tools": [], "traps_sections": []})
    presets = all_presets()
    assert "batch_etl" in presets
    assert presets["batch_etl"]["custom"] is True
    p = get_preset("batch_etl")
    assert p["label"] == "Batch ETL"


def test_snapshot_and_state(tmp_path, monkeypatch):
    storage, d = _storage_env(tmp_path, monkeypatch)
    snap = storage.save_snapshot({"health": "ok"})
    assert snap["ok"] is True
    assert storage.list_snapshots()  # al menos 1 snapshot

    storage.set_state("last_scan", {"when": "now"})
    assert storage.get_state("last_scan")["when"] == "now"
    st = storage.storage_status()
    assert st["data_dir"] == str(d)
    assert st["custom_patterns"] == 0


# ─── Knowledge (3-tier) ──────────────────────────────────────────────────────

def test_knowledge_load(tmp_path, monkeypatch):
    storage, d = _storage_env(tmp_path, monkeypatch)
    # Simular knowledge/ patterns (usar get_knowledge_dir, respeta el env)
    kdir = storage.get_knowledge_dir() / "patterns"
    kdir.mkdir(parents=True, exist_ok=True)
    (kdir / "community_p.json").write_text(json.dumps(
        {"name": "community_p", "domain": "knowledge", "description": "community pattern"}))
    loaded = storage.load_knowledge_patterns()
    assert any(p["name"] == "community_p" for p in loaded)


def test_3tier_fusion(tmp_path, monkeypatch):
    from agentic_ecos import patterns
    storage, _ = _storage_env(tmp_path, monkeypatch)
    # tier 2 (knowledge) — usar get_knowledge_dir
    kdir = storage.get_knowledge_dir() / "patterns"
    kdir.mkdir(parents=True, exist_ok=True)
    (kdir / "k.json").write_text(json.dumps(
        {"name": "tier2_p", "domain": "coordination", "description": "d"}))
    # tier 3 (custom)
    storage.add_custom_pattern({"name": "tier3_p", "domain": "coordination",
                                "description": "d"})
    names = [p["name"] for p in patterns.list_patterns()]
    assert "tier2_p" in names
    assert "tier3_p" in names
    assert patterns.get_pattern("tier2_p") is not None
    assert patterns.get_pattern("tier3_p") is not None


def test_promote_to_workspace(tmp_path, monkeypatch):
    from agentic_ecos import knowledge
    storage, _ = _storage_env(tmp_path, monkeypatch)
    storage.add_custom_pattern({"name": "exp_p", "domain": "knowledge",
                                "description": "experimental"})
    r = knowledge.promote_to_workspace("exp_p")
    assert r["ok"] is True
    # se guardó en workspace/ del repo
    ws = storage.get_workspace_dir() / "patterns"
    assert (ws / "exp_p.json").exists()
    # ya no está en custom
    assert storage.load_custom_patterns() == []


def test_promote_to_knowledge(tmp_path, monkeypatch):
    from agentic_ecos import knowledge
    storage, _ = _storage_env(tmp_path, monkeypatch)
    # patrón en workspace
    storage.save_workspace_pattern({"name": "stable_p", "domain": "knowledge",
                                    "description": "stable"})
    r = knowledge.promote_to_knowledge("stable_p", source="workspace", kind="pattern")
    assert r["ok"] is True
    kdir = storage.get_knowledge_dir() / "patterns"
    assert (kdir / "stable_p.json").exists()


def test_knowledge_status(tmp_path, monkeypatch):
    from agentic_ecos import knowledge
    storage, _ = _storage_env(tmp_path, monkeypatch)
    st = knowledge.knowledge_status()
    assert st["tier1_builtin_patterns"] >= 15
    assert "tier2_knowledge_patterns" in st


# ─── Tasks cross-cutting ─────────────────────────────────────────────────────

def test_ecosystem_task_add(tmp_path, monkeypatch):
    from agentic_ecos import storage as s
    from agentic_ecos.ecosystem import ecosystem_task_add, ecosystem_tasks
    storage, d = _storage_env(tmp_path, monkeypatch)
    r = ecosystem_task_add("Migrar satet", priority="high", type="iac", scope="satet")
    assert r["ok"] is True
    assert r["task_id"] == "E1"
    tasks = storage.load_workspace_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == "E1"
    # segunda tarea → E2
    r2 = ecosystem_task_add("Onboard proyectos")
    assert r2["task_id"] == "E2"


def test_ecosystem_tasks_aggregate(tmp_path, monkeypatch):
    from agentic_ecos.ecosystem import ecosystem_task_add, ecosystem_tasks
    storage, d = _storage_env(tmp_path, monkeypatch)
    ecosystem_task_add("Tarea cross", priority="high")
    t = ecosystem_tasks()
    assert t["cross_cutting_count"] == 1
    assert t["cross_cutting_backlog"] == 1
    assert "per_project" in t


# ─── Connect multi-agente ────────────────────────────────────────────────────

def test_connect_claude(tmp_path):
    r = connect(target=str(tmp_path), agent="claude")
    assert r["ok"] is True
    mcp_json = tmp_path / ".mcp.json"
    assert mcp_json.exists()
    content = mcp_json.read_text()
    assert "mcpServers" in content
    assert '"agentic-ecos"' in content


def test_connect_cursor(tmp_path):
    r = connect(target=str(tmp_path), agent="cursor")
    assert r["ok"] is True
    mcp_json = tmp_path / ".cursor" / "mcp.json"
    assert mcp_json.exists()
    assert '"agentic-ecos"' in mcp_json.read_text()


def test_connect_snippet(tmp_path):
    r = connect(target=str(tmp_path), agent="snippet")
    assert r["ok"] is True
    assert r["mode"] == "snippet"
    assert "opencode" in r["snippets"]
    assert "claude" in r["snippets"]
    # no escribe archivos
    assert not (tmp_path / "opencode.jsonc").exists()


def test_connect_status(tmp_path):
    connect(target=str(tmp_path), agent="opencode")
    r = connect_status(str(tmp_path))
    assert r["ok"] is True
    assert r["agents"]["opencode"]["connected"] is True


# ─── Operaciones git del ecosistema ─────────────────────────────────────────

def _make_git_repo(tmp_path, monkeypatch):
    """Crea un repo git temporal y apunta ecosystem a él."""
    import subprocess
    from agentic_ecos import ecosystem
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    (repo / "README.md").write_text("# repo")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    # Apuntar ecosystem a este repo
    monkeypatch.setattr(ecosystem, "repo_root", lambda config_path=None: repo)
    return repo


def test_ecosystem_branch_create(tmp_path, monkeypatch):
    import subprocess
    repo = _make_git_repo(tmp_path, monkeypatch)
    from agentic_ecos.ecosystem import ecosystem_branch_create
    r = ecosystem_branch_create("mi-eco", base="main")
    assert r["ok"] is True
    assert r["branch"] == "ecosystem/mi-eco"
    # branch creada
    branches = subprocess.run(["git", "branch", "--list"], cwd=repo, capture_output=True, text=True)
    assert "ecosystem/mi-eco" in branches.stdout
    # workspace/ creado
    assert (repo / "workspace" / ".gitkeep").exists()

    # duplicado → error
    r2 = ecosystem_branch_create("mi-eco", base="main")
    assert r2["ok"] is False


def test_ecosystem_branch_create_bad_name(tmp_path, monkeypatch):
    _make_git_repo(tmp_path, monkeypatch)
    from agentic_ecos.ecosystem import ecosystem_branch_create
    r = ecosystem_branch_create("bad name with spaces!!")
    assert r["ok"] is False


def test_ecosystem_merge_main(tmp_path, monkeypatch):
    import subprocess
    repo = _make_git_repo(tmp_path, monkeypatch)
    from agentic_ecos.ecosystem import ecosystem_branch_create, ecosystem_merge_main
    ecosystem_branch_create("mi-eco", base="main")
    # commit en la branch ecosystem
    subprocess.run(["git", "checkout", "-q", "ecosystem/mi-eco"], cwd=repo, check=True)
    (repo / "feature.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feature"], cwd=repo, check=True)
    # merge main → sin conflictos (main no cambió)
    r = ecosystem_merge_main("ecosystem/mi-eco")
    assert r["ok"] is True
    assert r["status"] == "merged" or r["status"] == "up_to_date"


def test_ecosystem_sync_no_upstream(tmp_path, monkeypatch):
    repo = _make_git_repo(tmp_path, monkeypatch)
    from agentic_ecos.ecosystem import ecosystem_sync_upstream
    r = ecosystem_sync_upstream(branch="main")
    assert r["ok"] is False
    assert "upstream" in r["error"]
