from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

from core.agent_runtime import run_react_agent
from core.security import is_safe_code


# =============================================================================
# 1. Security Analyzer Tests
# =============================================================================
class TestSecurityAnalyzer:
    """core.security 모듈 테스트"""

    def test_hp_01_safe_code(self):
        """[HP-01] 정상적인 안전한 코드는 통과해야 함"""
        safe_code = "a = 1 + 1\nprint(a)"
        assert is_safe_code(safe_code) is None

    def test_edge_01_blocked_import(self):
        """[EDGE-01] 차단된 모듈(os.path) 임포트 시 차단"""
        code = "import os.path\nprint('hack')"
        result = is_safe_code(code)
        assert result is not None
        assert (
            "Security: Import of 'os' is restricted" in result
            or "Security Violation" in result
        )

    def test_edge_02_blocked_function(self):
        """[EDGE-02] 차단된 함수(eval) 사용 시 차단"""
        code = "eval('2 + 2')"
        result = is_safe_code(code)
        assert result is not None
        assert "Function 'eval' is blocked" in result

    def test_chaos_01_complex_obfuscation(self):
        """[CHAOS-01] 복합적인 위험 구문 차단 시도"""
        # __import__ 사용
        code = "__import__('subprocess').run(['ls'])"
        result = is_safe_code(code)
        assert result is not None
        assert "Function '__import__' is blocked" in result


# =============================================================================
# 2. Agent Runtime Tests
# =============================================================================
@tool
def dummy_tool(arg: str) -> str:
    """테스트용 더미 도구"""
    return f"Processed: {arg}"


@pytest.fixture
def mock_llm():
    with patch("core.agent_runtime.get_llm") as mock:
        yield mock


class TestAgentRuntime:
    """core.agent_runtime 모듈 테스트"""

    def test_hp_01_happy_path(self, mock_llm):
        """[HP-01] Think -> Tool Call -> Final Answer 정상 흐름"""
        # Mock LLM Responses:
        # 1. Tool Call
        # 2. Final Answer
        mock_llm.return_value.invoke.side_effect = [
            AIMessage(
                content='Thinking...\n```json\n[{"name": "dummy_tool", "arguments": {"arg": "test"}}]\n```'
            ),
            AIMessage(content="Final Answer: Done."),
        ]

        history = [HumanMessage(content="Do something")]
        response = run_react_agent(
            "Tester", "Prompt", [dummy_tool], history, max_iterations=2
        )

        assert "Final Answer: Done." in response
        # LLM이 2번 호출되었는지 확인 (Tool Call -> Final)
        assert mock_llm.return_value.invoke.call_count == 2

    def test_edge_01_empty_response_retry(self, mock_llm):
        """[EDGE-01] 빈 응답 시 재시도 로직 동작 확인"""
        # 1. Empty -> 2. Final Answer
        mock_llm.return_value.invoke.side_effect = [
            AIMessage(content=""),  # Empty
            AIMessage(content="Final Answer: Recovered."),
        ]

        history = [HumanMessage(content="Start")]
        response = run_react_agent("Tester", "Prompt", [], history, max_iterations=3)

        assert "Final Answer: Recovered." in response
        # 빈 응답 처리 로직이 실행되었음을 간접 확인 (호출 횟수 2회)
        assert mock_llm.return_value.invoke.call_count == 2

    def test_edge_02_tool_hallucination_warning(self, mock_llm):
        """[EDGE-02] JSON 없이 도구 이름만 언급 시 경고 메시지 주입 확인"""
        # 1. Hallucination ("I will use file_write...") -> 2. Correct JSON -> 3. Final
        mock_llm.return_value.invoke.side_effect = [
            AIMessage(
                content="I will use run_python to do this."
            ),  # No JSON code block
            AIMessage(
                content='```json\n[{"name": "dummy_tool", "arguments": {"arg": "retry"}}]\n```'
            ),
            AIMessage(content="Done."),
        ]

        history = [HumanMessage(content="Start")]
        response = run_react_agent(
            "Tester", "Prompt", [dummy_tool], history, max_iterations=5
        )

        assert "Done." in response
        # 호출 횟수 3회 (Warning -> Retry -> Final)
        assert mock_llm.return_value.invoke.call_count == 3
