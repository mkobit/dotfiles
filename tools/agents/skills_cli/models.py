"""Data models for skill sync operations."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class SkillSource(BaseModel):
    """A discovered skill and its source location."""

    name: str
    path: Path
    origin: Literal["local", "upstream"]


class SyncResult(BaseModel):
    """Result of syncing a single skill to a single tool."""

    skill: str
    tool: str
    action: Literal["synced", "up_to_date", "created"]


class DriftResult(BaseModel):
    """Result of checking a single skill against a single tool."""

    skill: str
    tool: str
    drifted: bool
    details: str | None = None
