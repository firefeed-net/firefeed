import pytest
from unittest.mock import patch, MagicMock, call
from utils.retry import retry_on_failure

class TestRetry:
    @patch('utils.retry.time.sleep')
    def test_retry_success_first_try(self, mock_sleep):
        func = MagicMock(return_value="success")
        result = retry_on_failure(func)
        assert result == "success"
        func.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('utils.retry.time.sleep')
    def test_retry_success_after_retry(self, mock_sleep):
        func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        result = retry_on_failure(func, max_retries=3)
        assert result == "success"
        assert func.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(1), call(2.0)])

    @patch('utils.retry.time.sleep')
    def test_retry_failure_all_attempts(self, mock_sleep):
        func = MagicMock(side_effect=Exception("fail"))
        with pytest.raises(Exception, match="fail"):
            retry_on_failure(func, max_retries=1)
        assert func.call_count == 2
        assert mock_sleep.call_count == 1