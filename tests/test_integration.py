from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver

# Import system components
from coding_agent import create_graph


class FakeResponder:
    """RunnableLambda로 래핑될 가짜 응답기 (Stateful)"""

    def __init__(self, responses):
        self.responses = responses
        self.idx = 0

    def __call__(self, input):
        if self.idx < len(self.responses):
            result = self.responses[self.idx]
            self.idx += 1
            return result
        return self.responses[-1]


class TestIntegrationWorkflow:
    """통합 테스트: 전체 에이전트 워크플로우 검증"""

    def test_full_workflow_happy_path(self):
        """
        [HP-01] 전체 워크플로우 정상 동작 검증
        Flow: START -> Supervisor -> Planner -> Supervisor -> Coder -> Supervisor -> Reviewer -> Supervisor -> END
        """

        # 시나리오별 LLM 응답 정의
        responses = [
            # 1. Supervisor (User input -> Planner)
            AIMessage(content="Planner"),
            # 2. Planner (Thinking -> Execution -> Final Answer)
            AIMessage(content="I will create a plan.\nPLAN_CREATED"),
            # 3. Supervisor (Plan created -> Coder)
            AIMessage(content="Coder"),
            # 4. Coder (Working...)
            AIMessage(
                content='Thinking...\n```json\n[{"name": "file_write", "arguments": {"file_path": "hello.py", "content": "print(1)"}}]\n```'
            ),
            AIMessage(content="Code written successfully."),
            # 5. Supervisor (Code done -> Reviewer)
            AIMessage(content="Reviewer"),
            # 6. Reviewer (Lint & Test)
            AIMessage(
                content='Thinking...\n```json\n[{"name": "run_linter", "arguments": {}}]\n```'
            ),
            AIMessage(content="Approved"),
            # 7. Supervisor (Approved -> FINISH)
            AIMessage(content="FINISH"),
        ]

        # RunnableLambda로 감싸서 Chain과 호환되도록 만듦
        responder = FakeResponder(responses)
        fake_llm = RunnableLambda(responder)

        # Patch get_llm to return our fake_llm
        # We need to patch where it is used.
        with (
            patch("coding_agent.get_llm", return_value=fake_llm),
            patch("core.agent_runtime.get_llm", return_value=fake_llm),
        ):
            # 그래프 생성 (In-Memory Checkpointer 사용)
            workflow = create_graph()
            memory = MemorySaver()
            app = workflow.compile(checkpointer=memory)

            config = {"configurable": {"thread_id": "test_thread"}}
            inputs = {"messages": [HumanMessage(content="Make a hello world script")]}

            # 실행 및 노드 방문 기록
            visited_nodes = []

            # stream 모드로 실행
            # 주의: 무한 루프 방지를 위해 recursion_limit 설정
            for event in app.stream(inputs, config=config, stream_mode="updates"):
                for node_name, _ in event.items():
                    visited_nodes.append(node_name)

            # 검증
            print(f"Visited Nodes: {visited_nodes}")

            # Supervisor가 최소 4번 동작해야 함
            assert visited_nodes.count("Supervisor") >= 4
            assert "Planner" in visited_nodes
            assert "Coder" in visited_nodes
            assert "Reviewer" in visited_nodes
