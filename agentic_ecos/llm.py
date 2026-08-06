"""Motor de síntesis LLM agnóstico para agentic-ecos.

Soporta cualquier provider compatible con OpenAI Chat Completions
(DeepSeek, OpenAI, Groq, Ollama, etc.) y Anthropic Messages API.

Configuración vía env vars (opcional — el sistema funciona sin LLM):
    LLM_API_KEY    API key del provider
    LLM_MODEL      Modelo (ej: deepseek-chat, gpt-4o, claude-3-5-sonnet)
    LLM_BASE_URL   Base URL para OpenAI-compatible (default: https://api.openai.com/v1)

El módulo es opt-in: si LLM_API_KEY no está configurada, synthesize()
retorna {"ok": False, "error": "..."} sin lanzar excepción.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Optional

# ─── Config por defecto ─────────────────────────────────────────────────────

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"  # DeepSeek como default

DEFAULT_API_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
}

# ─── Prompt templates ───────────────────────────────────────────────────────

PROMPTS = {
    "propose_tasks": """Eres un product manager de infraestructura agéntica.

Contexto del ecosistema (JSON): {context}
Tareas existentes: {tasks}

Basándote en los gaps detectados en el contexto, propón 3-5 tareas priorizadas
para el próximo ciclo de desarrollo. Cada tarea debe ser:

- Específica y accionable
- Referenciar el gap concreto que resuelve
- Incluir el tipo (feature | bug | docs | ops | iac | monitoring)

Formato markdown con checkboxes:
- [ ] TX: Descripción [priority:: high|medium|low] [type:: tipo] [repo:: nombre]
""",
    "summarize_ecosystem": """Eres un analista de infraestructura digital.

Contexto del ecosistema (JSON): {context}

Genera un resumen ejecutivo (máximo 15 líneas) del estado del ecosistema:
1. Salud general (healthy/degraded/critical y por qué)
2. Proyectos operativos vs pendientes
3. Gaps de cobertura agéntica más críticos
4. Riesgos u observaciones relevantes

Responde en español, directo, sin preámbulos.""",
    "review_pr": """Eres un revisor de código para un sistema de infraestructura agéntica.

Archivos modificados en el PR:
{files_diff}

Estado del conocimiento: {knowledge_status}

Revisa los cambios y proporciona feedback constructivo:
1. Correctez general y posibles bugs
2. Consistencia con los patrones del sistema
3. Impacto en documentación (README/ARCHITECTURE)
4. Sugerencias concretas (máximo 5)
""",
    "review_knowledge": """Eres un revisor de conocimiento agéntico.

Patrones candidatos a promoción (JSON): {patterns}

Recomienda cuáles deberían promoverse a tier 1 (built-in) o tier 2 (comunitario)
y por qué. Considera: completitud (description, when_to_use, implementation_guide),
solapamiento con patrones existentes, y valor para múltiples ecosistemas.
""",
}

# Prompt de echo para llm-test
DEFAULT_PROMPTS = {"echo": "{prompt}"}


# ─── Detección de provider ──────────────────────────────────────────────────

def detect_provider(model: str) -> str:
    """Detecta el provider según el modelo.

    Returns: 'anthropic' | 'openai_compatible'
    """
    if model.startswith("claude"):
        return "anthropic"
    return "openai_compatible"


def resolve_endpoint(model: str, base_url: Optional[str] = None) -> str:
    """Resuelve la URL del endpoint según provider y base_url configurado."""
    provider = detect_provider(model)
    if base_url:
        return base_url.rstrip("/")
    if provider == "anthropic":
        return DEFAULT_API_URLS["anthropic"]
    # OpenAI-compatible: deepseek si el modelo es deepseek, si no openai
    if "deepseek" in model:
        return DEFAULT_API_URLS["deepseek"]
    return DEFAULT_API_URLS["openai"]


# ─── Llamada HTTP ───────────────────────────────────────────────────────────

def _call_openai_compatible(model: str, api_key: str, base_url: str, prompt: str) -> dict:
    """POST a {base_url}/chat/completions (formato OpenAI)."""
    endpoint = f"{base_url}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {"ok": True, "text": content,
                "tokens": usage.get("total_tokens", 0),
                "model": model}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}",
                "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
        return {"ok": False, "error": str(e)}


def _call_anthropic(model: str, api_key: str, base_url: str, prompt: str) -> dict:
    """POST a {base_url}/messages (formato Anthropic)."""
    endpoint = f"{base_url}/messages"
    payload = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = "".join(block.get("text", "") for block in data.get("content", []))
        usage = data.get("usage", {})
        return {"ok": True, "text": content,
                "tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "model": model}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}",
                "detail": e.read().decode("utf-8", errors="replace")[:500]}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
        return {"ok": False, "error": str(e)}


# ─── Función principal ──────────────────────────────────────────────────────

def synthesize(context: dict, role: str = "summarize_ecosystem",
               prompt: Optional[str] = None,
               model: Optional[str] = None,
               api_key: Optional[str] = None,
               base_url: Optional[str] = None) -> dict:
    """Ejecuta una síntesis LLM con contexto del ecosistema.

    Args:
        context: dict con datos del ecosistema (status, tasks, etc.).
        role: 'propose_tasks' | 'summarize_ecosystem' | 'review_pr'
              | 'review_knowledge' | 'echo' (para llm-test).
        prompt: prompt override (si se pasa, ignora el template del role).
        model: modelo LLM (default: LLM_MODEL env o 'deepseek-chat').
        api_key: API key (default: LLM_API_KEY env).
        base_url: Base URL para OpenAI-compatible (default: por provider).

    Returns:
        dict con ok, text, model, tokens, o error si no configurado.
    """
    model = model or os.environ.get("LLM_MODEL") or DEFAULT_MODEL
    api_key = api_key or os.environ.get("LLM_API_KEY")

    if not api_key:
        return {
            "ok": False,
            "error": "LLM_API_KEY no configurado. Agregá el secret en GitHub "
                     "(Settings → Secrets → Actions) o exportá la env var.",
            "role": role, "model": model,
        }

    # Resolver prompt
    if prompt is None:
        template = PROMPTS.get(role) or DEFAULT_PROMPTS.get(role)
        if template is None:
            return {"ok": False, "error": f"Rol '{role}' no soportado. "
                                          f"Disponibles: {', '.join(PROMPTS)} + echo"}
        if role == "echo":
            prompt = template.format(prompt="test")
        elif role == "propose_tasks":
            prompt = template.format(context=json.dumps(context, default=str),
                                     tasks=context.get("_tasks", "[]"))
        else:
            prompt = template.format(context=json.dumps(context, default=str))

    provider = detect_provider(model)
    base_url = base_url or os.environ.get("LLM_BASE_URL") or resolve_endpoint(model, None)

    if provider == "anthropic":
        result = _call_anthropic(model, api_key, base_url, prompt)
    else:
        result = _call_openai_compatible(model, api_key, base_url, prompt)

    result["role"] = role
    result["provider"] = provider
    return result
