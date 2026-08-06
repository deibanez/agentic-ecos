"""Tests para el motor LLM agnóstico (llm.py) y el output --json del CLI."""

import json
import os
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic_ecos import llm


class TestProviderDetection(unittest.TestCase):
    def test_claude_uses_anthropic(self):
        assert llm.detect_provider("claude-3-5-sonnet") == "anthropic"

    def test_deepseek_uses_openai_compatible(self):
        assert llm.detect_provider("deepseek-chat") == "openai_compatible"

    def test_gpt_uses_openai_compatible(self):
        assert llm.detect_provider("gpt-4o") == "openai_compatible"


class TestEndpointResolution(unittest.TestCase):
    def test_deepseek_default_url(self):
        url = llm.resolve_endpoint("deepseek-chat")
        assert "deepseek" in url

    def test_anthropic_default_url(self):
        url = llm.resolve_endpoint("claude-3-5-sonnet")
        assert "anthropic" in url

    def test_custom_base_url_wins(self):
        url = llm.resolve_endpoint("deepseek-chat", "http://localhost:11434/v1")
        assert url == "http://localhost:11434/v1"


class TestSynthesizeNoKey(unittest.TestCase):
    def test_missing_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            r = llm.synthesize({"test": True})
            assert r["ok"] is False
            assert "LLM_API_KEY" in r["error"]


class TestSynthesizeOpenAICompat(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    def test_deepseek_success(self, mock_urlopen):
        # Simular respuesta OpenAI-compatible
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Task proposal..."}}],
            "usage": {"total_tokens": 42},
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with mock.patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=True):
            r = llm.synthesize({"health": "ok"}, role="propose_tasks")
            assert r["ok"] is True
            assert "Task proposal" in r["text"]
            assert r["provider"] == "openai_compatible"
            assert r["tokens"] == 42


class TestSynthesizeAnthropic(unittest.TestCase):
    @mock.patch("urllib.request.urlopen")
    def test_claude_success(self, mock_urlopen):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [{"type": "text", "text": "Summary here"}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        with mock.patch.dict(os.environ, {"LLM_API_KEY": "test-key"}, clear=True):
            r = llm.synthesize({"health": "ok"}, role="summarize_ecosystem",
                               model="claude-3-5-sonnet")
            assert r["ok"] is True
            assert "Summary here" in r["text"]
            assert r["provider"] == "anthropic"
            assert r["tokens"] == 30


class TestPromptTemplates(unittest.TestCase):
    def test_all_roles_have_templates(self):
        for role in ["propose_tasks", "summarize_ecosystem", "review_pr", "review_knowledge"]:
            assert role in llm.PROMPTS, f"Falta template para {role}"
            assert "{" in llm.PROMPTS[role]  # tiene placeholders

    def test_echo_role(self):
        assert "echo" in llm.DEFAULT_PROMPTS


class TestCLIJsonOutput(unittest.TestCase):
    """Verifica que el CLI con --json produce JSON válido."""

    def run_cli(self, *args, env_extra=None):
        import subprocess
        env = dict(os.environ)
        env["AGENTIC_ECOS_DATA_DIR"] = "/tmp/ae-test-cli-data"
        env["AGENTIC_ECOS_WORKSPACE_DIR"] = "/tmp/ae-test-cli-ws"
        env.pop("LLM_API_KEY", None)
        if env_extra:
            env.update(env_extra)
        r = subprocess.run(
            [sys.executable, "-m", "agentic_ecos.generator", *args],
            capture_output=True, text=True, env=env,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        return r

    def test_ecosystem_status_json(self):
        r = self.run_cli("ecosystem", "status", "--json")
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "projects_count" in data

    def test_validate_json(self):
        r = self.run_cli("validate", "/tmp", "--json")
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert "coverage_pct" in data

    def test_protocols_json(self):
        r = self.run_cli("protocols", "--json")
        assert r.returncode == 0, r.stderr
        data = json.loads(r.stdout)
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_llm_test_no_key_json(self):
        r = self.run_cli("llm-test", "--json")
        data = json.loads(r.stdout)
        assert data["ok"] is False
        assert "LLM_API_KEY" in data["error"]


if __name__ == "__main__":
    unittest.main()
