"""Tests para Task Loop (desarrollo continuo automático)."""

import json
import os
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic_ecos import task_loop, storage


def _make_workspace(tmp_path):
    """Crea un workspace temporal con tasks.md de prueba."""
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    tasks = tmp_path / "ws" / "tasks.md"
    tasks.write_text(
        "---\ntags: [layer/l0, tasks, ecosystem]\n---\n\n# ECOSYSTEM_TASKS\n\n"
        "<!-- TASKS_START -->\n"
        "- [ ] E1: Tarea docs [priority:: medium] [status:: backlog] [type:: docs] [scope:: ecosystem]\n"
        "- [ ] E2: Tarea feature [priority:: high] [status:: backlog] [type:: feature] [scope:: ecosystem]\n"
        "<!-- TASKS_END -->\n"
    )
    return ws, tasks


class TestFindTask(unittest.TestCase):
    def test_find_existing(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            t = task_loop.find_task("E1", tasks)
            assert t is not None
            assert t["id"] == "E1"
            assert t["fields"]["type"] == "docs"

    def test_find_missing(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            assert task_loop.find_task("E99", tasks) is None


class TestFindAvailable(unittest.TestCase):
    def test_filters_by_type(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            available = task_loop.find_available_tasks("docs", tasks_file=tasks)
            assert len(available) == 1
            assert available[0]["id"] == "E1"

            # feature no se encuentra con filter docs
            feat = task_loop.find_available_tasks("feature", tasks_file=tasks)
            assert len(feat) == 1
            assert feat[0]["id"] == "E2"

    def test_excludes_claimed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            # Marcar E1 como reclamada
            content = tasks.read_text().replace(
                "type:: docs]", "type:: docs] [agent:: otro]")
            tasks.write_text(content)
            available = task_loop.find_available_tasks("docs", tasks_file=tasks)
            assert len(available) == 0


class TestCheckRisk(unittest.TestCase):
    def test_safe_types(self):
        assert task_loop.check_risk({"fields": {"type": "docs"}})["level"] == "safe"
        assert task_loop.check_risk({"fields": {"type": "ops"}})["level"] == "safe"

    def test_risky_types_require_confirm(self):
        r = task_loop.check_risk({"fields": {"type": "feature"}})
        assert r["level"] == "blocked"
        assert not r["ok"]

        r2 = task_loop.check_risk({"fields": {"type": "feature"}}, confirm=True)
        assert r2["level"] == "confirmed"
        assert r2["ok"]

        r3 = task_loop.check_risk({"fields": {"type": "bug"}})
        assert not r3["ok"]

    def test_unknown_type_allowed(self):
        r = task_loop.check_risk({"fields": {"type": "weird"}})
        assert r["ok"] is True
        assert r["level"] == "unknown"


class TestRunLoopDryRun(unittest.TestCase):
    def test_dry_run_safe_task(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            os.environ["AGENTIC_ECOS_WORKSPACE_DIR"] = str(ws)
            try:
                r = task_loop.run_loop(task_id="E1", dry_run=True)
                assert r["ok"] is True
                assert r["dry_run"] is True
                assert r["agent_id"] == "bot-ci"
                assert r["results"][0]["status"] == "done"
                assert r["results"][0]["plan_source"] in ("fallback", "llm")
            finally:
                os.environ.pop("AGENTIC_ECOS_WORKSPACE_DIR", None)

    def test_dry_run_blocks_feature_without_confirm(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            os.environ["AGENTIC_ECOS_WORKSPACE_DIR"] = str(ws)
            try:
                r = task_loop.run_loop(task_id="E2", dry_run=True, confirm=False)
                assert r["results"][0]["status"] == "blocked"
                assert "confirmación humana" in r["results"][0]["error"]
            finally:
                os.environ.pop("AGENTIC_ECOS_WORKSPACE_DIR", None)

    def test_dry_run_allows_feature_with_confirm(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            os.environ["AGENTIC_ECOS_WORKSPACE_DIR"] = str(ws)
            try:
                r = task_loop.run_loop(task_id="E2", dry_run=True, confirm=True)
                assert r["results"][0]["status"] == "done"
                assert r["results"][0]["risk"] == "confirmed"
            finally:
                os.environ.pop("AGENTIC_ECOS_WORKSPACE_DIR", None)

    def test_no_available_tasks(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            ws, tasks = _make_workspace(Path(d))
            os.environ["AGENTIC_ECOS_WORKSPACE_DIR"] = str(ws)
            try:
                r = task_loop.run_loop(type_filter="iac", dry_run=True)
                assert r["ok"] is True
                assert r["results"] == []
                assert "No hay tareas" in r.get("note", "")
            finally:
                os.environ.pop("AGENTIC_ECOS_WORKSPACE_DIR", None)


class TestPlanTask(unittest.TestCase):
    def test_fallback_without_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            r = task_loop.plan_task({"id": "E1", "label": "test"})
            assert r["ok"] is True
            assert r["source"] == "fallback"
            assert "E1" in r["plan"]


if __name__ == "__main__":
    unittest.main()
