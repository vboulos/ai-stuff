#!/usr/bin/env python3
"""
Test Failure Fix Generator
Analyzes test failures and provides specific code fix suggestions.
"""

import json
import re
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FailureType(Enum):
    AUTHENTICATION = "authentication"
    DATABASE_CONNECTION = "database_connection"
    API_TIMEOUT = "api_timeout"
    VALIDATION_ERROR = "validation_error"
    ELEMENT_NOT_FOUND = "element_not_found"
    TEXT_MISMATCH = "text_mismatch"
    ASSERTION_ERROR = "assertion_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


@dataclass
class FixSuggestion:
    failure_type: FailureType
    root_cause: str
    suggested_fix: str
    code_example: str
    confidence_score: float
    additional_notes: List[str]


class TestFailureAnalyzer:
    def __init__(self):
        self.failure_patterns = {
            # Authentication patterns
            r"(?i)(authentication|auth|login|token|401|unauthorized)": FailureType.AUTHENTICATION,
            r"(?i)(invalid.*token|expired.*token|missing.*token)": FailureType.AUTHENTICATION,
            
            # Database patterns
            r"(?i)(database|db|connection.*refused|psycopg2|mysql|sqlite)": FailureType.DATABASE_CONNECTION,
            r"(?i)(server.*running|tcp.*connections|port.*5432|port.*3306)": FailureType.DATABASE_CONNECTION,
            
            # API/Network patterns
            r"(?i)(timeout|request.*timed.*out|connection.*timeout)": FailureType.API_TIMEOUT,
            r"(?i)(rate.*limit|too.*many.*requests|429)": FailureType.API_TIMEOUT,
            
            # Validation patterns
            r"(?i)(invalid.*literal|valueerror|int.*base.*10)": FailureType.VALIDATION_ERROR,
            r"(?i)(validation.*failed|invalid.*input|parse.*error)": FailureType.VALIDATION_ERROR,
            
            # UI/Element patterns
            r"(?i)(element.*not.*found|expected.*to.*find.*element)": FailureType.ELEMENT_NOT_FOUND,
            r"(?i)(selector.*not.*found|#.*but.*never.*found)": FailureType.ELEMENT_NOT_FOUND,
            
            # Text matching patterns
            r"(?i)(expected.*to.*contain.*text|text.*was.*but.*expected)": FailureType.TEXT_MISMATCH,
            r"(?i)(string.*mismatch|content.*mismatch)": FailureType.TEXT_MISMATCH,
            
            # General assertion patterns
            r"(?i)(assertionerror|assertion.*failed|expected.*but.*got)": FailureType.ASSERTION_ERROR,
        }
    
    def detect_failure_type(self, failure_message: str) -> FailureType:
        """Detect the type of failure based on the error message."""
        for pattern, failure_type in self.failure_patterns.items():
            if re.search(pattern, failure_message):
                return failure_type
        return FailureType.UNKNOWN
    
    def generate_fix_suggestion(self, test_data: Dict) -> FixSuggestion:
        """Generate a fix suggestion for a test failure."""
        test_name = test_data.get("test_name", "")
        failure_message = test_data.get("failure_message", "")
        test_code = test_data.get("test_code", "")
        file_path = test_data.get("file_path", "")
        
        failure_type = self.detect_failure_type(failure_message)
        
        if failure_type == FailureType.AUTHENTICATION:
            return self._generate_auth_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.DATABASE_CONNECTION:
            return self._generate_db_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.API_TIMEOUT:
            return self._generate_api_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.VALIDATION_ERROR:
            return self._generate_validation_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.ELEMENT_NOT_FOUND:
            return self._generate_element_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.TEXT_MISMATCH:
            return self._generate_text_fix(test_name, failure_message, test_code)
        elif failure_type == FailureType.ASSERTION_ERROR:
            return self._generate_assertion_fix(test_name, failure_message, test_code)
        else:
            return self._generate_unknown_fix(test_name, failure_message, test_code)
    
    def _generate_auth_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for authentication-related failures."""
        if "401" in failure_message or "unauthorized" in failure_message.lower():
            root_cause = "Test is using invalid or expired authentication credentials"
            suggested_fix = "Use valid test credentials or mock the authentication system"
            code_example = '''# Fix Option 1: Use valid test token
def test_user_authentication():
    valid_token = get_valid_test_token()  # Create helper function
    response = authenticate_user(valid_token)
    assert response.status_code == 200
    assert response.json()['user_id'] is not None

# Fix Option 2: Mock authentication
from unittest.mock import patch, MagicMock

@patch('your_module.authenticate_user')
def test_user_authentication(mock_auth):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'user_id': 'test_user_123'}
    mock_auth.return_value = mock_response
    
    response = authenticate_user('any_token')
    assert response.status_code == 200
    assert response.json()['user_id'] is not None'''
            confidence_score = 0.9
            additional_notes = [
                "Consider creating separate tests for valid and invalid authentication",
                "Use environment variables for test credentials",
                "Implement proper test data fixtures"
            ]
        else:
            root_cause = "Authentication system configuration issue"
            suggested_fix = "Check authentication configuration and test setup"
            code_example = "# Review authentication middleware and test configuration"
            confidence_score = 0.6
            additional_notes = ["Review logs for more specific authentication errors"]
        
        return FixSuggestion(
            failure_type=FailureType.AUTHENTICATION,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_db_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for database connection failures."""
        root_cause = "Database server is not running or not accessible from test environment"
        suggested_fix = "Use database mocking, in-memory database, or containerized test database"
        
        code_example = '''# Fix Option 1: Mock database connection
import pytest
from unittest.mock import patch, MagicMock

@patch('psycopg2.connect')
def test_database_connection(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [1]
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn
    
    conn = psycopg2.connect(
        host='localhost',
        database='testdb',
        user='testuser',
        password='testpass'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    assert result[0] == 1

# Fix Option 2: Use test database fixture
@pytest.fixture(scope="session")
def test_db():
    # Use Docker container or in-memory SQLite
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    # Setup test schema
    return engine

def test_database_connection(test_db):
    # Use test_db fixture instead of localhost connection
    pass'''
        
        confidence_score = 0.8
        additional_notes = [
            "Consider using Docker for consistent test database setup",
            "Use pytest fixtures for database setup/teardown",
            "Implement database migration scripts for test data"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.DATABASE_CONNECTION,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_api_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for API timeout and rate limiting failures."""
        if "timeout" in failure_message.lower():
            root_cause = "API requests are timing out, possibly due to network issues or server overload"
            suggested_fix = "Mock API responses or reduce timeout values and request frequency"
            code_example = '''# Fix Option 1: Mock API responses
import responses
import requests

@responses.activate
def test_api_rate_limiting():
    # Mock the API endpoint
    responses.add(
        responses.GET,
        'https://api.example.com/data',
        json={'data': 'test_response'},
        status=200
    )
    
    # Now requests will be mocked and won't timeout
    for i in range(100):
        response = requests.get('https://api.example.com/data', timeout=5)
        assert response.status_code == 200
    
    final_response = requests.get('https://api.example.com/data', timeout=5)
    assert final_response.status_code == 200

# Fix Option 2: Reduce test scope
def test_api_rate_limiting_realistic():
    # Test with fewer requests and shorter timeout
    for i in range(5):  # Reduced from 100
        try:
            response = requests.get('https://api.example.com/data', timeout=10)
            assert response.status_code in [200, 429]  # Accept rate limit responses
        except requests.exceptions.Timeout:
            pytest.skip("API timeout - network issue")'''
        else:
            root_cause = "Rate limiting or network connectivity issues"
            suggested_fix = "Implement proper retry logic and handle rate limiting gracefully"
            code_example = '''# Implement retry logic with backoff
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def test_api_with_retry():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    response = session.get('https://api.example.com/data', timeout=30)
    assert response.status_code == 200'''
        
        confidence_score = 0.85
        additional_notes = [
            "Consider using circuit breaker pattern for API calls",
            "Implement proper logging for API failures",
            "Use test doubles for external API dependencies"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.API_TIMEOUT,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_validation_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for validation and data conversion errors."""
        root_cause = "Input validation function lacks proper error handling for invalid data types"
        suggested_fix = "Add try-catch blocks and proper input validation to handle edge cases"
        
        code_example = '''# Fix the validation function
def validate_age(age_str):
    """Validate and convert age string to integer with proper error handling."""
    if age_str is None:
        return None
    
    try:
        age = int(age_str)
        # Add reasonable bounds checking
        if age < 0 or age > 150:
            return None
        return age
    except (ValueError, TypeError):
        return None

# Updated test with proper assertions
def test_data_validation():
    # Test valid age
    assert validate_age('25') == 25
    assert validate_age('0') == 0
    
    # Test invalid ages - should return None
    assert validate_age('abc') is None
    assert validate_age('-5') is None
    assert validate_age('200') is None
    assert validate_age(None) is None
    assert validate_age('') is None
    
    # Test edge cases
    assert validate_age('25.5') is None  # Float string
    assert validate_age(' 25 ') == 25   # Whitespace handling'''
        
        confidence_score = 0.9
        additional_notes = [
            "Consider using a validation library like Pydantic or marshmallow",
            "Add logging for validation failures in production code",
            "Implement comprehensive input sanitization"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.VALIDATION_ERROR,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_element_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for UI element not found errors."""
        # Extract element selector from error message
        selector_match = re.search(r'[`#]([^`\']*)[`\']', failure_message)
        selector = selector_match.group(1) if selector_match else "unknown-selector"
        
        root_cause = f"UI element with selector '{selector}' is not present on the page when test runs"
        suggested_fix = "Add proper wait conditions, verify page state, or update selectors"
        
        code_example = f'''# Fix Option 1: Add explicit wait for element
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def test_element_interaction():
    # Wait for element to be present
    wait = WebDriverWait(driver, 10)
    element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#{selector}"))
    )
    assert element is not None

# Fix Option 2: Check element existence conditionally
def test_element_with_fallback():
    try:
        element = driver.find_element(By.CSS_SELECTOR, "#{selector}")
        # Perform actions on element
        element.click()
    except NoSuchElementException:
        # Log the actual page state for debugging
        print(f"Page source: {{driver.page_source[:500]}}")
        # Use alternative selector or skip test
        pytest.skip(f"Element #{selector} not found - possible UI change")

# Fix Option 3: Verify page navigation first
def test_with_page_verification():
    # Ensure we're on the correct page
    assert "expected-page-title" in driver.title
    # Wait for page to fully load
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    # Now look for element
    element = driver.find_element(By.CSS_SELECTOR, "#{selector}")'''
        
        confidence_score = 0.8
        additional_notes = [
            "Check if the selector has changed in recent UI updates",
            "Verify test is running against correct environment/page",
            "Consider using data-testid attributes for more stable selectors",
            "Add screenshot capture on element not found for debugging"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.ELEMENT_NOT_FOUND,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_text_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for text content mismatch errors."""
        # Extract expected and actual text from error message
        expected_match = re.search(r"expected.*?['\"]([^'\"]*)['\"]", failure_message, re.IGNORECASE)
        actual_match = re.search(r"(?:but the text was|actual).*?['\"]([^'\"]*)['\"]", failure_message, re.IGNORECASE)
        
        expected_text = expected_match.group(1) if expected_match else "expected text"
        actual_text = actual_match.group(1) if actual_match else "actual text"
        
        # Check for common text issues
        if expected_text.replace(" ", "") == actual_text.replace(" ", ""):
            root_cause = "Text content matches but has spacing differences (missing space between sentences)"
            suggested_fix = "Fix spacing in the source content or normalize text in test"
            confidence_score = 0.95
        else:
            root_cause = "Text content on page doesn't match expected test value"
            suggested_fix = "Update test expectation or fix source content generation"
            confidence_score = 0.7
        
        code_example = f'''# Fix Option 1: Normalize whitespace in test
def normalize_text(text):
    """Normalize whitespace for text comparison."""
    import re
    return re.sub(r'\\s+', ' ', text.strip())

def test_text_content():
    element = driver.find_element(By.CSS_SELECTOR, "dd.pf-v5-c-description-list__description")
    actual_text = normalize_text(element.text)
    expected_text = normalize_text("{expected_text}")
    assert expected_text in actual_text

# Fix Option 2: Use partial text matching
def test_text_content_partial():
    element = driver.find_element(By.CSS_SELECTOR, "dd.pf-v5-c-description-list__description")
    # Check for key phrases instead of exact match
    assert "Policy is placed on hub" in element.text
    assert "Creates a velero Schedule" in element.text
    assert "backup-vm label" in element.text

# Fix Option 3: Fix source content (if you control the content)
# In your application code, ensure proper spacing:
description = f"Policy is placed on hub or managed clusters with label {{label}}. Creates a velero Schedule..."
#                                                                    ^ Add space here

# Fix Option 4: Use regex for flexible matching
import re

def test_text_content_regex():
    element = driver.find_element(By.CSS_SELECTOR, "dd.pf-v5-c-description-list__description")
    # Pattern allows for optional spacing issues
    pattern = r"Policy is placed.*?acm-dr-virt-config-file-name\\.?\\s*Creates a velero Schedule"
    assert re.search(pattern, element.text, re.DOTALL)'''
        
        additional_notes = [
            "Check if content is dynamically generated and may have timing issues",
            "Consider if text content changes between environments",
            "Use data-testid attributes instead of text content when possible",
            "Add logging to capture actual vs expected text for debugging"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.TEXT_MISMATCH,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_assertion_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate fix for general assertion errors."""
        root_cause = "Test assertion failed - expected behavior doesn't match actual behavior"
        suggested_fix = "Review test logic and verify expected vs actual values"
        
        code_example = '''# General assertion error debugging approach
def test_with_better_assertions():
    # Add detailed logging before assertions
    actual_value = get_actual_value()
    expected_value = get_expected_value()
    
    print(f"Expected: {expected_value}")
    print(f"Actual: {actual_value}")
    print(f"Type expected: {type(expected_value)}")
    print(f"Type actual: {type(actual_value)}")
    
    # Use more descriptive assertion messages
    assert actual_value == expected_value, f"Expected {expected_value}, but got {actual_value}"
    
    # Or use pytest's detailed assertions
    import pytest
    assert actual_value == expected_value  # pytest will show detailed diff'''
        
        confidence_score = 0.5
        additional_notes = [
            "Add more detailed logging to understand the failure",
            "Check if test data setup is correct",
            "Verify test environment matches expected conditions",
            "Consider if the assertion logic is correct"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.ASSERTION_ERROR,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )
    
    def _generate_unknown_fix(self, test_name: str, failure_message: str, test_code: str) -> FixSuggestion:
        """Generate generic fix for unknown failure types."""
        root_cause = "Unable to determine specific failure type from error message"
        suggested_fix = "Review error message and test code for specific issues"
        
        code_example = '''# General debugging approach for unknown failures
def debug_test_failure():
    try:
        # Original test code here
        pass
    except Exception as e:
        # Add detailed error logging
        import traceback
        print(f"Test failed with: {type(e).__name__}: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Log test environment state
        print(f"Test environment: {os.environ.get('TEST_ENV', 'unknown')}")
        
        # Re-raise for pytest to handle
        raise'''
        
        confidence_score = 0.3
        additional_notes = [
            "Add more specific error handling and logging",
            "Check for environment-specific issues",
            "Review recent code changes that might affect this test",
            "Consider consulting documentation or team members"
        ]
        
        return FixSuggestion(
            failure_type=FailureType.UNKNOWN,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            code_example=code_example,
            confidence_score=confidence_score,
            additional_notes=additional_notes
        )


def analyze_test_failures(input_file: str, output_file: str = None) -> Dict:
    """Analyze test failures and generate fix suggestions."""
    analyzer = TestFailureAnalyzer()
    
    # Read input file
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return {}
    
    # Process failed tests
    failed_tests = data.get("failed_tests", [])
    results = []
    
    for test in failed_tests:
        try:
            fix_suggestion = analyzer.generate_fix_suggestion(test)
            
            result = {
                "test_name": test.get("test_name"),
                "failure_message": test.get("failure_message"),
                "file_path": test.get("file_path"),
                "line_number": test.get("line_number"),
                "failure_type": fix_suggestion.failure_type.value,
                "root_cause": fix_suggestion.root_cause,
                "suggested_fix": fix_suggestion.suggested_fix,
                "code_example": fix_suggestion.code_example,
                "confidence_score": fix_suggestion.confidence_score,
                "additional_notes": fix_suggestion.additional_notes,
                "analysis_successful": True,
                "error_message": None
            }
        except Exception as e:
            result = {
                "test_name": test.get("test_name"),
                "failure_message": test.get("failure_message"),
                "analysis_successful": False,
                "error_message": str(e),
                "confidence_score": 0.0
            }
        
        results.append(result)
    
    # Create output data
    output_data = {
        "analysis_summary": {
            "total_failures": len(failed_tests),
            "successful_analyses": sum(1 for r in results if r.get("analysis_successful", False)),
            "failed_analyses": sum(1 for r in results if not r.get("analysis_successful", True)),
            "average_confidence": sum(r.get("confidence_score", 0) for r in results) / len(results) if results else 0,
            "generated_by": "Test Failure Fix Generator",
            "timestamp": __import__('datetime').datetime.now().strftime("%c")
        },
        "fix_suggestions": results
    }
    
    # Write output file
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Fix suggestions written to {output_file}")
    
    return output_data


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print("Usage: python test_failure_fix_generator.py <input_file> [output_file]")
        print("Example: python test_failure_fix_generator.py enhanced_test_failures.json fix_suggestions.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "fix_suggestions.json"
    
    results = analyze_test_failures(input_file, output_file)
    
    # Print summary
    summary = results.get("analysis_summary", {})
    print(f"\nAnalysis Complete:")
    print(f"Total failures analyzed: {summary.get('total_failures', 0)}")
    print(f"Successful analyses: {summary.get('successful_analyses', 0)}")
    print(f"Average confidence: {summary.get('average_confidence', 0):.2f}")


if __name__ == "__main__":
    main()