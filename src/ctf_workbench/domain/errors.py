from __future__ import annotations


class WorkbenchError(Exception):
    """Base error for domain and service failures."""


class ConflictError(WorkbenchError):
    def __init__(self, message: str, *, current_revision: int | None = None) -> None:
        super().__init__(message)
        self.current_revision = current_revision


class NotFoundError(WorkbenchError):
    pass


class StaleReferenceError(ConflictError):
    def __init__(self, message: str, *, current_version: str | None = None) -> None:
        super().__init__(message)
        self.current_version = current_version


class SchemaMismatchError(WorkbenchError):
    """Database is not at the Alembic head revision."""
