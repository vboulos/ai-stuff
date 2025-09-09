#!/usr/bin/env python3
"""
Simple function to analyze test failures using Claude CLI
"""

import subprocess
import re
from typing import Dict, Any, Optional


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


# Quick test
if __name__ == "__main__":
    result = analyze_failure(
        "test_login", 
        "AssertionError: Expected 200, got 401",
        "pytest"
    )
    
    if result["success"]:
        print("Root Cause:", result["root_cause"])
        print("Fix:", result["suggested_fix"])
        print("Confidence:", result["confidence_score"])
    else:
        print("Error:", result["error"])