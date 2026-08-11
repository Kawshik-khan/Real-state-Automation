from dataclasses import dataclass
from typing import Any, Callable


class ToolPolicyError(Exception):
    pass


@dataclass(frozen=True)
class ToolRegistration:
    name: str
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    roles: frozenset[str]
    side_effect: bool
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolGateway:
    def __init__(self) -> None:
        self._tools: dict[str, ToolRegistration] = {}

    def register(self, tool: ToolRegistration) -> None:
        self._tools[tool.name] = tool

    def execute(self, name: str, arguments: dict[str, Any], roles: frozenset[str], confirmed: bool = False) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolPolicyError("TOOL_NOT_FOUND")
        if not tool.roles.intersection(roles):
            raise ToolPolicyError("TOOL_UNAUTHORIZED")
        if tool.side_effect and not confirmed:
            raise ToolPolicyError("CONFIRMATION_REQUIRED")
        required = tool.input_schema.get("required", [])
        missing = [field for field in required if field not in arguments]
        if missing:
            raise ToolPolicyError(f"TOOL_INPUT_INVALID:{','.join(missing)}")
        return tool.handler(arguments)