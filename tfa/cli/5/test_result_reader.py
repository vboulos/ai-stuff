#!/usr/bin/env python3
"""
TestResultReader - Reads test case results from JSON files
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TestCase:
    """Represents a single test case result."""
    name: str
    status: str
    failure_message: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    duration: Optional[float] = None
    framework: Optional[str] = None


class TestResultReader:
    """Reads and parses test case results from JSON files."""
    
    def __init__(self):
        """Initialize the test result reader."""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def read_json_file(self, file_path: str) -> List[TestCase]:
        """
        Read test results from a JSON file.
        
        Supports multiple JSON formats:
        - Format 1: {"test_results": [{"name": "test1", "status": "failed", "failure_message": "..."}]}
        - Format 2: {"failed_tests": [{"test_name": "test1", "failure_message": "..."}]}
        - Format 3: [{"test_name": "test1", "status": "failed", "error": "..."}]
        - Format 4: JUnit XML converted to JSON format
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of TestCase objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"Reading test results from: {file_path}")
            
            # Try different JSON formats
            test_cases = []
            
            if isinstance(data, list):
                # Format 3: Direct array of test results
                test_cases = self._parse_array_format(data)
            elif isinstance(data, dict):
                if 'test_results' in data:
                    # Format 1: Standard test results format
                    test_cases = self._parse_test_results_format(data['test_results'])
                elif 'failed_tests' in data:
                    # Format 2: Failed tests only format
                    test_cases = self._parse_failed_tests_format(data['failed_tests'])
                elif 'testsuites' in data:
                    # Format 4: JUnit XML style
                    test_cases = self._parse_junit_format(data)
                else:
                    # Try to infer format from keys
                    test_cases = self._infer_format(data)
            
            self.logger.info(f"Loaded {len(test_cases)} test cases")
            return test_cases
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading test results from {file_path}: {e}")
            return []
    
    def _parse_array_format(self, data: List[Dict[str, Any]]) -> List[TestCase]:
        """Parse array format JSON."""
        test_cases = []
        
        for item in data:
            test_case = TestCase(
                name=item.get('test_name') or item.get('name') or item.get('testName', 'Unknown Test'),
                status=item.get('status') or ('failed' if item.get('failure_message') or item.get('error') else 'passed'),
                failure_message=item.get('failure_message') or item.get('error') or item.get('message'),
                file_path=item.get('file_path') or item.get('file') or item.get('filename'),
                line_number=item.get('line_number') or item.get('line'),
                duration=item.get('duration') or item.get('time'),
                framework=item.get('framework')
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _parse_test_results_format(self, data: List[Dict[str, Any]]) -> List[TestCase]:
        """Parse standard test_results format."""
        test_cases = []
        
        for item in data:
            test_case = TestCase(
                name=item.get('name', 'Unknown Test'),
                status=item.get('status', 'unknown'),
                failure_message=item.get('failure_message') or item.get('error_message'),
                file_path=item.get('file_path') or item.get('file'),
                line_number=item.get('line_number'),
                duration=item.get('duration'),
                framework=item.get('framework')
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _parse_failed_tests_format(self, data: List[Dict[str, Any]]) -> List[TestCase]:
        """Parse failed_tests format (assumes all are failed)."""
        test_cases = []
        
        for item in data:
            test_case = TestCase(
                name=item.get('test_name', 'Unknown Test'),
                status='failed',
                failure_message=item.get('failure_message'),
                file_path=item.get('file_path'),
                line_number=item.get('line_number'),
                duration=item.get('duration'),
                framework=item.get('framework')
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _parse_junit_format(self, data: Dict[str, Any]) -> List[TestCase]:
        """Parse JUnit XML converted to JSON format."""
        test_cases = []
        
        testsuites = data.get('testsuites', {})
        if isinstance(testsuites, dict):
            testsuites = [testsuites]
        
        for testsuite in testsuites:
            suite_name = testsuite.get('name', 'Unknown Suite')
            testcases = testsuite.get('testcase', [])
            
            if isinstance(testcases, dict):
                testcases = [testcases]
            
            for testcase in testcases:
                name = f"{suite_name}.{testcase.get('name', 'Unknown Test')}"
                
                # Check for failure or error
                failure = testcase.get('failure') or testcase.get('error')
                status = 'failed' if failure else 'passed'
                failure_message = None
                
                if failure:
                    if isinstance(failure, dict):
                        failure_message = failure.get('message') or failure.get('text')
                    elif isinstance(failure, str):
                        failure_message = failure
                
                test_case = TestCase(
                    name=name,
                    status=status,
                    failure_message=failure_message,
                    file_path=testcase.get('file') or testcase.get('classname'),
                    duration=float(testcase.get('time', 0)),
                    framework='junit'
                )
                test_cases.append(test_case)
        
        return test_cases
    
    def _infer_format(self, data: Dict[str, Any]) -> List[TestCase]:
        """Try to infer the JSON format and parse accordingly."""
        test_cases = []
        
        # Look for common patterns
        for key, value in data.items():
            if isinstance(value, list) and value:
                # Check if this looks like test results
                first_item = value[0]
                if isinstance(first_item, dict):
                    if any(field in first_item for field in ['name', 'test_name', 'testName']):
                        self.logger.info(f"Inferred format: using key '{key}' as test results")
                        return self._parse_array_format(value)
        
        self.logger.warning("Could not infer JSON format, returning empty list")
        return test_cases
    
    def get_test_summary(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """
        Get a summary of test results.
        
        Args:
            test_cases: List of TestCase objects
            
        Returns:
            Dictionary with test summary statistics
        """
        total = len(test_cases)
        failed = sum(1 for tc in test_cases if tc.status == 'failed')
        passed = sum(1 for tc in test_cases if tc.status == 'passed')
        skipped = sum(1 for tc in test_cases if tc.status in ['skipped', 'skip'])
        other = total - failed - passed - skipped
        
        # Calculate total duration if available
        total_duration = sum(tc.duration for tc in test_cases if tc.duration is not None)
        
        # Get frameworks used
        frameworks = set(tc.framework for tc in test_cases if tc.framework)
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'other': other,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'total_duration': total_duration,
            'frameworks': list(frameworks)
        }
    
    def print_summary(self, test_cases: List[TestCase]):
        """Print a formatted summary of test results."""
        summary = self.get_test_summary(test_cases)
        
        print("\n📊 Test Results Summary")
        print("=" * 30)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        if summary['other'] > 0:
            print(f"❓ Other: {summary['other']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['total_duration'] > 0:
            print(f"Total Duration: {summary['total_duration']:.2f}s")
        
        if summary['frameworks']:
            print(f"Frameworks: {', '.join(summary['frameworks'])}")


def main():
    """Example usage of TestResultReader."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_result_reader.py <json_file>")
        sys.exit(1)
    
    reader = TestResultReader()
    test_cases = reader.read_json_file(sys.argv[1])
    
    if test_cases:
        reader.print_summary(test_cases)
        
        # Show failed tests
        failed_tests = [tc for tc in test_cases if tc.status == 'failed']
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for i, test in enumerate(failed_tests, 1):
                print(f"{i}. {test.name}")
                if test.failure_message:
                    print(f"   Error: {test.failure_message[:100]}...")
    else:
        print("No test cases found")


if __name__ == "__main__":
    main()