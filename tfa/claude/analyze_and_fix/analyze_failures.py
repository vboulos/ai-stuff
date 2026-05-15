#!/usr/bin/env python3
"""
Failure Analysis Class - Analyzes test failures using Ollama
"""

import os
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

    def __init__(self, model: str = "llama3.1", timeout: int = 120, prompt_file: str = None):
        """
        Initialize the FailureAnalyzer.

        Args:
            model: Ollama model to use (e.g., 'llama3.1', 'mistral', 'codellama')
            timeout: Timeout for Ollama calls in seconds
            prompt_file: Path to custom prompt file (default: prompts/analysis_prompt.txt)
        """
        self.model = model
        self.timeout = timeout

        # Load prompt template
        if prompt_file is None:
            prompt_file = os.path.join(
                os.path.dirname(__file__),
                "prompts",
                "analysis_prompt_openshift_acm.txt"
            )

        self.prompt_template = self._load_prompt_template(prompt_file)
    
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
            - error_category: str
            - severity: str
            - additional_context: str (optional, depends on prompt)
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
    
    def _load_prompt_template(self, prompt_file: str) -> str:
        """Load prompt template from file."""
        try:
            with open(prompt_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt template file not found: {prompt_file}\n"
                f"Please ensure the prompts directory exists with analysis_prompt.txt"
            )

    def _create_analysis_prompt(self, test_name: str, failure_message: str, framework: str) -> str:
        """Create a prompt for failure analysis."""

        framework_info = f" (Framework: {framework})" if framework else ""

        return self.prompt_template.format(
            framework_info=framework_info,
            test_name=test_name,
            failure_message=failure_message
        )

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
            "additional_context": "",
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
        analysis_data["additional_context"] = sections.get("ADDITIONAL_CONTEXT", "")

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
        import time
        results = []
        start_time = time.time()

        for i, test_case in enumerate(test_cases, 1):
            test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i}"
            failure_message = test_case.get('failure_message') or test_case.get('error') or test_case.get('message', '')
            test_framework = test_case.get('framework') or framework

            iteration_start = time.time()
            print(f"🔬 [{i}/{len(test_cases)}] Analyzing: {test_name[:80]}...")

            analysis = self.analyze_failure(test_name, failure_message, test_framework)

            iteration_time = time.time() - iteration_start
            elapsed_total = time.time() - start_time
            avg_time = elapsed_total / i
            est_remaining = avg_time * (len(test_cases) - i)

            # Add original test info
            result = {
                "test_name": test_name,
                "framework": test_framework,
                "original_test": test_case,
                "analysis": analysis
            }

            results.append(result)

            if analysis["success"]:
                print(f"   ✅ Done in {iteration_time:.1f}s (confidence: {analysis['confidence_score']:.2f}) | ETA: {est_remaining:.0f}s")
            else:
                print(f"   ❌ Failed in {iteration_time:.1f}s: {analysis.get('error', 'Unknown error')[:60]}")

        return results

# Example usage and testing
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Analyze test failures using Ollama')
    parser.add_argument('--model', default='llama3.1', help='Ollama model to use (default: llama3.1)')
    parser.add_argument('--input', help='JSON file with test failures to analyze')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--framework', help='Test framework (e.g., pytest, jest)')

    args = parser.parse_args()

    analyzer = FailureAnalyzer(model=args.model)

    # If input file is provided, process it
    if args.input:
        try:
            with open(args.input, 'r') as f:
                test_failures = json.load(f)

            # Handle both list and dict formats
            if isinstance(test_failures, dict):
                for key in ['tests', 'failures', 'failed_tests']:
                    if key in test_failures:
                        test_failures = test_failures[key]
                        break

            results = analyzer.analyze_multiple_failures(test_failures, args.framework)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n✅ Results saved to: {args.output}")
            else:
                print(json.dumps(results, indent=2))

        except Exception as e:
            print(f"❌ Error: {e}")
    else:
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