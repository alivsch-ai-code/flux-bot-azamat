"""Tests für src.utils.temp_cleanup – Aufräumen des temp/-Ordners."""
import os
import tempfile
import time

from src.utils.temp_cleanup import cleanup_temp_folder


class TestCleanupTempFolder:
    """Prüft cleanup_temp_folder: Löscht nur Dateien älter als max_age_seconds."""

    def test_nonexistent_dir_returns_zero(self):
        """Nicht existierender Ordner liefert 0."""
        assert cleanup_temp_folder(max_age_seconds=0, base_dir="/nonexistent/path/xyz") == 0

    def test_deletes_old_files(self):
        """Dateien älter als max_age werden gelöscht."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "old.txt")
            with open(f1, "w") as fp:
                fp.write("x")
            time.sleep(1.1)
            count = cleanup_temp_folder(max_age_seconds=1, base_dir=tmpdir)
            assert count == 1
            assert not os.path.exists(f1)

    def test_keeps_recent_files(self):
        """Dateien jünger als max_age bleiben erhalten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = os.path.join(tmpdir, "recent.txt")
            with open(f1, "w") as fp:
                fp.write("x")
            count = cleanup_temp_folder(max_age_seconds=999999, base_dir=tmpdir)
            assert count == 0
            assert os.path.exists(f1)

    def test_returns_count_of_deleted(self):
        """Rückgabe ist die Anzahl gelöschter Dateien."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                with open(os.path.join(tmpdir, f"f{i}.txt"), "w") as fp:
                    fp.write("x")
            time.sleep(1.1)
            count = cleanup_temp_folder(max_age_seconds=1, base_dir=tmpdir)
            assert count == 3

    def test_ignores_subdirs(self):
        """Unterordner werden nicht rekursiv gelöscht, nur Dateien im Base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "nested.txt"), "w") as fp:
                fp.write("x")
            with open(os.path.join(tmpdir, "top.txt"), "w") as fp:
                fp.write("x")
            time.sleep(1.1)
            count = cleanup_temp_folder(max_age_seconds=1, base_dir=tmpdir)
            assert count == 1
            assert os.path.exists(os.path.join(subdir, "nested.txt"))
