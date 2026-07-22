"""Centralized chat-model builder.
All model calls in this project (the Deep Agents coding harness in
``agent_graph.make_agent`` and the improver in ``improver.propose_config``) go
through :func:`build_chat_model`, so switching providers only requires editing
this file and ``.env``.

The project targets DeepSeek via its OpenAI-compatible endpoint. Configure it in
``.env``::
    base_url = https://api.deepseek.com
    AGENT_MODEL = deepseek-v4-flash
    OPENAI_API_KEY = sk-...
"""

from __future__ import annotations
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI##===================================
# from langchain_openai  ##===================================三种都可以
# from langchain.chat_models import init_chat_model ##===================================
load_dotenv()
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com"


def resolve_model(model: str | None = None) -> str:
    """Return the bare model name, dropping any ``provider:`` prefix."""
    model = model or os.getenv("AGENT_MODEL") or DEFAULT_MODEL
    if ":" in model:
        # Tolerate legacy strings like "openai:gpt-4.1-mini".
        model = model.split(":", 1)[1]
    return model


def _base_url() -> str:
    return (
        os.getenv("base_url")
        or os.getenv("BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    )
def build_chat_model(model: str | None = None, **kwargs) -> ChatOpenAI:
    """Build a chat model pointed at the DeepSeek OpenAI-compatible API."""
    return ChatOpenAI(
        model=resolve_model(model),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=_base_url(),
        **kwargs,
    )
