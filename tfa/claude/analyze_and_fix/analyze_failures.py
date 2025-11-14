#!/usr/bin/env python3
"""
Failure Analysis Class - Analyzes test failures using Claude CLI
"""

import subprocess
import re
from datetime import datetime
from typing import Dict, Any, Optional

class FailureAnalyzer:
    """
    Class to analyze test failures using Claude CLI.
    """
    
    def __init__(self, claude_timeout: int = 120, runbook_path: str = None):
        """
        Initialize the FailureAnalyzer.
        
        Args:
            claude_timeout: Timeout for Claude CLI calls in seconds
            runbook_path: Optional path to runbook template file. If provided,
                         prompts will be read from this file instead of hardcoded.
        """
        self.claude_timeout = claude_timeout
        self.runbook_path = runbook_path
    
    def analyze_failure(self, test_name: str, failure_message: str, framework: str = None) -> Dict[str, Any]:
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
            - analyzed_at: str (timestamp)
        """
        
        try:
            # Create prompt for analysis
            if self.runbook_path:
                prompt = self._create_analysis_prompt_from_runbook(
                    test_name, failure_message, framework, self.runbook_path
                )
            else:
                prompt = self._create_analysis_prompt(test_name, failure_message, framework)
            
            # Query Claude CLI
            result = subprocess.run(
                ["claude", "--"],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.claude_timeout
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Claude CLI error: {result.stderr}",
                    "analyzed_at": datetime.now().isoformat()
                }
            
            response = result.stdout.strip()
            
            # Parse response
            analysis_data = self._parse_analysis_response(response)
            analysis_data["analyzed_at"] = datetime.now().isoformat()
            
            return analysis_data
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Claude CLI timeout after {self.claude_timeout} seconds",
                "analyzed_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
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
    
    def _create_analysis_prompt_from_runbook(self, test_name: str, failure_message: str, 
                                             framework: str, runbook_path: str = "analysis_runbook.txt") -> str:
        """
        Create a prompt for failure analysis from a runbook file.
        
        Args:
            test_name: Name of the failed test
            failure_message: The failure message/error text
            framework: Optional test framework
            runbook_path: Path to the runbook template file
            
        Returns:
            Formatted prompt string with variables substituted
            
        The runbook template can use these placeholders:
            {test_name} - The name of the test
            {failure_message} - The error/failure message
            {framework} - The test framework (or "Not specified")
            {framework_info} - Formatted framework info for display
        """
        try:
            # Read runbook template
            with open(runbook_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Prepare variables for substitution
            framework_info = f" (Framework: {framework})" if framework else ""
            framework_display = framework if framework else "Not specified"
            
            # Substitute variables in template
            prompt = template.format(
                test_name=test_name,
                failure_message=failure_message,
                framework=framework_display,
                framework_info=framework_info
            )
            
            return prompt
            
        except FileNotFoundError:
            # Fallback to hardcoded prompt if runbook not found
            print(f"⚠️  Runbook not found at '{runbook_path}', using default prompt")
            return self._create_analysis_prompt(test_name, failure_message, framework)
        except KeyError as e:
            # Handle missing template variable
            print(f"⚠️  Missing template variable in runbook: {e}, using default prompt")
            return self._create_analysis_prompt(test_name, failure_message, framework)
        except Exception as e:
            # Handle other errors
            print(f"⚠️  Error reading runbook: {e}, using default prompt")
            return self._create_analysis_prompt(test_name, failure_message, framework)

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the Claude response into structured analysis data with flexible fallback."""
        
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
        
        # First, try structured parsing
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            sections[section_name.strip().upper()] = content.strip()
        
        # Map sections to analysis_data
        if sections:
            # Structured response found
            analysis_data["root_cause"] = sections.get("ROOT CAUSE", "")
            analysis_data["suggested_fix"] = sections.get("SUGGESTED FIX", "")
            analysis_data["code_example"] = sections.get("CODE EXAMPLE", "")
            analysis_data["error_category"] = self._extract_category(sections.get("ERROR_CATEGORY", ""), "unknown")
            analysis_data["severity"] = self._extract_severity(sections.get("SEVERITY", ""), "medium")
            
            # Extract confidence score
            confidence_text = sections.get("CONFIDENCE", "0.5")
            analysis_data["confidence_score"] = self._extract_confidence(confidence_text)
        else:
            # Fallback: unstructured response - extract what we can
            print("⚠️  Response not in structured format, using flexible parsing...")
            analysis_data = self._parse_unstructured_analysis(response, analysis_data)
        
        # Validate that we got meaningful content - be more lenient
        has_content = any([
            analysis_data["root_cause"],
            analysis_data["suggested_fix"],
            analysis_data["code_example"],
            len(response.strip()) > 50  # At least some meaningful text
        ])
        
        if not has_content:
            analysis_data["success"] = False
            analysis_data["error"] = "Failed to parse meaningful analysis from response"
        
        return analysis_data
    
    def _extract_category(self, text: str, default: str) -> str:
        """Extract error category from text."""
        if not text:
            return default
        
        text_lower = text.lower()
        categories = ['timeout', 'assertion', 'network', 'configuration', 'dependency', 
                     'ui_interaction', 'database', 'authentication']
        
        for category in categories:
            if category in text_lower:
                return category
        return default
    
    def _extract_severity(self, text: str, default: str) -> str:
        """Extract severity from text."""
        if not text:
            return default
        
        text_lower = text.lower()
        if 'critical' in text_lower:
            return 'critical'
        elif 'high' in text_lower:
            return 'high'
        elif 'low' in text_lower:
            return 'low'
        elif 'medium' in text_lower:
            return 'medium'
        return default
    
    def _parse_unstructured_analysis(self, response: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parser for unstructured/natural language responses."""
        
        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+\n)?(.*?)```', response, re.DOTALL)
        if code_blocks:
            analysis_data["code_example"] = code_blocks[0].strip()
        
        # Extract numbered lists (likely suggested fixes)
        numbered_items = re.findall(r'^\d+\.\s+(.+)$', response, re.MULTILINE)
        if numbered_items:
            analysis_data["suggested_fix"] = "\n".join(numbered_items)
        
        # Use first substantial paragraph as root cause if we don't have other content
        if not analysis_data["root_cause"]:
            paragraphs = [p.strip() for p in response.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                analysis_data["root_cause"] = paragraphs[0]
                # If we have more paragraphs and no suggested fix, use the second one
                if len(paragraphs) > 1 and not analysis_data["suggested_fix"]:
                    analysis_data["suggested_fix"] = paragraphs[1]
        
        # Infer error category from content
        response_lower = response.lower()
        if any(word in response_lower for word in ['timeout', 'timed out', 'time out']):
            analysis_data["error_category"] = 'timeout'
        elif any(word in response_lower for word in ['assert', 'expect', 'should']):
            analysis_data["error_category"] = 'assertion'
        elif any(word in response_lower for word in ['network', 'connection', 'http']):
            analysis_data["error_category"] = 'network'
        elif any(word in response_lower for word in ['config', 'setting', 'environment']):
            analysis_data["error_category"] = 'configuration'
        elif any(word in response_lower for word in ['ui', 'element', 'selector', 'click', 'button']):
            analysis_data["error_category"] = 'ui_interaction'
        
        # Infer severity
        if any(word in response_lower for word in ['critical', 'severe', 'blocker']):
            analysis_data["severity"] = 'critical'
        elif any(word in response_lower for word in ['high', 'important', 'major']):
            analysis_data["severity"] = 'high'
        elif 'low' in response_lower or 'minor' in response_lower:
            analysis_data["severity"] = 'low'
        else:
            analysis_data["severity"] = 'medium'
        
        # Try to extract confidence if mentioned
        confidence_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', response_lower)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                if confidence > 1:  # If it's a percentage like 80, convert to 0.8
                    confidence = confidence / 100
                analysis_data["confidence_score"] = max(0.1, min(1.0, confidence))
            except:
                pass
        
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
    print("=" * 70)
    print("Example 1: Using hardcoded prompt (default)")
    print("=" * 70)
    
    analyzer = FailureAnalyzer()
    
    # # Test with sample failure
    # result = analyzer.analyze_failure(
    #     "test_login",
    #     "AssertionError: Expected status code 200, but got 401",
    #     "pytest"
    # )
    
    # if result["success"]:
    #     print("Root Cause:", result["root_cause"])
    #     print("Fix:", result["suggested_fix"])
    #     print("Confidence:", result["confidence_score"])
    #     print("Category:", result["error_category"])
    #     print("Severity:", result["severity"])
    # else:
    #     print("Error:", result["error"])
    
    print("\n" + "=" * 70)
    print("Example 2: Using runbook template file")
    print("=" * 70)
    
    # Initialize with runbook path
    analyzer_with_runbook = FailureAnalyzer(runbook_path="analysis_runbook.txt")
    
    result2 = analyzer_with_runbook.analyze_failure(
        "test_database_connection",
        "TimeoutError: Connection to database timed out after 30s",
        "pytest"
    )
    
    if result2["success"]:
        print("Root Cause:", result2["root_cause"])
        print("Fix:", result2["suggested_fix"])
        print("Confidence:", result2["confidence_score"])
        print("Category:", result2["error_category"])
        print("Severity:", result2["severity"])
    else:
        print("Error:", result2["error"])