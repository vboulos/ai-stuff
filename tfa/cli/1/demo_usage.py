#!/usr/bin/env python3
"""
Demo usage of the Test Failure Analysis system
Shows how to use all the separate classes together and individually
"""

import json
import tempfile
from pathlib import Path

from json_test_reader import JSONTestReader
from failure_filter import FailureFilter  
from failure_analyzer import FailureAnalyzer
from fix_suggester import FixSuggester
from json_report_generator import JSONReportGenerator
from test_failure_orchestrator import TestFailureOrchestrator


def demo_individual_classes():
    """Demonstrate using each class individually."""
    
    print("="*60)
    print("DEMO: Using Individual Classes")
    print("="*60)
    
    # 1. JSONTestReader Demo
    print("\n1. 📖 JSONTestReader - Reading test results")
    print("-" * 40)
    
    reader = JSONTestReader()
    test_results = reader.read_test_results("example_test_results.json")
    summary = reader.get_test_summary(test_results)
    
    print(f"Total tests read: {len(test_results)}")
    print(f"Test summary: {summary}")
    
    # 2. FailureFilter Demo
    print("\n2. 🔍 FailureFilter - Filtering and categorizing failures")
    print("-" * 40)
    
    filter_obj = FailureFilter()
    failed_tests = filter_obj.filter_failed_tests(test_results)
    
    print(f"Failed tests found: {len(failed_tests)}")
    
    # Show categorization
    for test in failed_tests[:3]:  # Show first 3
        category = filter_obj.categorize_failure(test)
        error_details = filter_obj.extract_error_details(test)
        print(f"  {test['test_name']}: {category}")
        print(f"    Error type: {error_details['error_type']}")
        print(f"    Location: {error_details['error_location']}")
    
    # Show failure statistics
    stats = filter_obj.get_failure_statistics(failed_tests)
    print(f"Failure statistics: {stats}")
    
    # 3. FailureAnalyzer Demo (Note: requires Claude CLI)
    print("\n3. 🧠 FailureAnalyzer - Root cause analysis")
    print("-" * 40)
    print("Note: This would require Claude CLI to be installed and working")
    print("Example of what it would do:")
    
    analyzer = FailureAnalyzer()
    print("  - Analyze each failure with Claude CLI")
    print("  - Extract root causes")
    print("  - Assess confidence levels")
    print("  - Cache results for efficiency")
    
    # 4. FixSuggester Demo (Note: requires Claude CLI)
    print("\n4. 🔧 FixSuggester - Code fix suggestions")
    print("-" * 40)
    print("Note: This would require Claude CLI to be installed and working")
    print("Example of what it would do:")
    
    fix_suggester = FixSuggester()
    print("  - Generate specific code fixes")
    print("  - Provide before/after code examples")
    print("  - Assess fix complexity")
    print("  - Include testing recommendations")
    
    # 5. JSONReportGenerator Demo
    print("\n5. 📊 JSONReportGenerator - Creating reports")
    print("-" * 40)
    
    report_generator = JSONReportGenerator()
    
    # Create a mock result with analysis and fix data
    mock_result = {
        **failed_tests[0],
        'root_cause_analysis': {
            'primary_root_cause': 'Logic error in calculation - adding instead of multiplying',
            'technical_details': 'The calculate_total function adds price + quantity instead of price * quantity',
            'impact_assessment': 'Medium - affects pricing calculations',
            'confidence_level': 'High'
        },
        'fix_suggestion': {
            'fix_approach': 'Change addition to multiplication in calculation',
            'code_changes': [{
                'type': 'replace',
                'before': 'total += item["price"] + item["quantity"]',
                'after': 'total += item["price"] * item["quantity"]',
                'description': 'Fix calculation logic'
            }],
            'explanation': 'Change + to * to properly calculate price * quantity',
            'confidence': 'High',
            'testing_notes': 'Test with various price/quantity combinations',
            'side_effects': 'None expected'
        }
    }
    
    # Generate comprehensive report
    comprehensive_report = report_generator.generate_comprehensive_report([mock_result])
    print("Generated comprehensive report structure:")
    print(f"  - Report metadata: {bool(comprehensive_report.get('report_metadata'))}")
    print(f"  - Failed tests: {len(comprehensive_report.get('failed_tests', []))}")
    print(f"  - Insights: {bool(comprehensive_report.get('insights'))}")
    
    # Generate summary report
    summary_report = report_generator.generate_summary_report([mock_result])
    print(f"Generated summary report with {summary_report['summary']['total_failed_tests']} tests")


def demo_orchestrator():
    """Demonstrate using the main orchestrator class."""
    
    print("\n" + "="*60)
    print("DEMO: Using TestFailureOrchestrator")
    print("="*60)
    
    orchestrator = TestFailureOrchestrator()
    
    print("\n📋 What the orchestrator would do:")
    print("1. Read JSON test results")
    print("2. Filter and prioritize failed tests")
    print("3. Analyze failures with Claude CLI")
    print("4. Generate fix suggestions") 
    print("5. Create comprehensive JSON reports")
    print("6. Provide processing statistics")
    
    print("\nExample command line usage:")
    print("python test_failure_orchestrator.py example_test_results.json -o analysis_report.json")
    
    print("\nWith source files:")
    print("python test_failure_orchestrator.py example_test_results.json -o report.json --source-files src/calculator.py tests/test_calculator.py")


def demo_expected_output_structure():
    """Show what the expected output JSON structure looks like."""
    
    print("\n" + "="*60)
    print("DEMO: Expected Output Structure")
    print("="*60)
    
    expected_output = {
        "report_metadata": {
            "generated_at": "2024-01-15T10:30:00",
            "generator": {
                "tool_name": "Claude CLI Test Failure Analyzer",
                "version": "1.0"
            },
            "total_failed_tests": 5
        },
        "execution_summary": {
            "original_test_summary": {"total": 10, "passed": 3, "failed": 5, "error": 1, "skipped": 1},
            "analysis_summary": {"total_analyzed": 5, "analysis_errors": 0},
            "fix_summary": {"fixes_generated": 5, "actionable_fixes": 4}
        },
        "failed_tests": [
            {
                "test_identification": {
                    "test_name": "test_calculate_total_price",
                    "test_class": "TestPriceCalculation",
                    "file_path": "tests/test_calculator.py",
                    "line_number": 25,
                    "status": "failed"
                },
                "failure_details": {
                    "error_message": "AssertionError: assert 35.0 == 30.0",
                    "error_category": "assertion_error"
                },
                "root_cause_analysis": {
                    "primary_cause": "Logic error in calculate_total function",
                    "technical_details": "Function adds price + quantity instead of price * quantity",
                    "confidence_level": "High",
                    "analysis_successful": True
                },
                "fix_suggestion": {
                    "approach": "Change addition to multiplication in calculation",
                    "confidence": "High",
                    "code_changes": [
                        {
                            "change_type": "replace",
                            "before_code": "total += item['price'] + item['quantity']",
                            "after_code": "total += item['price'] * item['quantity']",
                            "description": "Fix calculation logic"
                        }
                    ],
                    "fix_generation_successful": True
                },
                "quality_indicators": {
                    "analysis_confidence": "High",
                    "fix_confidence": "High", 
                    "has_code_changes": True,
                    "actionable_fix": True,
                    "completeness_score": 0.95
                }
            }
        ],
        "insights": {
            "failure_patterns": {"assertion_error": 2, "type_error": 1, "attribute_error": 1},
            "common_root_causes": {"Logic errors": 3, "Type mismatches": 1},
            "actionable_fixes_count": 4,
            "recommendations": [
                "Focus on assertion_error issues - they account for 2 out of 5 failures",
                "Consider adding type validation to prevent type errors"
            ]
        }
    }
    
    print("📄 Expected JSON report structure:")
    print(json.dumps(expected_output, indent=2)[:1500] + "...")
    
    print(f"\n📊 Key sections included:")
    print("  ✅ Report metadata with timestamps")
    print("  ✅ Execution summary with statistics")
    print("  ✅ Detailed failed test analysis")
    print("  ✅ Root cause analysis for each failure")
    print("  ✅ Specific code fix suggestions")
    print("  ✅ Quality indicators and confidence scores")
    print("  ✅ Aggregate insights and recommendations")


def create_sample_source_files():
    """Create sample source files to demonstrate source code analysis."""
    
    calculator_source = '''
def calculate_total(items):
    """Calculate total price for a list of items."""
    total = 0
    for item in items:
        # BUG: Should multiply price * quantity, not add them
        total += item['price'] + item['quantity']
    return total

def apply_discount(price, discount_percent):
    """Apply a percentage discount to a price."""
    # BUG: discount_percent might be passed as string
    discount_amount = price * discount_percent / 100
    return price - discount_amount

def calculate_tax(price, tax_rate=0.08):
    """Calculate tax amount for a given price."""
    return price * tax_rate
'''
    
    auth_source = '''
class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password

def register_user(email, password):
    """Register a new user."""
    if not email or not password:
        return None  # BUG: Should raise exception or return proper error
    
    # BUG: Missing validation and user creation logic
    # This returns None which causes AttributeError in tests
    pass

def authenticate_user(email, password):
    """Authenticate user credentials."""
    # Simplified authentication logic
    if email and password:
        return User(email, password)
    return None
'''
    
    with open('src_calculator.py', 'w') as f:
        f.write(calculator_source)
    
    with open('src_auth.py', 'w') as f:
        f.write(auth_source)
    
    print("📁 Created sample source files:")
    print("  - src_calculator.py (with calculation bugs)")
    print("  - src_auth.py (with authentication bugs)")
    
    return {
        'src/calculator.py': calculator_source,
        'src/auth.py': auth_source
    }


def main():
    """Run all demos."""
    
    print("🎯 Test Failure Analysis System - Complete Demo")
    print("=" * 80)
    
    # Check if example test results exist
    if not Path("example_test_results.json").exists():
        print("❌ example_test_results.json not found!")
        print("Please make sure the example file is in the current directory.")
        return
    
    # Demo individual classes
    demo_individual_classes()
    
    # Demo orchestrator
    demo_orchestrator()
    
    # Show expected output structure
    demo_expected_output_structure()
    
    # Create sample source files
    print("\n" + "="*60)
    print("DEMO: Sample Source Files")
    print("="*60)
    source_files = create_sample_source_files()
    
    print("\n🚀 To run the complete analysis:")
    print("1. Install Claude CLI: pip install claude-cli")
    print("2. Run orchestrator: python test_failure_orchestrator.py example_test_results.json -o report.json --source-files src_calculator.py src_auth.py")
    print("3. Check generated report.json and report_summary.json")
    
    print("\n✅ Demo complete! All classes are ready for use.")


if __name__ == "__main__":
    main()