"""
SDK adapters for ontology-driven agents.

Adapters wrap external agent SDKs (OpenAI, LangChain, AutoGen) to integrate
with our ontology-first architecture. This enables:
- Testing multiple orchestration frameworks
- Swapping SDKs without changing core logic
- Gradual migration to new frameworks
"""

from .openai_sdk import OpenAISDKAdapter

__all__ = ['OpenAISDKAdapter']

