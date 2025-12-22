import pytest
from unittest.mock import patch
import runpy


class TestMain:
    @patch('uvicorn.run')
    def test_main_runs_uvicorn(self, mock_uvicorn_run):
        """Test that __main__.py runs uvicorn with correct parameters"""
        # Run the module as __main__ to execute the if block
        runpy.run_module('apps.api.__main__', run_name='__main__')

        # Assert that uvicorn.run was called with correct arguments
        mock_uvicorn_run.assert_called_once()
        args, kwargs = mock_uvicorn_run.call_args
        assert kwargs['host'] == "127.0.0.1"
        assert kwargs['port'] == 8000
        # The app should be passed as first positional argument
        from apps.api.app import app
        assert args[0] == app

    @patch('uvicorn.run')
    def test_main_py_runs_uvicorn(self, mock_uvicorn_run):
        """Test that main.py runs uvicorn with correct parameters"""
        # Run the module as __main__ to execute the if block
        runpy.run_module('apps.api.main', run_name='__main__')

        # Assert that uvicorn.run was called with correct arguments
        mock_uvicorn_run.assert_called_once()
        args, kwargs = mock_uvicorn_run.call_args
        assert kwargs['host'] == "127.0.0.1"
        assert kwargs['port'] == 8000
        # The app should be passed as first positional argument
        from apps.api.app import app
        assert args[0] == app