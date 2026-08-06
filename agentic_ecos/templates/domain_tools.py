#!/usr/bin/env python3
"""Domain tools for {{PROJECT_NAME}}.

CUSTOMIZE: Implement each tool handler with your project's logic.
Cada tool es un stub — reemplaza el cuerpo con la lógica real de tu dominio
(consultas a CI/CD, healthchecks, pipelines, etc.).

Firma: register_tools(server, HANDLERS, TOOL_DEFINITIONS, make_tool)
  - server: el mcp.server.Server instance
  - HANDLERS: dict de dispatch que debes extender con tus handlers
  - TOOL_DEFINITIONS: lista de definiciones de tools a extender
  - make_tool: helper _make_tool(name, desc, properties, required)

Ejemplo de registro:
    async def _project_health(args):
        # TODO: implementar — consulta tu CI/CD, healthchecks o pipelines
        return {"status": "healthy", "components": []}
    HANDLERS["project_health"] = _project_health
    TOOL_DEFINITIONS.append(make_tool("project_health", "Health de componentes", {}))
"""

# CUSTOMIZE: importa aquí tus librerías de dominio
# import requests
# import json


def register_tools(server, HANDLERS, TOOL_DEFINITIONS, make_tool):
    """Register domain-specific tools.

    Extiende HANDLERS y TOOL_DEFINITIONS con las tools de tu dominio.
    """
{{TOOL_STUBS}}
