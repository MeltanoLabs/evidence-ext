"""Evidence cli entrypoint."""

from __future__ import annotations

import os
import sys
import typing as t

import structlog
import typer
from meltano.edk.extension import DescribeFormat
from meltano.edk.logging import default_logging_config, parse_log_level

from evidence_ext.extension import Evidence

APP_NAME = "Evidence"

log = structlog.get_logger(APP_NAME)

ext = Evidence()

typer.core.rich = None  # remove to enable stylized help output when `rich` is installed
app = typer.Typer(
    name=APP_NAME,
    pretty_exceptions_enable=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,  # noqa: ARG001
    *,
    log_level: str = typer.Option("INFO", envvar="LOG_LEVEL"),
    log_timestamps: bool = typer.Option(
        False,  # noqa: FBT003
        envvar="LOG_TIMESTAMPS",
        help="Show timestamp in logs",
    ),
    log_levels: bool = typer.Option(
        False,  # noqa: FBT003
        "--log-levels",
        envvar="LOG_LEVELS",
        help="Show log levels",
    ),
    meltano_log_json: bool = typer.Option(
        False,  # noqa: FBT003
        "--meltano-log-json",
        envvar="MELTANO_LOG_JSON",
        help="Log in the meltano JSON log format",
    ),
) -> None:
    """Simple Meltano extension that wraps the npm CLI.

    Args:
        ctx: The typer context.
        log_level: The log level.
        log_timestamps: Whether to show timestamps in logs.
        log_levels: Whether to show log levels.
        meltano_log_json: Whether to log in the meltano JSON log format.
    """
    default_logging_config(
        level=parse_log_level(log_level),
        timestamps=log_timestamps,
        levels=log_levels,
        json_format=meltano_log_json,
    )


@app.command()
def initialize(
    ctx: typer.Context,  # noqa: ARG001
    *,
    force: bool = typer.Option(
        False,  # noqa: FBT003
        help="Force initialization (if supported)",
    ),
) -> None:
    """Initialize the Evidence plugin."""
    try:
        ext.initialize(force)
    except Exception:
        log.exception(
            "initialize failed with uncaught exception, please report to maintainer",
        )
        sys.exit(1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def invoke(ctx: typer.Context, command_args: t.List[str]) -> None:  # noqa: ARG001
    """Invoke the plugin.

    Note: that if a command argument is a list, such as command_args,
    then unknown options are also included in the list and NOT stored in the
    context as usual.
    """
    command_name, command_args = command_args[0], command_args[1:]
    log.debug(
        "called",
        command_name=command_name,
        command_args=command_args,
        env=os.environ,
    )
    ext.pass_through_invoker(log, command_name, *command_args)


@app.command()
def describe(
    output_format: DescribeFormat = typer.Option(
        DescribeFormat.text,
        "--format",
        help="Output format",
    ),
) -> None:
    """Describe the available commands of this extension."""
    try:
        typer.echo(ext.describe_formatted(output_format))
    except Exception:
        log.exception(
            "describe failed with uncaught exception, please report to maintainer",
        )
        sys.exit(1)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def npm(ctx: typer.Context, command_args: t.List[str]) -> None:  # noqa: ARG001
    """Run npm commands inside the Evidence project directory."""
    ext.npm(*command_args)


@app.command()
def build(
    ctx: typer.Context,  # noqa: ARG001
    *,
    strict: bool = typer.Option(
        False,  # noqa: FBT003
        "--strict",
        help="build:strict",
    ),
) -> None:
    """Build the Evidence project."""
    ext.build(strict=strict)


@app.command()
def dev(ctx: typer.Context) -> None:  # noqa: ARG001
    """Launch the Evidence dev server."""
    ext.dev()


if __name__ == "__main__":
    app()
