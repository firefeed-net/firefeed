import pytest
from exceptions.database_exceptions import DatabaseException, DatabaseConnectionError, DatabaseQueryError


class TestDatabaseException:
    """Test the DatabaseException base class"""
    
    def test_database_exception_no_details(self):
        """Test DatabaseException with no details"""
        message = "Database operation failed"
        exception = DatabaseException(message)
        
        assert str(exception) == "Database operation failed"
        assert exception.message == "Database operation failed"
        assert exception.details == {}
    
    def test_database_exception_with_details(self):
        """Test DatabaseException with details"""
        message = "Database operation failed"
        details = {"operation": "insert", "table": "users"}
        exception = DatabaseException(message, details)
        
        assert str(exception) == "Database operation failed"
        assert exception.message == "Database operation failed"
        assert exception.details == {"operation": "insert", "table": "users"}


class TestDatabaseConnectionError:
    """Test the DatabaseConnectionError exception"""
    
    def test_database_connection_error_no_details(self):
        """Test DatabaseConnectionError with no details"""
        exception = DatabaseConnectionError()
        
        assert str(exception) == "Database connection failed"
        assert exception.message == "Database connection failed"
        assert exception.details == {}
    
    def test_database_connection_error_with_details(self):
        """Test DatabaseConnectionError with details"""
        details = {"host": "localhost", "port": 5432, "database": "firefeed"}
        exception = DatabaseConnectionError(details)
        
        assert str(exception) == "Database connection failed"
        assert exception.message == "Database connection failed"
        assert exception.details == {"host": "localhost", "port": 5432, "database": "firefeed"}
    
    def test_database_connection_error_inheritance(self):
        """Test that DatabaseConnectionError inherits from DatabaseException"""
        exception = DatabaseConnectionError()
        
        assert isinstance(exception, DatabaseException)
        assert isinstance(exception, Exception)


class TestDatabaseQueryError:
    """Test the DatabaseQueryError exception"""
    
    def test_database_query_error_no_details(self):
        """Test DatabaseQueryError with no details"""
        query = "SELECT * FROM users"
        error = "Connection timeout"
        exception = DatabaseQueryError(query, error)
        
        assert str(exception) == "Database query failed: Connection timeout"
        assert exception.message == "Database query failed: Connection timeout"
        assert exception.query == "SELECT * FROM users"
        assert exception.error == "Connection timeout"
        assert exception.details == {}
    
    def test_database_query_error_with_details(self):
        """Test DatabaseQueryError with details"""
        query = "INSERT INTO users (name) VALUES (?)"
        error = "Constraint violation"
        details = {"constraint": "unique_name", "value": "test"}
        exception = DatabaseQueryError(query, error, details)
        
        assert str(exception) == "Database query failed: Constraint violation"
        assert exception.message == "Database query failed: Constraint violation"
        assert exception.query == "INSERT INTO users (name) VALUES (?)"
        assert exception.error == "Constraint violation"
        assert exception.details == {"constraint": "unique_name", "value": "test"}
    
    def test_database_query_error_inheritance(self):
        """Test that DatabaseQueryError inherits from DatabaseException"""
        query = "SELECT 1"
        error = "Syntax error"
        exception = DatabaseQueryError(query, error)
        
        assert isinstance(exception, DatabaseException)
        assert isinstance(exception, Exception)