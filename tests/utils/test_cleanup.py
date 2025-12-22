import pytest
from unittest.mock import patch
from utils.cleanup import cleanup_temp_files, cleanup_old_files

class TestCleanup:
    @patch('utils.cleanup.shutil.rmtree')
    @patch('utils.cleanup.os.path.exists')
    def test_cleanup_temp_files_exists(self, mock_exists, mock_rmtree):
        mock_exists.return_value = True
        cleanup_temp_files("/tmp/test")
        mock_rmtree.assert_called_once_with("/tmp/test")

    @patch('utils.cleanup.shutil.rmtree')
    @patch('utils.cleanup.os.path.exists')
    def test_cleanup_temp_files_not_exists(self, mock_exists, mock_rmtree):
        mock_exists.return_value = False
        cleanup_temp_files("/tmp/test")
        mock_rmtree.assert_not_called()

    @patch('utils.cleanup.os.rmdir')
    @patch('utils.cleanup.os.listdir')
    @patch('utils.cleanup.os.remove')
    @patch('utils.cleanup.os.path.getmtime')
    @patch('utils.cleanup.os.walk')
    @patch('utils.cleanup.time.time')
    def test_cleanup_old_files(self, mock_time, mock_walk, mock_getmtime, mock_remove, mock_listdir, mock_rmdir):
        mock_time.return_value = 1000000000  # current time
        mock_walk.return_value = [
            ("/dir", ["subdir"], ["file1.txt", "file2.txt"]),
            ("/dir/subdir", [], ["oldfile.txt"])
        ]
        mock_getmtime.side_effect = lambda path: 900000000 if "old" in path else 1100000000  # old file mtime < cutoff
        mock_listdir.return_value = []  # empty subdir
        cleanup_old_files("/dir", days=1)
        mock_remove.assert_called_once_with("/dir/subdir/oldfile.txt")
        mock_rmdir.assert_called_once_with("/dir/subdir")