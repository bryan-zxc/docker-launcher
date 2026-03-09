"""Tests for docker_launcher.prerequisites."""

from unittest.mock import patch, MagicMock
import subprocess

from docker_launcher.prerequisites import (
    gh_installed,
    gh_authenticated,
    get_prerequisites,
)


class TestGhInstalled:
    def test_found(self):
        with patch("docker_launcher.prerequisites.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert gh_installed() is True

    def test_not_found(self):
        with patch(
            "docker_launcher.prerequisites.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert gh_installed() is False

    def test_timeout(self):
        with patch(
            "docker_launcher.prerequisites.subprocess.run",
            side_effect=subprocess.TimeoutExpired("gh", 5),
        ):
            assert gh_installed() is False


class TestGhAuthenticated:
    def test_authenticated(self):
        with patch("docker_launcher.prerequisites.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert gh_authenticated() is True

    def test_not_authenticated(self):
        with patch("docker_launcher.prerequisites.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert gh_authenticated() is False

    def test_gh_not_installed(self):
        with patch(
            "docker_launcher.prerequisites.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            assert gh_authenticated() is False


class TestGetPrerequisites:
    def test_all_ok(self):
        with patch("docker_launcher.prerequisites.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = get_prerequisites()
            assert result["gh_installed"] is True
            assert result["gh_authenticated"] is True

    def test_nothing_installed(self):
        with patch(
            "docker_launcher.prerequisites.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = get_prerequisites()
            assert result["gh_installed"] is False
            assert result["gh_authenticated"] is False
