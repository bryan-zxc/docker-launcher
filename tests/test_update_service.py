"""Tests for the auto-update service."""

import json

import pytest


class TestParseVersion:
    def test_simple(self):
        from docker_launcher.update_service import _parse_version

        assert _parse_version("0.1.4") == (0, 1, 4)

    def test_with_v_prefix(self):
        from docker_launcher.update_service import _parse_version

        assert _parse_version("v0.2.0") == (0, 2, 0)

    def test_comparison(self):
        from docker_launcher.update_service import _parse_version

        assert _parse_version("0.1.4") < _parse_version("0.2.0")
        assert _parse_version("0.2.0") > _parse_version("0.1.4")
        assert _parse_version("1.0.0") > _parse_version("0.99.99")

    def test_equal(self):
        from docker_launcher.update_service import _parse_version

        assert _parse_version("0.1.4") == _parse_version("v0.1.4")


class TestUpdateState:
    def test_load_empty(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        monkeypatch.setattr(mod, "UPDATE_FILE", tmp_docker_launcher / "update.json")
        assert mod._load_state() == {}

    def test_save_and_load(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        monkeypatch.setattr(mod, "UPDATE_FILE", tmp_docker_launcher / "update.json")
        mod._save_state({"latest_version": "0.2.0", "update_available": True})
        state = mod._load_state()
        assert state["latest_version"] == "0.2.0"
        assert state["update_available"] is True

    def test_corrupt_json(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        f = tmp_docker_launcher / "update.json"
        f.write_text("{corrupt", encoding="utf-8")
        monkeypatch.setattr(mod, "UPDATE_FILE", f)
        assert mod._load_state() == {}


class TestGetUpdateState:
    def test_download_ready(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        f = tmp_docker_launcher / "update.json"
        fake_zip = tmp_docker_launcher / "docker-launcher-v0.2.0.zip"
        fake_zip.write_bytes(b"PK")
        f.write_text(
            json.dumps(
                {
                    "downloaded_version": "0.2.0",
                    "download_path": str(fake_zip),
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "UPDATE_FILE", f)
        monkeypatch.setattr(mod, "_current_version", lambda: "0.1.4")
        state = mod.get_update_state()
        assert state["download_ready"] is True

    def test_download_not_ready_same_version(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        f = tmp_docker_launcher / "update.json"
        fake_zip = tmp_docker_launcher / "docker-launcher-v0.2.0.zip"
        fake_zip.write_bytes(b"PK")
        f.write_text(
            json.dumps(
                {
                    "downloaded_version": "0.2.0",
                    "download_path": str(fake_zip),
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "UPDATE_FILE", f)
        monkeypatch.setattr(mod, "_current_version", lambda: "0.2.0")
        state = mod.get_update_state()
        assert state["download_ready"] is False

    def test_download_not_ready_no_file(self, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        f = tmp_docker_launcher / "update.json"
        f.write_text(
            json.dumps(
                {
                    "downloaded_version": "0.2.0",
                    "download_path": str(tmp_docker_launcher / "nonexistent.zip"),
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "UPDATE_FILE", f)
        monkeypatch.setattr(mod, "_current_version", lambda: "0.1.4")
        state = mod.get_update_state()
        assert state["download_ready"] is False


@pytest.fixture
def client(monkeypatch):
    """Test client that stubs out update background checker."""
    import docker_launcher.update_service as update_mod

    monkeypatch.setattr(update_mod, "start_background_checker", lambda: None)

    from starlette.testclient import TestClient

    from docker_launcher.main import app

    return TestClient(app)


class TestUpdateAPI:
    def test_update_check_endpoint(self, client, tmp_docker_launcher, monkeypatch):
        import docker_launcher.update_service as mod

        monkeypatch.setattr(mod, "UPDATE_FILE", tmp_docker_launcher / "update.json")
        monkeypatch.setattr(mod, "_current_version", lambda: "0.1.4")
        r = client.get("/api/update-check")
        assert r.status_code == 200
        assert r.json()["current_version"] == "0.1.4"

    def test_shutdown_endpoint(self, client, monkeypatch):
        import os as _os

        # Prevent actual shutdown by intercepting os.kill
        killed = []
        monkeypatch.setattr(_os, "kill", lambda pid, sig: killed.append((pid, sig)))
        r = client.post("/api/shutdown")
        assert r.status_code == 200
        assert r.json()["status"] == "shutting_down"
