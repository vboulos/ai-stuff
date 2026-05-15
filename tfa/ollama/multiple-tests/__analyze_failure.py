#!/usr/bin/env python3
"""
Simple function to analyze test failures using Claude CLI
"""

import subprocess
import re
import json
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List


def analyze_failure(test_name: str, failure_message: str, framework: str = None) -> Dict[str, Any]:
    """
    Analyze a test failure using Claude CLI.
    
    Args:
        test_name: Name of the failed test
        failure_message: The failure message/error text  
        framework: Optional test framework (pytest, jest, cypress, etc.)
        
    Returns:
        Dictionary with:
        - success: bool
        - root_cause: str  
        - suggested_fix: str
        - code_example: str
        - confidence_score: float (0.1-1.0)
        - error: str (if failed)
    """
    
    try:
        # Create prompt
        framework_info = f" (Framework: {framework})" if framework else ""
        
        prompt = f"""Analyze this test failure{framework_info}:

Test: {test_name}
Error: {failure_message}

Provide analysis in this format:

**ROOT CAUSE:**
[Why did it fail?]

**SUGGESTED FIX:**  
[How to fix it?]

**CODE EXAMPLE:**
[Code example if helpful]

**CONFIDENCE:**
[0.1 to 1.0]"""

        # Query Claude CLI
        result = subprocess.run(
            ["claude", "--"],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {"success": False, "error": f"Claude CLI error: {result.stderr}"}
        
        response = result.stdout.strip()
        
        # Parse response
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            sections[section_name.strip().upper()] = content.strip()
        
        # Extract confidence score
        confidence = 0.5
        confidence_text = sections.get("CONFIDENCE", "0.5")
        try:
            confidence = float(re.findall(r'[\d.]+', confidence_text)[0])
            confidence = max(0.1, min(1.0, confidence))
        except:
            pass
        
        return {
            "success": True,
            "root_cause": sections.get("ROOT CAUSE", ""),
            "suggested_fix": sections.get("SUGGESTED FIX", ""),
            "code_example": sections.get("CODE EXAMPLE", ""),
            "confidence_score": confidence
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_multiple_failures(failures: List[Dict[str, str]], output_file: str = None) -> Dict[str, Any]:
    """
    Analyze multiple test failures and export results to JSON.
    
    Args:
        failures: List of dicts with 'test_name', 'failure_message', and optional 'framework'
        output_file: Path to output JSON file (default: 'failure_analysis.json')
    
    Returns:
        Dictionary with analysis results and metadata
    """
    output_file = output_file or "failure_analysis.json"
    
    results = {
        "analysis_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_failures": len(failures),
            "analyzed_failures": 0,
            "successful_analyses": 0,
            "failed_analyses": 0
        },
        "failure_analyses": []
    }
    
    for i, failure in enumerate(failures, 1):
        test_name = failure.get("test_name", f"unknown_test_{i}")
        failure_message = failure.get("failure_message", "")
        framework = failure.get("framework", None)
        
        print(f"Analyzing {i}/{len(failures)}: {test_name}")
        
        analysis = analyze_failure(test_name, failure_message, framework)
        
        # Add metadata to analysis
        analysis_result = {
            "test_name": test_name,
            "framework": framework,
            "failure_message": failure_message,
            "analysis": analysis,
            "analyzed_at": datetime.now().isoformat()
        }
        
        results["failure_analyses"].append(analysis_result)
        results["analysis_metadata"]["analyzed_failures"] += 1
        
        if analysis.get("success", False):
            results["analysis_metadata"]["successful_analyses"] += 1
        else:
            results["analysis_metadata"]["failed_analyses"] += 1
    
    # Export to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nAnalysis complete! Results saved to: {output_file}")
    print(f"Successfully analyzed: {results['analysis_metadata']['successful_analyses']}")
    print(f"Failed to analyze: {results['analysis_metadata']['failed_analyses']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Analyze test failures using Claude CLI')
    parser.add_argument('-t', '--test-name', help='Single test name to analyze')
    parser.add_argument('-m', '--message', help='Failure message for single test')
    parser.add_argument('-f', '--framework', help='Test framework (pytest, jest, cypress, etc.)')
    parser.add_argument('-i', '--input-file', help='JSON file with multiple failures to analyze')
    parser.add_argument('-o', '--output', help='Output JSON file (default: failure_analysis.json)')
    
    args = parser.parse_args()
    
    if args.input_file:
        # Analyze multiple failures from input file
        try:
            with open(args.input_file, 'r') as f:
                failures = json.load(f)
            
            # Convert input format if needed
            if isinstance(failures, list) and failures:
                # Handle different input formats
                processed_failures = []
                for failure in failures:
                    if isinstance(failure, dict):
                        processed_failure = {
                            "test_name": failure.get("name", failure.get("test_name", "unknown")),
                            "failure_message": failure.get("failure_message", failure.get("message", "")),
                            "framework": failure.get("framework", args.framework)
                        }
                        processed_failures.append(processed_failure)
                
                analyze_multiple_failures(processed_failures, args.output)
            else:
                print("Error: Input file should contain a list of failure objects")
                return 1
                
        except FileNotFoundError:
            print(f"Error: Input file '{args.input_file}' not found")
            return 1
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in input file '{args.input_file}'")
            return 1
    
    elif args.test_name and args.message:
        # Analyze single failure
        result = analyze_failure(args.test_name, args.message, args.framework)
        
        # Export single result
        output_file = args.output or "single_failure_analysis.json"
        single_result = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_failures": 1,
                "analyzed_failures": 1,
                "successful_analyses": 1 if result.get("success") else 0,
                "failed_analyses": 0 if result.get("success") else 1
            },
            "failure_analyses": [{
                "test_name": args.test_name,
                "framework": args.framework,
                "failure_message": args.message,
                "analysis": result,
                "analyzed_at": datetime.now().isoformat()
            }]
        }
        
        with open(output_file, 'w') as f:
            json.dump(single_result, f, indent=2)
        
        print(f"Analysis saved to: {output_file}")
        
        if result["success"]:
            print("\nRoot Cause:", result["root_cause"])
            print("Fix:", result["suggested_fix"])
            print("Confidence:", result["confidence_score"])
        else:
            print("Error:", result["error"])
    
    else:
        # Run quick test
        print("Running quick test...")
        result = analyze_failure(
            "test_login", 
            "AssertionError: Expected 200, got 401",
            "pytest"
        )
        
        # Export test result
        test_result = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_failures": 1,
                "analyzed_failures": 1,
                "successful_analyses": 1 if result.get("success") else 0,
                "failed_analyses": 0 if result.get("success") else 1,
                "note": "This is a test run"
            },
            "failure_analyses": [{
                "test_name": "test_login",
                "framework": "pytest",
                "failure_message": "AssertionError: Expected 200, got 401",
                "analysis": result,
                "analyzed_at": datetime.now().isoformat()
            }]
        }
        
        output_file = "test_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(test_result, f, indent=2)
        
        print(f"Test analysis saved to: {output_file}")
        
        if result["success"]:
            print("\nRoot Cause:", result["root_cause"])
            print("Fix:", result["suggested_fix"])
            print("Confidence:", result["confidence_score"])
        else:
            print("Error:", result["error"])
    
    return 0


if __name__ == "__main__":
    exit(main())