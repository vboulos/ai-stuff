#!/usr/bin/env python3
"""
Simple test failure analyzer using Claude CLI
"""

import subprocess
import json
import sys

def analyze_test_failure(test_name, error_message):
    """Analyze a single test failure using Claude CLI."""
    
    prompt = f"""Analyze this test failure:

Test: {test_name}
Error: {error_message}

Please provide:
1. Root cause of the failure
2. Suggested fix
3. Confidence level (0-1)

Keep your response concise and practical."""

    try:
        result = subprocess.run(
            ['claude'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Failed to run Claude CLI: {e}"

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 simple_test_analyzer.py <test_name> <error_message>")
        sys.exit(1)
    
    test_name = sys.argv[1]
    error_message = sys.argv[2]
    
    print(f"Analyzing test failure: {test_name}")
    print("=" * 50)
    
    analysis = analyze_test_failure(test_name, error_message)
    print(analysis)

if __name__ == "__main__":
    main()