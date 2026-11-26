from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class Settings(BaseSettings):
    """Process-wide configuration. Secrets are never included in repr or logs."""

    model_config = SettingsConfigDict(
        env_prefix="CTF_WORKBENCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str = "sqlite:///./data/workbench.db"
    data_root: Path = Path("./data")
    bind_host: str = "127.0.0.1"
    bind_port: int = Field(default=8745, ge=1, le=65535)
    session_secret: SecretStr
    docker_host: str | None = None
    log_level: LogLevel = "INFO"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    allow_nonlocal_bind: bool = False

    @field_validator("session_secret")
    @classmethod
    def _secret_length(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret) < 32:
            raise ValueError(
                "CTF_WORKBENCH_SESSION_SECRET must be at least 32 characters. "
                "Copy .env.example to .env and set a random secret so session cookies "
                "cannot be forged."
            )
        return value

    @field_validator("docker_host")
    @classmethod
    def _empty_docker_host(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value

    @model_validator(mode="after")
    def _bind_localhost(self) -> Self:
        if self.bind_host not in _LOCAL_HOSTS and not self.allow_nonlocal_bind:
            raise ValueError(
                f"bind_host {self.bind_host!r} is not localhost. The workbench binds "
                "to 127.0.0.1 by default. Set CTF_WORKBENCH_ALLOW_NONLOCAL_BIND=true "
                "only if you understand that the control plane executes tools."
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    def redacted_database_url(self) -> str:
        parts = urlsplit(self.database_url)
        if parts.password is None:
            return self.database_url
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        netloc = f"{parts.username}:***@{host}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

    def ensure_data_root(self) -> Path:
        path = self.data_root.expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def __repr__(self) -> str:
        return (
            "Settings("
            f"database_url={self.redacted_database_url()!r}, "
            f"data_root={str(self.data_root)!r}, "
            f"bind_host={self.bind_host!r}, "
            f"bind_port={self.bind_port}, "
            f"docker_host={self.docker_host!r}, "
            f"log_level={self.log_level!r}"
            ")"
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_data_root()
    return settings


def reset_settings_cache() -> None:
    get_settings.cache_clear()
