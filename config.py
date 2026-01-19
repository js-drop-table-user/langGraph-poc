"""
Ollama 기반 코딩 에이전트 설정
"""

import os
from dotenv import load_dotenv

load_dotenv()


class OllamaConfig:
    """Ollama 로컬 LLM 설정"""

    # Ollama 서버 설정
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # 모델 설정
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "devstral-small-2")
    TEMPERATURE = 0.0

    # 워크플로우 설정
    MAX_ITERATIONS = 10  # Self-correction 최대 반복 횟수
    TIMEOUT_SECONDS = 120

    # 작업 디렉토리 설정
    # 기본값: 현재 프로젝트 루트의 'workspace' 폴더
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.join(os.getcwd(), "workspace"))


class AgentConfig:
    """에이전트 시스템 프롬프트 설정"""

    SYSTEM_PROMPT = """You are an expert coding agent that can read, write, and execute code.

## CRITICAL RULES:
- You MUST use tools to complete tasks. DO NOT just describe what tools you would use.
- When you want to create a file, call the file_write tool directly.
- When you want to read a file, call the file_read tool directly.
- When you want to run code, call the run_python tool directly.
- NEVER output JSON or tool call syntax in your response. Just call the tools.

## Your Tools:
1. **file_read**: Read contents of any file
2. **file_write**: Create or modify files  
3. **list_directory**: List files in a directory
4. **run_python**: Execute Python code and get output

## Workflow:
1. Read existing files before modifying them
2. Write clean, well-documented code
3. Test your changes by running the code
4. If an error occurs, analyze it and fix the issue
5. Explain what you did after completing the task
"""
