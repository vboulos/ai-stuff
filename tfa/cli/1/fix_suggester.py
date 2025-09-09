#!/usr/bin/env python3
"""
FixSuggester - Generates code fix suggestions using Claude CLI
"""

import subprocess
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class FixSuggester:
    """Generates specific code fix suggestions based on test failure analysis."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
        self.fix_cache = {}  # Cache to avoid re-generating identical fixes
    
    def run_claude_cli(self, prompt: str) -> str:
        """Execute Claude CLI with the given prompt and return response."""
        try:
            result = subprocess.run(
                [self.claude_cli_path, "chat", "--message", prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=90  # 90 second timeout for fix generation
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Claude CLI error: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI request timed out")
        except FileNotFoundError:
            raise Exception("Claude CLI not found. Please ensure it's installed and in PATH.")
    
    def suggest_fix_for_failure(self, test_result: Dict[str, Any], 
                               root_cause_analysis: Dict[str, str],
                               source_code: Optional[str] = None) -> Dict[str, Any]:
        """Generate code fix suggestions for a single test failure."""
        
        # Create cache key
        cache_key = self._create_fix_cache_key(test_result, root_cause_analysis)
        if cache_key in self.fix_cache:
            return self.fix_cache[cache_key]
        
        # Build fix suggestion prompt
        prompt = self._build_fix_prompt(test_result, root_cause_analysis, source_code)
        
        try:
            fix_response = self.run_claude_cli(prompt)
            
            # Parse the fix response
            fix_suggestion = self._parse_fix_response(fix_response, test_result)
            
            # Cache the result
            self.fix_cache[cache_key] = fix_suggestion
            
            return fix_suggestion
            
        except Exception as e:
            return {
                'fix_approach': f'Fix generation failed: {str(e)}',
                'code_changes': [],
                'explanation': 'Unable to generate fix due to Claude CLI error',
                'confidence': 'Low',
                'testing_notes': 'Manual investigation required',
                'side_effects': 'Unknown',
                'fix_error': str(e)
            }
    
    def suggest_fixes_for_multiple(self, analyzed_results: List[Dict[str, Any]],
                                 source_files: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Generate fix suggestions for multiple analyzed test failures."""
        
        results_with_fixes = []
        
        for i, result in enumerate(analyzed_results):
            print(f"Generating fix {i+1}/{len(analyzed_results)}: {result.get('test_name', 'Unknown')}")
            
            # Get source code if available
            source_code = None
            if source_files and result.get('file_path'):
                source_code = source_files.get(result['file_path'])
            
            # Generate fix suggestion
            root_cause_analysis = result.get('root_cause_analysis', {})
            fix_suggestion = self.suggest_fix_for_failure(result, root_cause_analysis, source_code)
            
            # Add fix suggestion to result
            result_with_fix = {
                **result,
                'fix_suggestion': fix_suggestion
            }
            
            results_with_fixes.append(result_with_fix)
        
        return results_with_fixes
    
    def _build_fix_prompt(self, test_result: Dict[str, Any], 
                         root_cause_analysis: Dict[str, str],
                         source_code: Optional[str] = None) -> str:
        """Build the prompt for fix suggestion generation."""
        
        prompt_parts = []
        
        prompt_parts.append("GENERATE CODE FIX SUGGESTIONS")
        prompt_parts.append("=" * 50)
        
        # Test information
        prompt_parts.append("\nTEST FAILURE INFORMATION:")
        prompt_parts.append(f"Test: {test_result.get('test_name', 'Unknown')}")
        prompt_parts.append(f"File: {test_result.get('file_path', 'Unknown')}")
        prompt_parts.append(f"Error: {test_result.get('message', 'No message')}")
        
        # Root cause analysis
        prompt_parts.append("\nROOT CAUSE ANALYSIS:")
        prompt_parts.append(f"Primary Cause: {root_cause_analysis.get('primary_root_cause', 'Unknown')}")
        prompt_parts.append(f"Technical Details: {root_cause_analysis.get('technical_details', 'None')}")
        prompt_parts.append(f"Confidence: {root_cause_analysis.get('confidence_level', 'Medium')}")
        
        # Source code
        if source_code:
            prompt_parts.append("\nCURRENT SOURCE CODE:")
            if test_result.get('line_number'):
                context_lines = self._get_source_context(source_code, test_result['line_number'])
                prompt_parts.append(context_lines)
            else:
                lines = source_code.split('\n')[:100]  # First 100 lines
                prompt_parts.append('\n'.join(f"{i+1:4d}: {line}" for i, line in enumerate(lines)))
        
        # Fix request
        prompt_parts.append("\nPlease provide SPECIFIC CODE FIX SUGGESTIONS:")
        prompt_parts.append("""
1. FIX APPROACH:
   - What is your recommended approach to fix this issue?
   - Are there multiple possible solutions?

2. CODE CHANGES:
   - Show the exact lines that need to be changed
   - Provide the corrected code with line numbers
   - Use BEFORE/AFTER format for clarity

3. EXPLANATION:
   - Why will this fix resolve the issue?
   - How does it address the root cause?

4. CONFIDENCE:
   - How confident are you that this fix will work? (High/Medium/Low)

5. TESTING NOTES:
   - How should this fix be tested?
   - Are there specific test cases to verify?

6. SIDE EFFECTS:
   - Could this fix affect other parts of the code?
   - Are there any risks or considerations?

Please be specific and provide actionable code changes.
""")
        
        return '\n'.join(prompt_parts)
    
    def _get_source_context(self, source_code: str, line_number: int, context_size: int = 15) -> str:
        """Get source code context around a specific line number."""
        lines = source_code.split('\n')
        start = max(0, line_number - context_size - 1)
        end = min(len(lines), line_number + context_size)
        
        context_lines = []
        for i in range(start, end):
            marker = ">>> " if i == line_number - 1 else "    "
            context_lines.append(f"{marker}{i+1:4d}: {lines[i]}")
        
        return '\n'.join(context_lines)
    
    def _parse_fix_response(self, response: str, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structured fix response from Claude."""
        
        fix_data = {
            'fix_approach': '',
            'code_changes': [],
            'explanation': '',
            'confidence': 'Medium',
            'testing_notes': '',
            'side_effects': '',
            'raw_response': response
        }
        
        # Parse structured sections
        section_patterns = {
            'fix_approach': r'(?:1\.|FIX APPROACH:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'explanation': r'(?:3\.|EXPLANATION:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'testing_notes': r'(?:5\.|TESTING NOTES:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)',
            'side_effects': r'(?:6\.|SIDE EFFECTS:)(.*?)(?=\n(?:\d\.|[A-Z\s]+:)|\Z)'
        }
        
        for section, pattern in section_patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                fix_data[section] = match.group(1).strip()
        
        # Extract confidence level
        confidence_match = re.search(r'confidence.*?:?\s*(high|medium|low)', response, re.IGNORECASE)
        if confidence_match:
            fix_data['confidence'] = confidence_match.group(1).title()
        
        # Extract code changes
        fix_data['code_changes'] = self._extract_code_changes(response)
        
        # If no structured data found, use fallback
        if not any(fix_data[key] for key in fix_data if key not in ['raw_response', 'code_changes']):
            fix_data = self._fallback_fix_parse(response)
        
        return fix_data
    
    def _extract_code_changes(self, response: str) -> List[Dict[str, str]]:
        """Extract specific code changes from the response."""
        
        code_changes = []
        
        # Look for BEFORE/AFTER patterns
        before_after_pattern = r'(?:BEFORE:|Original:|Current:)(.*?)(?:AFTER:|Fixed:|New:)(.*?)(?=\n\n|\n(?:[A-Z\s]+:)|\Z)'
        matches = re.findall(before_after_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for before, after in matches:
            code_changes.append({
                'type': 'replace',
                'before': before.strip(),
                'after': after.strip(),
                'description': 'Code replacement'
            })
        
        # Look for line-specific changes
        line_pattern = r'Line (\d+):(.*?)(?=\n(?:Line \d+:|[A-Z\s]+:)|\Z)'
        line_matches = re.findall(line_pattern, response, re.DOTALL | re.IGNORECASE)
        
        for line_num, change_desc in line_matches:
            code_changes.append({
                'type': 'line_change',
                'line_number': int(line_num),
                'description': change_desc.strip(),
                'before': '',
                'after': ''
            })
        
        # Look for code blocks
        code_block_pattern = r'```(?:python|java|javascript|js|py)?\n?(.*?)\n?```'
        code_blocks = re.findall(code_block_pattern, response, re.DOTALL)
        
        for i, code_block in enumerate(code_blocks):
            code_changes.append({
                'type': 'code_block',
                'code': code_block.strip(),
                'description': f'Code suggestion {i+1}',
                'before': '',
                'after': ''
            })
        
        return code_changes
    
    def _fallback_fix_parse(self, response: str) -> Dict[str, Any]:
        """Fallback parsing when structured response parsing fails."""
        
        # Extract confidence if possible
        confidence_match = re.search(r'confidence.*?:?\s*(high|medium|low)', response, re.IGNORECASE)
        confidence = confidence_match.group(1).title() if confidence_match else 'Medium'
        
        # Use response as general fix approach
        return {
            'fix_approach': response[:1000] + '...' if len(response) > 1000 else response,
            'code_changes': self._extract_code_changes(response),
            'explanation': 'See fix approach for details',
            'confidence': confidence,
            'testing_notes': 'Test thoroughly after applying changes',
            'side_effects': 'Review for potential impacts',
            'raw_response': response
        }
    
    def _create_fix_cache_key(self, test_result: Dict[str, Any], 
                            root_cause_analysis: Dict[str, str]) -> str:
        """Create cache key for fix suggestions."""
        key_components = [
            test_result.get('test_name', ''),
            test_result.get('message', ''),
            root_cause_analysis.get('primary_root_cause', '')[:200]  # First 200 chars
        ]
        return '|'.join(key_components)
    
    def generate_fix_summary(self, results_with_fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of fix suggestions."""
        
        summary = {
            'total_fixes_generated': len(results_with_fixes),
            'confidence_distribution': {'High': 0, 'Medium': 0, 'Low': 0},
            'fix_types': {},
            'generation_errors': 0,
            'common_fix_approaches': {}
        }
        
        for result in results_with_fixes:
            fix_suggestion = result.get('fix_suggestion', {})
            
            # Count confidence levels
            confidence = fix_suggestion.get('confidence', 'Medium')
            if confidence in summary['confidence_distribution']:
                summary['confidence_distribution'][confidence] += 1
            
            # Count generation errors
            if 'fix_error' in fix_suggestion:
                summary['generation_errors'] += 1
            
            # Count fix types
            code_changes = fix_suggestion.get('code_changes', [])
            for change in code_changes:
                change_type = change.get('type', 'unknown')
                summary['fix_types'][change_type] = summary['fix_types'].get(change_type, 0) + 1
            
            # Common approaches
            approach = fix_suggestion.get('fix_approach', '')[:100]
            if approach:
                summary['common_fix_approaches'][approach] = summary['common_fix_approaches'].get(approach, 0) + 1
        
        return summary