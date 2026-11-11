from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from mosaicolabs.examples import config
from mosaicolabs_cli.commands import examples
from mosaicolabs_cli.main import app

runner = CliRunner()


@pytest.fixture
def no_profile_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MOSAICO_CONFIG_PATH", str(tmp_path / "empty.toml"))
    for name in (
        "MOSAICO_DAEMON_URL",
        "MOSAICO_API_KEY",
        "MOSAICO_TLS",
        "MOSAICO_CERT_PATH",
        "MOSAICO_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_examples_list_needs_no_connection_profile(no_profile_env):
    result = runner.invoke(app, ["examples", "ls"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == sorted(examples.EXAMPLES_MAP)


def test_example_uses_active_profile(monkeypatch, no_profile_env, tmp_path):
    certificate = tmp_path / "ca.pem"
    monkeypatch.setenv("MOSAICO_DAEMON_URL", "examples.test:7443")
    monkeypatch.setenv("MOSAICO_API_KEY", "test-key")
    monkeypatch.setenv("MOSAICO_TLS", "true")
    monkeypatch.setenv("MOSAICO_CERT_PATH", str(certificate))
    observed = []

    def main():
        observed.append(
            (
                config.MOSAICO_HOST,
                config.MOSAICO_PORT,
                config.ENABLE_TLS,
                config.TLS_CERT_PATH,
                config.API_KEY,
                config.LOG_LEVEL,
            )
        )

    monkeypatch.setattr(
        examples.importlib,
        "import_module",
        lambda name: SimpleNamespace(main=main),
    )

    result = runner.invoke(app, ["examples", "data_inspection", "--log", "debug"])

    assert result.exit_code == 0, result.output
    assert observed == [
        ("examples.test", 7443, True, str(certificate), "test-key", "DEBUG")
    ]
    assert "test-key" not in result.output


def test_example_requires_connection_profile(monkeypatch, no_profile_env):
    monkeypatch.setattr(
        examples.importlib,
        "import_module",
        lambda name: pytest.fail("example must not load without a profile"),
    )

    result = runner.invoke(app, ["examples", "data_inspection"])

    assert result.exit_code == 1


def test_examples_are_listed_in_main_help():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "examples" in result.output
