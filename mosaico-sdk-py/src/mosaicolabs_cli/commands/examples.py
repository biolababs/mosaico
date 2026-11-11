import importlib
import logging

import typer

from mosaicolabs.examples import config
from mosaicolabs_cli.utils.bridge import LogLevel, LogLevelOpt, require_profile
from mosaicolabs_cli.utils.config import console, error_console

EXAMPLES_MAP = {
    "mcap_injection": "mosaicolabs.examples.bridges.mcap.injection",
    "reconstruct_mcaps": "mosaicolabs.examples.bridges.mcap.reconstruct",
    "ros_injection": "mosaicolabs.examples.bridges.ros.injection",
    "reconstruct_rosbags": "mosaicolabs.examples.bridges.ros.reconstruct",
    "data_inspection": "mosaicolabs.examples.data_inspection",
    "query_catalogs": "mosaicolabs.examples.query_catalogs",
    "mujoco_vis": "mosaicolabs.examples.mujoco_vis",
}

app = typer.Typer(no_args_is_help=True)


@app.command(name="ls")
def list_examples() -> None:
    """List the available SDK examples."""
    for name in sorted(EXAMPLES_MAP):
        console.print(name)


def _run_example(ctx: typer.Context, example: str, log_level: LogLevel) -> None:
    profile = require_profile(ctx)
    logging.basicConfig(level=getattr(logging, log_level.value))

    config.MOSAICO_HOST = profile.host
    config.MOSAICO_PORT = profile.port
    config.ENABLE_TLS = profile.enable_tls
    config.TLS_CERT_PATH = profile.tls_cert_path
    config.API_KEY = profile.api_key or None
    config.LOG_LEVEL = log_level.value

    console.print(f"Launching example: {example}")
    console.print(
        f"Target host: {profile.host}:{profile.port} "
        f"(TLS {'enabled' if profile.enable_tls else 'disabled'})"
    )

    try:
        module = importlib.import_module(EXAMPLES_MAP[example])
        entry_point = getattr(module, "main", None)
        if not callable(entry_point):
            error_console.print(f"Example '{example}' has no callable main function.")
            raise typer.Exit(code=1)
        entry_point()
    except typer.Exit:
        raise
    except Exception:
        logging.exception("Example execution failed")
        error_console.print(f"Example '{example}' failed.")
        raise typer.Exit(code=1)


def _example_command(example: str):
    def command(
        ctx: typer.Context,
        log_level: LogLevelOpt = LogLevel.INFO,
    ) -> None:
        _run_example(ctx, example, log_level)

    command.__name__ = f"run_{example}"
    command.__doc__ = f"Run the {example} SDK example."
    return command


for _example_name in EXAMPLES_MAP:
    app.command(name=_example_name)(_example_command(_example_name))
