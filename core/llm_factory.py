from langchain_ollama import ChatOllama

from config import OllamaConfig


def get_llm():
    """Ollama LLM 인스턴스 반환"""
    return ChatOllama(
        model=OllamaConfig.DEFAULT_MODEL,
        temperature=OllamaConfig.TEMPERATURE,
        base_url=OllamaConfig.BASE_URL,
    )
