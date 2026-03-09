"""Tests for docker_launcher.database."""

from docker_launcher.database import (
    cleanup_orphans,
    delete_metadata,
    get_metadata,
    update_last_opened,
)


class TestUpdateLastOpened:
    def test_creates_entry(self, tmp_docker_launcher):
        update_last_opened("container-abc")
        meta = get_metadata("container-abc")
        assert meta is not None
        assert "last_opened_at" in meta

    def test_updates_existing(self, tmp_docker_launcher):
        update_last_opened("c1")
        first = get_metadata("c1")["last_opened_at"]

        update_last_opened("c1")
        second = get_metadata("c1")["last_opened_at"]

        assert second >= first


class TestGetMetadata:
    def test_missing(self, tmp_docker_launcher):
        assert get_metadata("nonexistent") is None

    def test_existing(self, tmp_docker_launcher):
        update_last_opened("c2")
        assert get_metadata("c2") is not None


class TestDeleteMetadata:
    def test_delete_existing(self, tmp_docker_launcher):
        update_last_opened("c3")
        delete_metadata("c3")
        assert get_metadata("c3") is None

    def test_delete_missing(self, tmp_docker_launcher):
        # Should not raise
        delete_metadata("nonexistent")


class TestCleanupOrphans:
    def test_removes_orphans(self, tmp_docker_launcher):
        update_last_opened("alive")
        update_last_opened("dead1")
        update_last_opened("dead2")

        cleanup_orphans({"alive"})

        assert get_metadata("alive") is not None
        assert get_metadata("dead1") is None
        assert get_metadata("dead2") is None

    def test_no_orphans(self, tmp_docker_launcher):
        update_last_opened("a")
        update_last_opened("b")
        cleanup_orphans({"a", "b"})
        assert get_metadata("a") is not None
        assert get_metadata("b") is not None

    def test_empty_store(self, tmp_docker_launcher):
        # Should not raise
        cleanup_orphans({"x", "y"})
