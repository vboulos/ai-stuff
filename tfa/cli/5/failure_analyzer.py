#!/usr/bin/env python3
"""
FailureAnalyzer - Analyzes test failures using Claude CLI to find root causes
"""

import subprocess
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from failure_filter import FailedTestCase


@dataclass
class AnalysisResult:
    """Represents the analysis result for a failed test."""
    test_name: str
    failure_message: str
    root_cause: str
    suggested_fix: str
    confidence_score: float
    analysis_successful: bool = True
    error_message: Optional[str] = None


class FailureAnalyzer:
    """Analyzes test failures using Claude CLI to determine root causes."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        """
        Initialize the failure analyzer.
        
        Args:
            claude_cli_path: Path to Claude CLI executable
        """
        self.claude_cli_path = claude_cli_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def test_connection(self) -> bool:
        """
        Test Claude CLI connection and availability.
        
        Returns:
            True if Claude CLI is working, False otherwise
        """
        try:
            # Test Claude CLI version
            result = subprocess.run(
                [self.claude_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Claude CLI found: {result.stdout.strip()}")
                
                # Test with a simple query
                test_result = self._query_claude("Can you help analyze test failures?", timeout=30)
                
                if test_result and ("yes" in test_result.lower() or "help" in test_result.lower()):
                    self.logger.info("Claude CLI connection verified")
                    return True
                else:
                    self.logger.error(f"Claude CLI test query failed: {test_result}")
                    return False
            else:
                self.logger.error(f"Claude CLI error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("Claude CLI not found. Please install it first.")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Claude CLI timeout during connection test")
            return False
        except Exception as e:
            self.logger.error(f"Error testing Claude CLI connection: {e}")
            return False
    
    def analyze_failure(self, failed_test: FailedTestCase) -> AnalysisResult:
        """
        Analyze a single test failure to determine root cause.
        
        Args:
            failed_test: FailedTestCase object to analyze
            
        Returns:
            AnalysisResult with root cause analysis
        """
        try:
            prompt = self._create_analysis_prompt(failed_test)
            
            self.logger.info(f"Analyzing failure: {failed_test.name}")
            
            # Get analysis from Claude
            response = self._query_claude(prompt, timeout=120)
            
            if not response:
                raise Exception("No response from Claude CLI")
            
            # Parse the response
            analysis = self._parse_claude_response(response)
            
            return AnalysisResult(
                test_name=failed_test.name,
                failure_message=failed_test.failure_message,
                root_cause=analysis.get('root_cause', 'Unable to determine root cause'),
                suggested_fix=analysis.get('suggested_fix', 'No specific fix suggested'),
                confidence_score=analysis.get('confidence_score', 0.7),
                analysis_successful=True
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing failure {failed_test.name}: {e}")
            return AnalysisResult(
                test_name=failed_test.name,
                failure_message=failed_test.failure_message,
                root_cause=f"Analysis failed: {str(e)}",
                suggested_fix="Manual investigation required",
                confidence_score=0.0,
                analysis_successful=False,
                error_message=str(e)
            )
    
    def _create_analysis_prompt(self, failed_test: FailedTestCase) -> str:
        """
        Create a prompt for Claude to analyze the test failure.
        
        Args:
            failed_test: FailedTestCase to analyze
            
        Returns:
            Formatted prompt string
        """
        # Include context about the test
        context = []
        if failed_test.framework:
            context.append(f"Framework: {failed_test.framework}")
        if failed_test.category:
            context.append(f"Category: {failed_test.category}")
        if failed_test.severity:
            context.append(f"Severity: {failed_test.severity}")
        if failed_test.file_path:
            context.append(f"File: {failed_test.file_path}")
        if failed_test.line_number:
            context.append(f"Line: {failed_test.line_number}")
        
        context_str = " | ".join(context) if context else "No additional context"
        
        prompt = f"""You are an expert software engineer analyzing a test failure. Please analyze the following test failure and provide insights.

TEST DETAILS:
- Test Name: {failed_test.name}
- Context: {context_str}

FAILURE MESSAGE:
{failed_test.failure_message}

Please analyze this failure and provide your response in this exact format:

**ROOT CAUSE:**
[Detailed explanation of what caused the test to fail]

**SUGGESTED FIX:**
[Specific, actionable steps to fix the issue]

**CONFIDENCE:**
[Your confidence level from 0.0 to 1.0]

Focus on:
1. The most likely root cause based on the error message
2. Practical, actionable fix suggestions
3. Consider common patterns in test failures
4. Account for the testing framework and context if provided

Be concise but thorough in your analysis."""
        
        return prompt
    
    def _query_claude(self, prompt: str, timeout: int = 60) -> Optional[str]:
        """
        Send a query to Claude CLI and get the response.
        
        Args:
            prompt: The prompt to send to Claude
            timeout: Timeout in seconds
            
        Returns:
            Claude's response or None if failed
        """
        try:
            result = subprocess.run(
                [self.claude_cli_path],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.logger.error(f"Claude CLI error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude CLI query timeout after {timeout}s")
            return None
        except Exception as e:
            self.logger.error(f"Error querying Claude: {e}")
            return None
    
    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's response to extract root cause and suggested fix.
        
        Args:
            response: Claude's response text
            
        Returns:
            Dictionary with parsed analysis
        """
        analysis = {
            'root_cause': '',
            'suggested_fix': '',
            'confidence_score': 0.7
        }
        
        # Try to parse markdown-style sections
        if self._parse_markdown_sections(response, analysis):
            return analysis
        
        # Fallback to flexible parsing
        return self._flexible_parse_response(response)
    
    def _parse_markdown_sections(self, response: str, analysis: Dict[str, Any]) -> bool:
        """Parse markdown-style sections with ** headers."""
        found_sections = 0
        
        # Look for **ROOT CAUSE:** pattern
        root_cause_match = re.search(r'\*\*ROOT CAUSE:\*\*(.*?)(?=\*\*[A-Z ]+:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
        if root_cause_match:
            analysis['root_cause'] = root_cause_match.group(1).strip()
            found_sections += 1
        
        # Look for **SUGGESTED FIX:** pattern
        fix_match = re.search(r'\*\*SUGGESTED FIX:\*\*(.*?)(?=\*\*[A-Z ]+:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
        if fix_match:
            analysis['suggested_fix'] = fix_match.group(1).strip()
            found_sections += 1
        
        # Look for **CONFIDENCE:** pattern
        confidence_match = re.search(r'\*\*CONFIDENCE:\*\*(.*?)(?=\*\*[A-Z ]+:\*\*|$)', response, re.DOTALL | re.IGNORECASE)
        if confidence_match:
            confidence_text = confidence_match.group(1).strip()
            try:
                numbers = re.findall(r'[0-9]*\\.?[0-9]+', confidence_text)
                if numbers:
                    confidence_score = float(numbers[0])
                    analysis['confidence_score'] = max(0.0, min(1.0, confidence_score))
            except (ValueError, IndexError):
                analysis['confidence_score'] = 0.7
        
        return found_sections >= 2
    
    def _flexible_parse_response(self, response: str) -> Dict[str, Any]:
        """
        Flexible parsing when structured format fails.
        
        Args:
            response: Claude's response text
            
        Returns:
            Dictionary with extracted analysis
        """
        self.logger.debug("Using flexible parsing for Claude response")
        
        lines = response.split('\\n')
        text_lines = [line.strip() for line in lines if line.strip()]
        
        root_cause = ""
        suggested_fix = ""
        confidence_score = 0.6
        
        # Look for key phrases that indicate analysis content
        for i, line in enumerate(text_lines):
            line_lower = line.lower()
            
            # Look for root cause indicators
            if any(phrase in line_lower for phrase in ['because', 'due to', 'caused by', 'issue is', 'problem is']):
                root_cause = ' '.join(text_lines[i:i+2])
                break
            elif any(phrase in line_lower for phrase in ['failure occurs', 'error indicates', 'suggests that']):
                root_cause = ' '.join(text_lines[i:i+2])
                break
        
        # Look for fix suggestions
        for i, line in enumerate(text_lines):
            line_lower = line.lower()
            
            if any(phrase in line_lower for phrase in ['should', 'need to', 'try', 'fix', 'solve', 'resolve']):
                suggested_fix = ' '.join(text_lines[i:i+2])
                break
            elif any(phrase in line_lower for phrase in ['recommend', 'suggest', 'consider']):
                suggested_fix = ' '.join(text_lines[i:i+2])
                break
        
        # If we still don't have content, use the response in parts
        if not root_cause and text_lines:
            root_cause = ' '.join(text_lines[:len(text_lines)//2]) or "Analysis provided by Claude"
        
        if not suggested_fix and text_lines:
            suggested_fix = ' '.join(text_lines[len(text_lines)//2:]) or "Review Claude's analysis for suggestions"
        
        return {
            'root_cause': root_cause or "Unable to parse root cause from Claude's response",
            'suggested_fix': suggested_fix or "Unable to parse suggested fix from Claude's response", 
            'confidence_score': confidence_score
        }
    
    def analyze_multiple_failures(self, failed_tests: List[FailedTestCase]) -> List[AnalysisResult]:
        """
        Analyze multiple test failures.
        
        Args:
            failed_tests: List of FailedTestCase objects
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        total_failures = len(failed_tests)
        
        self.logger.info(f"Starting analysis of {total_failures} failed tests")
        
        for i, failed_test in enumerate(failed_tests, 1):
            self.logger.info(f"Analyzing failure {i}/{total_failures}: {failed_test.name}")
            result = self.analyze_failure(failed_test)
            results.append(result)
        
        # Log summary
        successful_analyses = sum(1 for r in results if r.analysis_successful)
        avg_confidence = sum(r.confidence_score for r in results if r.analysis_successful) / max(1, successful_analyses)
        
        self.logger.info(f"Analysis complete: {successful_analyses}/{total_failures} successful")
        self.logger.info(f"Average confidence score: {avg_confidence:.2f}")
        
        return results
    
    def get_analysis_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Get summary statistics for analysis results.
        
        Args:
            results: List of AnalysisResult objects
            
        Returns:
            Dictionary with analysis summary
        """
        if not results:
            return {}
        
        successful = [r for r in results if r.analysis_successful]
        failed = [r for r in results if not r.analysis_successful]
        
        avg_confidence = sum(r.confidence_score for r in successful) / len(successful) if successful else 0
        
        return {
            'total_analyses': len(results),
            'successful_analyses': len(successful),
            'failed_analyses': len(failed),
            'success_rate': len(successful) / len(results) * 100,
            'average_confidence': avg_confidence,
            'high_confidence_count': sum(1 for r in successful if r.confidence_score >= 0.8),
            'low_confidence_count': sum(1 for r in successful if r.confidence_score < 0.5)
        }


def main():
    """Example usage of FailureAnalyzer."""
    import sys
    from test_result_reader import TestResultReader
    from failure_filter import FailureFilter
    
    if len(sys.argv) < 2:
        print("Usage: python3 failure_analyzer.py <json_file>")
        sys.exit(1)
    
    # Read and filter test results
    reader = TestResultReader()
    test_cases = reader.read_json_file(sys.argv[1])
    
    filter_obj = FailureFilter()
    failed_tests = filter_obj.extract_failed_tests(test_cases)
    
    if not failed_tests:
        print("🎉 No failed tests to analyze!")
        sys.exit(0)
    
    # Analyze failures
    analyzer = FailureAnalyzer()
    
    if not analyzer.test_connection():
        print("❌ Cannot connect to Claude CLI")
        sys.exit(1)
    
    # Analyze first few failures as example
    sample_tests = failed_tests[:3]  # Limit to first 3 for demonstration
    results = analyzer.analyze_multiple_failures(sample_tests)
    
    # Show results
    print(f"\\n📊 Analysis Results:")
    summary = analyzer.get_analysis_summary(results)
    print(f"Successful analyses: {summary['successful_analyses']}/{summary['total_analyses']}")
    print(f"Average confidence: {summary['average_confidence']:.2f}")
    
    print(f"\\n🔍 Sample Analysis:")
    for result in results[:2]:  # Show first 2 results
        print(f"\\n{result.test_name}:")
        print(f"Root Cause: {result.root_cause[:150]}...")
        print(f"Suggested Fix: {result.suggested_fix[:150]}...")
        print(f"Confidence: {result.confidence_score:.2f}")


if __name__ == "__main__":
    main()