#!/usr/bin/env python3
"""
Command line tool to analyze any test failure message
"""

import sys
import argparse
from analyze_failure import analyze_failure

def main():
    parser = argparse.ArgumentParser(description="Analyze test failure messages using Claude CLI")
    parser.add_argument("test_name", help="Name of the failed test")
    parser.add_argument("failure_message", help="The failure message text")
    parser.add_argument("--framework", help="Test framework (cypress, pytest, jest, etc.)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print(f"🔍 Analyzing: {args.test_name}")
    if args.framework:
        print(f"Framework: {args.framework}")
    print("=" * 50)
    
    result = analyze_failure(args.test_name, args.failure_message, args.framework)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print("✅ Analysis Results:")
            print(f"\n📋 Root Cause:\n{result['root_cause']}")
            print(f"\n🔧 Suggested Fix:\n{result['suggested_fix']}")
            
            if result['code_example']:
                print(f"\n💻 Code Example:\n{result['code_example']}")
            
            print(f"\n📊 Confidence: {result['confidence_score']:.2f}")
        else:
            print(f"❌ Analysis failed: {result['error']}")
            sys.exit(1)

if __name__ == "__main__":
    main()