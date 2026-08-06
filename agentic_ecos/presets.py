"""Presets de tipos de proyecto para el bootstrap agéntico.

Cada preset define los valores por defecto que `init_project` usa para
generar un esqueleto adaptado al tipo de proyecto:
  - monorepo:         múltiples servicios/repos con CI/CD compartido
  - single_service:   un repo con múltiples componentes en subdirectorios
  - data_pipeline:    lambdas, jobs batch, pipeline de ingesta/procesamiento

Los presets custom (data/presets-custom.json) se fusionan sobre los built-in.
"""

from . import storage

PRESETS: dict[str, dict] = {
    "monorepo": {
        "label": "Monorepo multi-servicio",
        "description": "Múltiples servicios/repos con CI/CD compartido e IaC centralizada.",
        "default_repos": [
            {"name": "api", "type": "backend", "language": "python", "iac": "terraform"},
            {"name": "frontend", "type": "frontend", "language": "typescript", "iac": "terraform"},
            {"name": "workers", "type": "worker", "language": "python", "iac": "terraform"},
            {"name": "docs", "type": "docs", "language": "markdown", "iac": "none"},
        ],
        "domain_tools": [
            {
                "name": "project_health",
                "description": "Health status of all project components (CI/CD, deploy recency, services).",
                "returns": '{"status": "healthy", "components": [], "stale": []}',
            },
            {
                "name": "repo_details",
                "description": "Metadata of a specific component (build, deploy, IaC, workflows).",
                "returns": '{"name": "...", "type": "...", "deploy": "...", "iac": "..."}',
            },
            {
                "name": "deploy_service",
                "description": "Trigger deploy of a service to an environment.",
                "returns": '{"status": "triggered", "environment": "...", "service": "..."}',
            },
            {
                "name": "branch_health",
                "description": "Health scores of all components in a branch.",
                "returns": '{"branch": "...", "scores": {}}',
            },
        ],
        "traps_sections": ["CI/CD", "IaC", "Cross-repo"],
        "workflow_model": "CI/CD compartido con deploys por servicio",
        "protection_rules": [
            "| 1 | Nunca hacer push/commit directo a `main` | Todos los repos |",
            "| 2 | Nunca modificar la DB de producción | Sin excepción |",
            "| 3 | Solo feature branches → PR → develop | Todos los cambios |",
        ],
    },
    "single_service": {
        "label": "Single service",
        "description": "Un solo servicio con componentes en subdirectorios (backend + frontend + infra).",
        "default_repos": [
            {"name": "backend", "type": "backend", "language": "python", "iac": "docker"},
            {"name": "frontend", "type": "frontend", "language": "typescript", "iac": "none"},
            {"name": "infra", "type": "infra", "language": "hcl", "iac": "terraform"},
        ],
        "domain_tools": [
            {
                "name": "build_status",
                "description": "Current build status of the service.",
                "returns": '{"status": "success", "last_build": "...", "branch": "..."}',
            },
            {
                "name": "test_report",
                "description": "Latest test report (passed/failed/skipped counts).",
                "returns": '{"passed": 0, "failed": 0, "skipped": 0, "duration": 0}',
            },
            {
                "name": "deploy_status",
                "description": "Deploy status per environment.",
                "returns": '{"environments": {"dev": "ok", "prod": "ok"}}',
            },
        ],
        "traps_sections": ["Docker", "CI/CD", "Local Dev"],
        "workflow_model": "Pipeline single repo por branches",
        "protection_rules": [
            "| 1 | Nunca hacer push/commit directo a `main` | Todas las branches |",
            "| 2 | Feature branches → PR → main | Todos los cambios |",
            "| 3 | Tests obligatorios antes de merge | Cualquier código |",
        ],
    },
    "data_pipeline": {
        "label": "Data pipeline / ETL",
        "description": "Lambdas, jobs batch y pipelines de ingesta/procesamiento de datos.",
        "default_repos": [
            {"name": "ingestor", "type": "data", "language": "python", "iac": "lambda"},
            {"name": "processor", "type": "data", "language": "python", "iac": "batch"},
            {"name": "api", "type": "backend", "language": "python", "iac": "lambda"},
        ],
        "domain_tools": [
            {
                "name": "pipeline_status",
                "description": "Status of data pipelines (last run, duration, success/fail).",
                "returns": '{"pipelines": [], "last_runs": {}}',
            },
            {
                "name": "data_freshness",
                "description": "Freshness of data sources by table/pipeline (staleness in hours).",
                "returns": '{"sources": [], "stale": []}',
            },
            {
                "name": "run_metrics",
                "description": "Metrics of the last pipeline run (rows processed, errors, duration).",
                "returns": '{"rows_processed": 0, "errors": 0, "duration_s": 0}',
            },
        ],
        "traps_sections": ["Lambda", "Batch", "Data Processing", "Schemas"],
        "workflow_model": "Pipelines con triggers por evento/schedule",
        "protection_rules": [
            "| 1 | Nunca modificar datos de producción directamente | Sin excepción |",
            "| 2 | Toda operación de datos referenciada a un T-ID | Migraciones |",
            "| 3 | Dry-run obligatorio antes de migraciones | Operaciones de datos |",
        ],
    },
}


def all_presets() -> dict[str, dict]:
    """Devuelve todos los presets (built-in + knowledge + custom)."""
    merged = dict(PRESETS)                                    # tier 1
    merged.update(storage.load_knowledge_presets())           # tier 2
    merged.update(storage.load_custom_presets())              # tier 3
    return merged


def get_preset(name: str) -> dict:
    """Return a preset by name (built-in or custom), or raise KeyError."""
    presets = all_presets()
    if name not in presets:
        raise KeyError(f"Preset '{name}' not found. Available: {', '.join(sorted(presets))}")
    return presets[name]
