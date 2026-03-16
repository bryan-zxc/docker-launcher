"""Tests for docker_launcher.docker_service."""

import json
from unittest.mock import MagicMock


from docker_launcher.docker_service import (
    _container_info,
    _read_metadata,
    list_images,
    CONTAINER_LABEL,
)


class TestReadMetadata:
    def test_reads_metadata(self, tmp_path):
        meta = {"name": "Base", "description": "A base image"}
        (tmp_path / "metadata.json").write_text(json.dumps(meta))
        assert _read_metadata(tmp_path) == meta

    def test_missing_file(self, tmp_path):
        assert _read_metadata(tmp_path) is None


class TestContainerInfo:
    def test_extracts_fields(self):
        container = MagicMock()
        container.short_id = "abc123"
        container.id = "abc123full"
        container.name = "test-container"
        container.status = "running"
        container.labels = {
            f"{CONTAINER_LABEL}.image": "base",
            f"{CONTAINER_LABEL}.repo": "https://github.com/test/repo",
            f"{CONTAINER_LABEL}.created": "2025-01-01T00:00:00+00:00",
        }

        info = _container_info(container)
        assert info["id"] == "abc123"
        assert info["full_id"] == "abc123full"
        assert info["name"] == "test-container"
        assert info["image"] == "base"
        assert info["repo_url"] == "https://github.com/test/repo"
        assert info["status"] == "running"

    def test_missing_labels(self):
        container = MagicMock()
        container.short_id = "xyz"
        container.id = "xyzfull"
        container.name = "no-labels"
        container.status = "exited"
        container.labels = {}

        info = _container_info(container)
        assert info["image"] == ""
        assert info["repo_url"] == ""


class TestListImages:
    def test_lists_images(self, tmp_path, monkeypatch):
        import docker_launcher.docker_service as mod

        # Create a fake images dir with one image
        images_dir = tmp_path / "images"
        base_dir = images_dir / "base"
        base_dir.mkdir(parents=True)
        (base_dir / "metadata.json").write_text(
            json.dumps({"name": "Base", "description": "Base image"})
        )

        monkeypatch.setattr(mod, "IMAGES_DIR", images_dir)

        mock_client = MagicMock()
        mock_client.images.get.side_effect = Exception("not found")
        monkeypatch.setattr(mod, "_client", mock_client)

        # _image_is_built, _image_built_at, _image_needs_rebuild will raise, so mock them
        monkeypatch.setattr(mod, "_image_is_built", lambda name: False)
        monkeypatch.setattr(mod, "_image_built_at", lambda name: None)
        monkeypatch.setattr(mod, "_image_needs_rebuild", lambda name: True)

        result = list_images()
        assert len(result) == 1
        assert result[0]["id"] == "base"
        assert result[0]["name"] == "Base"
        assert result[0]["built"] is False

    def test_empty_dir(self, tmp_path, monkeypatch):
        import docker_launcher.docker_service as mod

        images_dir = tmp_path / "images"
        images_dir.mkdir()
        monkeypatch.setattr(mod, "IMAGES_DIR", images_dir)

        assert list_images() == []

    def test_missing_dir(self, tmp_path, monkeypatch):
        import docker_launcher.docker_service as mod

        monkeypatch.setattr(mod, "IMAGES_DIR", tmp_path / "nonexistent")
        assert list_images() == []

    def test_skips_dirs_without_metadata(self, tmp_path, monkeypatch):
        import docker_launcher.docker_service as mod

        images_dir = tmp_path / "images"
        (images_dir / "no-meta").mkdir(parents=True)
        monkeypatch.setattr(mod, "IMAGES_DIR", images_dir)

        assert list_images() == []


class TestGetClaudeOauthToken:
    def test_env_var_takes_priority(self, monkeypatch):
        """Host env var overrides bundled default."""
        import docker_launcher._auth_defaults as defaults
        import docker_launcher.docker_service as mod

        monkeypatch.setattr(defaults, "CLAUDE_CODE_OAUTH_TOKEN", "bundled-token")
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "env-token")

        assert mod._get_claude_oauth_token() == "env-token"

    def test_falls_back_to_bundled(self, monkeypatch):
        """Uses bundled token when env var is not set."""
        import docker_launcher._auth_defaults as defaults
        import docker_launcher.docker_service as mod

        monkeypatch.setattr(defaults, "CLAUDE_CODE_OAUTH_TOKEN", "bundled-token")
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

        assert mod._get_claude_oauth_token() == "bundled-token"

    def test_returns_none_when_nothing_available(self, monkeypatch):
        """Returns None when neither env var nor bundled token exist."""
        import docker_launcher._auth_defaults as defaults
        import docker_launcher.docker_service as mod

        monkeypatch.setattr(defaults, "CLAUDE_CODE_OAUTH_TOKEN", None)
        monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)

        assert mod._get_claude_oauth_token() is None

    def test_empty_env_var_ignored(self, monkeypatch):
        """Empty string env var falls through to bundled token."""
        import docker_launcher._auth_defaults as defaults
        import docker_launcher.docker_service as mod

        monkeypatch.setattr(defaults, "CLAUDE_CODE_OAUTH_TOKEN", "bundled-token")
        monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "")

        assert mod._get_claude_oauth_token() == "bundled-token"
