"""Meltano Evidence extension."""
from __future__ import annotations

import json
import os
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog
from meltano.edk import models
from meltano.edk.extension import ExtensionBase
from meltano.edk.process import Invoker, log_subprocess_error

log = structlog.get_logger()


class Evidence(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    def __init__(self) -> None:
        """Initialize the extension."""
        self.app_name = "evidence_extension"
        self.evidence_home = os.environ.get("EVIDENCE_HOME") or os.environ.get(
            "EVIDENCE_HOME_DIR"
        )
        if not self.evidence_home:
            log.debug("env dump", env=os.environ)
            log.error(
                "EVIDENCE_HOME not found in environment, unable to function without it"
            )
            sys.exit(1)
        self.npm = Invoker("npm")
        self.npx = Invoker("npx")

    def _get_config_duckdb(self):
        return {
            "database": "duckdb",
            "credentials": {
                "filename": os.environ["EVIDENCE_CREDENTIALS_FILENAME"],
                "gitignoreDuckdb": os.environ.get(
                    "EVIDENCE_CREDENTIALS_GITIGNORE_DUCKDB"
                ),
            },
        }

    def _get_config(self):
        database = os.environ["EVIDENCE_DATABASE"]
        if database == "duckdb":
            return self._get_config_duckdb()
        else:
            raise KeyError(
                f"Database connection {database} is not yet supported by evidence-ext."
            )

    def _write_config(self):
        config_file = (
            Path(self.evidence_home)
            / ".evidence"
            / "template"
            / "evidence.settings.json"
        )
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config = self._get_config()
        with config_file.open("w", encoding="utf-8") as cf:
            json.dump(config, cf)

    def initialize(self, force: bool):
        """Initialize a new project."""
        try:
            self.npx.run_and_log(
                *["degit", "evidence-dev/template", self.evidence_home]
            )
        except subprocess.CalledProcessError as err:
            log_subprocess_error("npx degit", err, "npx degit failed")
            sys.exit(err.returncode)

    def invoke(self, command_name: str | None, *command_args: Any) -> None:
        """Invoke the underlying cli, that is being wrapped by this extension.

        Args:
            command_name: The name of the command to invoke.
            command_args: The arguments to pass to the command.
        """
        try:
            self.npm.run_and_log(*command_args)
        except subprocess.CalledProcessError as err:
            log_subprocess_error(f"npm {command_name}", err, "npm invocation failed")
            sys.exit(err.returncode)

    def describe(self) -> models.Describe:
        """Describe the extension.

        Returns:
            The extension description
        """
        return models.Describe(
            commands=[
                models.ExtensionCommand(
                    name="evidence_extension", description="extension commands"
                )
            ]
        )

    def build(self):
        self._write_config()
        self.npm.run_and_log(*["install", "--prefix", self.evidence_home])
        self.npm.run_and_log(*["run", "build", "--prefix", self.evidence_home])

    def dev(self):
        self._write_config()
        self.npm.run_and_log(*["install", "--prefix", self.evidence_home])
        self.npm.run_and_log(*["run", "dev", "--prefix", self.evidence_home])
