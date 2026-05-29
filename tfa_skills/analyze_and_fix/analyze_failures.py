#!/usr/bin/env python3
"""
Failure Analysis Class - Analyzes test failures using Ollama with analyze-test-failures skill

Implements the analyze-test-failures skill for comprehensive test failure analysis:
- JUnit XML scanning and parsing
- Root cause analysis with Ollama LLM
- Structured JSON output following skill schema
- Source code mapping and fix suggestions
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

    def __init__(self, model: str = "llama3.1", timeout: int = 120, prompt_file: str = None, skill_mode: bool = True):
        """
        Initialize the FailureAnalyzer.

        Args:
            model: Ollama model to use (e.g., 'llama3.1', 'mistral', 'codellama')
            timeout: Timeout for Ollama calls in seconds
            prompt_file: Path to custom prompt file (default: loads from skill)
            skill_mode: Use analyze-test-failures skill format (default: True)
        """
        self.model = model
        self.timeout = timeout
        self.skill_mode = skill_mode

        # Load prompt template
        if prompt_file is None:
            if skill_mode:
                prompt_file = os.path.join(
                    os.path.dirname(__file__),
                    "skills",
                    "analyze-test-failures.md"
                )
            else:
                prompt_file = os.path.join(
                    os.path.dirname(__file__),
                    "prompts",
                    "analysis_prompt_openshift_acm.txt"
                )

        self.prompt_template = self._load_prompt_template(prompt_file)
    
    def analyze_failure(self, test_name: str, failure_message: str, framework: str = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze a test failure using Ollama with analyze-test-failures skill.

        Args:
            test_name: Name of the failed test
            failure_message: The failure message/error text
            framework: Optional test framework (pytest, jest, cypress, etc.)
            **kwargs: Additional parameters for skill-based analysis:
                - pipeline_name: Jenkins pipeline name
                - build_number: Build number
                - source_file_path: Path to test source file
                - github_repo: GitHub repository URL

        Returns:
            Dictionary following analyze-test-failures skill schema:
            - success: bool
            - testCaseName: str (skill format)
            - failureMessage: str (skill format)
            - rootCauseAnalysis: str (skill format)
            - codeFixSuggestion: str (skill format)
            - sourceCodeMapping: dict (skill format)
            - failureDetails: dict (skill format)
            - fixMetadata: dict (skill format)
            - analyzed_at: str (timestamp)
        """

        try:
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(test_name, failure_message, framework, **kwargs)

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

            # Parse response based on mode
            if self.skill_mode:
                analysis_data = self._parse_skill_response(response_text)
            else:
                analysis_data = self._parse_analysis_response(response_text)
                
            analysis_data["analyzed_at"] = datetime.now().isoformat()
            analysis_data["success"] = True

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

    def _create_analysis_prompt(self, test_name: str, failure_message: str, framework: str, **kwargs) -> str:
        """Create a prompt for failure analysis using skill format."""
        
        if self.skill_mode:
            # Use skill-based prompt format
            skill_prompt = f"""
You are implementing the analyze-test-failures skill for comprehensive test failure analysis.

Following the skill specification, analyze this test failure and provide structured JSON output:

Test Case: {test_name}
Framework: {framework or 'Unknown'}
Failure Message:
{failure_message}

Additional Context:
{self._format_kwargs(kwargs)}

Provide your analysis in the exact JSON format specified by the analyze-test-failures skill schema:
{{
  "testCaseName": "string",
  "failureMessage": "string",
  "rootCauseAnalysis": "string", 
  "codeFixSuggestion": "string",
  "sourceCodeMapping": {{
    "filePath": "string",
    "lineNumber": "integer",
    "testMethod": "string",
    "testClass": "string"
  }},
  "failureDetails": {{
    "stackTrace": "string",
    "errorType": "string",
    "severity": "string",
    "category": "automation|infrastructure|product|environment"
  }},
  "fixMetadata": {{
    "confidenceScore": "float (0-1)",
    "automationBug": "boolean",
    "estimatedEffort": "string",
    "suggestedLines": ["string"]
  }}
}}

Focus on:
1. Identifying if this is an automation bug vs infrastructure/product issue
2. Providing specific, actionable fix suggestions
3. Accurate confidence scoring based on analysis certainty
4. Proper categorization for triage and routing
"""
            return skill_prompt
        else:
            # Use legacy format
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
    
    def _format_kwargs(self, kwargs: Dict[str, Any]) -> str:
        """Format additional keyword arguments for skill prompt."""
        if not kwargs:
            return "None provided"
        
        formatted = []
        for key, value in kwargs.items():
            if value:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted) if formatted else "None provided"
    
    def _parse_skill_response(self, response: str) -> Dict[str, Any]:
        """Parse response following analyze-test-failures skill schema."""
        
        try:
            # Try to extract JSON from response
            import json
            import re
            
            # Look for JSON block in response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                try:
                    skill_data = json.loads(json_match.group())
                    
                    # Validate required skill fields
                    required_fields = ["testCaseName", "failureMessage", "rootCauseAnalysis", "codeFixSuggestion"]
                    if all(field in skill_data for field in required_fields):
                        return skill_data
                except json.JSONDecodeError:
                    pass
            
            # Fallback: try to parse structured sections
            return self._parse_structured_response(response)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse skill response: {str(e)}",
                "raw_response": response
            }
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse response with structured sections into skill format."""
        
        skill_data = {
            "testCaseName": "",
            "failureMessage": "",
            "rootCauseAnalysis": "",
            "codeFixSuggestion": "",
            "sourceCodeMapping": {
                "filePath": "",
                "lineNumber": 0,
                "testMethod": "",
                "testClass": ""
            },
            "failureDetails": {
                "stackTrace": "",
                "errorType": "unknown",
                "severity": "medium",
                "category": "automation"
            },
            "fixMetadata": {
                "confidenceScore": 0.5,
                "automationBug": True,
                "estimatedEffort": "medium",
                "suggestedLines": []
            },
            "raw_response": response
        }
        
        # Parse sections using regex patterns
        sections = {}
        patterns = [
            (r'(?:Root Cause|rootCauseAnalysis)[:s]+(.*?)(?=\n\n|\n[A-Z]|$)', 'rootCauseAnalysis'),
            (r'(?:Code Fix|codeFixSuggestion|Fix Suggestion)[:s]+(.*?)(?=\n\n|\n[A-Z]|$)', 'codeFixSuggestion'),
            (r'(?:Test Case|testCaseName)[:s]+(.*?)(?=\n\n|\n[A-Z]|$)', 'testCaseName'),
            (r'(?:Failure Message|failureMessage)[:s]+(.*?)(?=\n\n|\n[A-Z]|$)', 'failureMessage'),
            (r'(?:Confidence|confidenceScore)[:s]*([0-9.]+)', 'confidence'),
            (r'(?:Category)[:s]+(automation|infrastructure|product|environment)', 'category')
        ]
        
        for pattern, field in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field == 'confidence':
                    try:
                        skill_data['fixMetadata']['confidenceScore'] = float(value)
                    except:
                        pass
                elif field == 'category':
                    skill_data['failureDetails']['category'] = value.lower()
                else:
                    skill_data[field] = value
        
        return skill_data
    
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
            
            # Add skill metadata if in skill mode
            if self.skill_mode and analysis.get("success"):
                result["skill_format"] = True
                result["skill_version"] = "3.0.0"

            results.append(result)

            if analysis["success"]:
                if self.skill_mode:
                    confidence = analysis.get('fixMetadata', {}).get('confidenceScore', 0.5)
                    category = analysis.get('failureDetails', {}).get('category', 'unknown')
                    print(f"   ✅ Done in {iteration_time:.1f}s (confidence: {confidence:.2f}, category: {category}) | ETA: {est_remaining:.0f}s")
                else:
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
    parser.add_argument('--framework', help='Test framework (e.g., pytest, jest, cypress)')
    parser.add_argument('--pipeline', help='Jenkins pipeline name for skill context')
    parser.add_argument('--build', help='Build number for skill context')
    parser.add_argument('--github-repo', help='GitHub repository URL for source analysis')
    parser.add_argument('--legacy-mode', action='store_true', help='Use legacy analysis format instead of skill format')

    args = parser.parse_args()

    # Use skill mode unless legacy mode is specified
    use_skill_mode = not args.legacy_mode if hasattr(args, 'legacy_mode') else True
    analyzer = FailureAnalyzer(model=args.model, skill_mode=use_skill_mode)

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
        kwargs = {}
        if hasattr(args, 'pipeline') and args.pipeline:
            kwargs['pipeline_name'] = args.pipeline
        if hasattr(args, 'build') and args.build:
            kwargs['build_number'] = args.build
        if hasattr(args, 'github_repo') and args.github_repo:
            kwargs['github_repo'] = args.github_repo
        
        result = analyzer.analyze_failure(
            "test_login",
            "AssertionError: Expected status code 200, but got 401",
            "pytest",
            **kwargs
        )

        if result["success"]:
            if "rootCauseAnalysis" in result:  # Skill format
                print("Root Cause:", result["rootCauseAnalysis"])
                print("Fix:", result["codeFixSuggestion"])
                print("Confidence:", result.get("fixMetadata", {}).get("confidenceScore", "N/A"))
                print("Category:", result.get("failureDetails", {}).get("category", "N/A"))
                print("Automation Bug:", result.get("fixMetadata", {}).get("automationBug", "N/A"))
            else:  # Legacy format
                print("Root Cause:", result["root_cause"])
                print("Fix:", result["suggested_fix"])
                print("Confidence:", result["confidence_score"])
                print("Category:", result["error_category"])
                print("Severity:", result["severity"])
        else:
            print("Error:", result["error"])