"""Configuration management for Evidence.

This is currently only used to suppress the config file.

Evidence tries to read the config file first, therefore we must remove it
in order to reliably pass settings through as env vars from Meltano.

Started along the path to manage (overwrite) `evidence.settings.json`,
but that approach heavy-handed, and may not be necessary unless there are settings
not accessible via env vars (which it doesn't seem like there are).
"""

from __future__ import annotations

import contextlib
import json
import os
import typing as t
from pathlib import Path

if t.TYPE_CHECKING:
    from typing import Iterable, Iterator


class MissingEnvVarError(Exception):
    """Missing env var."""

    def __init__(self, env_var: str, database: str | None) -> None:
        """Initialize exception.

        Args:
            env_var: Name of the missing env var.
            database: Name of the database.
        """
        msg = f"Environment variable '{env_var}' required for database type"

        if database:
            msg = f"{msg} '{database}'"

        super().__init__(msg)


class EvidenceConfig:
    """Evidence Config."""

    def __init__(self, evidence_home: str) -> None:
        """Initialize Evidence configuation.

        Args:
            evidence_home: Path to the Evidence home directory.
        """
        self.evidence_home = evidence_home
        self._config_file = (
            Path(self.evidence_home)
            / ".evidence"
            / "template"
            / "evidence.settings.json"
        )
        self.database = os.environ.get("EVIDENCE_DATABASE")

    @contextlib.contextmanager
    def suppress_config_file(self) -> Iterator[None]:
        """Suppress Evidence config file.

        As evidence checks its config file _before_ env vars,
        we need to remove it before run and replace it after (if it exists).
        """
        config = None
        if self._config_file.exists():
            with self._config_file.open("r") as cfg:
                config = json.load(cfg)
        self._cleanup_config()
        try:
            yield
        finally:
            if config:
                with self._config_file.open("w", encoding="utf-8") as cfg:
                    json.dump(config, cfg)

    @contextlib.contextmanager
    def config_file(self) -> Iterator[None]:
        """Context manager for JIT creation of Evidence config file."""
        self._write_config()
        yield
        self._cleanup_config()

    def get_config(self) -> dict:
        """Read config from Env Vars, validating by database type.

        Returns:
            dict: Evidence configuation.

        Raises:
            KeyError: If database type is not supported.
        """
        if not self.database:
            return {}

        if self.database in ("duckdb", "sqlite"):
            return self._get_config_duckdb_sqlite()
        if self.database == "bigquery":
            return self._get_config_bigquery()
        if self.database == "mysql":
            return self._get_config_mysql()

        msg = (
            f"Database connection {self.database} is not yet supported by evidence-ext."
        )
        raise KeyError(msg)

    def _write_config(self) -> None:
        """Write Evidence config from env vars."""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        config = self.get_config()
        with self._config_file.open("w", encoding="utf-8") as cf:
            json.dump(config, cf)

    def _cleanup_config(self) -> None:
        """To prevent secrets leaking.

        If the config file exists, remove it.
        """
        if self._config_file.exists():
            Path(self._config_file).unlink()

    def _check_required_env_vars(self, env_vars: Iterable[str]) -> None:
        """Check that required env vars are set."""
        for env_var in env_vars:
            try:
                os.environ[env_var]
            except KeyError as e:  # noqa: PERF203
                raise MissingEnvVarError(env_var, self.database) from e

    def _get_config_duckdb_sqlite(self) -> dict:
        """Get config for duckdb or sqlite."""
        self._check_required_env_vars(["EVIDENCE_CREDENTIALS_FILENAME"])
        config: dict[str, t.Any] = {
            "database": self.database,
            "credentials": {"filename": os.environ["EVIDENCE_CREDENTIALS_FILENAME"]},
        }
        if self.database == "duckdb":
            config["credentials"]["gitignoreDuckdb"] = os.environ.get(
                "EVIDENCE_CREDENTIALS_GITIGNORE_DUCKDB",
            )
        return config

    def _get_config_bigquery(self) -> dict:
        """Get config for BigQuery."""
        self._check_required_env_vars(
            [
                "EVIDENCE_CREDENTIALS_CLIENT_EMAIL",
                "EVIDENCE_CREDENTIALS_PRIVATE_KEY",
            ],
        )
        return {
            "database": self.database,
            "credentials": {
                "client_email": os.environ["EVIDENCE_CREDENTIALS_CLIENT_EMAIL"],
                "private_key": os.environ["EVIDENCE_CREDENTIALS_PRIVATE_KEY"],
            },
        }

    def _get_config_mysql(self) -> dict:
        """Get config for MySQL."""
        raise NotImplementedError
