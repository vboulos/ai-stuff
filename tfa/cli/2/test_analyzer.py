#!/usr/bin/env python3
"""
TestAnalyzer - Main class that orchestrates the test failure analysis
"""

from test_reader import TestReader
from failure_analyzer import FailureAnalyzer
from report_generator import ReportGenerator
from typing import List, Dict


class TestAnalyzer:
    """Main class that orchestrates the complete test failure analysis process."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.reader = TestReader()
        self.analyzer = FailureAnalyzer(claude_cli_path)
        self.reporter = ReportGenerator()
    
    def analyze_test_failures(self, input_file: str, output_file: str) -> None:
        """Complete analysis pipeline: read -> analyze -> generate report."""
        
        print(f"Reading test results from: {input_file}")
        failed_tests = self.reader.read_failed_tests(input_file)
        
        if not failed_tests:
            print("No failed tests found!")
            return
        
        print(f"Found {len(failed_tests)} failed tests")
        
        analyzed_results = []
        for i, test in enumerate(failed_tests, 1):
            print(f"Analyzing test {i}/{len(failed_tests)}: {test['test_name']}")
            
            analysis = self.analyzer.analyze_failure(
                test['test_name'], 
                test['failure_message']
            )
            
            result = {
                'test_name': test['test_name'],
                'failure_message': test['failure_message'],
                'root_cause': analysis['root_cause'],
                'code_fix': analysis['code_fix']
            }
            analyzed_results.append(result)
        
        self.reporter.generate_report(analyzed_results, output_file)


def main():
    """CLI interface for the test analyzer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze test failures using Claude CLI")
    parser.add_argument("input_file", help="JSON file with test results")
    parser.add_argument("output_file", help="Output JSON file for analysis results")
    parser.add_argument("--claude-cli", default="claude", help="Path to Claude CLI")
    
    args = parser.parse_args()
    
    analyzer = TestAnalyzer(args.claude_cli)
    analyzer.analyze_test_failures(args.input_file, args.output_file)


if __name__ == "__main__":
    main()