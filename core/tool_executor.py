from typing import Dict, List


def execute_tools_internal(tool_calls: List[Dict], tools_map: Dict) -> str:
    """도구 호출 목록을 실행하고 결과를 문자열로 반환"""
    results = []
    for call in tool_calls:
        name = call.get("name")
        args = call.get("arguments", {})

        if name in tools_map:
            try:
                # invoke wrapper
                tool_instance = tools_map[name]
                # Tool의 args 스키마에 맞춰 호출
                output = tool_instance.invoke(args)
                results.append(f"Tool '{name}' Output: {output}")
            except Exception as e:
                results.append(f"Tool '{name}' Error: {e}")
        else:
            results.append(f"Error: Tool '{name}' not found.")

    return "\n".join(results)
