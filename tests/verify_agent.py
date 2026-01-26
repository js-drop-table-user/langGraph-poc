import os
import sys

# 프로젝트 루트를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from coding_agent import create_graph
from config import OllamaConfig


def test_agent_flow():
    print(">>> Starting Verification Test")

    # DB 초기화 (테스트용)
    db_path = os.path.join(OllamaConfig.WORKSPACE_DIR, "test_memory.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    app = create_graph()

    with SqliteSaver.from_conn_string(db_path) as memory:
        graph = app.compile(checkpointer=memory)
        config = {"configurable": {"thread_id": "test_thread_1"}}

        # 간단한 요청
        user_input = "Create a hello_world.py that prints 'Hello Verified World'"
        print(f"User: {user_input}")

        step_count = 0
        max_steps = 20

        try:
            for event in graph.stream(
                {"messages": [HumanMessage(content=user_input)]}, config=config
            ):
                step_count += 1
                for node, values in event.items():
                    if "messages" in values:
                        msg = values["messages"][-1]
                        sender = msg.name if hasattr(msg, "name") else node
                        print(f"\n[{sender}]: {msg.content[:100]}...")

                        # Reviewer 승인 확인
                        if sender == "Reviewer" and "Approved" in msg.content:
                            print("\n>>> Reviewer Approved detected!")

                    # Supervisor Decision
                    if node == "Supervisor":
                        print(f"\n[Supervisor Decision]: Next -> {values.get('next')}")
                        if values.get("next") == "FINISH":
                            print("\n>>> FINISH detected! Test Passed.")
                            return

                if step_count >= max_steps:
                    print("\n>>> Test Failed: Max steps reached without FINISH.")
                    return

        except Exception as e:
            print(f"\n>>> Test Error: {e}")


if __name__ == "__main__":
    test_agent_flow()
