import shutil
import tempfile
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_workspace():
    """테스트용 임시 워크스페이스 디렉리 생성 및 제거"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ollama_config(temp_workspace):
    """임시 워크스페이스를 사용하는 OllamaConfig 모킹"""
    from config import OllamaConfig

    original_workspace = OllamaConfig.WORKSPACE_DIR
    OllamaConfig.WORKSPACE_DIR = temp_workspace
    yield OllamaConfig
    OllamaConfig.WORKSPACE_DIR = original_workspace


@pytest.fixture
def mock_chat_ollama():
    """ChatOllama 인스턴스 모킹"""
    with MagicMock() as mock:
        yield mock
