#!/usr/bin/env python3
"""
Analyze test failures from JSON file using Claude CLI
"""

import json
import sys
import argparse
from typing import List, Dict, Any
from analyze_failure import analyze_failure

def process_json_file(input_file: str, output_file: str = None, framework: str = None, max_failures: int = None) -> Dict[str, Any]:
    """
    Process a JSON file with test failures and analyze them.
    
    Args:
        input_file: Path to JSON file with test failures
        output_file: Optional output file for results
        framework: Optional framework name to apply to all tests
        max_failures: Maximum number of failures to process
        
    Returns:
        Dictionary with analysis results
    """
    
    try:
        # Read JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Extract test cases from different JSON formats
        test_cases = extract_test_cases(data)
        
        if not test_cases:
            return {"success": False, "error": "No test cases found in JSON file"}
        
        print(f"📖 Found {len(test_cases)} test cases")
        
        # Filter failed tests only
        failed_tests = [tc for tc in test_cases if tc.get('status') == 'failed' or tc.get('failure_message')]
        
        if not failed_tests:
            return {"success": True, "message": "No failed tests found", "results": []}
        
        print(f"🔍 Found {len(failed_tests)} failed tests")
        
        # Limit processing if specified
        if max_failures and len(failed_tests) > max_failures:
            print(f"⚠️  Limiting analysis to first {max_failures} failures")
            failed_tests = failed_tests[:max_failures]
        
        # Analyze each failure
        results = []
        for i, test_case in enumerate(failed_tests, 1):
            test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i}"
            failure_message = test_case.get('failure_message') or test_case.get('error') or test_case.get('message', '')
            test_framework = test_case.get('framework') or framework
            
            print(f"\n🔬 Analyzing {i}/{len(failed_tests)}: {test_name}")
            
            result = analyze_failure(test_name, failure_message, test_framework)
            
            # Add original test info
            result['original_test'] = test_case
            results.append(result)
            
            if result['success']:
                print(f"✅ Analysis completed (confidence: {result['confidence_score']:.2f})")
            else:
                print(f"❌ Analysis failed: {result['error']}")
        
        # Create summary
        successful_analyses = sum(1 for r in results if r['success'])
        summary = {
            "success": True,
            "total_tests": len(test_cases),
            "failed_tests": len(failed_tests),
            "analyzed_tests": len(results),
            "successful_analyses": successful_analyses,
            "average_confidence": sum(r.get('confidence_score', 0) for r in results if r['success']) / max(successful_analyses, 1),
            "results": results
        }
        
        # Save results if output file specified
        if output_file:
            save_results(summary, output_file)
            print(f"\n📁 Results saved to: {output_file}")
        
        return summary
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_test_cases(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract test cases from various JSON formats.
    
    Supports formats like:
    - {"test_results": [...]}
    - {"failed_tests": [...]}
    - {"tests": [...]}
    - Direct array: [...]
    """
    
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

def save_results(summary: Dict[str, Any], output_file: str):
    """Save analysis results to JSON file."""
    
    # Create simplified output for better readability
    output_data = {
        "analysis_summary": {
            "total_tests": summary["total_tests"],
            "failed_tests": summary["failed_tests"], 
            "successful_analyses": summary["successful_analyses"],
            "average_confidence": round(summary["average_confidence"], 2)
        },
        "test_analyses": []
    }
    
    for result in summary["results"]:
        if result["success"]:
            analysis = {
                "test_name": result.get("test_name", "unknown"),
                "framework": result.get("framework"),
                "root_cause": result["root_cause"],
                "suggested_fix": result["suggested_fix"],
                "code_example": result["code_example"],
                "confidence_score": result["confidence_score"],
                "original_failure": result["original_test"].get("failure_message", "")
            }
        else:
            analysis = {
                "test_name": result.get("test_name", "unknown"),
                "error": result["error"],
                "original_failure": result.get("original_test", {}).get("failure_message", "")
            }
        
        output_data["test_analyses"].append(analysis)
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

def create_sample_json():
    """Create a sample JSON file for testing."""
    sample_data = {
        "test_results": [
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
                "name": "test_cypress_text_assertion",
                "status": "failed",
                "failure_message": "Timed out retrying after 120000ms: expected '<dd.pf-v5-c-description-list__description>' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule'",
                "framework": "cypress"
            },
            {
                "name": "test_successful_operation",
                "status": "passed"
            }
        ]
    }
    
    with open('sample_failures.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📝 Sample JSON file created: sample_failures.json")

def main():
    parser = argparse.ArgumentParser(
        description="Analyze test failures from JSON file using Claude CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all failures in JSON file
  python3 analyze_json_failures.py test_results.json
  
  # Save results to output file
  python3 analyze_json_failures.py input.json --output results.json
  
  # Limit to first 5 failures
  python3 analyze_json_failures.py input.json --max-failures 5
  
  # Specify framework for all tests
  python3 analyze_json_failures.py input.json --framework pytest
  
  # Create sample JSON file
  python3 analyze_json_failures.py --sample

Supported JSON formats:
  {"test_results": [{"name": "test1", "status": "failed", "failure_message": "..."}]}
  {"failed_tests": [{"test_name": "test1", "error": "..."}]}
  [{"name": "test1", "failure_message": "..."}]
        """
    )
    
    parser.add_argument("input_file", nargs='?', help="JSON file with test failures")
    parser.add_argument("--output", "-o", help="Output file for analysis results")
    parser.add_argument("--framework", help="Framework to apply to all tests")
    parser.add_argument("--max-failures", type=int, help="Maximum number of failures to analyze")
    parser.add_argument("--sample", action="store_true", help="Create sample JSON file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    
    args = parser.parse_args()
    
    try:
        if args.sample:
            create_sample_json()
            return
        
        if not args.input_file:
            parser.error("input_file is required (or use --sample)")
        
        print(f"🚀 Processing test failures from: {args.input_file}")
        print("=" * 60)
        
        # Process the JSON file
        summary = process_json_file(
            args.input_file,
            args.output,
            args.framework,
            args.max_failures
        )
        
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            if summary["success"]:
                print(f"\n✅ Analysis Complete!")
                print(f"📊 Summary:")
                print(f"  Total tests: {summary['total_tests']}")
                print(f"  Failed tests: {summary['failed_tests']}")
                print(f"  Successful analyses: {summary['successful_analyses']}")
                print(f"  Average confidence: {summary['average_confidence']:.2f}")
                
                # Show brief results
                print(f"\n📋 Analysis Results:")
                for result in summary['results']:
                    if result['success']:
                        test_name = result.get('test_name', 'unknown')
                        confidence = result['confidence_score']
                        cause = result['root_cause'][:80] + "..." if len(result['root_cause']) > 80 else result['root_cause']
                        print(f"  ✅ {test_name} (confidence: {confidence:.2f})")
                        print(f"     {cause}")
                    else:
                        test_name = result.get('test_name', 'unknown')
                        print(f"  ❌ {test_name}: {result['error']}")
            else:
                print(f"❌ Processing failed: {summary['error']}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()