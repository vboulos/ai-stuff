#!/usr/bin/env python3
"""
Simple Failure Analyzer - Analyzes test failures using Claude CLI
"""

import subprocess
from typing import Dict, Any


class SimpleFailureAnalyzer:
    """Analyzes test failures using Claude CLI to find root causes and suggest fixes."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
    
    def run_claude(self, prompt: str) -> str:
        """Run Claude CLI with prompt and return response."""
        try:
            result = subprocess.run(
                [self.claude_cli_path, "chat", "--message", prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_failure(self, test_name: str, failure_message: str) -> Dict[str, Any]:
        """Analyze a single test failure and return root cause and fix suggestion."""
        
        prompt = f"""
Analyze this test failure:

Test Name: {test_name}
Failure Message: {failure_message}

Please provide:
1. ROOT CAUSE: What is causing this test to fail?
2. CODE FIX: Specific code changes to fix the issue

Format your response as:
ROOT CAUSE: [explanation]
CODE FIX: [specific fix suggestion]
"""
        
        response = self.run_claude(prompt)
        
        # Parse response
        root_cause = ""
        code_fix = ""
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('ROOT CAUSE:'):
                current_section = 'root_cause'
                root_cause = line.replace('ROOT CAUSE:', '').strip()
            elif line.startswith('CODE FIX:'):
                current_section = 'code_fix'
                code_fix = line.replace('CODE FIX:', '').strip()
            elif current_section == 'root_cause' and line:
                root_cause += " " + line
            elif current_section == 'code_fix' and line:
                code_fix += " " + line
        
        return {
            'test_name': test_name,
            'failure_message': failure_message,
            'root_cause': root_cause or response,  # Fallback to full response
            'code_fix': code_fix or "See root cause analysis"
        }