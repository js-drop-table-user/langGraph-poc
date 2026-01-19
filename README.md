# 🤖 LangGraph Coding Agent

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**로컬 LLM으로 파일을 읽고, 코드를 작성하고, 실행까지 하는 AI 코딩 에이전트**

> 💡 클라우드 API 없이 **내 컴퓨터**에서 동작하는 코딩 어시스턴트

---

## ✨ 주요 기능

- � **작업 폴더 분리**: 모든 파일 작업은 `workspace/` 폴더 내부에서 수행
- 🔄 **실시간 스트리밍**: 에이전트의 생각과 도구 실행 결과를 즉시 확인
- 🛠️ **4가지 도구**: 파일 읽기/쓰기, 디렉토리 조회, Python 코드 실행
- 🏠 **100% 로컬**: Ollama 기반으로 인터넷 연결 없이 동작
- 🔁 **반복 실행**: 에러 발생 시 재시도 가능 (모델 성능에 따라 다름)

---

## 📦 설치

### 1. Ollama 설치 및 모델 다운로드

```bash
# Ollama 설치: https://ollama.ai
# 도구 호출을 지원하는 모델 다운로드
ollama pull devstral-small-2
```

### 2. 프로젝트 설치

```bash
git clone https://github.com/js-drop-table-user/langGraph-poc.git
cd langGraph-poc

# uv 사용 (권장)
uv sync

# 또는 pip 사용
pip install -e .
```

### 3. 환경 설정 (선택사항)

```bash
cp .env.example .env
# .env 파일에서 모델명, Ollama URL 등 수정
```

---

## 🚀 사용법

```bash
uv run python coding_agent.py
```

### 예시 대화

```
============================================================
🤖 Ollama Coding Agent
============================================================
Model: devstral-small-2
Workspace: ./workspace
------------------------------------------------------------

You: 피즈버즈 앱을 만들어줘

----------------------------------------
Agent:
Tool Call: file_write ({'file_path': 'fizzbuzz.py', ...})

Tool Output: Successfully wrote 643 bytes to fizzbuzz.py

Agent:
Tool Call: run_python ({'code': 'exec(open("fizzbuzz.py").read())'})

Tool Output: STDOUT:
1
2
Fizz
4
Buzz
...

Agent: 피즈버즈 앱을 성공적으로 생성하고 테스트했습니다!
----------------------------------------
```

---

## 📁 프로젝트 구조

```
langGraph-poc/
├── coding_agent.py       # 메인 에이전트 코드
├── config.py             # 설정 (모델, URL, 프롬프트)
├── workspace/            # 에이전트 작업 폴더
├── pyproject.toml        # 의존성 설정
├── .env.example          # 환경변수 템플릿
├── .gitignore
└── LICENSE
```

---

## 🛠️ 사용 가능한 도구

| 도구             | 설명               |
| ---------------- | ------------------ |
| `file_read`      | 파일 내용 읽기     |
| `file_write`     | 파일 생성/수정     |
| `list_directory` | 디렉토리 목록 조회 |
| `run_python`     | Python 코드 실행   |

> 📌 기본적으로 모든 파일 작업은 `workspace/` 폴더 내부에서 수행됩니다

---

## ⚙️ 설정

### config.py

```python
class OllamaConfig:
    BASE_URL = "http://localhost:11434"  # Ollama 서버
    DEFAULT_MODEL = "devstral-small-2"   # 모델명
    TEMPERATURE = 0.0                     # 일관성
    MAX_ITERATIONS = 10                   # 최대 도구 호출 횟수
    WORKSPACE_DIR = "./workspace"         # 작업 폴더
```

### 모델 선택 가이드

| 모델               | 도구 호출 | 추천 용도       |
| ------------------ | --------- | --------------- |
| `devstral-small-2` | ✅ 지원   | 에이전트 (추천) |
| `qwen2.5-coder`    | ❌ 불안정 | 코드 생성     |

---

## 🔧 확장하기

### 새 도구 추가

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """웹에서 정보를 검색합니다."""
    # 구현
    return result

# TOOLS 리스트에 추가
TOOLS = [..., search_web]
```

---

## ⚠️ 주의사항

- **경로 제한**: `../` 등으로 상위 폴더 접근 시 에러 발생
- **타임아웃**: Python 코드 실행은 30초로 제한
- **격리 없음**: Docker 등의 실제 격리 환경이 아니므로 신뢰할 수 없는 코드 실행에 주의

---

## 📚 기술 스택

- **LangGraph** - 상태 기반 에이전트 워크플로우
- **LangChain** - LLM 도구 바인딩
- **Ollama** - 로컬 LLM 서버

---

## 📄 라이선스

MIT License
