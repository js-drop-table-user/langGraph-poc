import ast
from typing import Optional


class SecurityAnalyzer(ast.NodeVisitor):
    """Python AST 기반 보안 분석기"""

    # 차단된 모듈 및 위험한 함수 정의
    BLOCKED_MODULES = {
        "shutil",
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "os",  # os 전체 차단
        "sys",
        "pathlib",
    }

    BLOCKED_FUNCTIONS = {
        "exec",
        "eval",
        "__import__",
        "input",
        "exit",
        "quit",
        "compile",
        "open",  # open은 별도 도구를 통해서만 허용
    }

    def __init__(self):
        self.errors = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            # Check full module name and base module
            module_name = alias.name
            base_module = module_name.split(".")[0]

            if (
                module_name in self.BLOCKED_MODULES
                or base_module in self.BLOCKED_MODULES
            ):
                self.errors.append(
                    f"Security: Import of '{module_name}' is restricted."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module in self.BLOCKED_MODULES:
                self.errors.append(
                    f"Security: Import from '{base_module}' is restricted."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BLOCKED_FUNCTIONS:
                self.errors.append(f"Security: Function '{node.func.id}' is blocked.")
        # 속성 접근을 통한 우회 방지 (예: os.system)
        elif isinstance(node.func, ast.Attribute):
            # 기본적으로 모든 외부 속성 호출을 허용하되, 위험한 모듈의 메소드 호출인지 확인하는 로직은
            # 타입 추론이 없으면 어렵습니다.
            # 여기서는 명백히 위험한 패턴만 추가할 수 있습니다.
            pass

        self.generic_visit(node)


def is_safe_code(code: str) -> Optional[str]:
    """코드가 안전한지 검사합니다. 안전하면 None, 위험하면 에러 메시지 반환."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax Error during security check: {e}"

    analyzer = SecurityAnalyzer()
    analyzer.visit(tree)

    if analyzer.errors:
        return "Security Violation:\n" + "\n".join(analyzer.errors)
    return None
