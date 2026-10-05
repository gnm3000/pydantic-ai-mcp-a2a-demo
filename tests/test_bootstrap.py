"""Tests for environment loading and CLI startup bootstrap."""

from experiment_mcp import bootstrap


def test_load_environment_reads_project_env_file(monkeypatch):
    calls = []
    monkeypatch.setattr(bootstrap, "load_dotenv", lambda path: calls.append(path))

    bootstrap.load_environment()

    assert calls == [bootstrap.PROJECT_ROOT / ".env"]


def test_main_loads_environment_then_starts_server(monkeypatch):
    calls = []
    monkeypatch.setattr(bootstrap, "load_environment", lambda: calls.append("environment"))
    monkeypatch.setattr("experiment_mcp.server.main", lambda: calls.append("server"))

    bootstrap.main()

    assert calls == ["environment", "server"]
