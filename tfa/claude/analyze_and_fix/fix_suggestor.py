#!/usr/bin/env python3
"""
Fix Suggester Class - Suggests code fixes for test failures using Claude CLI
"""

import subprocess
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

class FixSuggestor:
    """
    Class to suggest code fixes for test failures using Claude CLI.
    """
    
    def __init__(self, claude_timeout: int = 300, runbook_path: str = None):
        """
        Initialize the FixSuggestor.
        
        Args:
            claude_timeout: Timeout for Claude CLI calls in seconds (default: 300)
                          Fix suggestions take longer than analysis, so higher default
            runbook_path: Optional path to runbook template file for fix prompts
        """
        self.claude_timeout = claude_timeout
        self.runbook_path = runbook_path
    
    def suggest_fix(self, test_name: str, failure_message: str, framework: str = None, 
                   analysis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a code fix suggestion for a test failure.
        
        Args:
            test_name: Name of the failed test
            failure_message: The failure message/error text
            framework: Optional test framework
            analysis_data: Optional previous analysis data to enhance fix suggestions
            
        Returns:
            Dictionary with:
            - success: bool
            - fix_type: str
            - priority: str  
            - estimated_effort: str
            - code_changes: str
            - configuration_changes: str
            - dependencies: str
            - validation_steps: list
            - prevention: str
            - impact_assessment: str
            - error: str (if failed)
            - suggested_at: str (timestamp)
        """
        
        try:
            # Create prompt for fix suggestion
            if self.runbook_path:
                prompt = self._create_fix_prompt_from_runbook(
                    test_name, failure_message, framework, analysis_data, self.runbook_path
                )
            else:
                prompt = self._create_fix_prompt(test_name, failure_message, framework, analysis_data)
            
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
                    "suggested_at": datetime.now().isoformat()
                }
            
            response = result.stdout.strip()
            
            # Parse response
            fix_data = self._parse_fix_response(response)
            fix_data["suggested_at"] = datetime.now().isoformat()
            
            return fix_data
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Claude CLI timeout after {self.claude_timeout} seconds",
                "suggested_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggested_at": datetime.now().isoformat()
            }
    
    def _create_fix_prompt(self, test_name: str, failure_message: str, framework: str, 
                          analysis_data: Dict[str, Any]) -> str:
        """Create a prompt for fix suggestion."""
        
        framework_info = f" (Framework: {framework})" if framework else ""
        
        # Include analysis data if available
        analysis_context = ""
        if analysis_data and analysis_data.get("success"):
            analysis_context = f"""
Previous Analysis:
- Root Cause: {analysis_data.get('root_cause', '')}
- Category: {analysis_data.get('error_category', '')}
- Severity: {analysis_data.get('severity', '')}
"""
        
        return f"""Provide specific fix suggestions for this failed test{framework_info}:

Test: {test_name}
Error: {failure_message}{analysis_context}

IMPORTANT: Use this EXACT format with ** markers:

**FIX_TYPE:**
quick_fix

**PRIORITY:**
high

**ESTIMATED_EFFORT:**
hours

**CODE_CHANGES:**
```javascript
// Specific code changes here
```

**CONFIGURATION_CHANGES:**
```
// Config changes here or "None needed"
```

**DEPENDENCIES:**
```
// Dependencies here or "None needed"
```

**VALIDATION_STEPS:**
1. First validation step
2. Second validation step
3. Third validation step

**PREVENTION:**
Specific prevention steps

**IMPACT_ASSESSMENT:**
Areas affected by this fix

**ROLLBACK_PLAN:**
How to rollback if needed"""
    
    def _create_fix_prompt_from_runbook(self, test_name: str, failure_message: str, 
                                       framework: str, analysis_data: Dict[str, Any],
                                       runbook_path: str = "fix_runbook.txt") -> str:
        """
        Create a fix prompt from a runbook file.
        
        Args:
            test_name: Name of the failed test
            failure_message: The failure message/error text
            framework: Optional test framework
            analysis_data: Optional previous analysis data
            runbook_path: Path to the runbook template file
            
        Returns:
            Formatted prompt string with variables substituted
            
        The runbook template can use these placeholders:
            {test_name} - The name of the test
            {failure_message} - The error/failure message
            {framework} - The test framework (or "Not specified")
            {framework_info} - Formatted framework info for display
            {analysis_context} - Previous analysis context (or empty)
        """
        try:
            # Read runbook template
            with open(runbook_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Prepare variables for substitution
            framework_info = f" (Framework: {framework})" if framework else ""
            framework_display = framework if framework else "Not specified"
            
            # Include analysis data if available
            analysis_context = ""
            if analysis_data and analysis_data.get("success"):
                analysis_context = f"""
**PREVIOUS ANALYSIS:**
- Root Cause: {analysis_data.get('root_cause', '')}
- Suggested Fix: {analysis_data.get('suggested_fix', '')}
- Confidence: {analysis_data.get('confidence_score', 0)}
- Category: {analysis_data.get('error_category', '')}
- Severity: {analysis_data.get('severity', '')}
"""
            
            # Substitute variables in template
            prompt = template.format(
                test_name=test_name,
                failure_message=failure_message,
                framework=framework_display,
                framework_info=framework_info,
                analysis_context=analysis_context
            )
            
            return prompt
            
        except FileNotFoundError:
            # Fallback to hardcoded prompt if runbook not found
            print(f"⚠️  Runbook not found at '{runbook_path}', using default prompt")
            return self._create_fix_prompt(test_name, failure_message, framework, analysis_data)
        except KeyError as e:
            # Handle missing template variable
            print(f"⚠️  Missing template variable in runbook: {e}, using default prompt")
            return self._create_fix_prompt(test_name, failure_message, framework, analysis_data)
        except Exception as e:
            # Handle other errors
            print(f"⚠️  Error reading runbook: {e}, using default prompt")
            return self._create_fix_prompt(test_name, failure_message, framework, analysis_data)

    def _parse_fix_response(self, response: str) -> Dict[str, Any]:
        """Parse the Claude response into structured fix data with flexible fallback."""
        
        fix_data = {
            "success": True,
            "fix_type": "unknown",
            "priority": "medium",
            "estimated_effort": "unknown",
            "code_changes": "",
            "configuration_changes": "",
            "dependencies": "",
            "validation_steps": [],
            "prevention": "",
            "impact_assessment": "",
            "rollback_plan": "",
            "raw_response": response
        }
        
        # First, try structured parsing
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            section_key = section_name.strip().upper()
            sections[section_key] = content.strip()
        
        # Map sections to fix_data
        if sections:
            # Structured response found
            fix_data["fix_type"] = self._extract_value(sections.get("FIX_TYPE", ""), ["quick_fix", "refactor", "configuration", "dependency", "infrastructure", "test_update"], "unknown")
            fix_data["priority"] = self._extract_value(sections.get("PRIORITY", ""), ["critical", "high", "medium", "low"], "medium")
            fix_data["estimated_effort"] = self._extract_value(sections.get("ESTIMATED_EFFORT", ""), ["minutes", "hours", "days"], "unknown")
            fix_data["prevention"] = sections.get("PREVENTION", "")
            fix_data["impact_assessment"] = sections.get("IMPACT_ASSESSMENT", "")
            fix_data["rollback_plan"] = sections.get("ROLLBACK_PLAN", "")
            
            # Extract code blocks
            fix_data["code_changes"] = self._extract_code_block(sections.get("CODE_CHANGES", ""))
            fix_data["configuration_changes"] = self._extract_code_block(sections.get("CONFIGURATION_CHANGES", ""))
            fix_data["dependencies"] = self._extract_code_block(sections.get("DEPENDENCIES", ""))
            
            # Parse validation steps
            validation_text = sections.get("VALIDATION_STEPS", "")
            fix_data["validation_steps"] = self._parse_validation_steps(validation_text)
        else:
            # Fallback: unstructured response - extract what we can
            print("⚠️  Response not in structured format, using flexible parsing...")
            fix_data = self._parse_unstructured_response(response, fix_data)
        
        # Validate that we got meaningful content
        has_content = any([
            fix_data["code_changes"],
            fix_data["configuration_changes"], 
            fix_data["dependencies"],
            fix_data["prevention"],
            fix_data["impact_assessment"],
            fix_data["rollback_plan"],
            len(fix_data["validation_steps"]) > 0,
            len(response.strip()) > 50  # At least some meaningful text
        ])
        
        if not has_content:
            fix_data["success"] = False
            fix_data["error"] = "Failed to parse meaningful fix suggestions from response"
        
        return fix_data
    
    def _extract_value(self, text: str, valid_values: list, default: str) -> str:
        """Extract value from text, checking against valid values."""
        if not text:
            return default
        
        text_lower = text.lower().strip()
        for value in valid_values:
            if value in text_lower:
                return value
        return default
    
    def _parse_unstructured_response(self, response: str, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parser for unstructured/natural language responses."""
        
        # Extract all code blocks
        code_blocks = re.findall(r'```(?:\w+\n)?(.*?)```', response, re.DOTALL)
        if code_blocks:
            # First code block goes to code_changes
            fix_data["code_changes"] = code_blocks[0].strip()
            # Additional blocks go to configuration_changes
            if len(code_blocks) > 1:
                fix_data["configuration_changes"] = "\n\n".join(cb.strip() for cb in code_blocks[1:])
        
        # Extract numbered lists (likely validation steps or suggestions)
        numbered_items = re.findall(r'^\d+\.\s+(.+)$', response, re.MULTILINE)
        if numbered_items:
            fix_data["validation_steps"] = numbered_items
        
        # Look for priority indicators
        if any(word in response.lower() for word in ['critical', 'urgent', 'immediate']):
            fix_data["priority"] = "critical"
        elif 'high' in response.lower():
            fix_data["priority"] = "high"
        elif 'low' in response.lower():
            fix_data["priority"] = "low"
        
        # Look for effort indicators
        if any(word in response.lower() for word in ['quick', 'simple', 'easy', 'minutes']):
            fix_data["estimated_effort"] = "minutes"
        elif 'days' in response.lower() or 'week' in response.lower():
            fix_data["estimated_effort"] = "days"
        elif any(word in response.lower() for word in ['hour', 'moderate']):
            fix_data["estimated_effort"] = "hours"
        
        # Use first paragraph or sentence as prevention if we don't have other content
        if not fix_data["prevention"] and not fix_data["code_changes"]:
            # Take first substantial paragraph as the main content
            paragraphs = [p.strip() for p in response.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                fix_data["prevention"] = paragraphs[0]
                if len(paragraphs) > 1:
                    fix_data["impact_assessment"] = paragraphs[1]
        
        # Infer fix type from content
        response_lower = response.lower()
        if any(word in response_lower for word in ['timeout', 'increase timeout', 'wait']):
            fix_data["fix_type"] = "configuration"
        elif any(word in response_lower for word in ['update', 'upgrade', 'install', 'dependency', 'package']):
            fix_data["fix_type"] = "dependency"
        elif any(word in response_lower for word in ['refactor', 'restructure', 'redesign']):
            fix_data["fix_type"] = "refactor"
        elif any(word in response_lower for word in ['test', 'assertion', 'expect']):
            fix_data["fix_type"] = "test_update"
        else:
            fix_data["fix_type"] = "quick_fix"
        
        return fix_data
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks or return raw text."""
        if not text:
            return ""
        
        # Try to extract from code blocks first
        code_match = re.search(r'```(?:\w+\n)?(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code block, return the text as-is (after stripping)
        # This allows for more flexible responses
        stripped = text.strip()
        
        # Filter out obvious non-code content markers
        if stripped.lower() in ['none', 'n/a', 'not applicable', 'no changes needed']:
            return ""
        
        return stripped
    
    def _parse_validation_steps(self, text: str) -> List[str]:
        """Parse validation steps from numbered list."""
        steps = []
        for line in text.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.', line):
                steps.append(re.sub(r'^\d+\.\s*', '', line))
        return steps if steps else [text.strip()] if text.strip() else []
    
    def suggest_fixes_for_analyses(self, analysis_results: list) -> list:
        """
        Generate fix suggestions for multiple analysis results.
        
        Args:
            analysis_results: List of analysis result dictionaries
            
        Returns:
            List of results with added fix suggestions
        """
        results = []
        
        for i, analysis_result in enumerate(analysis_results, 1):
            test_name = analysis_result.get("test_name", f"test_{i}")
            framework = analysis_result.get("framework")
            original_test = analysis_result.get("original_test", {})
            analysis = analysis_result.get("analysis", {})
            
            failure_message = original_test.get("failure_message", "")
            
            print(f"🛠️  Generating fix {i}/{len(analysis_results)}: {test_name}")
            
            fix_suggestion = self.suggest_fix(
                test_name, 
                failure_message, 
                framework, 
                analysis
            )
            
            # Add fix suggestion to the result
            result = analysis_result.copy()
            result["fix_suggestion"] = fix_suggestion
            
            results.append(result)
            
            if fix_suggestion["success"]:
                fix_type = fix_suggestion.get("fix_type", "unknown")
                priority = fix_suggestion.get("priority", "medium")
                print(f"✅ Fix generated (Type: {fix_type}, Priority: {priority})")
            else:
                print(f"❌ Fix generation failed: {fix_suggestion.get('error', 'Unknown error')}")
        
        return results
    
    def get_fix_summary(self, results_with_fixes: list) -> Dict[str, Any]:
        """
        Generate a summary of fix suggestions.
        
        Args:
            results_with_fixes: List of results with fix suggestions
            
        Returns:
            Summary dictionary
        """
        total_fixes = len(results_with_fixes)
        successful_fixes = sum(1 for r in results_with_fixes if r.get("fix_suggestion", {}).get("success"))
        
        # Count by fix type
        fix_types = {}
        priorities = {}
        efforts = {}
        
        for result in results_with_fixes:
            fix_suggestion = result.get("fix_suggestion", {})
            if fix_suggestion.get("success"):
                fix_type = fix_suggestion.get("fix_type", "unknown")
                priority = fix_suggestion.get("priority", "unknown")
                effort = fix_suggestion.get("estimated_effort", "unknown")
                
                fix_types[fix_type] = fix_types.get(fix_type, 0) + 1
                priorities[priority] = priorities.get(priority, 0) + 1
                efforts[effort] = efforts.get(effort, 0) + 1
        
        return {
            "total_fixes": total_fixes,
            "successful_fixes": successful_fixes,
            "failed_fixes": total_fixes - successful_fixes,
            "success_rate": round(successful_fixes / total_fixes, 2) if total_fixes > 0 else 0,
            "fix_type_distribution": fix_types,
            "priority_distribution": priorities,
            "effort_distribution": efforts
        }

# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Example 1: Using hardcoded prompt (default)")
    print("=" * 70)
    
    suggestor = FixSuggestor()
    
    # Test with sample failure and analysis
    sample_analysis = {
        "success": True,
        "root_cause": "Authentication token is invalid or expired",
        "suggested_fix": "Check token validation logic",
        "confidence_score": 0.8,
        "error_category": "authentication",
        "severity": "high"
    }
    
    result = suggestor.suggest_fix(
        "test_login",
        "AssertionError: Expected status code 200, but got 401",
        "pytest",
        sample_analysis
    )
    
    if result["success"]:
        print("Fix Type:", result["fix_type"])
        print("Priority:", result["priority"])
        print("Effort:", result["estimated_effort"])
        print("Code Changes:", result["code_changes"][:100] + "..." if len(result["code_changes"]) > 100 else result["code_changes"])
        print("Validation Steps:", len(result["validation_steps"]), "steps")
    else:
        print("Error:", result["error"])
    
    print("\n" + "=" * 70)
    print("Example 2: Using runbook template file")
    print("=" * 70)
    
    # Initialize with runbook path
    suggestor_with_runbook = FixSuggestor(runbook_path="fix_runbook.txt")
    
    result2 = suggestor_with_runbook.suggest_fix(
        "test_database_connection",
        "TimeoutError: Connection to database timed out after 30s",
        "pytest",
        sample_analysis
    )
    
    if result2["success"]:
        print("Fix Type:", result2["fix_type"])
        print("Priority:", result2["priority"])
        print("Effort:", result2["estimated_effort"])
        print("Prevention:", result2["prevention"][:100] + "..." if len(result2["prevention"]) > 100 else result2["prevention"])
    else:
        print("Error:", result2["error"])