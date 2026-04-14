#!/usr/bin/env python3
"""
Failure Analysis Class - Analyzes test failures using Ollama
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import ollama
except ImportError:
    raise ImportError("Please install ollama: pip install ollama")

class FailureAnalyzer:
    """
    Class to analyze test failures using Ollama.
    """

    def __init__(self, model: str = "llama3.1", timeout: int = 120):
        """
        Initialize the FailureAnalyzer.

        Args:
            model: Ollama model to use (e.g., 'llama3.1', 'mistral', 'codellama')
            timeout: Timeout for Ollama calls in seconds
        """
        self.model = model
        self.timeout = timeout
    
    def analyze_failure(self, test_name: str, failure_message: str, framework: str = None) -> Dict[str, Any]:
        """
        Analyze a test failure using Ollama.

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
            - analyzed_at: str (timestamp)
        """

        try:
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(test_name, failure_message, framework)

            # Query Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.1,  # Low temperature for more consistent analysis
                }
            )

            if not response or 'message' not in response:
                return {
                    "success": False,
                    "error": "Invalid response from Ollama",
                    "analyzed_at": datetime.now().isoformat()
                }

            response_text = response['message']['content']

            # Parse response
            analysis_data = self._parse_analysis_response(response_text)
            analysis_data["analyzed_at"] = datetime.now().isoformat()

            return analysis_data

        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama error: {str(e)}",
                "analyzed_at": datetime.now().isoformat()
            }
    
    def _create_analysis_prompt(self, test_name: str, failure_message: str, framework: str) -> str:
        """Create a prompt for failure analysis."""
        
        framework_info = f" (Framework: {framework})" if framework else ""
        
        return f"""Analyze this test failure{framework_info}:

Test: {test_name}
Error: {failure_message}

Provide analysis in this format:

**ROOT CAUSE:**
[Why did it fail? Be specific about the underlying issue]

**SUGGESTED FIX:**
[High-level approach to fix the issue]

**CODE EXAMPLE:**
[Code example if helpful - show specific changes needed]

**CONFIDENCE:**
[0.1 to 1.0 - how confident are you in this analysis]

**ERROR_CATEGORY:**
[timeout|assertion|network|configuration|dependency|ui_interaction|database|authentication]

**SEVERITY:**
[critical|high|medium|low]"""

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the Claude response into structured analysis data."""
        
        analysis_data = {
            "success": True,
            "root_cause": "",
            "suggested_fix": "",
            "code_example": "",
            "confidence_score": 0.5,
            "error_category": "unknown",
            "severity": "medium",
            "raw_response": response
        }
        
        # Parse sections using regex
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            sections[section_name.strip().upper()] = content.strip()
        
        # Map sections to analysis_data
        analysis_data["root_cause"] = sections.get("ROOT CAUSE", "")
        analysis_data["suggested_fix"] = sections.get("SUGGESTED FIX", "")
        analysis_data["code_example"] = sections.get("CODE EXAMPLE", "")
        analysis_data["error_category"] = sections.get("ERROR_CATEGORY", "unknown").lower()
        analysis_data["severity"] = sections.get("SEVERITY", "medium").lower()
        
        # Extract confidence score
        confidence_text = sections.get("CONFIDENCE", "0.5")
        analysis_data["confidence_score"] = self._extract_confidence(confidence_text)
        
        # Validate that we got meaningful content
        if not analysis_data["root_cause"] and not analysis_data["suggested_fix"]:
            analysis_data["success"] = False
            analysis_data["error"] = "Failed to parse meaningful analysis from response"
        
        return analysis_data
    
    def _extract_confidence(self, confidence_text: str) -> float:
        """Extract confidence score from text."""
        try:
            confidence = float(re.findall(r'[\d.]+', confidence_text)[0])
            return max(0.1, min(1.0, confidence))
        except:
            return 0.5
    
    def analyze_multiple_failures(self, test_cases: list, framework: str = None) -> list:
        """
        Analyze multiple test failures.
        
        Args:
            test_cases: List of test case dictionaries
            framework: Optional framework to apply to all tests
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i}"
            failure_message = test_case.get('failure_message') or test_case.get('error') or test_case.get('message', '')
            test_framework = test_case.get('framework') or framework
            
            print(f"🔬 Analyzing {i}/{len(test_cases)}: {test_name}")
            
            analysis = self.analyze_failure(test_name, failure_message, test_framework)
            
            # Add original test info
            result = {
                "test_name": test_name,
                "framework": test_framework,
                "original_test": test_case,
                "analysis": analysis
            }
            
            results.append(result)
            
            if analysis["success"]:
                print(f"✅ Analysis completed (confidence: {analysis['confidence_score']:.2f})")
            else:
                print(f"❌ Analysis failed: {analysis['error']}")
        
        return results

# Example usage and testing
if __name__ == "__main__":
    analyzer = FailureAnalyzer()
    
    # Test with sample failure
    result = analyzer.analyze_failure(
        "test_login",
        "AssertionError: Expected status code 200, but got 401",
        "pytest"
    )
    
    if result["success"]:
        print("Root Cause:", result["root_cause"])
        print("Fix:", result["suggested_fix"])
        print("Confidence:", result["confidence_score"])
        print("Category:", result["error_category"])
        print("Severity:", result["severity"])
    else:
        print("Error:", result["error"])