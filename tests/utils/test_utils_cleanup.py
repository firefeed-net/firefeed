import pytest
import asyncio
import tempfile
import os
import shutil
import time
from unittest.mock import patch, MagicMock, AsyncMock
from utils.cleanup import cleanup_old_files


class TestCleanup:
    """Test the cleanup utility functions"""
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files_success(self):
        """Test successful cleanup of old files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with different modification times
            current_time = time.time()
            
            # Create a file that should be deleted (older than 7 days)
            old_file_path = os.path.join(temp_dir, "old_file.txt")
            with open(old_file_path, 'w') as f:
                f.write("old content")
            # Set modification time to 8 days ago
            old_time = current_time - (8 * 24 * 60 * 60)
            os.utime(old_file_path, (old_time, old_time))
            
            # Create a file that should be kept (newer than 7 days)
            new_file_path = os.path.join(temp_dir, "new_file.txt")
            with open(new_file_path, 'w') as f:
                f.write("new content")
            # Set modification time to 1 day ago
            new_time = current_time - (1 * 24 * 60 * 60)
            os.utime(new_file_path, (new_time, new_time))
            
            # Run cleanup on the directory with default 7 days
            cleanup_old_files(temp_dir, days=7)
            
            # Verify the old file was deleted
            assert not os.path.exists(old_file_path)
            
            # Verify the new file was kept
            assert os.path.exists(new_file_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files_no_files_to_delete(self):
        """Test cleanup when no files need to be deleted"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create only new files
            current_time = time.time()
            new_file_path = os.path.join(temp_dir, "new_file.txt")
            with open(new_file_path, 'w') as f:
                f.write("new content")
            new_time = current_time - (1 * 24 * 60 * 60)
            os.utime(new_file_path, (new_time, new_time))
            
            # Run cleanup on the directory with default 7 days
            cleanup_old_files(temp_dir, days=7)
            
            # Verify the new file was kept
            assert os.path.exists(new_file_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files_empty_directory(self):
        """Test cleanup on empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Run cleanup on empty directory - should not raise exception
            cleanup_old_files(temp_dir, days=30)
            # Test passes if no exception is raised
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files_nonexistent_directory(self):
        """Test cleanup on non-existent directory"""
        non_existent_dir = "/tmp/non_existent_cleanup_test_dir"
        
        # Run cleanup on non-existent directory - should not raise exception
        cleanup_old_files(non_existent_dir, days=30)
        # Test passes if no exception is raised