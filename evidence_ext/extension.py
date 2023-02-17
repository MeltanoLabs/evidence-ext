"""Meltano Evidence extension."""

from __future__ import annotations

import os
import subprocess
import sys
import typing as t

import structlog
from meltano.edk import models
from meltano.edk.extension import ExtensionBase
from meltano.edk.process import Invoker, log_subprocess_error

from evidence_ext.config import EvidenceConfig

if t.TYPE_CHECKING:
    from meltano.edk.types import ExecArg

log = structlog.get_logger()


def get_env_var(*names: str) -> str:
    """Get the value of the first non-empty environment variable.

    Args:
        names: The name of the environment variable.

    Returns:
        The value of the environment variable.
    """
    var = None
    for name in names:
        try:
            var = os.environ[name]
        except KeyError:
            continue
        else:
            break

    if not var:
        log.error("Environment variable not found", names=names)
        sys.exit(1)
    return var


class Evidence(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    def __init__(self) -> None:
        """Initialize the extension."""
        self.app_name = "evidence_extension"
        self.evidence_home = get_env_var("EVIDENCE_HOME", "EVIDENCE_HOME_DIR")
        self.config = EvidenceConfig(evidence_home=self.evidence_home)
        self._npm = Invoker("npm")
        self._npx = Invoker("npx")

    def initialize(self, force: bool) -> None:  # noqa: ARG002, FBT001
        """Initialize a new project.

        Args:
            force: Whether to force initialization.

        Raises:
            CalledProcessError: If the initialization fails.
        """
        try:
            self._npx.run_and_log("degit", "evidence-dev/template", self.evidence_home)
        except subprocess.CalledProcessError as err:
            log_subprocess_error("npx degit", err, "npx degit failed")
            sys.exit(err.returncode)

    def invoke(self, command_name: str | None, *command_args: ExecArg) -> None:
        """Invoke the underlying cli, that is being wrapped by this extension.

        Args:
            command_name: The name of the command to invoke.
            command_args: The arguments to pass to the command.
        """
        try:
            command_args = (
                "--prefix",
                self.evidence_home,
                *command_args,
            )
            self._npm.run_and_log(*command_args)
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
                    name="evidence_extension",
                    description="extension commands",
                ),
            ],
        )

    def npm(self, *command_args: ExecArg) -> None:
        """Run 'npm' inside Evidence home with args."""
        try:
            command_args = (
                "--prefix",
                self.evidence_home,
                *command_args,
            )
            self._npm.run_and_log(*command_args)
        except subprocess.CalledProcessError as err:
            log_subprocess_error("npm", err, "npm invocation failed")
            sys.exit(err.returncode)

    def build(self, strict: bool = False) -> None:  # noqa: FBT001, FBT002
        """Run 'npm run build' in the Evidence home dir.

        Args:
            strict: Whether to run in strict mode.
        """
        with self.config.suppress_config_file():
            self._npm.run_and_log(*["--prefix", self.evidence_home, "install"])
            build_cmds = ["--prefix", self.evidence_home, "run"]
            if strict:
                build_cmds.append("build:strict")
            else:
                build_cmds.append("build")
            self._npm.run_and_log(*build_cmds)

    def dev(self) -> None:
        """Run 'npm run dev' in the Evidence home dir."""
        with self.config.suppress_config_file():
            self._npm.run_and_log(*["--prefix", self.evidence_home, "install"])
            self._npm.run_and_log(*["--prefix", self.evidence_home, "run", "dev"])
