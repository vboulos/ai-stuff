#!/usr/bin/env python3
"""
Test Failure Analysis and Fix Suggestion Orchestrator
Combines FailureAnalyzer and FixSuggestor to provide comprehensive test failure analysis
"""

import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from analyze_failures import FailureAnalyzer
from fix_suggestor import FixSuggestor

class TestFailureOrchestrator:
    """
    Orchestrates failure analysis and fix suggestions using separate analyzer and suggestor classes.
    """
    
    def __init__(self, claude_timeout: int = 120, max_workers: int = 3, 
                 analysis_runbook: str = None, fix_runbook: str = None):
        """
        Initialize the orchestrator with analyzer and suggestor instances.
        
        Args:
            claude_timeout: Timeout for Claude CLI calls in seconds
            max_workers: Maximum number of parallel workers
            analysis_runbook: Optional path to runbook for analysis prompts
            fix_runbook: Optional path to runbook for fix prompts
        """
        self.analyzer = FailureAnalyzer(claude_timeout, analysis_runbook)
        self.suggestor = FixSuggestor(claude_timeout, fix_runbook)
        self.max_workers = max_workers
        self.claude_timeout = claude_timeout
    
    def process_test_failures(self, input_file: str, output_file: str = None, 
                            framework: str = None, max_failures: int = None,
                            parallel: bool = True, skip_fixes: bool = False) -> Dict[str, Any]:
        """
        Process test failures from JSON file with analysis and fix suggestions.
        
        Args:
            input_file: Path to JSON file with test failures
            output_file: Output file path (defaults to comprehensive_analysis.json)
            framework: Framework to apply to all tests
            max_failures: Maximum number of failures to process
            parallel: Whether to process in parallel
            skip_fixes: Whether to skip fix suggestions (analysis only)
            
        Returns:
            Processing results dictionary
        """
        try:
            start_time = time.time()
            
            # Read input file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Extract test cases
            test_cases = self._extract_test_cases(data)
            
            if not test_cases:
                return {"success": False, "error": "No test cases found in JSON file"}
            
            print(f"📖 Found {len(test_cases)} test cases")
            
            # Filter failed tests
            failed_tests = [tc for tc in test_cases if tc.get('status') == 'failed' or tc.get('failure_message')]
            
            if not failed_tests:
                return {"success": True, "message": "No failed tests found", "results": []}
            
            print(f"🔍 Found {len(failed_tests)} failed tests")
            
            # Limit processing if specified
            if max_failures and len(failed_tests) > max_failures:
                print(f"⚠️  Limiting analysis to first {max_failures} failures")
                failed_tests = failed_tests[:max_failures]
            
            # Step 1: Analyze failures
            print(f"\n📊 Step 1: Analyzing {len(failed_tests)} failures...")
            if parallel and len(failed_tests) > 1:
                analysis_results = self._analyze_parallel(failed_tests, framework)
            else:
                analysis_results = self._analyze_sequential(failed_tests, framework)
            
            # Step 2: Generate fix suggestions (unless skipped)
            if not skip_fixes:
                print(f"\n🔧 Step 2: Generating fix suggestions...")
                if parallel and len(analysis_results) > 1:
                    final_results = self._suggest_fixes_parallel(analysis_results)
                else:
                    final_results = self._suggest_fixes_sequential(analysis_results)
            else:
                final_results = analysis_results
                print(f"\n⏭️  Skipping fix suggestions as requested")
            
            # Calculate statistics
            processing_time = time.time() - start_time
            stats = self._calculate_statistics(final_results, processing_time, skip_fixes)
            
            # Create comprehensive output
            output_data = self._create_output_structure(
                input_file, test_cases, failed_tests, final_results, stats, skip_fixes
            )
            
            # Save output
            output_filename = output_file or "comprehensive_analysis.json"
            with open(output_filename, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n📁 Comprehensive analysis saved to: {output_filename}")
            
            return {
                "success": True,
                "output_file": output_filename,
                "statistics": stats
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_test_cases(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract test cases from various JSON formats."""
        
        # Handle direct array
        if isinstance(data, list):
            return data
        
        # Handle object with test arrays
        for key in ['test_results', 'failed_tests', 'tests', 'failures', 'test_cases']:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # Handle single test case
        if 'name' in data or 'test_name' in data:
            return [data]
        
        return []
    
    def _analyze_sequential(self, failed_tests: List[Dict[str, Any]], framework: str) -> List[Dict[str, Any]]:
        """Analyze tests sequentially."""
        print("🔄 Processing sequentially...")
        return self.analyzer.analyze_multiple_failures(failed_tests, framework)
    
    def _analyze_parallel(self, failed_tests: List[Dict[str, Any]], framework: str) -> List[Dict[str, Any]]:
        """Analyze tests in parallel."""
        print(f"🚀 Processing {len(failed_tests)} analyses in parallel (max {self.max_workers} workers)")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit analysis tasks
            future_to_test = {}
            for i, test_case in enumerate(failed_tests):
                test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i+1}"
                failure_message = test_case.get('failure_message') or test_case.get('error') or test_case.get('message', '')
                test_framework = test_case.get('framework') or framework
                
                future = executor.submit(self.analyzer.analyze_failure, test_name, failure_message, test_framework)
                future_to_test[future] = (i, test_case, test_name, test_framework)
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_test):
                i, test_case, test_name, test_framework = future_to_test[future]
                completed += 1
                
                try:
                    analysis = future.result()
                    
                    result = {
                        "test_name": test_name,
                        "framework": test_framework,
                        "original_test": test_case,
                        "analysis": analysis
                    }
                    
                    results.append((i, result))
                    
                    if analysis["success"]:
                        print(f"✅ {completed}/{len(failed_tests)} - {test_name}: Analyzed (confidence: {analysis['confidence_score']:.2f})")
                    else:
                        print(f"❌ {completed}/{len(failed_tests)} - {test_name}: Analysis failed")
                        
                except Exception as e:
                    print(f"❌ {completed}/{len(failed_tests)} - {test_name}: Error - {e}")
                    results.append((i, {"error": str(e)}))
        
        # Sort results by original order
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]
    
    def _suggest_fixes_sequential(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fix suggestions sequentially."""
        print("🔄 Generating fixes sequentially...")
        return self.suggestor.suggest_fixes_for_analyses(analysis_results)
    
    def _suggest_fixes_parallel(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fix suggestions in parallel."""
        print(f"🚀 Generating {len(analysis_results)} fix suggestions in parallel (max {self.max_workers} workers)")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit fix suggestion tasks
            future_to_analysis = {}
            for i, analysis_result in enumerate(analysis_results):
                test_name = analysis_result.get("test_name", f"test_{i+1}")
                framework = analysis_result.get("framework")
                original_test = analysis_result.get("original_test", {})
                analysis = analysis_result.get("analysis", {})
                
                failure_message = original_test.get("failure_message", "")
                
                future = executor.submit(self.suggestor.suggest_fix, test_name, failure_message, framework, analysis)
                future_to_analysis[future] = (i, analysis_result, test_name)
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_analysis):
                i, analysis_result, test_name = future_to_analysis[future]
                completed += 1
                
                try:
                    fix_suggestion = future.result()
                    
                    result = analysis_result.copy()
                    result["fix_suggestion"] = fix_suggestion
                    
                    results.append((i, result))
                    
                    if fix_suggestion["success"]:
                        fix_type = fix_suggestion.get("fix_type", "unknown")
                        priority = fix_suggestion.get("priority", "medium")
                        print(f"✅ {completed}/{len(analysis_results)} - {test_name}: Fix generated (Type: {fix_type}, Priority: {priority})")
                    else:
                        print(f"❌ {completed}/{len(analysis_results)} - {test_name}: Fix generation failed")
                        
                except Exception as e:
                    print(f"❌ {completed}/{len(analysis_results)} - {test_name}: Error - {e}")
                    result = analysis_result.copy()
                    result["fix_suggestion"] = {"success": False, "error": str(e)}
                    results.append((i, result))
        
        # Sort results by original order
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]
    
    def _calculate_statistics(self, results: List[Dict[str, Any]], processing_time: float, skip_fixes: bool) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        
        total_processed = len(results)
        successful_analyses = sum(1 for r in results if r.get("analysis", {}).get("success"))
        failed_analyses = total_processed - successful_analyses
        
        stats = {
            "processing_time_seconds": round(processing_time, 2),
            "total_processed": total_processed,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "analysis_success_rate": round(successful_analyses / total_processed, 2) if total_processed > 0 else 0
        }
        
        if not skip_fixes:
            successful_fixes = sum(1 for r in results if r.get("fix_suggestion", {}).get("success"))
            failed_fixes = total_processed - successful_fixes
            
            stats.update({
                "successful_fixes": successful_fixes,
                "failed_fixes": failed_fixes,
                "fix_success_rate": round(successful_fixes / total_processed, 2) if total_processed > 0 else 0
            })
            
            # Get fix summary
            fix_summary = self.suggestor.get_fix_summary(results)
            stats["fix_summary"] = fix_summary
        
        # Calculate average confidence for successful analyses
        if successful_analyses > 0:
            avg_confidence = sum(r["analysis"].get("confidence_score", 0) 
                               for r in results if r.get("analysis", {}).get("success")) / successful_analyses
            stats["average_confidence"] = round(avg_confidence, 2)
        else:
            stats["average_confidence"] = 0.0
        
        return stats
    
    def _create_output_structure(self, input_file: str, all_tests: List, failed_tests: List, 
                               results: List, stats: Dict, skip_fixes: bool) -> Dict[str, Any]:
        """Create the comprehensive output structure."""
        
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "input_file": input_file,
                "processing_mode": "analysis_and_fixes" if not skip_fixes else "analysis_only",
                "total_tests_in_input": len(all_tests),
                "failed_tests_found": len(failed_tests),
                "tests_processed": len(results),
                "claude_timeout": self.claude_timeout,
                "max_workers": self.max_workers
            },
            "statistics": stats,
            "test_results": results
        }

def create_sample_file():
    """Create a sample JSON file for testing."""
    sample_data = [
        {
            "name": "test_user_authentication",
            "status": "failed",
            "failure_message": "AssertionError: Expected status code 200, but got 401\nResponse: {'error': 'Invalid authentication token'}",
            "framework": "pytest"
        },
        {
            "name": "test_database_connection", 
            "status": "failed",
            "failure_message": "psycopg2.OperationalError: could not connect to server: Connection refused\nIs the server running on host \"localhost\" (127.0.0.1) and accepting TCP/IP connections on port 5432?",
            "framework": "pytest"
        },
        {
            "name": "test_cypress_element_timeout",
            "status": "failed",
            "failure_message": "Timed out retrying after 4000ms: Expected to find element: `.submit-button`, but never found it.",
            "framework": "cypress"
        },
        {
            "name": "test_successful_operation",
            "status": "passed"
        }
    ]
    
    with open('sample_test_failures.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📝 Sample test failures file created: sample_test_failures.json")

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Failure Analysis and Fix Suggestions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full analysis with fix suggestions (parallel)
  python analyze_and_suggest_fixes.py test_failures.json
  
  # Analysis only (no fix suggestions)
  python analyze_and_suggest_fixes.py input.json --analysis-only
  
  # Sequential processing with custom output
  python analyze_and_suggest_fixes.py input.json --output results.json --no-parallel
  
  # Limit processing and specify framework
  python analyze_and_suggest_fixes.py input.json --max-failures 5 --framework pytest
  
  # Create sample file for testing
  python analyze_and_suggest_fixes.py --sample
        """
    )
    
    parser.add_argument("input_file", nargs='?', help="JSON file with test failures")
    parser.add_argument("--output", "-o", help="Output file (default: comprehensive_analysis.json)")
    parser.add_argument("--framework", help="Framework to apply to all tests")
    parser.add_argument("--max-failures", type=int, help="Maximum number of failures to process")
    parser.add_argument("--timeout", type=int, default=300, help="Claude CLI timeout in seconds (default: 300 for fix suggestions)")
    parser.add_argument("--max-workers", type=int, default=3, help="Maximum parallel workers")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing")
    parser.add_argument("--analysis-only", action="store_true", help="Skip fix suggestions (analysis only)")
    parser.add_argument("--sample", action="store_true", help="Create sample test failures file")
    parser.add_argument("--analysis-runbook", help="Path to analysis runbook template file")
    parser.add_argument("--fix-runbook", help="Path to fix suggestion runbook template file")
    
    args = parser.parse_args()
    
    try:
        if args.sample:
            create_sample_file()
            return 0
        
        if not args.input_file:
            parser.error("input_file is required (or use --sample)")
        
        print(f"🚀 Comprehensive Test Failure Analysis")
        print(f"📁 Input: {args.input_file}")
        print("=" * 60)
        
        orchestrator = TestFailureOrchestrator(
            claude_timeout=args.timeout,
            max_workers=args.max_workers,
            analysis_runbook=args.analysis_runbook,
            fix_runbook=args.fix_runbook
        )
        
        result = orchestrator.process_test_failures(
            args.input_file,
            args.output,
            args.framework,
            args.max_failures,
            parallel=not args.no_parallel,
            skip_fixes=args.analysis_only
        )
        
        if result["success"]:
            stats = result["statistics"]
            print(f"\n✅ Processing Complete!")
            print(f"📊 Statistics:")
            print(f"  Processing time: {stats['processing_time_seconds']}s")
            print(f"  Total processed: {stats['total_processed']}")
            print(f"  Successful analyses: {stats['successful_analyses']}")
            print(f"  Analysis success rate: {stats['analysis_success_rate']}")
            print(f"  Average confidence: {stats['average_confidence']}")
            
            if not args.analysis_only:
                print(f"  Successful fixes: {stats['successful_fixes']}")
                print(f"  Fix success rate: {stats['fix_success_rate']}")
            
            print(f"  Output file: {result['output_file']}")
        else:
            print(f"❌ Processing failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
    # python3 analyze_and_suggest_fixes.py test_failures.json \
    #   --analysis-runbook analysis_runbook.txt \
    #   --fix-runbook fix_runbook.txt --output tfa-results.json