#!/usr/bin/env python3
"""
Complete TestReader - Reads JSON test results and filters failed tests
"""

import json
from typing import List, Dict, Any


class TestReader:
    """Reads JSON test results and extracts failed tests."""
    
    def read_failed_tests(self, json_file: str) -> List[Dict[str, str]]:
        """Read JSON file and return only failed tests with proper error handling."""
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File {json_file} not found")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {json_file}: {e}")
            return []
        except Exception as e:
            print(f"Error reading file {json_file}: {e}")
            return []
        
        # Handle different JSON structures
        tests = self._extract_tests(data)
        
        # Filter failed tests
        failed_tests = []
        for test in tests:
            if self._is_failed_test(test):
                failed_test = {
                    'test_name': self._get_test_name(test),
                    'failure_message': self._get_failure_message(test)
                }
                if failed_test['test_name'] and failed_test['failure_message']:
                    failed_tests.append(failed_test)
        
        return failed_tests
    
    def _extract_tests(self, data: Any) -> List[Dict[str, Any]]:
        """Extract test list from various JSON structures."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common keys
            for key in ['test_results', 'tests', 'results', 'testResults']:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # If no list found, treat the dict as a single test
            return [data]
        else:
            return []
    
    def _is_failed_test(self, test: Dict[str, Any]) -> bool:
        """Check if a test is failed/error status."""
        status = str(test.get('status', '')).lower()
        return status in ['failed', 'failure', 'error', 'fail']
    
    def _get_test_name(self, test: Dict[str, Any]) -> str:
        """Extract test name from various possible fields."""
        for key in ['test_name', 'name', 'testName', 'test', 'id']:
            if key in test and test[key]:
                return str(test[key])
        return 'Unknown Test'
    
    def _get_failure_message(self, test: Dict[str, Any]) -> str:
        """Extract failure message from various possible fields."""
        for key in ['message', 'error', 'failure_message', 'errorMessage', 'failureMessage', 'description']:
            if key in test and test[key]:
                return str(test[key])
        return 'No error message available'
    
    def print_summary(self, failed_tests: List[Dict[str, str]]) -> None:
        """Print summary of failed tests found."""
        print(f"Found {len(failed_tests)} failed tests:")
        for i, test in enumerate(failed_tests, 1):
            print(f"  {i}. {test['test_name']}")
            error_preview = test['failure_message'][:60] + "..." if len(test['failure_message']) > 60 else test['failure_message']
            print(f"     Error: {error_preview}")