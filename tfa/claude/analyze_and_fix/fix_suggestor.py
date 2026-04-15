#!/usr/bin/env python3
"""
Fix Suggester Class - Suggests code fixes for test failures using Ollama
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import ollama
except ImportError:
    raise ImportError("Please install ollama: pip install ollama")

class FixSuggestor:
    """
    Class to suggest code fixes for test failures using Ollama.
    """

    def __init__(self, model: str = "llama3.1", timeout: int = 120):
        """
        Initialize the FixSuggestor.

        Args:
            model: Ollama model to use (e.g., 'llama3.1', 'mistral', 'codellama')
            timeout: Timeout for Ollama calls in seconds
        """
        self.model = model
        self.timeout = timeout
    
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
            prompt = self._create_fix_prompt(test_name, failure_message, framework, analysis_data)

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
                    'temperature': 0.1,  # Low temperature for more consistent fix suggestions
                }
            )

            if not response or 'message' not in response:
                return {
                    "success": False,
                    "error": "Invalid response from Ollama",
                    "suggested_at": datetime.now().isoformat()
                }

            response_text = response['message']['content']

            # Parse response
            fix_data = self._parse_fix_response(response_text)
            fix_data["suggested_at"] = datetime.now().isoformat()

            return fix_data

        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama error: {str(e)}",
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
**PREVIOUS ANALYSIS:**
- Root Cause: {analysis_data.get('root_cause', '')}
- Suggested Fix: {analysis_data.get('suggested_fix', '')}
- Confidence: {analysis_data.get('confidence_score', 0)}
- Category: {analysis_data.get('error_category', '')}
- Severity: {analysis_data.get('severity', '')}
"""
        
        return f"""Generate specific code fixes for this failed test{framework_info}:

**TEST DETAILS:**
- Test Name: {test_name}
- Error: {failure_message}{analysis_context}

Provide detailed fix suggestions in this format:

**FIX_TYPE:**
[quick_fix|refactor|configuration|dependency|infrastructure|test_update]

**PRIORITY:**
[critical|high|medium|low]

**ESTIMATED_EFFORT:**
[minutes|hours|days]

**CODE_CHANGES:**
```language
// Show specific code changes needed
// Include before/after examples
// Be as specific as possible
```

**CONFIGURATION_CHANGES:**
```
// Any configuration file changes needed
// Include file paths and specific settings
```

**DEPENDENCIES:**
```
// New dependencies or version updates needed
// Include package names and versions
```

**VALIDATION_STEPS:**
1. [Step to verify the fix]
2. [How to test the fix]
3. [Expected outcome]
4. [Additional verification steps]

**PREVENTION:**
[How to prevent this issue in the future - be specific]

**IMPACT_ASSESSMENT:**
[What other areas might be affected by this fix]

**ROLLBACK_PLAN:**
[How to rollback if the fix causes issues]"""

    def _parse_fix_response(self, response: str) -> Dict[str, Any]:
        """Parse the Claude response into structured fix data."""
        
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
        
        # Parse sections using regex
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            section_key = section_name.strip().upper()
            sections[section_key] = content.strip()
        
        # Map sections to fix_data
        fix_data["fix_type"] = sections.get("FIX_TYPE", "unknown").lower()
        fix_data["priority"] = sections.get("PRIORITY", "medium").lower()
        fix_data["estimated_effort"] = sections.get("ESTIMATED_EFFORT", "unknown").lower()
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
        
        # Validate that we got meaningful content
        if not fix_data["code_changes"] and not fix_data["configuration_changes"] and not fix_data["dependencies"]:
            fix_data["success"] = False
            fix_data["error"] = "Failed to parse meaningful fix suggestions from response"
        
        return fix_data
    
    def _extract_code_block(self, text: str) -> str:
        """Extract code from markdown code blocks."""
        code_match = re.search(r'```(?:\w+\n)?(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return text.strip()
    
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
        import time
        results = []
        start_time = time.time()

        for i, analysis_result in enumerate(analysis_results, 1):
            test_name = analysis_result.get("test_name", f"test_{i}")
            framework = analysis_result.get("framework")
            original_test = analysis_result.get("original_test", {})
            analysis = analysis_result.get("analysis", {})

            failure_message = original_test.get("failure_message", "")

            iteration_start = time.time()
            print(f"🛠️  [{i}/{len(analysis_results)}] Generating fix: {test_name[:80]}...")

            fix_suggestion = self.suggest_fix(
                test_name,
                failure_message,
                framework,
                analysis
            )

            iteration_time = time.time() - iteration_start
            elapsed_total = time.time() - start_time
            avg_time = elapsed_total / i
            est_remaining = avg_time * (len(analysis_results) - i)

            # Add fix suggestion to the result
            result = analysis_result.copy()
            result["fix_suggestion"] = fix_suggestion

            results.append(result)

            if fix_suggestion["success"]:
                fix_type = fix_suggestion.get("fix_type", "unknown")
                priority = fix_suggestion.get("priority", "medium")
                print(f"   ✅ Done in {iteration_time:.1f}s (Type: {fix_type}, Priority: {priority}) | ETA: {est_remaining:.0f}s")
            else:
                print(f"   ❌ Failed in {iteration_time:.1f}s: {fix_suggestion.get('error', 'Unknown error')[:60]}")

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
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Suggest fixes for test failures using Ollama')
    parser.add_argument('--model', default='llama3.1', help='Ollama model to use (default: llama3.1)')
    parser.add_argument('--input', help='JSON file with analysis results')
    parser.add_argument('--output', help='Output JSON file for fix suggestions')

    args = parser.parse_args()

    suggestor = FixSuggestor(model=args.model)

    # If input file is provided, process it
    if args.input:
        try:
            with open(args.input, 'r') as f:
                analysis_results = json.load(f)

            # Handle both list and dict formats
            if isinstance(analysis_results, dict):
                if 'results' in analysis_results:
                    analysis_results = analysis_results['results']
                else:
                    analysis_results = [analysis_results]

            results = suggestor.suggest_fixes_for_analyses(analysis_results)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n✅ Results saved to: {args.output}")
            else:
                print(json.dumps(results, indent=2))

        except Exception as e:
            print(f"❌ Error: {e}")
    else:
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