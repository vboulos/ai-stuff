#!/usr/bin/env python3
"""
Complete FailureAnalyzer - Analyzes test failures using Claude CLI with robust error handling
"""

import subprocess
import json
import os
import requests
from typing import Dict, Optional


class FailureAnalyzer:
    """Analyzes test failures with multiple fallback options and robust error handling."""
    
    def __init__(self, claude_cli_path: str = "claude", model: Optional[str] = None, api_key: Optional[str] = None):
        self.claude_cli_path = claude_cli_path
        self.model = model
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.use_api_fallback = bool(self.api_key)
    
    def analyze_failure(self, test_name: str, failure_message: str) -> Dict[str, str]:
        """Analyze a test failure and return root cause and fix suggestion."""
        
        # Try Claude CLI first
        result = self._try_claude_cli(test_name, failure_message)
        
        # If CLI fails and we have API key, try direct API
        if self._is_error_result(result) and self.use_api_fallback:
            print(f"CLI failed for {test_name}, trying direct API...")
            result = self._try_direct_api(test_name, failure_message)
        
        return result
    
    def _try_claude_cli(self, test_name: str, failure_message: str) -> Dict[str, str]:
        """Try analyzing using Claude CLI."""
        
        prompt = self._create_analysis_prompt(test_name, failure_message)
        
        try:
            # Build command
            cmd = [self.claude_cli_path, "chat", "--message", prompt]
            
            # Add model if specified
            if self.model:
                cmd.extend(["--model", self.model])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            response = result.stdout.strip()
            return self._parse_response(response)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return self._handle_cli_error(error_msg)
            
        except subprocess.TimeoutExpired:
            return {
                'root_cause': "Analysis timed out after 60 seconds",
                'code_fix': "Try again or use a simpler test case"
            }
            
        except FileNotFoundError:
            return {
                'root_cause': "Claude CLI not found. Install with: pip install claude-cli",
                'code_fix': "Install Claude CLI or provide correct path"
            }
            
        except Exception as e:
            return {
                'root_cause': f"Unexpected error: {str(e)}",
                'code_fix': "Check Claude CLI installation and configuration"
            }
    
    def _try_direct_api(self, test_name: str, failure_message: str) -> Dict[str, str]:
        """Try analyzing using direct Anthropic API."""
        
        if not self.api_key:
            return {
                'root_cause': "No API key available for fallback",
                'code_fix': "Set ANTHROPIC_API_KEY environment variable"
            }
        
        prompt = self._create_analysis_prompt(test_name, failure_message)
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['content'][0]['text']
            return self._parse_response(content)
            
        except requests.exceptions.RequestException as e:
            return {
                'root_cause': f"API request failed: {str(e)}",
                'code_fix': "Check API key and network connection"
            }
            
        except Exception as e:
            return {
                'root_cause': f"API call error: {str(e)}",
                'code_fix': "Check API configuration"
            }
    
    def _create_analysis_prompt(self, test_name: str, failure_message: str) -> str:
        """Create analysis prompt for Claude."""
        return f"""
Analyze this test failure and provide actionable insights:

Test Name: {test_name}
Failure Message: {failure_message}

Please provide:
1. ROOT CAUSE: What is the underlying issue causing this test to fail?
2. CODE FIX: Specific code changes or steps to fix the issue

Format your response exactly like this:
ROOT CAUSE: [detailed explanation of what's wrong]
CODE FIX: [specific actionable fix]
"""
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's response to extract root cause and fix."""
        
        root_cause = ""
        code_fix = ""
        current_section = None
        
        for line in response.split('\n'):
            line = line.strip()
            
            if line.startswith('ROOT CAUSE:'):
                current_section = 'root_cause'
                root_cause = line.replace('ROOT CAUSE:', '').strip()
            elif line.startswith('CODE FIX:'):
                current_section = 'code_fix'
                code_fix = line.replace('CODE FIX:', '').strip()
            elif current_section == 'root_cause' and line and not line.startswith('CODE FIX:'):
                root_cause += " " + line
            elif current_section == 'code_fix' and line:
                code_fix += " " + line
        
        # Clean up and validate
        root_cause = root_cause.strip()
        code_fix = code_fix.strip()
        
        return {
            'root_cause': root_cause or response[:500] + "...",  # Fallback to truncated response
            'code_fix': code_fix or "See root cause analysis for guidance"
        }
    
    def _handle_cli_error(self, error_msg: str) -> Dict[str, str]:
        """Handle specific Claude CLI errors with helpful suggestions."""
        
        error_msg_lower = error_msg.lower()
        
        if "404" in error_msg and "model" in error_msg_lower:
            return {
                'root_cause': "Claude model not found. The specified model doesn't exist.",
                'code_fix': "Try using --model claude-3-sonnet-20240229 or claude-3-haiku-20240307"
            }
        elif "not_found" in error_msg_lower:
            return {
                'root_cause': "Claude CLI authentication or model access issue.",
                'code_fix': "Run 'claude auth login' or check your API key"
            }
        elif "unauthorized" in error_msg_lower or "401" in error_msg:
            return {
                'root_cause': "Authentication failed with Claude CLI.",
                'code_fix': "Check your API key with 'claude auth status'"
            }
        elif "rate limit" in error_msg_lower or "429" in error_msg:
            return {
                'root_cause': "Rate limit exceeded for Claude API.",
                'code_fix': "Wait a moment and try again, or upgrade your plan"
            }
        else:
            return {
                'root_cause': f"Claude CLI error: {error_msg}",
                'code_fix': "Check Claude CLI installation and authentication"
            }
    
    def _is_error_result(self, result: Dict[str, str]) -> bool:
        """Check if the result indicates an error that should trigger fallback."""
        root_cause = result.get('root_cause', '').lower()
        return any(keyword in root_cause for keyword in [
            'error', 'failed', 'not found', 'timeout', 'unauthorized'
        ])
    
    def test_connection(self) -> bool:
        """Test if Claude CLI or API is working."""
        
        # Test CLI first
        try:
            cmd = [self.claude_cli_path, "chat", "--message", "Hello"]
            if self.model:
                cmd.extend(["--model", self.model])
                
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
            if result.returncode == 0:
                print("✅ Claude CLI working")
                return True
        except Exception:
            print("❌ Claude CLI failed")
        
        # Test API if available
        if self.api_key:
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.api_key,
                    'anthropic-version': '2023-06-01'
                }
                data = {
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 10,
                    'messages': [{'role': 'user', 'content': 'Hi'}]
                }
                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data,
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Direct API working")
                    return True
            except Exception:
                print("❌ Direct API failed")
        
        return False