#!/usr/bin/env python3
"""
Complete TestAnalyzer - Main orchestrator for test failure analysis
"""

import argparse
import sys
import os
from typing import List, Dict

from complete_test_reader import TestReader
from complete_failure_analyzer import FailureAnalyzer
from complete_report_generator import ReportGenerator


class TestAnalyzer:
    """Main orchestrator class for complete test failure analysis pipeline."""
    
    def __init__(self, claude_cli_path: str = "claude", model: str = None, api_key: str = None):
        self.reader = TestReader()
        self.analyzer = FailureAnalyzer(claude_cli_path, model, api_key)
        self.reporter = ReportGenerator()
    
    def analyze_test_failures(self, input_file: str, output_file: str, 
                             validate_setup: bool = True) -> bool:
        """
        Complete analysis pipeline: read -> validate -> analyze -> generate report.
        
        Returns True if successful, False otherwise.
        """
        
        print("🚀 Starting Test Failure Analysis")
        print("=" * 50)
        
        # Step 1: Validate setup
        if validate_setup:
            if not self._validate_setup():
                return False
        
        # Step 2: Read and filter test results
        print(f"📖 Reading test results from: {input_file}")
        failed_tests = self.reader.read_failed_tests(input_file)
        
        if not failed_tests:
            print("🎉 No failed tests found! All tests are passing.")
            return True
        
        print(f"📉 Found {len(failed_tests)} failed tests")
        self.reader.print_summary(failed_tests)
        
        # Step 3: Analyze failures
        print(f"\n🔬 Analyzing test failures...")
        analyzed_results = self._analyze_all_failures(failed_tests)
        
        # Step 4: Generate report
        print(f"\n📊 Generating analysis report...")
        report_path = self.reporter.generate_report(analyzed_results, output_file)
        
        if report_path:
            # Also generate simple report
            self.reporter.generate_simple_report(analyzed_results, output_file)
            print(f"\n✅ Analysis complete! Check the reports for detailed results.")
            return True
        else:
            print(f"\n❌ Failed to generate report")
            return False
    
    def _validate_setup(self) -> bool:
        """Validate that the analysis setup is working."""
        
        print("🔧 Validating setup...")
        
        # Test Claude connection
        if self.analyzer.test_connection():
            print("✅ Claude analysis ready")
            return True
        else:
            print("❌ Claude setup failed")
            print("\n🛠️  Setup Options:")
            print("1. Install Claude CLI: pip install claude-cli")
            print("2. Authenticate: claude auth login")
            print("3. Or set API key: export ANTHROPIC_API_KEY='your-key'")
            print("4. Try specific model: --model claude-3-sonnet-20240229")
            return False
    
    def _analyze_all_failures(self, failed_tests: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Analyze all failed tests and return results."""
        
        analyzed_results = []
        total_tests = len(failed_tests)
        
        for i, test in enumerate(failed_tests, 1):
            print(f"   Analyzing {i}/{total_tests}: {test['test_name']}")
            
            # Analyze the failure
            analysis = self.analyzer.analyze_failure(
                test['test_name'], 
                test['failure_message']
            )
            
            # Combine original test info with analysis
            result = {
                'test_name': test['test_name'],
                'failure_message': test['failure_message'],
                'root_cause': analysis['root_cause'],
                'code_fix': analysis['code_fix']
            }
            
            analyzed_results.append(result)
        
        # Show analysis summary
        successful_analyses = sum(1 for r in analyzed_results 
                                if not self._is_error_result(r))
        
        print(f"\n📈 Analysis Results:")
        print(f"   Successful: {successful_analyses}/{total_tests}")
        print(f"   Success rate: {(successful_analyses/total_tests)*100:.1f}%")
        
        return analyzed_results
    
    def _is_error_result(self, result: Dict[str, str]) -> bool:
        """Check if analysis result is an error."""
        root_cause = result.get('root_cause', '').lower()
        return any(keyword in root_cause for keyword in [
            'error analyzing', 'analysis failed', 'timeout', 'not found'
        ])
    
    def quick_analyze(self, test_name: str, failure_message: str) -> Dict[str, str]:
        """Quick analysis of a single test failure."""
        return self.analyzer.analyze_failure(test_name, failure_message)


def main():
    """Command-line interface for the test analyzer."""
    
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Claude CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python complete_test_analyzer.py tests.json analysis_report.json
  
  # With specific model
  python complete_test_analyzer.py tests.json report.json --model claude-3-sonnet-20240229
  
  # With API key
  python complete_test_analyzer.py tests.json report.json --api-key sk-ant-...
  
  # Skip setup validation
  python complete_test_analyzer.py tests.json report.json --no-validate
        """
    )
    
    parser.add_argument("input_file", help="JSON file containing test results")
    parser.add_argument("output_file", help="Output JSON file for analysis results")
    parser.add_argument("--claude-cli", default="claude", help="Path to Claude CLI executable")
    parser.add_argument("--model", help="Claude model to use (e.g., claude-3-sonnet-20240229)")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--no-validate", action="store_true", help="Skip setup validation")
    parser.add_argument("--quick", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), 
                       help="Quick analysis of single test failure")
    
    args = parser.parse_args()
    
    try:
        # Handle quick analysis mode
        if args.quick:
            analyzer = TestAnalyzer(args.claude_cli, args.model, args.api_key)
            result = analyzer.quick_analyze(args.quick[0], args.quick[1])
            
            print(f"Test: {args.quick[0]}")
            print(f"Root Cause: {result['root_cause']}")
            print(f"Code Fix: {result['code_fix']}")
            return
        
        # Validate input file exists
        if not os.path.exists(args.input_file):
            print(f"❌ Error: Input file '{args.input_file}' not found")
            sys.exit(1)
        
        # Create analyzer
        analyzer = TestAnalyzer(args.claude_cli, args.model, args.api_key)
        
        # Run analysis
        success = analyzer.analyze_test_failures(
            args.input_file, 
            args.output_file, 
            validate_setup=not args.no_validate
        )
        
        if not success:
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()