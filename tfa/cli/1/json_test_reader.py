#!/usr/bin/env python3
"""
JSONTestReader - Reads test case results from JSON files
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class JSONTestReader:
    """Reads and validates test case results from JSON files."""
    
    def __init__(self):
        self.required_fields = ['test_name', 'status', 'message']
        self.optional_fields = ['file_path', 'line_number', 'duration', 'stack_trace', 'test_class']
    
    def read_test_results(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read test results from JSON file.
        
        Expected JSON format:
        {
            "test_results": [
                {
                    "test_name": "test_example",
                    "status": "passed|failed|skipped",
                    "message": "error message if failed",
                    "file_path": "path/to/test.py",
                    "line_number": 42,
                    "duration": 0.123,
                    "stack_trace": "full stack trace",
                    "test_class": "TestClass"
                }
            ]
        }
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Test results file not found: {file_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                test_results = data
            elif isinstance(data, dict):
                if 'test_results' in data:
                    test_results = data['test_results']
                elif 'tests' in data:
                    test_results = data['tests']
                elif 'results' in data:
                    test_results = data['results']
                else:
                    # Assume the dict itself contains test results
                    test_results = [data]
            else:
                raise ValueError("Invalid JSON format: expected list or dict")
            
            # Validate test results
            validated_results = []
            for i, test_result in enumerate(test_results):
                try:
                    validated_test = self._validate_test_result(test_result, i)
                    validated_results.append(validated_test)
                except ValueError as e:
                    print(f"Warning: Skipping invalid test result at index {i}: {e}")
                    continue
            
            return validated_results
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {file_path}: {e}")
        except Exception as e:
            raise Exception(f"Error reading test results from {file_path}: {e}")
    
    def _validate_test_result(self, test_result: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate and normalize a single test result."""
        if not isinstance(test_result, dict):
            raise ValueError(f"Test result must be a dictionary, got {type(test_result)}")
        
        # Check required fields
        for field in self.required_fields:
            if field not in test_result:
                raise ValueError(f"Missing required field '{field}' in test result")
        
        # Normalize status field
        status = test_result['status'].lower()
        if status not in ['passed', 'failed', 'skipped', 'error']:
            # Try to map common variations
            status_mapping = {
                'pass': 'passed',
                'fail': 'failed',
                'failure': 'failed',
                'skip': 'skipped',
                'success': 'passed',
                'ok': 'passed'
            }
            status = status_mapping.get(status, status)
            
            if status not in ['passed', 'failed', 'skipped', 'error']:
                raise ValueError(f"Invalid status '{test_result['status']}'. Must be one of: passed, failed, skipped, error")
        
        # Create normalized test result
        normalized_result = {
            'test_name': str(test_result['test_name']),
            'status': status,
            'message': str(test_result.get('message', '')),
            'file_path': str(test_result.get('file_path', '')),
            'line_number': test_result.get('line_number'),
            'duration': test_result.get('duration'),
            'stack_trace': str(test_result.get('stack_trace', '')),
            'test_class': str(test_result.get('test_class', '')),
            'original_index': index
        }
        
        return normalized_result
    
    def get_test_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary statistics of test results."""
        summary = {
            'total': len(test_results),
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 0
        }
        
        for test in test_results:
            status = test['status']
            if status in summary:
                summary[status] += 1
        
        return summary
    
    def validate_json_format(self, file_path: str) -> bool:
        """Validate if the JSON file has the expected format for test results."""
        try:
            test_results = self.read_test_results(file_path)
            return len(test_results) > 0
        except Exception:
            return False