#!/usr/bin/env python3
"""
Simple script to run test failure analysis with your own data.
"""

import json
from test_failure_analyzer import TestFailureAnalyzer

def main():
    """
    Run test failure analysis on your JSON file.
    
    Usage:
    1. Prepare your input JSON file with format:
       [
         {
           "test_case_id": "TC001",
           "test_case_name": "test_login",
           "failure_message": "AssertionError: Expected 200, got 401"
         }
       ]
    
    2. Set your API key: export ANTHROPIC_API_KEY=your_key_here
    3. Run this script: python run_analysis.py
    """
    
    # Configuration
    input_file = "test_failures.json"  # Change this to your input file
    output_file = "analysis_results.json"  # Change this to your desired output file
    
    try:
        # Initialize analyzer
        analyzer = TestFailureAnalyzer()
        
        # Check if input file exists
        try:
            with open(input_file, 'r') as f:
                test_cases = json.load(f)
            print(f"Found {len(test_cases)} test cases in {input_file}")
        except FileNotFoundError:
            print(f"Input file '{input_file}' not found.")
            print("Creating a sample file for you to modify...")
            create_sample_file(input_file)
            print(f"Please edit {input_file} with your test data and run again.")
            return
        
        # Run analysis
        print("Starting analysis...")
        results = analyzer.analyze_failures(input_file, output_file)
        
        print(f"\n✅ Analysis complete! Results saved to: {output_file}")
        
        # Show quick preview
        print("\n📋 Quick Preview:")
        for result in results[:2]:  # Show first 2 results
            print(f"\n🔍 {result['test_case_id']}: {result['test_case_name']}")
            print(f"   Type: {result['failure_type']}")
            print(f"   Fix: {result['fix_suggestion'][:80]}...")
            if result['fix_code']:
                print(f"   ✅ Code fix provided")
            else:
                print(f"   ❌ No code fix")
        
        if len(results) > 2:
            print(f"\n... and {len(results) - 2} more results in {output_file}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Setup Instructions:")
        print("1. Install required package: pip install anthropic")
        print("2. Get API key from: https://console.anthropic.com/")
        print("3. Set environment variable: export ANTHROPIC_API_KEY=your_key_here")
        print("4. Run again: python run_analysis.py")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def create_sample_file(filename: str):
    """Create a sample input file."""
    sample_data = [
        {
            "test_case_id": "TC001",
            "test_case_name": "test_user_login",
            "failure_message": "AssertionError: Expected status code 200, but got 401"
        },
        {
            "test_case_id": "TC002",
            "test_case_name": "test_database_query",
            "failure_message": "ConnectionError: could not connect to database server"
        },
        {
            "test_case_id": "TC003",
            "test_case_name": "test_api_endpoint",
            "failure_message": "TimeoutError: Request timed out after 30 seconds"
        }
    ]
    
    with open(filename, 'w') as f:
        json.dump(sample_data, f, indent=2)

if __name__ == "__main__":
    main()