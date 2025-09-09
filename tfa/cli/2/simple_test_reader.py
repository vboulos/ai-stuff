#!/usr/bin/env python3
"""
Simple JSON Test Reader - Reads test results and filters failed tests
"""

import json
from typing import List, Dict, Any


class SimpleTestReader:
    """Reads JSON test results and extracts failed tests."""
    
    def read_test_results(self, file_path: str) -> List[Dict[str, Any]]:
        """Read test results from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif 'test_results' in data:
            return data['test_results']
        elif 'tests' in data:
            return data['tests']
        else:
            return [data]
    
    def get_failed_tests(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract only failed test cases."""
        failed_tests = []
        
        for test in test_results:
            status = test.get('status', '').lower()
            if status in ['failed', 'failure', 'error']:
                # Ensure we have required fields
                failed_test = {
                    'test_name': test.get('test_name', test.get('name', 'Unknown')),
                    'failure_message': test.get('message', test.get('error', test.get('failure_message', '')))
                }
                failed_tests.append(failed_test)
        
        return failed_tests