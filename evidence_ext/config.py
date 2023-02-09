"""This is currently only used to suppress the config file.

Evidence tries to read the config file first, therefore we must remove it
in order to reliably pass settings through as env vars from Meltano.

Started along the path to manage (overwrite) `evidence.settings.json`,
but that approach heavy-handed, and may not be necessary unless there are settings
not accessible via env vars (which it doesn't seem like there are).
"""

import contextlib
import json
import os
from pathlib import Path


class EvidenceConfig:
    """Evidence Config."""

    def __init__(self, evidence_home):
        self.evidence_home = evidence_home
        self.config_file = (
            Path(self.evidence_home)
            / ".evidence"
            / "template"
            / "evidence.settings.json"
        )
        self.database = os.environ.get("EVIDENCE_DATABASE")

    @contextlib.contextmanager
    def suppress_config_file(self):
        """Suppress Evidence config file.

        As evidence checks its config file _before_ env vars,
        we need to remove it before run and replace it after (if it exists).
        """
        config = None
        if self.config_file.exists():
            with self.config_file.open("r") as cfg:
                config = json.load(cfg)
        self._cleanup_config()
        try:
            yield
        finally:
            if config:
                with self.config_file.open("w", encoding="utf-8") as cfg:
                    json.dump(config, cfg)

    @contextlib.contextmanager
    def config_file(self):
        """Context manager for JIT creation of Evidence config file."""
        self._write_config()
        yield
        self._cleanup_config()

    def get_config(self):
        """Read config from Env Vars, validating by database type."""
        if not self.database:
            return {}

        if self.database in ("duckdb", "sqlite"):
            return self._get_config_duckdb_sqlite()
        elif self.database == "bigquery":
            return self._get_config_bigquery()
        elif self.database == "mysql":
            return self._get_config_mysql()
        else:
            raise KeyError(
                f"Database connection {self.database} is not yet supported by evidence-ext."
            )

    def _write_config(self):
        """Write Evidence config from env vars."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        config = self._get_config()
        with self.config_file.open("w", encoding="utf-8") as cf:
            json.dump(config, cf)

    def _cleanup_config(self):
        """To prevent secrets leaking."""
        if self.config_file.exists():
            os.remove(self.config_file)

    def _check_required_env_vars(self, env_vars):
        for env_var in env_vars:
            assert os.environ.get(
                env_var
            ), f"Environment variable '{env_var}' required for database type '{self.database}'."

    def _get_config_duckdb_sqlite(self):
        """Get config for duckdb or sqlite."""
        self._check_required_env_vars(["EVIDENCE_CREDENTIALS_FILENAME"])
        config = {
            "database": self.database,
            "credentials": {"filename": os.environ["EVIDENCE_CREDENTIALS_FILENAME"]},
        }
        if self.database == "duckdb":
            config["credentials"]["gitignoreDuckdb"] = os.environ.get(
                "EVIDENCE_CREDENTIALS_GITIGNORE_DUCKDB"
            )
        return config

    def _get_config_bigquery(self):
        """Get config for BigQuery."""
        self._check_required_env_vars(
            [
                "EVIDENCE_CREDENTIALS_CLIENT_EMAIL",
                "EVIDENCE_CREDENTIALS_PRIVATE_KEY",
            ]
        )
        return {
            "database": self.database,
            "credentials": {
                "client_email": os.environ["EVIDENCE_CREDENTIALS_CLIENT_EMAIL"],
                "private_key": os.environ["EVIDENCE_CREDENTIALS_PRIVATE_KEY"],
            },
        }
