#!/usr/bin/env python3
"""
FailureAnalyzer - Analyzes test failures using Claude CLI
"""

import subprocess
from typing import Dict


class FailureAnalyzer:
    """Analyzes test failures to find root causes and suggest fixes using Claude CLI."""
    
    def __init__(self, claude_cli_path: str = "claude"):
        self.claude_cli_path = claude_cli_path
    
    def analyze_failure(self, test_name: str, failure_message: str) -> Dict[str, str]:
        """Analyze a test failure and return root cause and fix suggestion."""
        
        prompt = f"""
Analyze this test failure:

Test: {test_name}
Error: {failure_message}

Provide:
1. ROOT CAUSE: What's causing this failure?
2. CODE FIX: Specific code changes to fix it

Format:
ROOT CAUSE: [your analysis]
CODE FIX: [your fix suggestion]
"""
        
        try:
            # result = subprocess.run(
            #     [self.claude_cli_path, "chat", "--message", prompt],
            #     capture_output=True,
            #     text=True,
            #     check=True,
            #     timeout=60
            # )

            command = [
            self.claude_cli_path,
            prompt,
            "-m", "claude-3-5-sonnet-20240620" #,
            # "-f", temp_filepath
        ]
            # --- END OF CHANGES ---
    
            result= subprocess.run(command, capture_output=True, text=True, check=True)



            response = result.stdout.strip()
        except Exception as e:
            return {
                'root_cause': f"Analysis failed: {str(e)}",
                'code_fix': "Could not generate fix suggestion"
            }
        
        # Parse response
        root_cause = ""
        code_fix = ""
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('ROOT CAUSE:'):
                root_cause = line.replace('ROOT CAUSE:', '').strip()
            elif line.startswith('CODE FIX:'):
                code_fix = line.replace('CODE FIX:', '').strip()
            elif root_cause and not code_fix and not line.startswith('CODE FIX:'):
                root_cause += " " + line
            elif code_fix and line:
                code_fix += " " + line
        
        return {
            'root_cause': root_cause or response,
            'code_fix': code_fix or "See root cause analysis"
        }