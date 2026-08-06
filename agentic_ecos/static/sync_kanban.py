import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent / "00_Global"
AGENT_TASKS_FILE = ROOT / "AGENT_TASKS.md"
TASKS_BOARD = ROOT / "kanban" / "tasks.md"
ROADMAP_BOARD = ROOT / "kanban" / "roadmap.md"
MARKER = "<!-- TASKS_START -->"

def parse_tasks(content: str):
    tasks = []
    in_tasks = False
    for line in content.splitlines():
        if MARKER in line:
            in_tasks = True
            continue
        if not in_tasks:
            continue
        m = re.match(r'^\s*(- \[([ xX])\]) (.+)$', line)
        if not m:
            continue
        text = m.group(3)
        checked = m.group(2).strip().lower() == 'x'
        fields = dict(re.findall(r'\[(\w+)::\s*(.+?)\s*\]', text))
        label = re.sub(r'\s*\[.*?\]', '', text).strip()
        if not label:
            continue
        tasks.append({
            "label": label,
            "checked": checked,
            "fields": fields,
            "raw": line,
        })
    return tasks

def quarter_from_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        q = (dt.month - 1) // 3 + 1
        return f"Q{q} {dt.year}"
    except ValueError:
        return None

def col_key(status):
    order = {"backlog": 0, "doing": 1, "blocked": 1, "review": 1, "done": 2}
    return order.get(status, 0)

def sort_key(task):
    p = task["fields"].get("priority", "low")
    porder = {"high": 0, "medium": 1, "low": 2}
    return (porder.get(p, 99), task["label"])

def generate_tasks_board(tasks):
    columns = defaultdict(list)
    for t in tasks:
        if t["checked"]:
            columns["done"].append(t)
            continue
        st = t["fields"].get("status", "backlog")
        if st == "doing":
            columns["in_progress"].append(t)
        elif st == "blocked":
            columns["blocked"].append(t)
        elif st == "review":
            columns["review"].append(t)
        elif st == "done":
            columns["done"].append(t)
        else:
            columns["backlog"].append(t)

    for k in columns:
        columns[k].sort(key=sort_key)

    lines = []
    lines.append("---")
    lines.append("tags: [kanban, tasks, ecosystem]")
    lines.append("kanban-plugin: board")
    lines.append("created: 2026-07-30")
    lines.append("purpose: Auto-generado desde AGENT_TASKS.md. NO EDITAR A MANO — editar AGENT_TASKS.md y re-ejecutar sync-kanban.py")
    lines.append("---")
    lines.append("")
    lines.append("# Task Kanban")
    lines.append("")
    lines.append("> ⚠️ **Auto-generado desde [[../AGENT_TASKS.md]]**. NO editar aquí. Editar AGENT_TASKS.md y ejecutar `python scripts/sync-kanban.py`.")
    lines.append("")

    col_config = [
        ("backlog", "📋 Backlog"),
        ("in_progress", "⏳ In Progress"),
        ("review", "🔍 Review"),
        ("blocked", "🚫 Blocked"),
        ("done", "✅ Done"),
    ]

    for key, title in col_config:
        items = columns.get(key, [])
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append("")
            continue
        for t in items:
            fields = t["fields"]
            tags = [fields.get("type", "task"), fields.get("repo", "")]
            tag_str = " ".join(f"#{t}" for t in tags if t)
            extra = " ".join(f"[{k}:: {v}]" for k, v in fields.items() if k not in ("type",))
            lines.append(f"- [ ] {tag_str} {t['label']} {extra}".strip())
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("[[00_Global/AGENT_TASKS.md|📋 Fuente Canónica]] · [[00_Global/kanban/roadmap.md|🗺 Roadmap]] · [[00_Global/Home.md|🏠 Home]]")
    lines.append("")
    return "\n".join(lines)

def generate_roadmap_board(tasks):
    # Only tasks with [due::]
    dated = [t for t in tasks if "due" in t["fields"]]
    if not dated:
        dated_placeholder = [{"label": "No hay milestones con fecha", "fields": {}, "checked": False, "raw": ""}]

    quarters = defaultdict(list)
    for t in dated:
        due = t["fields"]["due"]
        q = quarter_from_date(due)
        if q:
            quarters[q].append(t)
        else:
            quarters["Sin fecha"].append(t)

    for k in quarters:
        quarters[k].sort(key=lambda t: t["fields"].get("due", ""))

    lines = []
    lines.append("---")
    lines.append("tags: [kanban, roadmap, ecosystem]")
    lines.append("kanban-plugin: board")
    lines.append("created: 2026-07-30")
    lines.append("purpose: Auto-generado desde AGENT_TASKS.md. NO EDITAR A MANO — editar AGENT_TASKS.md y re-ejecutar sync-kanban.py")
    lines.append("---")
    lines.append("")
    lines.append("# Roadmap")
    lines.append("")
    lines.append("> ⚠️ **Auto-generado desde [[../AGENT_TASKS.md]]**. Solo items con `[due::]`. NO editar aquí.")
    lines.append("")

    for qname in sorted(quarters.keys(), reverse=True):
        items = quarters[qname]
        lines.append(f"## {qname}")
        lines.append("")
        for t in items:
            fields = t["fields"]
            tags = [fields.get("type", "task"), fields.get("repo", "")]
            tag_str = " ".join(f"#{t}" for t in tags if t)
            extra = " ".join(f"[{k}:: {v}]" for k, v in fields.items() if k not in ("type",))
            lines.append(f"- [ ] {tag_str} {t['label']} {extra}".strip())
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("[[00_Global/AGENT_TASKS.md|📋 Fuente Canónica]] · [[00_Global/kanban/tasks.md|💼 Tasks]] · [[00_Global/Home.md|🏠 Home]]")
    lines.append("")
    return "\n".join(lines)

def main():
    if not AGENT_TASKS_FILE.exists():
        print(f"ERROR: {AGENT_TASKS_FILE} not found")
        return 1

    content = AGENT_TASKS_FILE.read_text()
    tasks = parse_tasks(content)
    print(f"Parsed {len(tasks)} tasks from AGENT_TASKS.md")

    # Generate tasks board
    tasks_board = generate_tasks_board(tasks)
    TASKS_BOARD.parent.mkdir(parents=True, exist_ok=True)
    TASKS_BOARD.write_text(tasks_board)
    print(f"Written: {TASKS_BOARD}")

    # Generate roadmap board
    roadmap_board = generate_roadmap_board(tasks)
    ROADMAP_BOARD.parent.mkdir(parents=True, exist_ok=True)
    ROADMAP_BOARD.write_text(roadmap_board)
    print(f"Written: {ROADMAP_BOARD}")

    print("\nDone. Boards regenerated from AGENT_TASKS.md.")
    return 0

if __name__ == "__main__":
    exit(main())
