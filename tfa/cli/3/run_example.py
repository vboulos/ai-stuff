#!/usr/bin/env python3
"""
Complete usage example for the test failure analysis system
"""

import os
import sys
from complete_test_analyzer import TestAnalyzer


def main():
    print("🔍 Test Failure Analysis - Complete Example")
    print("=" * 60)
    
    # Check if sample test file exists
    sample_file = "sample_test_results.json"
    if not os.path.exists(sample_file):
        print(f"❌ Sample test file '{sample_file}' not found!")
        print("Please make sure the sample file is in the current directory.")
        return
    
    print(f"📁 Using sample test results: {sample_file}")
    
    # Create analyzer with multiple fallback options
    print("🔧 Setting up analyzer...")
    
    # Try to use environment API key if available
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ Found API key in environment")
    else:
        print("ℹ️  No API key found - will try Claude CLI only")
    
    analyzer = TestAnalyzer(
        claude_cli_path="claude",
        model="claude-3-sonnet-20240229",  # Specific model to avoid 404 errors
        api_key=api_key
    )
    
    # Run analysis
    output_file = "test_analysis_report.json"
    print(f"📊 Starting analysis, output will be saved to: {output_file}")
    
    success = analyzer.analyze_test_failures(sample_file, output_file)
    
    if success:
        print("\n🎉 Analysis completed successfully!")
        print(f"📄 Check these files for results:")
        print(f"   - {output_file} (detailed report)")
        print(f"   - test_analysis_report_simple.json (simple format)")
        
        # Show a preview of results if available
        try:
            import json
            with open(output_file, 'r') as f:
                report = json.load(f)
            
            metadata = report.get('metadata', {})
            summary = report.get('summary', {})
            
            print(f"\n📈 Quick Summary:")
            print(f"   Total failed tests: {metadata.get('total_failed_tests', 0)}")
            print(f"   Analysis success rate: {summary.get('analysis_success_rate', 0)}%")
            
            # Show first successful analysis
            failed_tests = report.get('failed_tests', [])
            for test in failed_tests:
                if not any(keyword in test.get('root_cause', '').lower() 
                          for keyword in ['error', 'failed', 'timeout']):
                    print(f"\n📝 Example Analysis:")
                    print(f"   Test: {test.get('test_name', 'Unknown')}")
                    print(f"   Root Cause: {test.get('root_cause', '')[:100]}...")
                    print(f"   Fix: {test.get('code_fix', '')[:100]}...")
                    break
                    
        except Exception as e:
            print(f"Could not preview results: {e}")
    
    else:
        print("\n❌ Analysis failed!")
        print("🛠️  Troubleshooting tips:")
        print("1. Install Claude CLI: pip install claude-cli")
        print("2. Authenticate: claude auth login")
        print("3. Set API key: export ANTHROPIC_API_KEY='your-key'")
        print("4. Try without validation: --no-validate flag")


def demo_quick_analysis():
    """Demonstrate quick single-test analysis."""
    
    print("\n" + "=" * 60)
    print("🚀 Quick Analysis Demo")
    print("=" * 60)
    
    analyzer = TestAnalyzer()
    
    # Example quick analysis
    test_cases = [
        ("test_division", "ZeroDivisionError: division by zero"),
        ("test_login", "AssertionError: assert False == True"),
        ("test_api", "KeyError: 'user_id'")
    ]
    
    for test_name, error_msg in test_cases:
        print(f"\n🔬 Analyzing: {test_name}")
        print(f"Error: {error_msg}")
        
        result = analyzer.quick_analyze(test_name, error_msg)
        
        print(f"Root Cause: {result['root_cause'][:80]}...")
        print(f"Fix: {result['code_fix'][:80]}...")


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        demo_quick_analysis()
    else:
        main()
        
        # Optionally run quick demo too
        if input("\n🎯 Run quick analysis demo too? (y/N): ").lower().startswith('y'):
            demo_quick_analysis()