from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIMessage:
    role: str
    content: str


@dataclass
class AICompletionResult:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Provider-independent chat completion interface."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format_json: bool = True,
    ) -> AICompletionResult:
        raise NotImplementedError
