"""
Ollama 기반 코딩 에이전트
LangGraph + Ollama LLM을 사용한 코드 수정/앱 빌딩 에이전트
"""

import os
import subprocess
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from config import AgentConfig, OllamaConfig


# =============================================================================
# State 정의
# =============================================================================
class AgentState(TypedDict):
    """에이전트 상태"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration_count: int


# =============================================================================
# 도구 정의
# =============================================================================
def get_safe_path(path: str) -> str:
    """워크스페이스 내부로 경로 제한 및 절대 경로 변환"""
    # 상대 경로를 절대 경로로 변환
    if not os.path.isabs(path):
        path = os.path.join(OllamaConfig.WORKSPACE_DIR, path)

    # 경로 정규화 (../ 제거)
    path = os.path.normpath(path)

    # 워크스페이스 내부에 있는지 확인 (보안)
    if not path.startswith(os.path.normpath(OllamaConfig.WORKSPACE_DIR)):
        raise ValueError(
            f"Access denied: Path must be within {OllamaConfig.WORKSPACE_DIR}"
        )

    return path


@tool
def file_read(file_path: str) -> str:
    """파일의 내용을 읽습니다.

    Args:
        file_path: 읽을 파일의 경로
    """
    try:
        safe_path = get_safe_path(file_path)
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
def run_python(code: str) -> str:
    """Python 코드를 실행합니다.

    주의: 쉘 명령어(예: 'python file.py')를 입력하면 안 됩니다.
    순수 Python 코드만 입력하세요.

    파일을 실행하려면 다음 패턴을 사용하세요:
    import sys; sys.argv=['filename.py']; exec(open('filename.py').read())

    Args:
        code: 실행할 Python 코드
    """
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


# 도구 목록
TOOLS = [file_read, file_write, list_directory, run_python]


# =============================================================================
# LLM 설정
# =============================================================================
def get_llm():
    """Ollama LLM 인스턴스 생성"""
    llm = ChatOllama(
        model=OllamaConfig.DEFAULT_MODEL,
        temperature=OllamaConfig.TEMPERATURE,
        base_url=OllamaConfig.BASE_URL,
    )
    return llm.bind_tools(TOOLS)


# =============================================================================
# 그래프 노드
# =============================================================================
def agent_node(state: AgentState) -> dict:
    """에이전트가 메시지를 처리하고 응답 생성"""
    llm = get_llm()

    # 시스템 프롬프트 추가 (첫 번째 메시지가 아닌 경우에만)
    messages = list(state["messages"])
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=AgentConfig.SYSTEM_PROMPT)] + messages

    response = llm.invoke(messages)
    return {
        "messages": [response],
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def should_continue(state: AgentState) -> str:
    """도구 호출이 필요한지 또는 종료할지 판단"""
    # 최대 반복 횟수 체크
    if state.get("iteration_count", 0) >= OllamaConfig.MAX_ITERATIONS:
        return END

    last_message = state["messages"][-1]

    # 도구 호출이 있으면 tools 노드로
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END


# =============================================================================
# 그래프 구성
# =============================================================================
def create_agent_graph():
    """코딩 에이전트 그래프 생성"""
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(TOOLS))

    # 엣지 추가
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# =============================================================================
# 메인 실행
# =============================================================================
def main():
    """대화형 코딩 에이전트 실행"""
    # 워크스페이스 생성
    os.makedirs(OllamaConfig.WORKSPACE_DIR, exist_ok=True)

    print("=" * 60)
    print("🤖 Ollama Coding Agent")
    print("=" * 60)
    print(f"Model: {OllamaConfig.DEFAULT_MODEL}")
    print(f"Ollama URL: {OllamaConfig.BASE_URL}")
    print(f"Workspace: {OllamaConfig.WORKSPACE_DIR}")
    print("-" * 60)
    print("Type your request (or 'quit' to exit):\n")

    agent = create_agent_graph()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye! 👋")
                break

            # 에이전트 실행 (Stream)
            print("\n" + "-" * 40)
            
            # 초기 입력 상태
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "iteration_count": 0,
            }

            # 스트리밍 실행
            for event in agent.stream(initial_state):
                for node_name, node_data in event.items():
                    if "messages" in node_data:
                        last_message = node_data["messages"][-1]
                        
                        # 에이전트 메시지 출력
                        if node_name == "agent":
                             print(f"\nAgent: {last_message.content}")
                             if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                                 for tool_call in last_message.tool_calls:
                                     print(f"Tool Call: {tool_call['name']} ({tool_call['args']})")
                        
                        # 도구 출력
                        elif node_name == "tools":
                            for msg in node_data["messages"]:
                                print(f"\nTool Output: {msg.content}")

            print("-" * 40 + "\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
