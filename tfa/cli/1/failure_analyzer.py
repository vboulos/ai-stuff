#!/usr/bin/env python3
"""
FailureAnalyzer - Analyzes test failures to determine root causes using Claude CLI
"""

import subprocess
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import re


class FailureAnalyzer:
    """Analyzes test failures using Claude CLI to determine root causes."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
        self.analysis_cache = {}  # Cache to avoid re-analyzing identical failures
    
    def run_claude_cli(self, prompt: str) -> str:
        """Execute Claude CLI with the given prompt and return response."""
        try:
            result = subprocess.run(
                [self.claude_cli_path, "chat", "--message", prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=60  # 60 second timeout
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Claude CLI error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI request timed out")
        except FileNotFoundError:
            raise Exception("Claude CLI not found. Please ensure it's installed and in PATH.")
    
    def analyze_single_failure(self, test_result: Dict[str, Any], 
                             source_code: Optional[str] = None) -> Dict[str, str]:
        """Analyze a single test failure to determine root cause."""
        
        # Create cache key for identical failures
        cache_key = self._create_cache_key(test_result)
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # Build context for Claude analysis
        context = self._build_analysis_context(test_result, source_code)
        
        # Create analysis prompt
        prompt = f"""
Analyze this test failure and provide a detailed root cause analysis:

{context}

Please provide a structured analysis with the following sections:

1. PRIMARY ROOT CAUSE:
   - What is the fundamental issue causing this test to fail?
   - Is it a logic error, incorrect assumption, missing validation, or something else?

2. TECHNICAL DETAILS:
   - What specific condition or state is causing the failure?
   - Are there any data type mismatches, null values, or boundary conditions?

3. IMPACT ASSESSMENT:
   - How severe is this issue?
   - Could this affect other parts of the system?

4. CONFIDENCE LEVEL:
   - How confident are you in this root cause analysis? (High/Medium/Low)
   - What additional information would help confirm the diagnosis?

Please be specific and technical in your analysis.
"""
        
        try:
            analysis_response = self.run_claude_cli(prompt)
            
            # Parse the structured response
            analysis_result = self._parse_analysis_response(analysis_response)
            
            # Cache the result
            self.analysis_cache[cache_key] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            return {
                'primary_root_cause': f'Analysis failed: {str(e)}',
                'technical_details': 'Unable to analyze due to Claude CLI error',
                'impact_assessment': 'Unknown',
                'confidence_level': 'Low',
                'raw_response': '',
                'analysis_error': str(e)
            }
    
    def analyze_multiple_failures(self, failed_tests: List[Dict[str, Any]], 
                                source_files: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Analyze multiple test failures, with optional source code context."""
        
        analyzed_results = []
        
        for i, test_result in enumerate(failed_tests):
            print(f"Analyzing failure {i+1}/{len(failed_tests)}: {test_result.get('test_name', 'Unknown')}")
            
            # Get source code if available
            source_code = None
            if source_files and test_result.get('file_path'):
                source_code = source_files.get(test_result['file_path'])
            
            # Analyze the failure
            analysis = self.analyze_single_failure(test_result, source_code)
            
            # Combine test result with analysis
            analyzed_result = {
                **test_result,
                'root_cause_analysis': analysis
            }
            
            analyzed_results.append(analyzed_result)
        
        return analyzed_results
    
    def _build_analysis_context(self, test_result: Dict[str, Any], 
                              source_code: Optional[str] = None) -> str:
        """Build context string for Claude analysis."""
        
        context_parts = []
        
        # Test information
        context_parts.append("TEST INFORMATION:")
        context_parts.append(f"Test Name: {test_result.get('test_name', 'Unknown')}")
        context_parts.append(f"Status: {test_result.get('status', 'Unknown')}")
        context_parts.append(f"File: {test_result.get('file_path', 'Unknown')}")
        if test_result.get('line_number'):
            context_parts.append(f"Line: {test_result['line_number']}")
        if test_result.get('test_class'):
            context_parts.append(f"Test Class: {test_result['test_class']}")
        
        # Error message
        context_parts.append("\nERROR MESSAGE:")
        context_parts.append(test_result.get('message', 'No error message available'))
        
        # Stack trace
        if test_result.get('stack_trace'):
            context_parts.append("\nSTACK TRACE:")
            context_parts.append(test_result['stack_trace'])
        
        # Source code context
        if source_code:
            context_parts.append("\nSOURCE CODE CONTEXT:")
            # If we have line number, show context around it
            if test_result.get('line_number'):
                context_lines = self._get_source_context(source_code, test_result['line_number'])
                context_parts.append(context_lines)
            else:
                # Show first 50 lines if no specific line
                lines = source_code.split('\n')[:50]
                context_parts.append('\n'.join(f"{i+1:4d}: {line}" for i, line in enumerate(lines)))
        
        return '\n'.join(context_parts)
    
    def _get_source_context(self, source_code: str, line_number: int, context_size: int = 10) -> str:
        """Get source code context around a specific line number."""
        lines = source_code.split('\n')
        start = max(0, line_number - context_size - 1)
        end = min(len(lines), line_number + context_size)
        
        context_lines = []
        for i in range(start, end):
            marker = ">>> " if i == line_number - 1 else "    "
            context_lines.append(f"{marker}{i+1:4d}: {lines[i]}")
        
        return '\n'.join(context_lines)
    
    def _parse_analysis_response(self, response: str) -> Dict[str, str]:
        """Parse structured analysis response from Claude."""
        
        sections = {
            'primary_root_cause': '',
            'technical_details': '',
            'impact_assessment': '',
            'confidence_level': '',
            'raw_response': response
        }
        
        # Try to extract structured sections
        section_patterns = {
            'primary_root_cause': r'(?:1\.|PRIMARY ROOT CAUSE:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'technical_details': r'(?:2\.|TECHNICAL DETAILS:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'impact_assessment': r'(?:3\.|IMPACT ASSESSMENT:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'confidence_level': r'(?:4\.|CONFIDENCE LEVEL:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)'
        }
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section] = match.group(1).strip()
        
        # If structured parsing failed, try to extract key information
        if not any(sections[key] for key in sections if key != 'raw_response'):
            sections = self._fallback_parse(response)
        
        return sections
    
    def _fallback_parse(self, response: str) -> Dict[str, str]:
        """Fallback parsing when structured response parsing fails."""
        
        # Try to extract confidence level
        confidence_match = re.search(r'confidence.*?:?\s*(high|medium|low)', response, re.IGNORECASE)
        confidence = confidence_match.group(1).title() if confidence_match else 'Medium'
        
        # Use the entire response as root cause if no structure found
        return {
            'primary_root_cause': response[:500] + '...' if len(response) > 500 else response,
            'technical_details': 'See primary root cause analysis',
            'impact_assessment': 'Requires manual assessment',
            'confidence_level': confidence,
            'raw_response': response
        }
    
    def _create_cache_key(self, test_result: Dict[str, Any]) -> str:
        """Create a cache key for identical test failures."""
        key_components = [
            test_result.get('test_name', ''),
            test_result.get('message', ''),
            test_result.get('file_path', ''),
            str(test_result.get('line_number', ''))
        ]
        return '|'.join(key_components)
    
    def get_analysis_summary(self, analyzed_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for analysis results."""
        
        summary = {
            'total_analyzed': len(analyzed_results),
            'confidence_distribution': {'High': 0, 'Medium': 0, 'Low': 0},
            'common_root_causes': {},
            'analysis_errors': 0
        }
        
        for result in analyzed_results:
            analysis = result.get('root_cause_analysis', {})
            
            # Count confidence levels
            confidence = analysis.get('confidence_level', 'Medium')
            if confidence in summary['confidence_distribution']:
                summary['confidence_distribution'][confidence] += 1
            
            # Count analysis errors
            if 'analysis_error' in analysis:
                summary['analysis_errors'] += 1
            
            # Extract common root causes (simplified)
            root_cause = analysis.get('primary_root_cause', '')[:100]  # First 100 chars
            if root_cause:
                summary['common_root_causes'][root_cause] = summary['common_root_causes'].get(root_cause, 0) + 1
        
        return summary