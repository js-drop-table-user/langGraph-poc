import ast
import json
import re
from typing import Any, Dict, List


def _extract_from_code_blocks(text: str) -> List[Dict[str, Any]]:
    """```json ... ``` 패턴에서 JSON을 추출합니다."""
    blocks = []
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        try:
            clean_json = match.strip()
            # Common fix: cleanup trailing commas which LLMs often add
            clean_json = re.sub(r",\s*([\]}])", r"\1", clean_json)
            data = json.loads(clean_json)
            if isinstance(data, (dict, list)):
                blocks.append(data) if isinstance(data, dict) else blocks.extend(data)
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(clean_json)
                if isinstance(data, (dict, list)):
                    blocks.append(data) if isinstance(data, dict) else blocks.extend(
                        data
                    )
            except Exception:
                pass
    return blocks


def _extract_from_text_fallback(text: str) -> List[Dict[str, Any]]:
    """코드 블록이 없을 때 텍스트 전반에서 {} 패턴을 찾아 추출합니다."""
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            sub = text[start : end + 1]
            sub = re.sub(r",\s*([\]}])", r"\1", sub)
            try:
                data = json.loads(sub)
            except Exception:
                data = ast.literal_eval(sub)

            if isinstance(data, dict):
                return [data]
    except Exception:
        pass
    return []


def extract_json(text: str) -> List[Dict[str, Any]]:
    """텍스트에서 JSON 블록을 추출합니다. (Modular & Robust Version)"""
    json_blocks = _extract_from_code_blocks(text)

    if not json_blocks:
        json_blocks = _extract_from_text_fallback(text)

    return json_blocks
