import os

from tools import file_read, file_write, is_safe_code, list_directory


def test_file_write_read(mock_ollama_config):
    """파일 쓰기 및 읽기 기능 검증"""
    test_file = "test.txt"
    test_content = "Hello, Pytest!"

    # Write
    write_result = file_write.invoke({"file_path": test_file, "content": test_content})
    assert "Successfully wrote" in write_result

    # Read
    read_result = file_read.invoke({"file_path": test_file})
    assert test_content in read_result


def test_list_directory(mock_ollama_config):
    """디렉토리 목록 조회 검증"""
    os.makedirs(os.path.join(mock_ollama_config.WORKSPACE_DIR, "subdir"), exist_ok=True)
    with open(os.path.join(mock_ollama_config.WORKSPACE_DIR, "file1.txt"), "w") as f:
        f.write("test")

    result = list_directory.invoke({"path": "."})
    assert "[DIR]  subdir/" in result
    assert "[FILE] file1.txt" in result


def test_security_analyzer():
    """보안 분석기(AST) 검증"""
    # Safe code
    assert is_safe_code("print('hello')") is None

    # Unsafe code (import blocked module)
    unsafe_code = "import subprocess\nsubprocess.run(['ls'])"
    assert "Security Violation" in is_safe_code(unsafe_code)

    # Unsafe code (blocked function)
    assert "Security Violation" in is_safe_code("eval('1+1')")
