#!/usr/bin/env python3
"""
Usage example for the simple test failure analysis system
"""

from test_analyzer import TestAnalyzer


def main():
    print("Simple Test Failure Analysis Example")
    print("=" * 40)
    
    # Create analyzer
    analyzer = TestAnalyzer()
    
    # Analyze test failures
    print("Running analysis...")
    analyzer.analyze_test_failures("simple_example.json", "analysis_report.json")
    
    print("\nDone! Check analysis_report.json for results.")
    
    # Show what the output looks like
    import json
    with open("analysis_report.json", "r") as f:
        report = json.load(f)
    
    print(f"\nGenerated report with {report['total_failed_tests']} failed tests")
    
    # Show first result
    if report['failed_tests']:
        first_test = report['failed_tests'][0]
        print(f"\nExample result:")
        print(f"Test: {first_test['test_name']}")
        print(f"Error: {first_test['failure_message'][:50]}...")
        print(f"Root Cause: {first_test['root_cause'][:100]}...")
        print(f"Fix: {first_test['code_fix'][:100]}...")


if __name__ == "__main__":
    main()