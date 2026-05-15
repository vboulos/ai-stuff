#!/usr/bin/env python3
"""
Test Failure Analyzer Function - Simple function to analyze test failures using Claude CLI
"""

import subprocess
import re
from typing import Dict, Any, Optional


def analyze_test_failure(test_name: str, failure_message: str, framework: str = None) -> Dict[str, Any]:
    """
    Analyze a test failure using Claude CLI and return fix suggestions.
    
    Args:
        test_name: Name of the failed test
        failure_message: The failure message/error text
        framework: Optional test framework (pytest, jest, cypress, etc.)
        
    Returns:
        Dictionary with analysis results including:
        - success: bool - Whether analysis was successful
        - root_cause: str - Root cause of the failure
        - suggested_fix: str - Suggested fix
        - code_example: str - Code example (if applicable)
        - confidence_score: float - Confidence in analysis (0.1-1.0)
        - error: str - Error message if analysis failed
    """
    
    try:
        # Create analysis prompt
        framework_context = f"\nTest Framework: {framework}" if framework else ""
        
        prompt = f"""Analyze this test failure and provide a fix suggestion:

Test Name: {test_name}{framework_context}
Failure Message:
{failure_message}

Please provide your analysis in this format:

**ROOT CAUSE:**
[Explain why the test failed]

**SUGGESTED FIX:**
[Provide specific steps to fix it]

**CODE EXAMPLE:**
[Show code example if applicable]

**CONFIDENCE:**
[Rate confidence from 0.1 to 1.0]

Be concise and practical."""
        
        # Query Claude CLI
        response = _query_claude_cli(prompt)
        
        if not response:
            return {
                "success": False,
                "error": "No response from Claude CLI"
            }
        
        # Parse the response
        analysis = _parse_claude_response(response)
        
        return {
            "success": True,
            "test_name": test_name,
            "failure_message": failure_message,
            "framework": framework,
            **analysis
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _query_claude_cli(prompt: str, claude_cli_path: str = "claude") -> Optional[str]:
    """
    Query Claude CLI with the given prompt.
    
    Args:
        prompt: The prompt to send to Claude
        claude_cli_path: Path to Claude CLI executable
        
    Returns:
        Claude's response text or None if failed
    """
    try:
        # Execute Claude CLI
        process = subprocess.run(
            [claude_cli_path, "--"],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        if process.returncode != 0:
            print(f"Claude CLI error: {process.stderr}")
            return None
        
        return process.stdout.strip()
        
    except subprocess.TimeoutExpired:
        print("Claude CLI query timed out")
        return None
    except Exception as e:
        print(f"Error querying Claude CLI: {e}")
        return None


def _parse_claude_response(response: str) -> Dict[str, Any]:
    """
    Parse Claude's response to extract structured information.
    
    Args:
        response: Raw response from Claude
        
    Returns:
        Dictionary with parsed analysis components
    """
    analysis = {
        "root_cause": "",
        "suggested_fix": "",
        "code_example": "",
        "confidence_score": 0.5,
        "raw_response": response
    }
    
    try:
        # Parse markdown sections using regex
        sections = {}
        
        # Pattern to match **SECTION:** content
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for section_name, content in matches:
            clean_name = section_name.strip().upper()
            clean_content = content.strip()
            sections[clean_name] = clean_content
        
        # Extract information
        analysis["root_cause"] = sections.get("ROOT CAUSE", "").strip()
        analysis["suggested_fix"] = sections.get("SUGGESTED FIX", "").strip()
        analysis["code_example"] = sections.get("CODE EXAMPLE", "").strip()
        
        # Parse confidence score
        confidence_text = sections.get("CONFIDENCE", "0.5")
        try:
            confidence_value = float(re.findall(r'[\d.]+', confidence_text)[0])
            analysis["confidence_score"] = max(0.1, min(1.0, confidence_value))
        except (ValueError, IndexError):
            analysis["confidence_score"] = 0.5
            
    except Exception as e:
        print(f"Warning: Error parsing response: {e}")
    
    return analysis


# Example usage and testing functions
def test_connection() -> bool:
    """Test if Claude CLI is available and working."""
    try:
        response = _query_claude_cli("Hello, can you help me?")
        return response is not None and len(response) > 0
    except Exception:
        return False


def main():
    """Example usage of the analyze_test_failure function."""
    
    # Test connection first
    print("Testing Claude CLI connection...")
    if not test_connection():
        print("❌ Claude CLI connection failed")
        print("Make sure Claude CLI is installed and authenticated")
        return
    
    print("✅ Claude CLI is working")
    
    # Example test failures
    examples = [
        {
            "test_name": "test_user_authentication",
            "failure_message": "AssertionError: Expected status code 200, but got 401\nResponse: {'error': 'Invalid authentication token'}",
            "framework": "pytest"
        },
        {
            "test_name": "test_database_connection", 
            "failure_message": "psycopg2.OperationalError: could not connect to server: Connection refused",
            "framework": "pytest"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*50}")
        print(f"Example {i}: Analyzing {example['test_name']}")
        print(f"{'='*50}")
        
        result = analyze_test_failure(
            example["test_name"],
            example["failure_message"], 
            example["framework"]
        )
        
        if result["success"]:
            print(f"✅ Analysis successful!")
            print(f"\nRoot Cause:\n{result['root_cause']}")
            print(f"\nSuggested Fix:\n{result['suggested_fix']}")
            
            if result['code_example']:
                print(f"\nCode Example:\n{result['code_example']}")
            
            print(f"\nConfidence Score: {result['confidence_score']:.2f}")
        else:
            print(f"❌ Analysis failed: {result['error']}")


if __name__ == "__main__":
    main()