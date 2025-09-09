#!/usr/bin/env python3
"""
FixSuggester - Generates detailed code fix suggestions using Claude CLI
"""

import subprocess
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from failure_analyzer import AnalysisResult


@dataclass
class CodeFixSuggestion:
    """Represents a code fix suggestion with details."""
    test_name: str
    original_failure: str
    root_cause: str
    fix_description: str
    code_example: Optional[str] = None
    framework_specific_advice: Optional[str] = None
    prevention_tips: Optional[str] = None
    estimated_effort: str = "medium"  # low, medium, high
    fix_category: str = "code_change"  # code_change, configuration, environment
    confidence_score: float = 0.7


class FixSuggester:
    """Generates detailed code fix suggestions using Claude CLI."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        """
        Initialize the fix suggester.
        
        Args:
            claude_cli_path: Path to Claude CLI executable
        """
        self.claude_cli_path = claude_cli_path
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def generate_fix_suggestion(self, analysis_result: AnalysisResult) -> CodeFixSuggestion:
        """
        Generate a detailed code fix suggestion based on analysis result.
        
        Args:
            analysis_result: AnalysisResult from failure analysis
            
        Returns:
            CodeFixSuggestion with detailed fix recommendations
        """
        try:
            if not analysis_result.analysis_successful:
                return self._create_fallback_suggestion(analysis_result)
            
            prompt = self._create_fix_prompt(analysis_result)
            
            self.logger.info(f"Generating code fix for: {analysis_result.test_name}")
            
            # Get detailed fix suggestions from Claude
            response = self._query_claude(prompt, timeout=120)
            
            if not response:
                raise Exception("No response from Claude CLI")
            
            # Parse the response
            fix_details = self._parse_fix_response(response)
            
            return CodeFixSuggestion(
                test_name=analysis_result.test_name,
                original_failure=analysis_result.failure_message,
                root_cause=analysis_result.root_cause,
                fix_description=fix_details.get('fix_description', analysis_result.suggested_fix),
                code_example=fix_details.get('code_example'),
                framework_specific_advice=fix_details.get('framework_advice'),
                prevention_tips=fix_details.get('prevention_tips'),
                estimated_effort=fix_details.get('effort', 'medium'),
                fix_category=fix_details.get('category', 'code_change'),
                confidence_score=fix_details.get('confidence_score', analysis_result.confidence_score)
            )
            
        except Exception as e:
            self.logger.error(f"Error generating fix suggestion for {analysis_result.test_name}: {e}")
            return self._create_fallback_suggestion(analysis_result, str(e))
    
    def _create_fix_prompt(self, analysis_result: AnalysisResult) -> str:
        """
        Create a detailed prompt for generating code fix suggestions.
        
        Args:
            analysis_result: AnalysisResult to create fix for
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert software engineer providing detailed code fix suggestions. Based on the following test failure analysis, provide comprehensive fix recommendations.

TEST FAILURE ANALYSIS:
- Test Name: {analysis_result.test_name}
- Root Cause: {analysis_result.root_cause}
- Initial Fix Suggestion: {analysis_result.suggested_fix}

ORIGINAL FAILURE MESSAGE:
{analysis_result.failure_message}

Please provide a detailed code fix suggestion in this exact format:

**FIX DESCRIPTION:**
[Detailed step-by-step explanation of how to fix the issue]

**CODE EXAMPLE:**
[Complete, working code example showing the fix implementation]

**FRAMEWORK ADVICE:**
[Specific best practices and recommendations for the testing framework]

**PREVENTION TIPS:**
[How to prevent similar issues in the future]

**EFFORT ESTIMATE:**
[low/medium/high - estimated effort to implement this fix]

**FIX CATEGORY:**
[code_change/configuration/environment - type of fix required]

**CONFIDENCE:**
[Your confidence level from 0.0 to 1.0 in this fix suggestion]

Guidelines for your response:
1. Provide specific, actionable fix steps
2. Include complete, working code examples when relevant
3. Consider framework-specific best practices
4. Suggest preventive measures for similar issues
5. Be realistic about implementation effort
6. Focus on the most effective solution

Make your suggestions practical and immediately actionable."""
        
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
    
    def _parse_fix_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's response to extract fix details.
        
        Args:
            response: Claude's response text
            
        Returns:
            Dictionary with parsed fix details
        """
        fix_details = {
            'fix_description': '',
            'code_example': '',
            'framework_advice': '',
            'prevention_tips': '',
            'effort': 'medium',
            'category': 'code_change',
            'confidence_score': 0.7
        }
        
        # Try to parse markdown-style sections
        if self._parse_markdown_sections(response, fix_details):
            return fix_details
        
        # Fallback to flexible parsing
        return self._flexible_parse_fix_response(response)
    
    def _parse_markdown_sections(self, response: str, fix_details: Dict[str, Any]) -> bool:
        """Parse markdown-style sections with ** headers."""
        found_sections = 0
        
        # Look for **FIX DESCRIPTION:** pattern
        fix_desc_match = re.search(r'\\*\\*FIX DESCRIPTION:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if fix_desc_match:
            fix_details['fix_description'] = fix_desc_match.group(1).strip()
            found_sections += 1
        
        # Look for **CODE EXAMPLE:** pattern
        code_match = re.search(r'\\*\\*CODE EXAMPLE:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if code_match:
            fix_details['code_example'] = code_match.group(1).strip()
            found_sections += 1
        
        # Look for **FRAMEWORK ADVICE:** pattern
        framework_match = re.search(r'\\*\\*FRAMEWORK ADVICE:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if framework_match:
            fix_details['framework_advice'] = framework_match.group(1).strip()
        
        # Look for **PREVENTION TIPS:** pattern
        prevention_match = re.search(r'\\*\\*PREVENTION TIPS:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if prevention_match:
            fix_details['prevention_tips'] = prevention_match.group(1).strip()
        
        # Look for **EFFORT ESTIMATE:** pattern
        effort_match = re.search(r'\\*\\*EFFORT ESTIMATE:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if effort_match:
            effort_text = effort_match.group(1).strip().lower()
            if any(level in effort_text for level in ['low', 'medium', 'high']):
                for level in ['low', 'medium', 'high']:
                    if level in effort_text:
                        fix_details['effort'] = level
                        break
        
        # Look for **FIX CATEGORY:** pattern
        category_match = re.search(r'\\*\\*FIX CATEGORY:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if category_match:
            category_text = category_match.group(1).strip().lower()
            if any(cat in category_text for cat in ['code_change', 'configuration', 'environment']):
                for cat in ['code_change', 'configuration', 'environment']:
                    if cat in category_text or cat.replace('_', ' ') in category_text:
                        fix_details['category'] = cat
                        break
        
        # Look for **CONFIDENCE:** pattern
        confidence_match = re.search(r'\\*\\*CONFIDENCE:\\*\\*(.*?)(?=\\*\\*[A-Z ]+:\\*\\*|$)', response, re.DOTALL | re.IGNORECASE)
        if confidence_match:
            confidence_text = confidence_match.group(1).strip()
            try:
                numbers = re.findall(r'[0-9]*\\.?[0-9]+', confidence_text)
                if numbers:
                    confidence_score = float(numbers[0])
                    fix_details['confidence_score'] = max(0.0, min(1.0, confidence_score))
            except (ValueError, IndexError):
                fix_details['confidence_score'] = 0.7
        
        return found_sections >= 2
    
    def _flexible_parse_fix_response(self, response: str) -> Dict[str, Any]:
        """
        Flexible parsing when structured format fails.
        
        Args:
            response: Claude's response text
            
        Returns:
            Dictionary with extracted fix details
        """
        self.logger.debug("Using flexible parsing for fix response")
        
        lines = response.split('\\n')
        text_lines = [line.strip() for line in lines if line.strip()]
        
        # Extract fix description (first part of response)
        fix_description = ' '.join(text_lines[:len(text_lines)//2]) or "Review Claude's detailed response for fix suggestions"
        
        # Look for code examples (lines with code-like patterns)
        code_lines = []
        for line in text_lines:
            if any(pattern in line for pattern in ['def ', 'function ', 'class ', 'import ', '```', 'assert', 'expect']):
                code_lines.append(line)
        
        code_example = '\\n'.join(code_lines) if code_lines else None
        
        return {
            'fix_description': fix_description,
            'code_example': code_example,
            'framework_advice': '',
            'prevention_tips': '',
            'effort': 'medium',
            'category': 'code_change',
            'confidence_score': 0.6
        }
    
    def _create_fallback_suggestion(self, analysis_result: AnalysisResult, error_msg: str = None) -> CodeFixSuggestion:
        """
        Create a fallback suggestion when Claude analysis fails.
        
        Args:
            analysis_result: Original analysis result
            error_msg: Optional error message
            
        Returns:
            Basic CodeFixSuggestion
        """
        fix_description = analysis_result.suggested_fix if analysis_result.analysis_successful else "Manual investigation required"
        
        if error_msg:
            fix_description += f" (Note: Detailed analysis failed: {error_msg})"
        
        return CodeFixSuggestion(
            test_name=analysis_result.test_name,
            original_failure=analysis_result.failure_message,
            root_cause=analysis_result.root_cause,
            fix_description=fix_description,
            confidence_score=max(0.2, analysis_result.confidence_score - 0.2)
        )
    
    def generate_multiple_fixes(self, analysis_results: List[AnalysisResult]) -> List[CodeFixSuggestion]:
        """
        Generate fix suggestions for multiple analysis results.
        
        Args:
            analysis_results: List of AnalysisResult objects
            
        Returns:
            List of CodeFixSuggestion objects
        """
        fix_suggestions = []
        total_results = len(analysis_results)
        
        self.logger.info(f"Generating fix suggestions for {total_results} test failures")
        
        for i, analysis_result in enumerate(analysis_results, 1):
            self.logger.info(f"Generating fix {i}/{total_results}: {analysis_result.test_name}")
            fix_suggestion = self.generate_fix_suggestion(analysis_result)
            fix_suggestions.append(fix_suggestion)
        
        self.logger.info(f"Generated {len(fix_suggestions)} fix suggestions")
        return fix_suggestions
    
    def get_fix_summary(self, fix_suggestions: List[CodeFixSuggestion]) -> Dict[str, Any]:
        """
        Get summary statistics for fix suggestions.
        
        Args:
            fix_suggestions: List of CodeFixSuggestion objects
            
        Returns:
            Dictionary with fix summary
        """
        if not fix_suggestions:
            return {}
        
        # Count by effort level
        effort_counts = {}
        category_counts = {}
        
        for fix in fix_suggestions:
            effort_counts[fix.estimated_effort] = effort_counts.get(fix.estimated_effort, 0) + 1
            category_counts[fix.fix_category] = category_counts.get(fix.fix_category, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(fix.confidence_score for fix in fix_suggestions) / len(fix_suggestions)
        
        # Count fixes with code examples
        with_code_examples = sum(1 for fix in fix_suggestions if fix.code_example)
        
        return {
            'total_fixes': len(fix_suggestions),
            'effort_distribution': effort_counts,
            'category_distribution': category_counts,
            'average_confidence': avg_confidence,
            'fixes_with_code_examples': with_code_examples,
            'high_confidence_fixes': sum(1 for fix in fix_suggestions if fix.confidence_score >= 0.8),
            'low_effort_fixes': effort_counts.get('low', 0)
        }


def main():
    """Example usage of FixSuggester."""
    import sys
    from test_result_reader import TestResultReader
    from failure_filter import FailureFilter
    from failure_analyzer import FailureAnalyzer
    
    if len(sys.argv) < 2:
        print("Usage: python3 fix_suggester.py <json_file>")
        sys.exit(1)
    
    # Read, filter, and analyze test results
    reader = TestResultReader()
    test_cases = reader.read_json_file(sys.argv[1])
    
    filter_obj = FailureFilter()
    failed_tests = filter_obj.extract_failed_tests(test_cases)
    
    if not failed_tests:
        print("🎉 No failed tests to generate fixes for!")
        sys.exit(0)
    
    analyzer = FailureAnalyzer()
    if not analyzer.test_connection():
        print("❌ Cannot connect to Claude CLI")
        sys.exit(1)
    
    # Analyze first few failures
    sample_tests = failed_tests[:2]  # Limit for demonstration
    analysis_results = analyzer.analyze_multiple_failures(sample_tests)
    
    # Generate fix suggestions
    fix_suggester = FixSuggester()
    fix_suggestions = fix_suggester.generate_multiple_fixes(analysis_results)
    
    # Show results
    print(f"\\n🔧 Fix Suggestions Generated:")
    summary = fix_suggester.get_fix_summary(fix_suggestions)
    print(f"Total fixes: {summary['total_fixes']}")
    print(f"Average confidence: {summary['average_confidence']:.2f}")
    print(f"Fixes with code examples: {summary['fixes_with_code_examples']}")
    
    # Show first fix suggestion
    if fix_suggestions:
        fix = fix_suggestions[0]
        print(f"\\n🔍 Sample Fix Suggestion:")
        print(f"Test: {fix.test_name}")
        print(f"Fix: {fix.fix_description[:200]}...")
        if fix.code_example:
            print(f"Has code example: Yes")
        print(f"Effort: {fix.estimated_effort}")
        print(f"Category: {fix.fix_category}")


if __name__ == "__main__":
    main()