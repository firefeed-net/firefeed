import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
from utils.retry import retry_operation, retry_db_operation, retry_api_call, retry_file_operation, retry_on_failure


class TestRetryOperation:
    """Test the retry_operation decorator"""
    
    @pytest.mark.asyncio
    async def test_retry_operation_success_first_attempt(self):
        """Test that retry operation succeeds on first attempt"""
        call_count = 0
        
        @retry_operation(max_attempts=3, backoff_multiplier=0.5, max_backoff=10.0)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_operation_success_after_retry(self):
        """Test that retry operation succeeds after initial failures"""
        call_count = 0
        
        @retry_operation(max_attempts=3, backoff_multiplier=0.5, max_backoff=10.0)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_operation_max_attempts_reached(self):
        """Test that retry operation fails after max attempts"""
        call_count = 0
        
        @retry_operation(max_attempts=3, backoff_multiplier=0.5, max_backoff=10.0)
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")
        
        with pytest.raises(Exception, match="Persistent failure"):
            await test_func()
        
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_operation_custom_parameters(self):
        """Test retry operation with custom parameters"""
        call_count = 0
        
        @retry_operation(max_attempts=2, backoff_multiplier=1.0, max_backoff=5.0)
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = await test_func()
        
        assert result == "success"
        assert call_count == 2


class TestReadyMadeDecorators:
    """Test the ready-made retry decorators"""
    
    @pytest.mark.asyncio
    async def test_retry_db_operation(self):
        """Test the retry_db_operation decorator"""
        call_count = 0
        
        @retry_db_operation
        async def test_db_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("DB connection failed")
            return "db_success"
        
        result = await test_db_func()
        
        assert result == "db_success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_api_call(self):
        """Test the retry_api_call decorator"""
        call_count = 0
        
        @retry_api_call
        async def test_api_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API timeout")
            return "api_success"
        
        result = await test_api_func()
        
        assert result == "api_success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_file_operation(self):
        """Test the retry_file_operation decorator"""
        call_count = 0
        
        @retry_file_operation
        async def test_file_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("File locked")
            return "file_success"
        
        result = await test_file_func()
        
        assert result == "file_success"
        assert call_count == 2


class TestRetryOnFailure:
    """Test the retry_on_failure function"""
    
    def test_retry_on_failure_success_first_attempt(self):
        """Test retry_on_failure succeeds on first attempt"""
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = retry_on_failure(test_func, max_retries=3, delay=0.1)
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure_success_after_retry(self):
        """Test retry_on_failure succeeds after initial failures"""
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = retry_on_failure(test_func, max_retries=3, delay=0.1)
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_failure_max_retries_reached(self):
        """Test retry_on_failure fails after max retries"""
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")
        
        with pytest.raises(Exception, match="Persistent failure"):
            retry_on_failure(test_func, max_retries=3, delay=0.1)
        
        assert call_count == 4  # Initial attempt + 3 retries
    
    def test_retry_on_failure_exponential_backoff(self):
        """Test retry_on_failure uses exponential backoff"""
        call_count = 0
        delays = []
        
        def mock_sleep(delay):
            delays.append(delay)
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        with patch('utils.retry.time.sleep', side_effect=mock_sleep):
            result = retry_on_failure(test_func, max_retries=3, delay=0.1)
        
        assert result == "success"
        assert call_count == 3
        # Check that delays follow exponential backoff pattern
        assert len(delays) == 2  # Two retries
        assert delays[0] == 0.1  # First retry delay
        assert delays[1] == 0.2  # Second retry delay (0.1 * 2)
    
    def test_retry_on_failure_logging(self):
        """Test retry_on_failure logs retry attempts"""
        call_count = 0
        
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        with patch('utils.retry.logger') as mock_logger:
            result = retry_on_failure(test_func, max_retries=3, delay=0.1)
            
            assert result == "success"
            assert call_count == 2
            # Verify warning was logged for the failed attempt
            mock_logger.warning.assert_called_once()
            assert "Attempt 1 failed" in str(mock_logger.warning.call_args)
            assert "Retrying in 0.1s" in str(mock_logger.warning.call_args)