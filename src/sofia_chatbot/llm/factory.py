from sofia_chatbot.config import Settings
from sofia_chatbot.llm.base import LLMClient
from sofia_chatbot.llm.mock import MockLLMClient
from sofia_chatbot.llm.openai_compatible import OpenAICompatibleLLMClient


def create_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower().strip()

    if provider == "mock":
        return MockLLMClient()

    if provider == "openai_compatible":
        if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
            raise ValueError("LLM_BASE_URL, LLM_API_KEY e LLM_MODEL precisam estar configurados.")
        return OpenAICompatibleLLMClient(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )

    raise ValueError(f"Provedor de LLM nao suportado: {settings.llm_provider}")
