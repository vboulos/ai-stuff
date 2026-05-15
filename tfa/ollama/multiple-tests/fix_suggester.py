#!/usr/bin/env python3
"""
Code fix suggester for test failures
"""

import json
import subprocess
import re
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

class FixSuggester:
    """
    Class to suggest code fixes for test failures and append them to analysis JSON files.
    """
    
    def __init__(self, claude_timeout: int = 120):
        """
        Initialize the FixSuggester.
        
        Args:
            claude_timeout: Timeout for Claude CLI calls in seconds
        """
        self.claude_timeout = claude_timeout
    
    def suggest_fix(self, test_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a code fix suggestion for a single test analysis.
        
        Args:
            test_analysis: Dictionary containing test analysis data
            
        Returns:
            Dictionary with fix suggestion or error information
        """
        try:
            test_name = test_analysis.get("test_name", "unknown_test")
            framework = test_analysis.get("framework", "unknown")
            
            # Extract analysis information
            if test_analysis.get("status") == "analyzed" and "analysis" in test_analysis:
                analysis = test_analysis["analysis"]
                root_cause = analysis.get("root_cause", "")
                suggested_fix = analysis.get("suggested_fix", "")
                failure_message = test_analysis.get("original_test", {}).get("failure_message", "")
            else:
                # Handle cases where analysis failed
                root_cause = "Analysis failed"
                suggested_fix = "Unable to analyze"
                failure_message = test_analysis.get("original_test", {}).get("failure_message", "")
            
            # Create comprehensive prompt for code fix generation
            prompt = self._create_fix_prompt(
                test_name, framework, root_cause, suggested_fix, failure_message
            )
            
            # Query Claude CLI for code fix
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
            
            # Parse the fix suggestion response
            fix_data = self._parse_fix_response(response)
            fix_data["suggested_at"] = datetime.now().isoformat()
            fix_data["success"] = True
            
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
    
    def _create_fix_prompt(self, test_name: str, framework: str, root_cause: str, 
                          suggested_fix: str, failure_message: str) -> str:
        """Create a comprehensive prompt for generating code fixes."""
        
        return f"""Generate specific code fixes for this failed test:

**TEST DETAILS:**
- Test Name: {test_name}
- Framework: {framework}
- Root Cause: {root_cause}
- Suggested Fix: {suggested_fix}
- Failure Message: {failure_message}

Please provide code fixes in this format:

**FIX_TYPE:**
[quick_fix|refactor|configuration|dependency|infrastructure]

**PRIORITY:**
[high|medium|low]

**ESTIMATED_EFFORT:**
[minutes|hours|days]

**CODE_CHANGES:**
```language
// Original problematic code (if applicable)
// ... existing code ...

// Fixed code
// ... corrected code ...
```

**CONFIGURATION_CHANGES:**
```language
// Any config file changes needed
```

**DEPENDENCIES:**
```language
// Any new dependencies or version updates needed
```

**VALIDATION_STEPS:**
1. Step to verify the fix
2. How to test the fix
3. Expected outcome

**PREVENTION:**
[How to prevent this issue in the future]

**RELATED_ISSUES:**
[Any other potential issues this fix might address]"""

    def _parse_fix_response(self, response: str) -> Dict[str, Any]:
        """Parse the Claude response into structured fix data."""
        
        fix_data = {
            "fix_type": "unknown",
            "priority": "medium",
            "estimated_effort": "unknown",
            "code_changes": "",
            "configuration_changes": "",
            "dependencies": "",
            "validation_steps": [],
            "prevention": "",
            "related_issues": "",
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
        fix_data["related_issues"] = sections.get("RELATED_ISSUES", "")
        
        # Extract code blocks
        fix_data["code_changes"] = self._extract_code_block(sections.get("CODE_CHANGES", ""))
        fix_data["configuration_changes"] = self._extract_code_block(sections.get("CONFIGURATION_CHANGES", ""))
        fix_data["dependencies"] = self._extract_code_block(sections.get("DEPENDENCIES", ""))
        
        # Parse validation steps
        validation_text = sections.get("VALIDATION_STEPS", "")
        fix_data["validation_steps"] = self._parse_validation_steps(validation_text)
        
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
    
    def process_analysis_file(self, analysis_file: str, output_file: str = None, 
                            max_fixes: int = None) -> Dict[str, Any]:
        """
        Process an analysis JSON file and append fix suggestions.
        
        Args:
            analysis_file: Path to the analysis JSON file
            output_file: Output file path (defaults to original file with _with_fixes suffix)
            max_fixes: Maximum number of fixes to generate
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Read the analysis file
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            
            if "test_analyses" not in data:
                return {"success": False, "error": "Invalid analysis file format"}
            
            test_analyses = data["test_analyses"]
            
            if max_fixes:
                test_analyses = test_analyses[:max_fixes]
            
            print(f"🔧 Generating code fixes for {len(test_analyses)} test analyses...")
            
            # Generate fixes for each test analysis
            fixes_generated = 0
            fixes_failed = 0
            
            for i, test_analysis in enumerate(test_analyses, 1):
                test_name = test_analysis.get("test_name", f"test_{i}")
                print(f"\n🛠️  Generating fix {i}/{len(test_analyses)}: {test_name}")
                
                fix_suggestion = self.suggest_fix(test_analysis)
                
                # Append fix suggestion to the test analysis
                test_analysis["fix_suggestion"] = fix_suggestion
                
                if fix_suggestion.get("success"):
                    fixes_generated += 1
                    fix_type = fix_suggestion.get("fix_type", "unknown")
                    priority = fix_suggestion.get("priority", "medium")
                    print(f"✅ Fix generated (Type: {fix_type}, Priority: {priority})")
                else:
                    fixes_failed += 1
                    print(f"❌ Fix generation failed: {fix_suggestion.get('error', 'Unknown error')}")
            
            # Update metadata
            if "analysis_metadata" not in data:
                data["analysis_metadata"] = {}
            
            data["analysis_metadata"]["fixes_generated"] = fixes_generated
            data["analysis_metadata"]["fixes_failed"] = fixes_failed
            data["analysis_metadata"]["fixes_generated_at"] = datetime.now().isoformat()
            
            # Update summary
            if "analysis_summary" not in data:
                data["analysis_summary"] = {}
            
            data["analysis_summary"]["fixes_generated"] = fixes_generated
            data["analysis_summary"]["fixes_failed"] = fixes_failed
            
            # Save the updated file
            if output_file is None:
                base_name = analysis_file.rsplit('.', 1)[0]
                output_file = f"{base_name}_with_fixes.json"
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n📁 Enhanced analysis with fixes saved to: {output_file}")
            
            return {
                "success": True,
                "output_file": output_file,
                "fixes_generated": fixes_generated,
                "fixes_failed": fixes_failed,
                "total_processed": len(test_analyses)
            }
            
        except FileNotFoundError:
            return {"success": False, "error": f"Analysis file not found: {analysis_file}"}
        except json.JSONDecodeError:
            return {"success": False, "error": f"Invalid JSON in file: {analysis_file}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(
        description="Generate code fix suggestions for test failure analyses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate fixes for all analyses
  python fix_suggester.py analysis_results.json
  
  # Save to specific output file
  python fix_suggester.py analysis_results.json --output enhanced_results.json
  
  # Limit to first 3 fixes
  python fix_suggester.py analysis_results.json --max-fixes 3
  
  # Use longer timeout for complex fixes
  python fix_suggester.py analysis_results.json --timeout 180
        """
    )
    
    parser.add_argument("analysis_file", help="JSON file with test failure analyses")
    parser.add_argument("--output", "-o", help="Output file (default: input_file_with_fixes.json)")
    parser.add_argument("--max-fixes", type=int, help="Maximum number of fixes to generate")
    parser.add_argument("--timeout", type=int, default=120, help="Claude CLI timeout in seconds")
    
    args = parser.parse_args()
    
    try:
        print(f"🚀 Processing analysis file: {args.analysis_file}")
        print("=" * 60)
        
        suggester = FixSuggester(claude_timeout=args.timeout)
        result = suggester.process_analysis_file(
            args.analysis_file,
            args.output,
            args.max_fixes
        )
        
        if result["success"]:
            print(f"\n✅ Fix Generation Complete!")
            print(f"📊 Summary:")
            print(f"  Fixes generated: {result['fixes_generated']}")
            print(f"  Fixes failed: {result['fixes_failed']}")
            print(f"  Total processed: {result['total_processed']}")
            print(f"  Output file: {result['output_file']}")
        else:
            print(f"❌ Processing failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Fix generation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())