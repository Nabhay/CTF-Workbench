from __future__ import annotations

from enum import StrEnum


class ActorKind(StrEnum):
    HUMAN = "human"
    TOOL = "tool"
    AGENT = "agent"
    SYSTEM = "system"


class ChallengeStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    SOLVED = "solved"
    ARCHIVED = "archived"


class ItemKind(StrEnum):
    LEAD = "lead"
    FACT = "fact"
    DEAD_END = "dead_end"


class ItemStatus(StrEnum):
    HYPOTHESIS = "hypothesis"
    VERIFIED = "verified"
    CONFIRMED = "confirmed"
    DEAD_END = "dead_end"
