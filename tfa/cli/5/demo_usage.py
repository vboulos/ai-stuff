#!/usr/bin/env python3
"""
Demo Usage - Shows how to use all the test failure analysis classes
"""

import json
from test_failure_orchestrator import TestFailureOrchestrator


def create_sample_test_data():
    """Create sample test data for demonstration."""
    sample_data = {
        "test_results": [
            {
                "name": "test_user_login",
                "status": "passed",
                "duration": 1.2,
                "framework": "pytest"
            },
            {
                "name": "test_user_authentication", 
                "status": "failed",
                "failure_message": "AssertionError: Expected status code 200, but got 401\\nResponse: {'error': 'Invalid authentication token'}",
                "file_path": "tests/test_auth.py",
                "line_number": 45,
                "framework": "pytest"
            },
            {
                "name": "test_database_connection",
                "status": "failed", 
                "failure_message": "psycopg2.OperationalError: could not connect to server: Connection refused\\nIs the server running on host \\"localhost\\" (127.0.0.1) and accepting TCP/IP connections on port 5432?",
                "file_path": "tests/test_database.py",
                "line_number": 23,
                "framework": "pytest"
            },
            {
                "name": "test_cypress_text_assertion",
                "status": "failed",
                "failure_message": "Timed out retrying after 120000ms: expected '<dd.pf-v5-c-description-list__description>' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule'",
                "file_path": "cypress/e2e/policy.cy.js",
                "line_number": 67,
                "framework": "cypress"
            },
            {
                "name": "test_api_response",
                "status": "passed",
                "duration": 0.8,
                "framework": "pytest" 
            },
            {
                "name": "test_timeout_error",
                "status": "failed",
                "failure_message": "TimeoutError: Request timed out after 30 seconds\\nExpected: API should respond within timeout\\nActual: No response received",
                "file_path": "tests/test_api.py", 
                "line_number": 89,
                "framework": "pytest"
            }
        ]
    }
    
    return sample_data


def demo_individual_components():
    """Demonstrate how to use individual components."""
    print("🔍 Demo: Using Individual Components")
    print("=" * 50)
    
    # Import individual components
    from test_result_reader import TestResultReader
    from failure_filter import FailureFilter
    from failure_analyzer import FailureAnalyzer
    from fix_suggester import FixSuggester
    from json_report_generator import JsonReportGenerator
    
    # Create sample data
    sample_data = create_sample_test_data()
    
    # Save sample data to file
    with open('demo_test_results.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📖 Step 1: Reading test results")
    reader = TestResultReader()
    test_cases = reader.read_json_file('demo_test_results.json')
    reader.print_summary(test_cases)
    
    print("\\n🔍 Step 2: Filtering failed tests")
    filter_obj = FailureFilter()
    failed_tests = filter_obj.extract_failed_tests(test_cases)
    filter_obj.print_failure_summary(failed_tests)
    
    print(f"\\n🔬 Step 3: Analyzing failures (showing first 2)")
    analyzer = FailureAnalyzer()
    
    if not analyzer.test_connection():
        print("❌ Cannot connect to Claude CLI. Skipping analysis demo.")
        return
    
    # Analyze first 2 failures for demo
    sample_failures = failed_tests[:2]
    analysis_results = analyzer.analyze_multiple_failures(sample_failures)
    
    for result in analysis_results:
        print(f"\\n📊 {result.test_name}:")
        print(f"  Root Cause: {result.root_cause[:100]}...")
        print(f"  Suggested Fix: {result.suggested_fix[:100]}...")
        print(f"  Confidence: {result.confidence_score:.2f}")
    
    print(f"\\n🔧 Step 4: Generating fix suggestions")
    fix_suggester = FixSuggester()
    fix_suggestions = fix_suggester.generate_multiple_fixes(analysis_results)
    
    fix_summary = fix_suggester.get_fix_summary(fix_suggestions)
    print(f"Generated {fix_summary['total_fixes']} fix suggestions")
    
    print(f"\\n📊 Step 5: Generating JSON report")
    report_generator = JsonReportGenerator()
    
    if report_generator.generate_report(fix_suggestions, 'demo_analysis_report.json'):
        print("✅ Report generated: demo_analysis_report.json")
        
        # Validate the report
        validation = report_generator.validate_report('demo_analysis_report.json')
        if validation['valid']:
            print("✅ Report validation passed")
        else:
            print(f"⚠️  Validation warnings: {len(validation['warnings'])}")


def demo_orchestrator():
    """Demonstrate the main orchestrator usage."""
    print("\\n\\n🚀 Demo: Using Test Failure Orchestrator")
    print("=" * 50)
    
    # Create sample data
    sample_data = create_sample_test_data()
    
    # Save sample data
    with open('demo_test_results.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("Creating orchestrator...")
    orchestrator = TestFailureOrchestrator()
    
    # Check pipeline status
    print("\\n🔍 Checking pipeline status:")
    status = orchestrator.get_pipeline_status()
    for component, info in status.items():
        status_icon = "✅" if info['available'] else "❌"
        print(f"  {status_icon} {component}: {info['description']}")
    
    # Demo single failure analysis
    print("\\n🔍 Demo: Single failure analysis")
    result = orchestrator.analyze_single_failure(
        test_name="test_sample_failure",
        failure_message="AssertionError: Expected 'success', got 'error'",
        framework="pytest"
    )
    
    if result['success']:
        print(f"✅ Single analysis successful:")
        print(f"  Root Cause: {result['root_cause'][:80]}...")
        print(f"  Confidence: {result['confidence_score']:.2f}")
    else:
        print(f"❌ Single analysis failed: {result['error']}")
    
    # Demo full pipeline
    print("\\n🚀 Demo: Full pipeline processing")
    success = orchestrator.process_test_failures(
        input_json_path='demo_test_results.json',
        output_json_path='demo_full_report.json',
        max_failures=3,  # Limit for demo
        validate_setup=True
    )
    
    if success:
        print("\\n✅ Full pipeline demo completed successfully!")
        print("📁 Check demo_full_report.json for results")
    else:
        print("❌ Full pipeline demo failed")


def demo_different_json_formats():
    """Demonstrate handling different JSON input formats."""
    print("\\n\\n📋 Demo: Different JSON Input Formats")
    print("=" * 50)
    
    from test_result_reader import TestResultReader
    
    # Format 1: Standard test_results format
    format1 = {
        "test_results": [
            {"name": "test1", "status": "failed", "failure_message": "Error 1"},
            {"name": "test2", "status": "passed"}
        ]
    }
    
    # Format 2: Failed tests only format
    format2 = {
        "failed_tests": [
            {"test_name": "test3", "failure_message": "Error 3"},
            {"test_name": "test4", "failure_message": "Error 4"}
        ]
    }
    
    # Format 3: Direct array format
    format3 = [
        {"test_name": "test5", "status": "failed", "error": "Error 5"},
        {"test_name": "test6", "status": "passed"}
    ]
    
    reader = TestResultReader()
    
    for i, format_data in enumerate([format1, format2, format3], 1):
        filename = f'demo_format_{i}.json'
        with open(filename, 'w') as f:
            json.dump(format_data, f, indent=2)
        
        print(f"\\n📖 Testing Format {i}:")
        test_cases = reader.read_json_file(filename)
        print(f"  Loaded {len(test_cases)} test cases")
        
        if test_cases:
            summary = reader.get_test_summary(test_cases)
            print(f"  Failed: {summary['failed']}, Passed: {summary['passed']}")


def cleanup_demo_files():
    """Clean up demo files created during demonstration."""
    import os
    
    demo_files = [
        'demo_test_results.json',
        'demo_analysis_report.json', 
        'demo_analysis_report_simple.json',
        'demo_full_report.json',
        'demo_full_report_simple.json',
        'demo_format_1.json',
        'demo_format_2.json', 
        'demo_format_3.json'
    ]
    
    print("\\n\\n🧹 Cleaning up demo files...")
    for filename in demo_files:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"  Removed: {filename}")
        except Exception as e:
            print(f"  Could not remove {filename}: {e}")


def main():
    """Run the complete demonstration."""
    print("🎯 Test Failure Analysis Framework Demo")
    print("=" * 60)
    print("This demo shows how to use the test failure analysis classes\\n")
    
    try:
        # Demo individual components
        demo_individual_components()
        
        # Demo the orchestrator
        demo_orchestrator()
        
        # Demo different JSON formats
        demo_different_json_formats()
        
        print("\\n\\n🎉 Demo completed successfully!")
        print("\\n📚 Key Components:")
        print("  • TestResultReader: Reads test results from JSON")
        print("  • FailureFilter: Extracts and categorizes failed tests")
        print("  • FailureAnalyzer: Analyzes failures using Claude CLI")
        print("  • FixSuggester: Generates detailed fix suggestions")
        print("  • JsonReportGenerator: Creates comprehensive reports")
        print("  • TestFailureOrchestrator: Coordinates the entire pipeline")
        
        print("\\n🚀 Usage:")
        print("  python3 test_failure_orchestrator.py input.json output.json")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\\n❌ Demo error: {e}")
    finally:
        # Always cleanup
        cleanup_demo_files()


if __name__ == "__main__":
    main()