#!/usr/bin/env python3
"""
TestFailureOrchestrator - Main orchestrator that coordinates all components
"""

import logging
import sys
from typing import List, Dict, Any
from test_result_reader import TestResultReader, TestCase
from failure_filter import FailureFilter, FailedTestCase
from failure_analyzer import FailureAnalyzer, AnalysisResult
from fix_suggester import FixSuggester, CodeFixSuggestion
from json_report_generator import JsonReportGenerator


class TestFailureOrchestrator:
    """
    Main orchestrator class that coordinates the entire test failure analysis pipeline.
    
    Pipeline:
    1. Read JSON test results
    2. Filter failed tests only
    3. Analyze failures using Claude CLI
    4. Generate fix suggestions
    5. Create comprehensive JSON report
    """
    
    def __init__(self, claude_cli_path: str = "claude"):
        """
        Initialize the orchestrator.
        
        Args:
            claude_cli_path: Path to Claude CLI executable
        """
        self.claude_cli_path = claude_cli_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Initialize components
        self.reader = TestResultReader()
        self.filter = FailureFilter()
        self.analyzer = FailureAnalyzer(claude_cli_path)
        self.fix_suggester = FixSuggester(claude_cli_path)
        self.report_generator = JsonReportGenerator()
    
    def process_test_failures(self, input_json_path: str, output_json_path: str, 
                            max_failures: int = None, validate_setup: bool = True) -> bool:
        """
        Process test failures through the complete pipeline.
        
        Args:
            input_json_path: Path to input JSON file with test results
            output_json_path: Path where to save the analysis report
            max_failures: Maximum number of failures to process (None for all)
            validate_setup: Whether to validate Claude CLI setup first
            
        Returns:
            True if processing was successful, False otherwise
        """
        
        print("🚀 Starting Test Failure Analysis Pipeline")
        print("=" * 60)
        
        try:
            # Step 1: Validate setup
            if validate_setup and not self._validate_setup():
                return False
            
            # Step 2: Read test results
            print(f"📖 Step 1: Reading test results from {input_json_path}")
            test_cases = self.reader.read_json_file(input_json_path)
            
            if not test_cases:
                print("❌ No test cases found in input file")
                return False
            
            print(f"Found {len(test_cases)} total test cases")
            self.reader.print_summary(test_cases)
            
            # Step 3: Filter failed tests
            print(f"\\n🔍 Step 2: Filtering failed tests")
            failed_tests = self.filter.extract_failed_tests(test_cases)
            
            if not failed_tests:
                print("🎉 No failed tests found! All tests are passing.")
                return True
            
            print(f"Found {len(failed_tests)} failed tests")
            self.filter.print_failure_summary(failed_tests)
            
            # Limit the number of failures to process if specified
            if max_failures and len(failed_tests) > max_failures:
                print(f"\\n⚠️  Limiting analysis to first {max_failures} failures")
                failed_tests = failed_tests[:max_failures]
            
            # Step 4: Analyze failures
            print(f"\\n🔬 Step 3: Analyzing {len(failed_tests)} test failures")
            analysis_results = self.analyzer.analyze_multiple_failures(failed_tests)
            
            successful_analyses = sum(1 for r in analysis_results if r.analysis_successful)
            print(f"Analysis completed: {successful_analyses}/{len(analysis_results)} successful")
            
            if successful_analyses == 0:
                print("❌ No successful analyses. Cannot proceed with fix suggestions.")
                return False
            
            # Step 5: Generate fix suggestions
            print(f"\\n🔧 Step 4: Generating fix suggestions")
            fix_suggestions = self.fix_suggester.generate_multiple_fixes(analysis_results)
            
            fix_summary = self.fix_suggester.get_fix_summary(fix_suggestions)
            print(f"Generated {fix_summary['total_fixes']} fix suggestions")
            print(f"Average confidence: {fix_summary['average_confidence']:.2f}")
            
            # Step 6: Generate JSON report
            print(f"\\n📊 Step 5: Generating comprehensive report")
            report_success = self.report_generator.generate_report(fix_suggestions, output_json_path)
            
            if report_success:
                # Also generate simple report
                self.report_generator.generate_simple_report(fix_suggestions, output_json_path)
                
                print(f"\\n✅ Analysis Pipeline Complete!")
                print(f"📁 Comprehensive report: {output_json_path}")
                print(f"📁 Simple report: {output_json_path.replace('.json', '_simple.json')}")
                
                # Show summary statistics
                self._print_final_summary(fix_suggestions)
                return True
            else:
                print("❌ Failed to generate report")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {e}")
            print(f"❌ Pipeline failed: {e}")
            return False
    
    def _validate_setup(self) -> bool:
        """Validate that all components are properly set up."""
        print("🔧 Validating setup...")
        
        # Test Claude CLI connection
        if self.analyzer.test_connection():
            print("✅ Claude CLI connection verified")
            return True
        else:
            print("❌ Claude CLI setup failed")
            print("\\n🛠️  Setup Requirements:")
            print("1. Install Claude CLI: npm install -g @anthropic/claude-cli")
            print("2. Authenticate: claude auth login")
            print("3. Test: claude --version")
            return False
    
    def _print_final_summary(self, fix_suggestions: List[CodeFixSuggestion]):
        """Print a final summary of the analysis results."""
        print("\\n📈 Analysis Summary:")
        print("-" * 30)
        
        total = len(fix_suggestions)
        high_confidence = sum(1 for fix in fix_suggestions if fix.confidence_score >= 0.8)
        with_code = sum(1 for fix in fix_suggestions if fix.code_example)
        low_effort = sum(1 for fix in fix_suggestions if fix.estimated_effort == 'low')
        
        print(f"Total failures analyzed: {total}")
        print(f"High confidence fixes: {high_confidence}")
        print(f"Fixes with code examples: {with_code}")
        print(f"Quick wins (low effort): {low_effort}")
        
        # Effort distribution
        effort_counts = {}
        for fix in fix_suggestions:
            effort_counts[fix.estimated_effort] = effort_counts.get(fix.estimated_effort, 0) + 1
        
        print(f"\\nEffort Distribution:")
        for effort, count in effort_counts.items():
            print(f"  {effort.title()}: {count}")
    
    def analyze_single_failure(self, test_name: str, failure_message: str, 
                              framework: str = None) -> Dict[str, Any]:
        """
        Analyze a single test failure without reading from file.
        
        Args:
            test_name: Name of the failed test
            failure_message: Failure message text
            framework: Optional framework name
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Create a failed test case
            failed_test = FailedTestCase(
                name=test_name,
                failure_message=failure_message,
                framework=framework
            )
            
            # Analyze the failure
            analysis_result = self.analyzer.analyze_failure(failed_test)
            
            if not analysis_result.analysis_successful:
                return {
                    'success': False,
                    'error': analysis_result.error_message or "Analysis failed"
                }
            
            # Generate fix suggestion
            fix_suggestion = self.fix_suggester.generate_fix_suggestion(analysis_result)
            
            return {
                'success': True,
                'test_name': test_name,
                'failure_message': failure_message,
                'root_cause': fix_suggestion.root_cause,
                'suggested_fix': fix_suggestion.fix_description,
                'code_example': fix_suggestion.code_example,
                'confidence_score': fix_suggestion.confidence_score,
                'effort_estimate': fix_suggestion.estimated_effort,
                'fix_category': fix_suggestion.fix_category,
                'framework_advice': fix_suggestion.framework_specific_advice,
                'prevention_tips': fix_suggestion.prevention_tips
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing single failure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the status of all pipeline components.
        
        Returns:
            Dictionary with component status information
        """
        status = {
            'reader': {'available': True, 'description': 'JSON test result reader'},
            'filter': {'available': True, 'description': 'Failed test filter'},
            'analyzer': {'available': False, 'description': 'Claude CLI failure analyzer'},
            'fix_suggester': {'available': False, 'description': 'Claude CLI fix suggester'},
            'report_generator': {'available': True, 'description': 'JSON report generator'}
        }
        
        # Test Claude CLI components
        try:
            if self.analyzer.test_connection():
                status['analyzer']['available'] = True
                status['fix_suggester']['available'] = True
            else:
                status['analyzer']['error'] = 'Claude CLI connection failed'
                status['fix_suggester']['error'] = 'Claude CLI connection failed'
        except Exception as e:
            error_msg = f"Claude CLI error: {e}"
            status['analyzer']['error'] = error_msg
            status['fix_suggester']['error'] = error_msg
        
        return status


def main():
    """Main entry point for the test failure analysis orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Claude CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 test_failure_orchestrator.py test_results.json analysis_report.json
  
  # Limit to first 5 failures
  python3 test_failure_orchestrator.py --max-failures 5 results.json report.json
  
  # Single test analysis
  python3 test_failure_orchestrator.py --single "test_login" "AssertionError: Login failed"
  
  # Check pipeline status
  python3 test_failure_orchestrator.py --status
  
  # Skip setup validation
  python3 test_failure_orchestrator.py --no-validate results.json report.json

Setup Requirements:
  1. Install Claude CLI: npm install -g @anthropic/claude-cli
  2. Authenticate: claude auth login
  3. Test: claude --version
        """
    )
    
    parser.add_argument("input_file", nargs='?', help="JSON file containing test results")
    parser.add_argument("output_file", nargs='?', help="Output JSON file for analysis report")
    parser.add_argument("--claude-cli", default="claude", help="Path to Claude CLI executable")
    parser.add_argument("--max-failures", type=int, help="Maximum number of failures to analyze")
    parser.add_argument("--single", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), 
                       help="Analyze single test failure")
    parser.add_argument("--status", action="store_true", help="Check pipeline component status")
    parser.add_argument("--no-validate", action="store_true", help="Skip setup validation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = TestFailureOrchestrator(claude_cli_path=args.claude_cli)
    
    try:
        if args.status:
            # Show pipeline status
            status = orchestrator.get_pipeline_status()
            print("🔍 Pipeline Component Status:")
            print("=" * 40)
            for component, info in status.items():
                status_icon = "✅" if info['available'] else "❌"
                print(f"{status_icon} {component.title()}: {info['description']}")
                if 'error' in info:
                    print(f"   Error: {info['error']}")
            
        elif args.single:
            # Single test analysis
            test_name, error_msg = args.single
            print(f"🔍 Analyzing single test failure: {test_name}")
            
            result = orchestrator.analyze_single_failure(test_name, error_msg)
            
            if result['success']:
                print(f"\\n✅ Analysis Results:")
                print(f"Root Cause: {result['root_cause']}")
                print(f"\\nSuggested Fix: {result['suggested_fix']}")
                if result['code_example']:
                    print(f"\\nCode Example: {result['code_example'][:200]}...")
                print(f"\\nConfidence: {result['confidence_score']:.2f}")
                print(f"Effort: {result['effort_estimate']}")
            else:
                print(f"❌ Analysis failed: {result['error']}")
            
        else:
            # Full pipeline processing
            if not args.input_file or not args.output_file:
                parser.error("input_file and output_file are required for pipeline processing")
            
            success = orchestrator.process_test_failures(
                input_json_path=args.input_file,
                output_json_path=args.output_file,
                max_failures=args.max_failures,
                validate_setup=not args.no_validate
            )
            
            if not success:
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()