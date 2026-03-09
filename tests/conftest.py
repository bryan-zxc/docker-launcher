import pytest


@pytest.fixture
def tmp_docker_launcher(tmp_path, monkeypatch):
    """Redirect all ~/.docker-launcher paths to a temp directory."""
    launcher_dir = tmp_path / ".docker-launcher"
    launcher_dir.mkdir()

    import docker_launcher.database as db_mod

    monkeypatch.setattr(db_mod, "DATA_FILE", launcher_dir / "containers.json")

    return launcher_dir
