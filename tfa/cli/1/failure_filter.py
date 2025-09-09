#!/usr/bin/env python3
"""
FailureFilter - Filters and categorizes failed test cases
"""

from typing import Dict, List, Any, Optional
import re


class FailureFilter:
    """Filters test results to extract only failed tests and categorizes them."""
    
    def __init__(self):
        self.failure_patterns = {
            'assertion_error': [
                r'AssertionError',
                r'assert .+ == .+',
                r'Expected .+ but got .+',
                r'assert .+ is .+'
            ],
            'type_error': [
                r'TypeError',
                r"unsupported operand type",
                r"'NoneType' object",
                r"object has no attribute"
            ],
            'value_error': [
                r'ValueError',
                r'invalid literal',
                r'could not convert'
            ],
            'import_error': [
                r'ImportError',
                r'ModuleNotFoundError',
                r'No module named'
            ],
            'attribute_error': [
                r'AttributeError',
                r"object has no attribute",
                r"module .+ has no attribute"
            ],
            'index_error': [
                r'IndexError',
                r'list index out of range',
                r'string index out of range'
            ],
            'key_error': [
                r'KeyError',
                r'key not found'
            ],
            'timeout_error': [
                r'TimeoutError',
                r'timeout',
                r'took too long'
            ]
        }
    
    def filter_failed_tests(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract only failed test cases from test results."""
        failed_tests = []
        
        for test in test_results:
            if test['status'] in ['failed', 'error']:
                failed_tests.append(test)
        
        return failed_tests
    
    def categorize_failure(self, test_result: Dict[str, Any]) -> str:
        """Categorize the type of failure based on error message and stack trace."""
        message = test_result.get('message', '').lower()
        stack_trace = test_result.get('stack_trace', '').lower()
        
        # Combine message and stack trace for analysis
        full_error_text = f"{message} {stack_trace}"
        
        # Check each failure pattern
        for category, patterns in self.failure_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_error_text, re.IGNORECASE):
                    return category
        
        return 'unknown_error'
    
    def extract_error_details(self, test_result: Dict[str, Any]) -> Dict[str, str]:
        """Extract detailed error information from test result."""
        message = test_result.get('message', '')
        stack_trace = test_result.get('stack_trace', '')
        
        details = {
            'error_type': self._extract_error_type(message, stack_trace),
            'error_location': self._extract_error_location(stack_trace),
            'expected_vs_actual': self._extract_expected_actual(message),
            'failing_line': self._extract_failing_line(stack_trace),
            'category': self.categorize_failure(test_result)
        }
        
        return details
    
    def _extract_error_type(self, message: str, stack_trace: str) -> str:
        """Extract the specific error type from message or stack trace."""
        error_pattern = r'(\w+Error|\w+Exception):'
        
        # Try message first
        match = re.search(error_pattern, message)
        if match:
            return match.group(1)
        
        # Try stack trace
        match = re.search(error_pattern, stack_trace)
        if match:
            return match.group(1)
        
        return 'Unknown'
    
    def _extract_error_location(self, stack_trace: str) -> str:
        """Extract file and line number where error occurred."""
        # Look for patterns like 'File "path/file.py", line 123'
        pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(pattern, stack_trace)
        
        if matches:
            # Get the last match (usually the actual error location)
            file_path, line_num = matches[-1]
            return f"{file_path}:{line_num}"
        
        return 'Unknown'
    
    def _extract_expected_actual(self, message: str) -> str:
        """Extract expected vs actual values from assertion errors."""
        patterns = [
            r'assert (.+) == (.+)',
            r'Expected: (.+), Actual: (.+)',
            r'Expected (.+) but got (.+)',
            r'AssertionError: (.+) != (.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return f"Expected: {match.group(1).strip()}, Actual: {match.group(2).strip()}"
        
        return ''
    
    def _extract_failing_line(self, stack_trace: str) -> str:
        """Extract the actual line of code that failed."""
        lines = stack_trace.split('\n')
        
        # Look for lines that start with '>' or contain the actual code
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('>') and len(line) > 1:
                return line[1:].strip()
            elif (line and not line.startswith('File') and 
                  not line.startswith('Traceback') and 
                  not re.match(r'\w+Error:', line) and
                  len(line) > 10):  # Likely actual code
                return line
        
        return ''
    
    def group_failures_by_type(self, failed_tests: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group failed tests by their failure category."""
        grouped_failures = {}
        
        for test in failed_tests:
            category = self.categorize_failure(test)
            
            if category not in grouped_failures:
                grouped_failures[category] = []
            
            grouped_failures[category].append(test)
        
        return grouped_failures
    
    def get_failure_statistics(self, failed_tests: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get statistics about different types of failures."""
        stats = {}
        
        for test in failed_tests:
            category = self.categorize_failure(test)
            stats[category] = stats.get(category, 0) + 1
        
        return stats
    
    def prioritize_failures(self, failed_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize failures based on severity and type."""
        priority_order = {
            'import_error': 1,      # High priority - breaks imports
            'type_error': 2,        # High priority - fundamental type issues
            'attribute_error': 3,   # Medium-high priority
            'assertion_error': 4,   # Medium priority - logic errors
            'value_error': 5,       # Medium priority
            'index_error': 6,       # Medium-low priority
            'key_error': 7,         # Medium-low priority
            'timeout_error': 8,     # Low priority - often environmental
            'unknown_error': 9      # Lowest priority
        }
        
        def get_priority(test):
            category = self.categorize_failure(test)
            return priority_order.get(category, 10)
        
        return sorted(failed_tests, key=get_priority)