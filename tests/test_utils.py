from utils.json_parser import extract_json


def test_extract_json_standard():
    """표준 JSON 블록 추출 테스트"""
    text = """
    Here is the plan:
    ```json
    {"name": "test", "arguments": {"a": 1}}
    ```
    """
    result = extract_json(text)
    assert len(result) == 1
    assert result[0]["name"] == "test"


def test_extract_json_multiple():
    """여러 개의 JSON 블록 추출 테스트"""
    text = """
    First tool:
    ```json
    {"name": "tool1"}
    ```
    Second tool:
    ```json
    {"name": "tool2"}
    ```
    """
    result = extract_json(text)
    assert len(result) == 2
    assert result[0]["name"] == "tool1"
    assert result[1]["name"] == "tool2"


def test_extract_json_fallback():
    """코드 블록이 없을 때 {} 패턴 추출 테스트"""
    text = 'Just a raw json: {"name": "raw"}'
    result = extract_json(text)
    assert len(result) == 1
    assert result[0]["name"] == "raw"


def test_extract_json_with_trailing_commas():
    """Trailing comma가 포함된 잘못된 JSON 처리 테스트"""
    text = """
    ```json
    {
        "name": "test",
        "args": [1, 2, ],
    }
    ```
    """
    result = extract_json(text)
    assert len(result) == 1
    assert result[0]["name"] == "test"
