"""
멀티 에이전트 코딩 시스템 (Supervisor Pattern + Custom ReAct Loop)
LangGraph + Ollama + Tools + Persistence
Refactored to Standard LangGraph Structure & Modular Runtime
"""

import functools
import os
import re
from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages

from config import AgentConfig, OllamaConfig
from core.agent_runtime import run_react_agent
from core.llm_factory import get_llm
from tools import CODER_TOOLS, PLANNER_TOOLS, REVIEWER_TOOLS

# SQLite DB 경로
DB_PATH = os.path.join(OllamaConfig.WORKSPACE_DIR, "agent_memory.sqlite")


# =============================================================================
# State 정의
# =============================================================================
class AgentState(TypedDict):
    """멀티 에이전트 통합 상태"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str  # 다음에 실행할 에이전트 이름


# =============================================================================
# Custom Agent Node (Internal ReAct Loop)
# =============================================================================
def custom_agent_node(state: AgentState, name: str, system_prompt: str, tools: List):
    """
    커스텀 에이전트 노드 Wrapper.
    Core Runtime을 호출하고 결과를 Graph State 형식으로 변환합니다.
    """
    history = state["messages"]

    # Core Runtime 실행 (Modularized)
    final_response = run_react_agent(name, system_prompt, tools, history)

    # 결과 반환 (HumanMessage로 포장하여 Supervisor에게 전달)
    return {"messages": [HumanMessage(content=final_response, name=name)]}


# =============================================================================
# Supervisor (Orchestrator)
# =============================================================================
def supervisor_node(state: AgentState):
    """Supervisor logic: 다음 에이전트를 결정"""
    llm = get_llm()
    conf = AgentConfig.SUPERVISOR_CONFIG

    # 프롬프트 구성
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", conf["prompt"]),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next? "
                "Select one of: {options}. "
                "Return ONLY the name of the next worker, or 'FINISH' if done.",
            ),
        ]
    ).partial(options=str(conf["options"]), members=", ".join(conf["members"]))

    chain = prompt | llm
    response = chain.invoke(state)
    decision = response.content.strip()

    # 정규식 기반 매칭 (견고성 강화)
    next_agent = "FINISH"  # Default fallback
    found_agents = []

    for option in conf["options"]:
        # 단어 경계(\b)를 사용하여 정확한 매칭 (Case-insensitive)
        if re.search(rf"\b{option}\b", decision, re.IGNORECASE):
            found_agents.append(option)

    # 여러 개가 매칭되면 가장 마지막에 언급된 것, 혹은 명시적 우선순위 적용
    # 여기서는 발견된 것 중 마지막 옵션을 선택 (문장 끝에 보통 결론이 오므로)
    if found_agents:
        next_agent = found_agents[-1]

    print(f"[Supervisor] Raw: {decision!r} -> Next: {next_agent}")

    return {
        "messages": [AIMessage(content=decision, name="Supervisor")],
        "next": next_agent,
    }


# =============================================================================
# Graph Construction
# =============================================================================
def create_graph():
    workflow = StateGraph(AgentState)

    # Supervisor Node
    workflow.add_node("Supervisor", supervisor_node)

    # Worker Nodes Check
    agents = [
        ("Planner", PLANNER_TOOLS, AgentConfig.PROMPTS["Planner"]),
        ("Coder", CODER_TOOLS, AgentConfig.PROMPTS["Coder"]),
        ("Reviewer", REVIEWER_TOOLS, AgentConfig.PROMPTS["Reviewer"]),
    ]

    for name, tools, prompt in agents:
        workflow.add_node(
            name,
            functools.partial(
                custom_agent_node, name=name, system_prompt=prompt, tools=tools
            ),
        )
        # 모든 Worker는 작업 후 Supervisor로 복귀
        workflow.add_edge(name, "Supervisor")

    # Start Edge
    workflow.add_edge(START, "Supervisor")

    # Conditional Edges from Supervisor
    # map: next_agent 이름 그대로 노드로 이동. FINISH면 종료.
    workflow.add_conditional_edges("Supervisor", lambda x: x["next"])

    return workflow


# =============================================================================
# Main
# =============================================================================
def main():
    print("=" * 60)
    print("🤖 Multi-Agent System (Standardized LangGraph v2)")
    print("=" * 60)

    workflow = create_graph()

    # DB 연결 (없으면 자동 생성)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with SqliteSaver.from_conn_string(DB_PATH) as memory:
        graph = workflow.compile(checkpointer=memory)
        config = {"configurable": {"thread_id": "standard_loop_1"}}

        print("Type your request (or 'quit'):\n")
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ("q", "quit", "exit"):
                    break
                if not user_input:
                    continue

                for event in graph.stream(
                    {"messages": [HumanMessage(content=user_input)]}, config=config
                ):
                    for node, values in event.items():
                        # Supervisor decision or Agent Final Output
                        if "messages" in values:
                            msg = values["messages"][-1]
                            sender = msg.name if hasattr(msg, "name") else node
                            print(f"\n> [{sender}]: {msg.content[:300]}...")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
