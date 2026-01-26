from typing import Dict, List, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from config import AgentConfig, OllamaConfig
from core.llm_factory import get_llm
from core.tool_executor import execute_tools_internal
from utils.json_parser import extract_json


def _prepare_agent_prompt(system_prompt: str, tools: List) -> str:
    """에이전트 시스템 프롬프트 및 도구 설명 구성"""
    tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
    return f"""{AgentConfig.SYSTEM_PROMPT}

## YOU HAVE ACCESS TO THE FOLLOWING TOOLS:
{tools_desc}

## SPECIFIC ROLE INSTRUCTIONS
{system_prompt}

## REMINDER
You MUST format your tool calls as JSON inside ```json ... ``` blocks.
If you are done, output a final explanation.
"""


def _handle_empty_response(messages: List[BaseMessage], name: str):
    """빈 응답 처리"""
    print(f"[{name}] Warning: Empty response received.")
    messages.append(AIMessage(content=""))
    messages.append(
        HumanMessage(
            content="You sent an empty response. Please provide the next step or final answer."
        )
    )


def _handle_tool_execution(
    content: str,
    tool_calls: List[Dict],
    tools_map: Dict,
    messages: List[BaseMessage],
    name: str,
):
    """도구 실행 및 결과 메시지 추가"""
    print(f"[{name}] Detected Tools: {[t.get('name') for t in tool_calls]}")
    tool_output = execute_tools_internal(tool_calls, tools_map)
    print(f"[{name}] Tool Output: {tool_output[:100]}...")

    messages.append(AIMessage(content=content))
    messages.append(SystemMessage(content=f"TOOL OBSERVATION:\n{tool_output}"))


def _handle_potential_tool_failure(
    content: str, messages: List[BaseMessage], name: str
) -> bool:
    """도구 호출 실패(할루시네이션) 감지 및 경고"""
    if "file_write" in content or "run_python" in content:
        print(f"[{name}] Warning: Potential failed tool call detected.")
        messages.append(AIMessage(content=content))
        messages.append(
            SystemMessage(
                content="SYSTEM WARNING: You mentioned a tool name but provided NO valid JSON tool call. \n"
                "You MUST wrap your tool arguments in ```json ... ``` block.\n"
                "Please TRY AGAIN with correct JSON format."
            )
        )
        return True
    return False


def run_react_agent(
    name: str,
    system_prompt: str,
    tools: List,
    history: Sequence[BaseMessage],
    max_iterations: int = OllamaConfig.MAX_ITERATIONS,
) -> str:
    """
    커스텀 ReAct 에이전트 실행 루프 (Refactored).
    [Think -> Tool Call -> Execute -> Observe] 반복.
    """
    print(f"\n[DEBUG] Executing node: {name}")
    try:
        llm = get_llm()
    except Exception as e:
        print(f"[ERROR] Failed to initialize LLM: {e}")
        return f"Error initializing LLM: {e}"

    tools_map = {t.name: t for t in tools}
    loop_system_prompt = _prepare_agent_prompt(system_prompt, tools)
    internal_messages = [SystemMessage(content=loop_system_prompt)] + list(history)

    final_response = ""
    print(f"\n--- [Internal Loop] {name} Started ---")

    for i in range(max_iterations):
        response = llm.invoke(internal_messages)
        content = response.content
        print(f"[{name}] Iteration {i + 1}: {content[:100]}...")

        if not content.strip():
            _handle_empty_response(internal_messages, name)
            continue

        tool_calls = extract_json(content)

        if tool_calls:
            _handle_tool_execution(
                content, tool_calls, tools_map, internal_messages, name
            )
        else:
            if _handle_potential_tool_failure(content, internal_messages, name):
                continue

            # Final Answer
            final_response = content
            break

    if not final_response:
        final_response = (
            "Error: Loop finished without valid final answer. (Empty or Max Iterations)"
        )

    print(f"--- [Internal Loop] {name} Finished ---\n")

    # Planner 강제 완료 시그널
    if name == "Planner" and "PLAN_CREATED" not in final_response:
        final_response += "\nPLAN_CREATED"

    return final_response
