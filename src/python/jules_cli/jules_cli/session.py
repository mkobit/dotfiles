from enum import StrEnum, auto
from typing import override

from pydantic import BaseModel, Field
from whenever import Instant

from jules_cli.core import frozen_config
from jules_cli.source import SourceContext


class AutomationMode(StrEnum):
    """Automation modes for a session."""

    @staticmethod
    @override
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:  # type: ignore[override]
        _ = start, count, last_values
        return name

    AUTOMATION_MODE_UNSPECIFIED = auto()
    AUTO_CREATE_PR = auto()


class CreateSessionRequest(BaseModel):
    """Request body for creating a session."""

    prompt: str
    source_context: SourceContext
    automation_mode: AutomationMode | None = None
    title: str | None = None
    require_plan_approval: bool | None = None
    model_config = frozen_config


class PullRequest(BaseModel):
    """Output details for a Pull Request."""

    url: str
    title: str
    description: str
    model_config = frozen_config


class SessionOutput(BaseModel):
    """Generic output wrapper."""

    pull_request: PullRequest | None = None
    model_config = frozen_config


class SessionState(StrEnum):
    """State of a session."""

    @staticmethod
    @override
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:  # type: ignore[override]
        _ = start, count, last_values
        return name

    STATE_UNSPECIFIED = auto()
    QUEUED = auto()
    PLANNING = auto()
    AWAITING_PLAN_APPROVAL = auto()
    AWAITING_USER_FEEDBACK = auto()
    IN_PROGRESS = auto()
    PAUSED = auto()
    FAILED = auto()
    COMPLETED = auto()


class Session(BaseModel):
    """Represents a Jules session."""

    name: str
    id: str
    title: str | None = None
    source_context: SourceContext
    prompt: str
    outputs: list[SessionOutput] | None = None
    create_time: Instant | None = None
    update_time: Instant | None = None
    state: SessionState | None = None
    url: str | None = None
    require_plan_approval: bool | None = None
    automation_mode: AutomationMode | None = None
    model_config = frozen_config


class ListSessionsResponse(BaseModel):
    """Response from listing sessions."""

    sessions: list[Session] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config
