#!/usr/bin/env python3
"""
TestFailureOrchestrator - Main orchestrator class that coordinates all test failure analysis components
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from json_test_reader import JSONTestReader
from failure_filter import FailureFilter
from failure_analyzer import FailureAnalyzer
from fix_suggester import FixSuggester
from json_report_generator import JSONReportGenerator


class TestFailureOrchestrator:
    """
    Main orchestrator that coordinates the entire test failure analysis pipeline:
    1. Read JSON test results
    2. Filter failed tests
    3. Analyze failures for root causes
    4. Generate fix suggestions
    5. Create comprehensive JSON report
    """
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
        
        # Initialize all components
        self.reader = JSONTestReader()
        self.filter = FailureFilter()
        self.analyzer = FailureAnalyzer(claude_cli_path)
        self.fix_suggester = FixSuggester(claude_cli_path)
        self.report_generator = JSONReportGenerator()
        
        # Track processing statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_tests': 0,
            'failed_tests': 0,
            'analyzed_tests': 0,
            'fixes_generated': 0,
            'processing_errors': []
        }
    
    def process_test_results(self, input_file: str, output_file: str,
                           source_files: Optional[Dict[str, str]] = None,
                           include_summary: bool = True,
                           prioritize_failures: bool = True) -> str:
        """
        Main processing pipeline for test failure analysis.
        
        Args:
            input_file: Path to JSON file containing test results
            output_file: Path for output JSON report
            source_files: Optional dict mapping file paths to source code content
            include_summary: Whether to include summary statistics
            prioritize_failures: Whether to prioritize failures by severity
            
        Returns:
            Path to generated report file
        """
        
        self.stats['start_time'] = time.time()
        
        try:
            print("🔍 Reading test results...")
            test_results = self._read_test_results(input_file)
            
            print("⚡ Filtering failed tests...")
            failed_tests = self._filter_failed_tests(test_results, prioritize_failures)
            
            print("🧠 Analyzing test failures...")
            analyzed_results = self._analyze_failures(failed_tests, source_files)
            
            print("🔧 Generating fix suggestions...")
            results_with_fixes = self._generate_fix_suggestions(analyzed_results, source_files)
            
            print("📊 Creating comprehensive report...")
            report_path = self._generate_report(results_with_fixes, test_results, 
                                              output_file, include_summary)
            
            self.stats['end_time'] = time.time()
            self._print_processing_summary()
            
            return report_path
            
        except Exception as e:
            self.stats['processing_errors'].append(str(e))
            raise Exception(f"Processing failed: {e}")
    
    def _read_test_results(self, input_file: str) -> List[Dict[str, Any]]:
        """Read and validate test results from JSON file."""
        
        try:
            test_results = self.reader.read_test_results(input_file)
            self.stats['total_tests'] = len(test_results)
            
            # Print test summary
            summary = self.reader.get_test_summary(test_results)
            print(f"   📋 Total tests: {summary['total']}")
            print(f"   ✅ Passed: {summary['passed']}")
            print(f"   ❌ Failed: {summary['failed']}")
            print(f"   ⚠️  Errors: {summary['error']}")
            print(f"   ⏭️  Skipped: {summary['skipped']}")
            
            return test_results
            
        except Exception as e:
            raise Exception(f"Failed to read test results: {e}")
    
    def _filter_failed_tests(self, test_results: List[Dict[str, Any]], 
                           prioritize: bool) -> List[Dict[str, Any]]:
        """Filter and prioritize failed tests."""
        
        try:
            # Get failed tests
            failed_tests = self.filter.filter_failed_tests(test_results)
            self.stats['failed_tests'] = len(failed_tests)
            
            if not failed_tests:
                print("   🎉 No failed tests found!")
                return []
            
            print(f"   📉 Found {len(failed_tests)} failed tests")
            
            # Add error details to each test
            for test in failed_tests:
                error_details = self.filter.extract_error_details(test)
                test.update(error_details)
            
            # Prioritize if requested
            if prioritize:
                failed_tests = self.filter.prioritize_failures(failed_tests)
                print("   🎯 Prioritized failures by severity")
            
            # Show failure statistics
            failure_stats = self.filter.get_failure_statistics(failed_tests)
            print("   📊 Failure types:")
            for error_type, count in sorted(failure_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"      {error_type}: {count}")
            
            return failed_tests
            
        except Exception as e:
            raise Exception(f"Failed to filter tests: {e}")
    
    def _analyze_failures(self, failed_tests: List[Dict[str, Any]], 
                         source_files: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Analyze failed tests to determine root causes."""
        
        if not failed_tests:
            return []
        
        try:
            print(f"   🔬 Analyzing {len(failed_tests)} failures...")
            
            analyzed_results = self.analyzer.analyze_multiple_failures(failed_tests, source_files)
            self.stats['analyzed_tests'] = len([r for r in analyzed_results 
                                              if 'analysis_error' not in r.get('root_cause_analysis', {})])
            
            # Show analysis summary
            analysis_summary = self.analyzer.get_analysis_summary(analyzed_results)
            print(f"   ✅ Successfully analyzed: {len(analyzed_results) - analysis_summary['analysis_errors']}")
            print(f"   ❌ Analysis errors: {analysis_summary['analysis_errors']}")
            
            confidence_dist = analysis_summary['confidence_distribution']
            print(f"   📊 Confidence levels - High: {confidence_dist['High']}, "
                  f"Medium: {confidence_dist['Medium']}, Low: {confidence_dist['Low']}")
            
            return analyzed_results
            
        except Exception as e:
            raise Exception(f"Failed to analyze failures: {e}")
    
    def _generate_fix_suggestions(self, analyzed_results: List[Dict[str, Any]], 
                                source_files: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Generate fix suggestions for analyzed failures."""
        
        if not analyzed_results:
            return []
        
        try:
            print(f"   🛠️  Generating fixes for {len(analyzed_results)} analyzed failures...")
            
            results_with_fixes = self.fix_suggester.suggest_fixes_for_multiple(
                analyzed_results, source_files
            )
            
            self.stats['fixes_generated'] = len([r for r in results_with_fixes 
                                               if 'fix_error' not in r.get('fix_suggestion', {})])
            
            # Show fix generation summary
            fix_summary = self.fix_suggester.generate_fix_summary(results_with_fixes)
            print(f"   ✅ Fixes generated: {len(results_with_fixes) - fix_summary['generation_errors']}")
            print(f"   ❌ Generation errors: {fix_summary['generation_errors']}")
            print(f"   🎯 Actionable fixes: {fix_summary.get('actionable_fixes_count', 0)}")
            
            confidence_dist = fix_summary['confidence_distribution']
            print(f"   📊 Fix confidence - High: {confidence_dist['High']}, "
                  f"Medium: {confidence_dist['Medium']}, Low: {confidence_dist['Low']}")
            
            return results_with_fixes
            
        except Exception as e:
            raise Exception(f"Failed to generate fix suggestions: {e}")
    
    def _generate_report(self, results_with_fixes: List[Dict[str, Any]], 
                        original_test_results: List[Dict[str, Any]],
                        output_file: str, include_summary: bool) -> str:
        """Generate comprehensive JSON report."""
        
        try:
            # Gather all summaries
            original_summary = self.reader.get_test_summary(original_test_results)
            analysis_summary = self.analyzer.get_analysis_summary(results_with_fixes) if results_with_fixes else {}
            fix_summary = self.fix_suggester.generate_fix_summary(results_with_fixes) if results_with_fixes else {}
            
            # Processing metadata
            processing_metadata = {
                'processing_time_seconds': round(time.time() - self.stats['start_time'], 2),
                'claude_cli_path': self.claude_cli_path,
                'total_tests_processed': self.stats['total_tests'],
                'failed_tests_found': self.stats['failed_tests'],
                'successful_analyses': self.stats['analyzed_tests'],
                'successful_fix_generations': self.stats['fixes_generated'],
                'processing_errors': self.stats['processing_errors']
            }
            
            # Generate comprehensive report
            comprehensive_report = self.report_generator.generate_comprehensive_report(
                results_with_fixes,
                original_summary,
                analysis_summary,
                fix_summary,
                processing_metadata
            )
            
            # Save comprehensive report
            report_path = self.report_generator.save_report(comprehensive_report, output_file)
            print(f"   📄 Comprehensive report saved: {report_path}")
            
            # Generate summary report if requested
            if include_summary:
                summary_path = output_file.replace('.json', '_summary.json')
                summary_report = self.report_generator.generate_summary_report(results_with_fixes)
                summary_file_path = self.report_generator.save_report(summary_report, summary_path)
                print(f"   📋 Summary report saved: {summary_file_path}")
            
            return report_path
            
        except Exception as e:
            raise Exception(f"Failed to generate report: {e}")
    
    def _print_processing_summary(self):
        """Print final processing summary."""
        
        processing_time = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*60)
        print("🎯 PROCESSING COMPLETE")
        print("="*60)
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        print(f"📊 Tests processed: {self.stats['total_tests']}")
        print(f"❌ Failed tests: {self.stats['failed_tests']}")
        print(f"🔬 Successfully analyzed: {self.stats['analyzed_tests']}")
        print(f"🛠️  Fixes generated: {self.stats['fixes_generated']}")
        
        if self.stats['processing_errors']:
            print(f"⚠️  Processing errors: {len(self.stats['processing_errors'])}")
            for error in self.stats['processing_errors']:
                print(f"   - {error}")
        
        success_rate = (self.stats['fixes_generated'] / self.stats['failed_tests'] * 100) if self.stats['failed_tests'] > 0 else 0
        print(f"✅ Success rate: {success_rate:.1f}%")
    
    def load_source_files(self, source_file_paths: List[str]) -> Dict[str, str]:
        """Load source files for analysis context."""
        
        source_files = {}
        
        for file_path in source_file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        source_files[str(path)] = f.read()
                    print(f"   📁 Loaded source file: {file_path}")
                else:
                    print(f"   ⚠️  Source file not found: {file_path}")
            except Exception as e:
                print(f"   ❌ Error loading {file_path}: {e}")
        
        return source_files
    
    def validate_requirements(self) -> bool:
        """Validate that all requirements are met for processing."""
        
        try:
            # Test Claude CLI availability
            result = self.analyzer.run_claude_cli("test")
            print("✅ Claude CLI is available")
            return True
        except Exception as e:
            print(f"❌ Claude CLI validation failed: {e}")
            return False


def main():
    """Main CLI interface for the test failure orchestrator."""
    
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Claude CLI and generate comprehensive reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python test_failure_orchestrator.py test_results.json -o analysis_report.json
  
  # With source files for better context
  python test_failure_orchestrator.py test_results.json -o report.json --source-files src/main.py tests/test_main.py
  
  # Skip prioritization and summary
  python test_failure_orchestrator.py test_results.json -o report.json --no-prioritize --no-summary
        """
    )
    
    parser.add_argument("input_file", help="JSON file containing test results")
    parser.add_argument("-o", "--output", required=True, help="Output file for the analysis report")
    parser.add_argument("--claude-cli", default="claude", help="Path to Claude CLI executable")
    parser.add_argument("--source-files", nargs="*", help="Source files to include for better analysis context")
    parser.add_argument("--no-prioritize", action="store_true", help="Don't prioritize failures by severity")
    parser.add_argument("--no-summary", action="store_true", help="Don't generate summary report")
    parser.add_argument("--validate-only", action="store_true", help="Only validate requirements and exit")
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = TestFailureOrchestrator(args.claude_cli)
        
        # Validate requirements
        if not orchestrator.validate_requirements():
            print("❌ Requirements validation failed")
            sys.exit(1)
        
        if args.validate_only:
            print("✅ All requirements validated successfully")
            sys.exit(0)
        
        # Load source files if provided
        source_files = None
        if args.source_files:
            print("📁 Loading source files...")
            source_files = orchestrator.load_source_files(args.source_files)
        
        # Process test results
        print("🚀 Starting test failure analysis...")
        report_path = orchestrator.process_test_results(
            args.input_file,
            args.output,
            source_files,
            include_summary=not args.no_summary,
            prioritize_failures=not args.no_prioritize
        )
        
        print(f"\n🎉 Analysis complete! Report available at: {report_path}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()