import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, UnprocessableError
from app.integrations.ai.base import AIMessage, AIProvider
from app.integrations.ai.factory import get_ai_provider
from app.models.ai_run import AIRun
from app.models.enums import AgentType, RunStatus
from app.services import ai_runs as ai_run_service
from app.utils.llm_json import coerce_for_schema, extract_json_object

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Rough OpenRouter-compatible estimate when provider does not return cost.
COST_PER_1K_TOKENS = Decimal("0.0005")


class BaseAgent(ABC):
    agent_type: AgentType
    system_prompt: str
    schema_model: type[BaseModel]

    def __init__(self, provider: AIProvider | None = None) -> None:
        self.provider = provider or get_ai_provider()

    @abstractmethod
    def build_user_prompt(self, **kwargs: Any) -> str:
        raise NotImplementedError

    def run(
        self,
        session: Session,
        *,
        project_id: UUID | None,
        content_asset_id: UUID | None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> tuple[BaseModel, AIRun]:
        run = ai_run_service.record_ai_run(
            session,
            project_id=project_id,
            content_asset_id=content_asset_id,
            agent_type=self.agent_type,
            model=getattr(self.provider, "default_model", None) or settings.default_ai_model,
            status=RunStatus.RUNNING,
            input_summary=self._summarize_input(**kwargs),
            started_at=datetime.now(UTC),
        )
        started = time.perf_counter()
        try:
            user_prompt = self.build_user_prompt(**kwargs)
            if len(user_prompt) > settings.ai_max_generation_chars:
                raise UnprocessableError("Input exceeds AI_MAX_GENERATION_CHARS safeguard")
            schema_hint = json.dumps(self.schema_model.model_json_schema(), ensure_ascii=True)
            messages = [
                AIMessage(
                    role="system",
                    content=(
                        f"{self.system_prompt}\n\n"
                        "Return ONLY a JSON object. Use null for unknown scalars, [] for unknown lists, "
                        "and true/false for booleans. Do not wrap the object in markdown.\n"
                        f"JSON SCHEMA:\n{schema_hint}"
                    ),
                ),
                AIMessage(role="user", content=user_prompt),
            ]
            result = self.provider.complete(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format_json=True,
            )
            parsed, validation_error = self._parse_and_validate(result.content)
            if parsed is None:
                repair_messages = messages + [
                    AIMessage(role="assistant", content=self._content_as_text(result.content)),
                    AIMessage(
                        role="user",
                        content=(
                            "Your previous response was invalid for the required schema. "
                            "Return ONLY valid JSON matching the schema exactly. "
                            "Booleans must be true/false/null. Lists must be arrays, never null. "
                            f"Validation error: {validation_error or 'unknown'}"
                        ),
                    ),
                ]
                result = self.provider.complete(
                    repair_messages,
                    temperature=min(temperature or settings.ai_temperature, 0.2),
                    max_tokens=max_tokens,
                    response_format_json=True,
                )
                parsed, validation_error = self._parse_and_validate(result.content)
            if parsed is None:
                logger.warning(
                    "structured_output_invalid",
                    extra={
                        "agent": self.agent_type.value,
                        "validation_error": (validation_error or "")[:300],
                    },
                )
                raise UnprocessableError(
                    "AI returned invalid structured output after retry"
                    + (f": {validation_error}" if validation_error else "")
                )

            elapsed = int((time.perf_counter() - started) * 1000)
            cost = (Decimal(result.total_tokens) / Decimal(1000)) * COST_PER_1K_TOKENS
            run.status = RunStatus.COMPLETED.value
            run.model = result.model
            run.input_tokens = result.input_tokens
            run.output_tokens = result.output_tokens
            run.total_tokens = result.total_tokens
            run.estimated_cost = cost
            run.execution_time_ms = elapsed
            run.output_summary = self._summarize_output(parsed)
            run.completed_at = datetime.now(UTC)
            session.flush()
            return parsed, run
        except Exception as exc:
            elapsed = int((time.perf_counter() - started) * 1000)
            run.status = RunStatus.FAILED.value
            run.execution_time_ms = elapsed
            run.error_message = str(exc)[:500]
            run.completed_at = datetime.now(UTC)
            session.flush()
            if isinstance(exc, (UnprocessableError, ServiceUnavailableError)):
                raise
            raise ServiceUnavailableError(f"{self.agent_type.value} agent failed") from exc

    def _content_as_text(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text") or ""))
                elif isinstance(part, str):
                    parts.append(part)
            return "".join(parts)
        try:
            return json.dumps(content)
        except TypeError:
            return str(content)

    def _parse_and_validate(self, content: Any) -> tuple[BaseModel | None, str | None]:
        text = self._content_as_text(content)
        data = extract_json_object(text)
        if data is None:
            return None, "Response was empty or not valid JSON"
        data = coerce_for_schema(self.schema_model, data)
        try:
            return self.schema_model.model_validate(data), None
        except ValidationError as exc:
            return None, str(exc).replace("\n", " ")[:400]

    def _summarize_input(self, **kwargs: Any) -> str:
        keys = ", ".join(sorted(kwargs.keys()))
        return f"{self.agent_type.value} inputs: {keys}"

    def _summarize_output(self, parsed: BaseModel) -> str:
        return f"{self.agent_type.value} completed ({type(parsed).__name__})"
