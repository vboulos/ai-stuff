#!/usr/bin/env python3
"""
TestReader - Reads JSON test results and filters failed tests
"""

import json
from typing import List, Dict


class TestReader:
    """Simple class to read test results and extract failed tests."""
    
    def read_failed_tests(self, json_file: str) -> List[Dict[str, str]]:
        """Read JSON file and return only failed tests."""
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            tests = data
        elif 'tests' in data:
            tests = data['tests']
        elif 'test_results' in data:
            tests = data['test_results']
        else:
            tests = [data]
        
        failed_tests = []
        for test in tests:
            status = test.get('status', '').lower()
            if status in ['failed', 'failure', 'error']:
                failed_tests.append({
                    'test_name': test.get('test_name', test.get('name', 'Unknown')),
                    'failure_message': test.get('message', test.get('error', ''))
                })
        
        return failed_tests