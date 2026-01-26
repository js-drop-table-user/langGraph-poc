"""
에이전트가 사용할 도구 및 유틸리티 함수 정의
"""

import os
import subprocess

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from config import OllamaConfig
from core.security import is_safe_code


def get_safe_path(path: str) -> str:
    """워크스페이스 내부로 경로 제한 및 절대 경로 변환"""
    # 상대 경로를 절대 경로로 변환
    if not os.path.isabs(path):
        # 만약 path가 'workspace/'로 시작하면 제거 (중복 방지)
        workspace_name = os.path.basename(OllamaConfig.WORKSPACE_DIR)

        # Normalize path separators
        clean_path = path.replace("\\", "/")
        if clean_path.startswith(f"{workspace_name}/"):
            path = clean_path[len(workspace_name) + 1 :]

        path = os.path.join(OllamaConfig.WORKSPACE_DIR, path)

    # 경로 정규화
    path = os.path.normpath(path)

    # 워크스페이스 내부에 있는지 확인
    if not path.startswith(os.path.normpath(OllamaConfig.WORKSPACE_DIR)):
        raise ValueError(
            f"Access denied: Path must be within {OllamaConfig.WORKSPACE_DIR}"
        )
    return path


# =============================================================================
# Tools
# =============================================================================
@tool
def file_read(file_path: str) -> str:
    """파일의 내용을 읽습니다.

    Args:
        file_path: 읽을 파일의 경로
    """
    try:
        safe_path = get_safe_path(file_path)
        if not os.path.exists(safe_path):
            return f"Error: File not found at {file_path}"

        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"=== File: {file_path} ===\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def file_write(file_path: str, content: str) -> str:
    """파일에 내용을 씁니다. 디렉토리가 없으면 생성합니다.

    Args:
        file_path: 쓸 파일의 경로
        content: 파일에 쓸 내용
    """
    try:
        safe_path = get_safe_path(file_path)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_directory(path: str = ".") -> str:
    """디렉토리의 파일 목록을 반환합니다.

    Args:
        path: 디렉토리 경로 (기본값: 현재 디렉토리)
    """
    try:
        safe_path = get_safe_path(path)
        items = os.listdir(safe_path)
        result = []
        for item in sorted(items):
            full_path = os.path.join(safe_path, item)
            if os.path.isdir(full_path):
                result.append(f"[DIR]  {item}/")
            else:
                size = os.path.getsize(full_path)
                result.append(f"[FILE] {item} ({size} bytes)")
        return f"=== Directory: {path} ===\n" + "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def run_python_secure(code: str) -> str:
    """[SECURE] Python 코드를 실행합니다 (Sandboxed).

    주의 사항:
    - 외부 모듈 import 불가 (pip install 불가)
    - 파일 시스템 접근은 제한적
    - 무한 루프 등 파괴적 행위 금지됨

    Args:
        code: 실행할 Python 코드
    """
    # 1. 정적 분석 (AST)
    security_error = is_safe_code(code)
    if security_error:
        return f"🚫 Security Blocked:\n{security_error}"

    # 2. 실행 (Subprocess)
    try:
        result = subprocess.run(
            ["python", "-c", code],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=OllamaConfig.WORKSPACE_DIR,
        )
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"Return code: {result.returncode}"
        return output or "Code executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30s limit)"
    except Exception as e:
        return f"Error executing code: {e}"


@tool
def web_search(query: str) -> str:
    """웹 검색을 수행하여 정보를 찾습니다.

    Args:
        query: 검색어
    """
    try:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"Error searching web: {e}"


@tool
def run_linter(file_path: str = ".") -> str:
    """Ruff를 사용하여 코드 린팅 및 포맷팅 검사를 수행합니다.

    Args:
        file_path: 검사할 파일 또는 디렉토리 경로 (기본값: 현재 디렉토리)
    """
    try:
        safe_path = get_safe_path(file_path)
        # ruff check
        result = subprocess.run(
            ["ruff", "check", safe_path],
            capture_output=True,
            text=True,
            cwd=OllamaConfig.WORKSPACE_DIR,
        )

        output = ""
        if result.returncode == 0:
            output = "✅ Lint check passed!"
        else:
            output = f"⚠️ Lint issues found:\n{result.stdout}"

        return output
    except FileNotFoundError:
        return "Error: 'ruff' is not installed. Please install it first."
    except Exception as e:
        return f"Error running linter: {e}"


# 에이전트별 허용 도구 목록 정의
CODER_TOOLS = [
    file_read,
    file_write,
    list_directory,
    run_python_secure,
    web_search,
    run_linter,
]
REVIEWER_TOOLS = [file_read, run_python_secure, run_linter]
PLANNER_TOOLS = [web_search]  # Planner는 주로 사고를 하지만, 검색 정도는 허용
