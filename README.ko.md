<div align="center">

# 🤖 LangGraph Coding Agent (PoC)

**로컬 LLM으로 안전하고 강력하게 동작하는 자율 코딩 에이전트**
*Reasoning, Coding, Verification on your Local Machine*

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange?logo=ollama&logoColor=white)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[English README](./README.md)

</div>

---

## 💡 소개 (Elevator Pitch)

**LangGraph-PoC**는 **LangGraph**와 **Ollama**를 결합하여, 로컬 환경에서 **기획(Planner) → 구현(Coder) → 검증(Reviewer)** 프로세스를 자율적으로 수행하는 AI 에이전트 시스템입니다.

클라우드 API 비용이나 데이터 유출 걱정 없이, 오직 당신의 로컬 컴퓨터 자원만으로 복잡한 코딩 작업을 수행합니다. 최근 업데이트된 **Robust JSON Strategy**를 통해 LLM의 불완전한 출력을 자동으로 보정하며, 엄격한 워크플로우 통제로 환각(Hallucination)을 최소화했습니다.

---

## ✨ 주요 기능 (Key Features)

- 🧠 **Supervisor 아키텍처**: 관리자(Supervisor)가 Planner, Coder, Reviewer 에이전트를 적재적소에 배치하여 체계적으로 협업합니다.
- 🛡️ **Robust JSON Parsing**: LLM이 JSON 형식을 틀리거나 텍스트를 섞어 보내도, 하이브리드 파싱 알고리즘이 도구 호출을 정확하게 추출합니다.
- 🔒 **Secure Workspace**: 모든 파일 작업은 `workspace/` 디렉토리 내로 엄격하게 제한되며, 상위 경로 접근 시도를 차단합니다.
- 🔄 **Self-Correction (자가 수정)**: 코드 실행 중 에러가 발생하면, 에이전트가 이를 인지하고 스스로 코드를 수정하여 재시도합니다.
- 🧹 **Auto-Cleanup**: 테스트 및 검증 과정에서 생성된 임시 DB와 파일들을 작업 완료 후 자동으로 정리합니다.

---

## 📦 설치 (Installation)

이 프로젝트는 최신 Python 패키지 매니저인 **uv** 사용을 권장합니다.

### 1. Ollama 설치 및 모델 준비
[Ollama](https://ollama.ai)를 설치하고, 코딩에 최적화된 모델을 다운로드합니다.

```bash
# 추천 모델: Qwen 2.5 Coder (14B 이상 권장)
ollama pull qwen2.5-coder:14b
```

### 2. 프로젝트 클론 및 의존성 설치

```bash
git clone https://github.com/js-drop-table-user/langGraph-poc.git
cd langGraph-poc

# 의존성 설치 (가상환경 자동 생성)
uv sync
```

### 3. 환경 설정 (.env)

```bash
cp .env.example .env
# .env 파일을 열어 OLLAMA_MODEL 등을 수정하세요.
# 예: OLLAMA_MODEL=qwen2.5-coder:14b
```

---

## 🚀 사용법 (Usage)

에이전트를 실행하고 원하는 작업을 자연어로 요청하세요.

```bash
uv run coding_agent.py
```

### 실행 예시

```text
Type your request (or 'quit'):

You: 피즈버즈 게임을 파이썬으로 만들어줘.

> [Supervisor]: Planner...

[Planner]: 피즈버즈 구현 계획을 수립합니다... (PLAN_CREATED)

> [Supervisor]: Coder...

[Coder]: 계획에 따라 workspace/fizzbuzz.py 파일을 작성합니다...
(Tool Call: file_write)

> [Supervisor]: Reviewer...

[Reviewer]: 코드를 실행하여 1부터 15까지 출력을 검증합니다...
(Tool Call: run_python_secure)
✅ Approved.

> [Supervisor]: FINISH
```

---

## 🛠️ 기술 스택 (Tech Stack)

- **Core**: [Python 3.9+](https://python.org)
- **Agent Framework**: [LangGraph](https://langchain-ai.github.io/langgraph/), [LangChain](https://www.langchain.com/)
- **LLM Runtime**: [Ollama](https://ollama.ai/)
- **Code Quality**: [Ruff](https://docs.astral.sh/ruff/) (Linter)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

---

## 🤝 기여 (Contributing)

이 프로젝트는 현재 PoC(개념 증명) 단계입니다. 버그 리포트나 기능 제안은 언제나 환영합니다!

1. Issue를 생성하여 논의합니다.
2. PR(Pull Request)을 보냅니다.

---

## 📄 라이선스

MIT License © 2024
