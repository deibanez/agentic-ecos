"""Tests para sync_home (Home.md dinámico) y suggestions del _context."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic_ecos import sync_home
from agentic_ecos.sync_home import (_get_pulse_block, _get_knowledge_table,
                                    _replace_block, sync_home_md)


def _make_home(tmp: Path) -> Path:
    """Crea un Home.md de prueba con bloques AUTO."""
    home = tmp / "00_Global" / "Home.md"
    home.parent.mkdir(parents=True)
    home.write_text(
        "# Test Home\n\n"
        "## Pulso del Ecosistema\n\n"
        "<!-- AUTO_START: pulse -->\n| Metrica | Valor |\n<!-- AUTO_END: pulse -->\n\n"
        "## Conocimiento\n\n"
        "<!-- AUTO_START: knowledge-table -->\n| Tier | Patrones |\n<!-- AUTO_END: knowledge-table -->\n\n"
        "## MOCs\n\n"
    )
    return home


class TestReplaceBlock(unittest.TestCase):
    def test_replaces_existing_block(self):
        content = "<!-- AUTO_START: pulse -->\nold\n<!-- AUTO_END: pulse -->\n"
        result = _replace_block(content, "pulse", "new content")
        assert "new content" in result
        assert "old" not in result

    def test_inserts_missing_block(self):
        content = "## Mapas de Contenido (MOCs)\n\nrest\n"
        result = _replace_block(content, "pulse", "pulse content")
        assert "pulse content" in result
        # Se inserta antes de MOCs
        assert result.index("pulse content") < result.index("Mapas de Contenido")


class TestSyncHome(unittest.TestCase):
    def test_sync_home_updates_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            home = _make_home(tmp)
            r = sync_home_md(target_path=tmp)
            assert r["ok"] is True
            content = home.read_text()
            # Los bloques fueron actualizados con datos reales
            assert "AUTO_START: pulse" in content
            assert "Patrones built-in" in content
            assert "AUTO_START: knowledge-table" in content

    def test_sync_preserves_static_content(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            home = _make_home(tmp)
            sync_home_md(target_path=tmp)
            content = home.read_text()
            # El título y las secciones estáticas se preservan
            assert "# Test Home" in content
            assert "## MOCs" in content

    def test_pulse_block_values(self):
        knowledge = {"tier1_builtin_patterns": 17, "tier2_knowledge_traps": 13,
                     "tier2_knowledge_patterns": 0, "tier3_custom_patterns": 0}
        ecosystem = {"projects_count": 5, "with_agentic_infra": 3,
                     "without_agentic_infra": 2}
        tasks = {"ecosystem_backlog": 8}
        block = _get_pulse_block(ecosystem, tasks, knowledge)
        assert "| 5 |" in block       # proyectos
        assert "| 3 |" in block       # con infra
        assert "| 2 |" in block       # sin infra
        assert "| 8 |" in block       # tareas backlog
        assert "| 17 |" in block      # patrones
        assert "| 13 |" in block      # traps


class TestSuggestions(unittest.TestCase):
    def test_suggestions_recommend_bootstrap(self):
        from agentic_ecos import server as srv
        # Con ecosistema vacío → sugerencia de bootstrap
        ctx = srv._context()
        assert isinstance(ctx["suggestions"], list)
        assert len(ctx["suggestions"]) > 0

    def test_inject_context_has_suggestions(self):
        from agentic_ecos import server as srv
        result = srv._inject_context({"ok": True})
        assert "suggestions" in result["_context"]
        assert isinstance(result["_context"]["suggestions"], list)


if __name__ == "__main__":
    unittest.main()
