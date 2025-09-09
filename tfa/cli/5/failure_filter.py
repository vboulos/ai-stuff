#!/usr/bin/env python3
"""
FailureFilter - Filters and selects failed test cases
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from test_result_reader import TestCase


@dataclass
class FailedTestCase:
    """Represents a failed test case with additional context."""
    name: str
    failure_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    framework: Optional[str] = None
    duration: Optional[float] = None
    severity: str = "medium"  # low, medium, high, critical
    category: Optional[str] = None  # assertion, timeout, connection, etc.


class FailureFilter:
    """Filters test cases to extract only failed ones with categorization."""
    
    def __init__(self):
        """Initialize the failure filter."""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def extract_failed_tests(self, test_cases: List[TestCase]) -> List[FailedTestCase]:
        """
        Extract only failed test cases from the list.
        
        Args:
            test_cases: List of all test cases
            
        Returns:
            List of FailedTestCase objects
        """
        failed_tests = []
        
        for test_case in test_cases:
            if self._is_failed_test(test_case):
                failed_test = self._convert_to_failed_test(test_case)
                failed_tests.append(failed_test)
        
        self.logger.info(f"Filtered {len(failed_tests)} failed tests from {len(test_cases)} total tests")
        return failed_tests
    
    def _is_failed_test(self, test_case: TestCase) -> bool:
        """
        Determine if a test case represents a failure.
        
        Args:
            test_case: TestCase to check
            
        Returns:
            True if the test is considered failed
        """
        # Check explicit status
        if test_case.status and test_case.status.lower() in ['failed', 'failure', 'error']:
            return True
        
        # Check if there's a failure message (implies failure)
        if test_case.failure_message and test_case.failure_message.strip():
            return True
        
        return False
    
    def _convert_to_failed_test(self, test_case: TestCase) -> FailedTestCase:
        """
        Convert a TestCase to a FailedTestCase with additional analysis.
        
        Args:
            test_case: TestCase to convert
            
        Returns:
            FailedTestCase with categorization and severity
        """
        failure_message = test_case.failure_message or "No failure message provided"
        
        # Analyze failure to determine category and severity
        category = self._categorize_failure(failure_message)
        severity = self._assess_severity(failure_message, category)
        
        return FailedTestCase(
            name=test_case.name,
            failure_message=failure_message,
            file_path=test_case.file_path,
            line_number=test_case.line_number,
            framework=test_case.framework,
            duration=test_case.duration,
            category=category,
            severity=severity
        )
    
    def _categorize_failure(self, failure_message: str) -> str:
        """
        Categorize the type of failure based on the failure message.
        
        Args:
            failure_message: The failure message text
            
        Returns:
            Category string
        """
        message_lower = failure_message.lower()
        
        # Assertion failures
        if any(keyword in message_lower for keyword in ['assertion', 'assert', 'expected', 'actual']):
            return "assertion"
        
        # Timeout failures
        if any(keyword in message_lower for keyword in ['timeout', 'timed out', 'time limit', 'deadline']):
            return "timeout"
        
        # Connection failures
        if any(keyword in message_lower for keyword in ['connection', 'connect', 'refused', 'unreachable', 'network']):
            return "connection"
        
        # Authentication/Authorization failures
        if any(keyword in message_lower for keyword in ['auth', '401', '403', 'unauthorized', 'forbidden', 'permission']):
            return "authentication"
        
        # File/Resource not found
        if any(keyword in message_lower for keyword in ['not found', '404', 'missing', 'does not exist']):
            return "not_found"
        
        # Configuration/Setup issues
        if any(keyword in message_lower for keyword in ['config', 'setup', 'environment', 'missing dependency']):
            return "configuration"
        
        # Syntax/Compilation errors
        if any(keyword in message_lower for keyword in ['syntax', 'compile', 'parse', 'invalid syntax']):
            return "syntax"
        
        # Memory/Resource issues
        if any(keyword in message_lower for keyword in ['memory', 'out of', 'resource', 'limit exceeded']):
            return "resource"
        
        # Database issues
        if any(keyword in message_lower for keyword in ['sql', 'database', 'db', 'postgresql', 'mysql', 'mongo']):
            return "database"
        
        # UI/Selenium issues
        if any(keyword in message_lower for keyword in ['selenium', 'element', 'locator', 'xpath', 'css selector', 'click']):
            return "ui_automation"
        
        # API/HTTP issues
        if any(keyword in message_lower for keyword in ['http', 'api', 'rest', 'status code', 'response']):
            return "api"
        
        return "unknown"
    
    def _assess_severity(self, failure_message: str, category: str) -> str:
        """
        Assess the severity of the failure.
        
        Args:
            failure_message: The failure message text
            category: The failure category
            
        Returns:
            Severity level: low, medium, high, critical
        """
        message_lower = failure_message.lower()
        
        # Critical issues
        if any(keyword in message_lower for keyword in ['critical', 'fatal', 'crash', 'segmentation fault', 'core dump']):
            return "critical"
        
        # High severity issues
        if category in ['connection', 'database', 'authentication'] or \
           any(keyword in message_lower for keyword in ['server error', '500', 'internal error', 'exception']):
            return "high"
        
        # Medium severity issues
        if category in ['timeout', 'api', 'configuration'] or \
           any(keyword in message_lower for keyword in ['warning', 'deprecated']):
            return "medium"
        
        # Low severity issues
        if category in ['assertion', 'ui_automation'] or \
           any(keyword in message_lower for keyword in ['minor', 'cosmetic']):
            return "low"
        
        # Default to medium
        return "medium"
    
    def filter_by_category(self, failed_tests: List[FailedTestCase], categories: List[str]) -> List[FailedTestCase]:
        """
        Filter failed tests by specific categories.
        
        Args:
            failed_tests: List of failed test cases
            categories: List of categories to include
            
        Returns:
            Filtered list of failed test cases
        """
        filtered = [test for test in failed_tests if test.category in categories]
        self.logger.info(f"Filtered to {len(filtered)} tests in categories: {', '.join(categories)}")
        return filtered
    
    def filter_by_severity(self, failed_tests: List[FailedTestCase], min_severity: str = "medium") -> List[FailedTestCase]:
        """
        Filter failed tests by minimum severity level.
        
        Args:
            failed_tests: List of failed test cases
            min_severity: Minimum severity level (low, medium, high, critical)
            
        Returns:
            Filtered list of failed test cases
        """
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order.get(min_severity, 1)
        
        filtered = [test for test in failed_tests 
                   if severity_order.get(test.severity, 1) >= min_level]
        
        self.logger.info(f"Filtered to {len(filtered)} tests with severity >= {min_severity}")
        return filtered
    
    def group_by_category(self, failed_tests: List[FailedTestCase]) -> Dict[str, List[FailedTestCase]]:
        """
        Group failed tests by category.
        
        Args:
            failed_tests: List of failed test cases
            
        Returns:
            Dictionary mapping categories to lists of test cases
        """
        groups = {}
        
        for test in failed_tests:
            category = test.category or "unknown"
            if category not in groups:
                groups[category] = []
            groups[category].append(test)
        
        return groups
    
    def get_failure_statistics(self, failed_tests: List[FailedTestCase]) -> Dict[str, Any]:
        """
        Get statistics about failure patterns.
        
        Args:
            failed_tests: List of failed test cases
            
        Returns:
            Dictionary with failure statistics
        """
        if not failed_tests:
            return {}
        
        # Category distribution
        categories = {}
        severities = {}
        frameworks = {}
        
        for test in failed_tests:
            # Count categories
            category = test.category or "unknown"
            categories[category] = categories.get(category, 0) + 1
            
            # Count severities
            severity = test.severity
            severities[severity] = severities.get(severity, 0) + 1
            
            # Count frameworks
            framework = test.framework or "unknown"
            frameworks[framework] = frameworks.get(framework, 0) + 1
        
        # Calculate average duration for failed tests
        durations = [test.duration for test in failed_tests if test.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_failures': len(failed_tests),
            'categories': categories,
            'severities': severities,
            'frameworks': frameworks,
            'average_failure_duration': avg_duration,
            'most_common_category': max(categories.items(), key=lambda x: x[1])[0] if categories else None,
            'most_common_severity': max(severities.items(), key=lambda x: x[1])[0] if severities else None
        }
    
    def print_failure_summary(self, failed_tests: List[FailedTestCase]):
        """Print a detailed summary of failure analysis."""
        stats = self.get_failure_statistics(failed_tests)
        
        if not stats:
            print("No failure statistics available")
            return
        
        print("\n🔍 Failure Analysis Summary")
        print("=" * 40)
        print(f"Total Failures: {stats['total_failures']}")
        
        if stats['most_common_category']:
            print(f"Most Common Category: {stats['most_common_category']}")
        
        if stats['most_common_severity']:
            print(f"Most Common Severity: {stats['most_common_severity']}")
        
        if stats['average_failure_duration'] > 0:
            print(f"Average Failure Duration: {stats['average_failure_duration']:.2f}s")
        
        print("\nCategory Breakdown:")
        for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        print("\nSeverity Breakdown:")
        for severity, count in sorted(stats['severities'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {severity}: {count}")


def main():
    """Example usage of FailureFilter."""
    import sys
    from test_result_reader import TestResultReader
    
    if len(sys.argv) < 2:
        print("Usage: python3 failure_filter.py <json_file>")
        sys.exit(1)
    
    # Read test results
    reader = TestResultReader()
    test_cases = reader.read_json_file(sys.argv[1])
    
    if not test_cases:
        print("No test cases found")
        sys.exit(1)
    
    # Filter failed tests
    filter_obj = FailureFilter()
    failed_tests = filter_obj.extract_failed_tests(test_cases)
    
    if failed_tests:
        filter_obj.print_failure_summary(failed_tests)
        
        # Show some examples
        print(f"\n❌ First 3 Failed Tests:")
        for i, test in enumerate(failed_tests[:3], 1):
            print(f"{i}. {test.name} [{test.category}/{test.severity}]")
            print(f"   {test.failure_message[:100]}...")
    else:
        print("🎉 No failed tests found!")


if __name__ == "__main__":
    main()