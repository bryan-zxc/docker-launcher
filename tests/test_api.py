"""API integration tests using FastAPI TestClient."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_docker_launcher, monkeypatch):
    """Create a TestClient with mocked external dependencies."""
    import docker_launcher.docker_service as docker_mod

    # Mock Docker client to avoid requiring Docker
    mock_docker = MagicMock()
    monkeypatch.setattr(docker_mod, "_client", mock_docker)

    from docker_launcher.main import app

    return TestClient(app)


# --- Version ---


class TestVersion:
    def test_get_version(self, client):
        r = client.get("/api/version")
        assert r.status_code == 200
        assert "version" in r.json()


# --- Images ---


class TestImages:
    def test_list_images(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        monkeypatch.setattr(
            main_mod, "list_images", lambda: [{"id": "base", "name": "Base"}]
        )

        r = client.get("/api/images")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_get_image_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        monkeypatch.setattr(
            main_mod, "get_image", lambda name: {"id": name, "name": "Base"}
        )

        r = client.get("/api/images/base")
        assert r.status_code == 200
        assert r.json()["id"] == "base"

    def test_get_image_not_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        monkeypatch.setattr(main_mod, "get_image", lambda name: None)

        r = client.get("/api/images/nonexistent")
        assert r.status_code == 404

    def test_build_stream(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fake_build(name, force=False):
            yield "Building..."
            yield "Done"

        monkeypatch.setattr(main_mod, "build_image", fake_build)

        r = client.post("/api/images/base/build")
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        assert "data: Building..." in r.text
        assert "data: Done" in r.text


# --- Containers ---


class TestContainers:
    def test_list_containers(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        monkeypatch.setattr(main_mod, "list_containers", lambda: [])

        r = client.get("/api/containers")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_container_bad_image(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fail(image, repo_url, name):
            raise ValueError("Image not built")

        monkeypatch.setattr(main_mod, "create_container", fail)

        r = client.post("/api/containers", json={"image": "nonexistent"})
        assert r.status_code == 400

    def test_start_not_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fail(cid):
            raise ValueError("not found")

        monkeypatch.setattr(main_mod, "start_container", fail)

        r = client.post("/api/containers/bad/start")
        assert r.status_code == 404

    def test_stop_not_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fail(cid):
            raise ValueError("not found")

        monkeypatch.setattr(main_mod, "stop_container", fail)

        r = client.post("/api/containers/bad/stop")
        assert r.status_code == 404

    def test_delete_not_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fail(cid):
            raise ValueError("not found")

        monkeypatch.setattr(main_mod, "delete_container", fail)

        r = client.delete("/api/containers/bad")
        assert r.status_code == 404

    def test_vscode_not_found(self, client, monkeypatch):
        import docker_launcher.main as main_mod

        def fail(cid):
            raise ValueError("not found")

        monkeypatch.setattr(main_mod, "open_in_vscode", fail)

        r = client.post("/api/containers/bad/vscode")
        assert r.status_code == 404


# --- Docker not available ---


class TestDockerNotAvailable:
    def test_503_on_docker_down(self, client, monkeypatch):
        import docker_launcher.main as main_mod
        from docker_launcher.docker_service import DockerNotAvailableError

        def fail():
            raise DockerNotAvailableError("Docker not running")

        monkeypatch.setattr(main_mod, "list_containers", fail)

        r = client.get("/api/containers")
        assert r.status_code == 503
        assert r.json()["docker_not_running"] is True
