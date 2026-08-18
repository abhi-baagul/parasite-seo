from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps_pagination import PaginationParams
from app.core.exceptions import NotFoundError
from app.models.ai_run import AIRun
from app.models.enums import AgentType, RunStatus
from app.models.user import User
from app.schemas.resources import AIRunRead
from app.services.ownership import get_owned_content, get_owned_project, owned_project_ids


def list_ai_runs(
    session: Session,
    user: User,
    pagination: PaginationParams,
    *,
    project_id: UUID | None = None,
) -> tuple[list[AIRunRead], int]:
    if project_id:
        get_owned_project(session, user, project_id)
        filters = [AIRun.project_id == project_id]
    else:
        ids = owned_project_ids(session, user)
        filters = [AIRun.project_id.in_(ids)] if ids else [AIRun.project_id.is_(None)]
    total = session.scalar(select(func.count()).select_from(AIRun).where(*filters)) or 0
    stmt = (
        select(AIRun)
        .where(*filters)
        .order_by(AIRun.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return [_to_read(row) for row in session.scalars(stmt)], total


def get_ai_run(session: Session, user: User, run_id: UUID) -> AIRunRead:
    run = session.get(AIRun, run_id)
    if not run:
        raise NotFoundError("AI run not found")
    if run.project_id:
        get_owned_project(session, user, run.project_id)
    elif run.content_asset_id:
        get_owned_content(session, user, run.content_asset_id)
    else:
        raise NotFoundError("AI run not found")
    return _to_read(run)


def record_ai_run(
    session: Session,
    *,
    project_id: UUID | None,
    content_asset_id: UUID | None,
    agent_type: AgentType | str,
    model: str | None = None,
    status: RunStatus | str = RunStatus.QUEUED,
    input_tokens: int = 0,
    output_tokens: int = 0,
    estimated_cost: Decimal | float = 0,
    execution_time_ms: int | None = None,
    input_summary: str | None = None,
    output_summary: str | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
) -> AIRun:
    """Persist an AI run row for Phase 3 agents."""
    agent = agent_type.value if hasattr(agent_type, "value") else agent_type
    run_status = status.value if hasattr(status, "value") else status
    completed_statuses = {
        RunStatus.SUCCESS.value,
        RunStatus.COMPLETED.value,
        RunStatus.ERROR.value,
        RunStatus.FAILED.value,
        RunStatus.WARNING.value,
    }
    run = AIRun(
        project_id=project_id,
        content_asset_id=content_asset_id,
        agent_type=agent,
        model=model,
        status=run_status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        estimated_cost=Decimal(str(estimated_cost)),
        execution_time_ms=execution_time_ms,
        input_summary=input_summary,
        output_summary=output_summary,
        error_message=error_message,
        started_at=started_at
        or (datetime.now(UTC) if run_status == RunStatus.RUNNING.value else None),
        completed_at=datetime.now(UTC) if run_status in completed_statuses else None,
    )
    session.add(run)
    session.flush()
    return run


def _to_read(run: AIRun) -> AIRunRead:
    return AIRunRead(
        id=run.id,
        project_id=run.project_id,
        content_asset_id=run.content_asset_id,
        agent_type=run.agent_type,
        model=run.model,
        status=run.status,
        input_tokens=run.input_tokens,
        output_tokens=run.output_tokens,
        total_tokens=run.total_tokens,
        estimated_cost=float(run.estimated_cost or 0),
        execution_time_ms=run.execution_time_ms,
        input_summary=run.input_summary,
        output_summary=run.output_summary,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )
