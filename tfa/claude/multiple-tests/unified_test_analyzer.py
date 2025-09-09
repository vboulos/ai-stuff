#!/usr/bin/env python3
"""
Unified Test Failure Analyzer - Analyzes failures and suggests fixes in one process
"""

import json
import sys
import argparse
import subprocess
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class UnifiedTestAnalyzer:
    """
    Unified analyzer that performs both failure analysis and fix suggestion in one process.
    """
    
    def __init__(self, claude_timeout: int = 120, max_workers: int = 3):
        """
        Initialize the analyzer.
        
        Args:
            claude_timeout: Timeout for Claude CLI calls in seconds
            max_workers: Maximum number of parallel Claude CLI calls
        """
        self.claude_timeout = claude_timeout
        self.max_workers = max_workers
    
    def analyze_and_suggest_fix(self, test_case: Dict[str, Any], framework: str = None) -> Dict[str, Any]:
        """
        Perform both failure analysis and fix suggestion for a single test case.
        
        Args:
            test_case: Test case dictionary with failure information
            framework: Optional framework override
            
        Returns:
            Complete analysis and fix suggestion dictionary
        """
        test_name = test_case.get('name') or test_case.get('test_name') or 'unknown_test'
        failure_message = test_case.get('failure_message') or test_case.get('error') or test_case.get('message', '')
        test_framework = test_case.get('framework') or framework or 'unknown'
        
        result = {
            "test_name": test_name,
            "framework": test_framework,
            "original_test": test_case,
            "analysis": {"success": False},
            "fix_suggestion": {"success": False},
            "processed_at": datetime.now().isoformat()
        }
        
        try:
            # Create comprehensive prompt that does both analysis and fix suggestion
            prompt = self._create_unified_prompt(test_name, failure_message, test_framework)
            
            # Single Claude CLI call for both analysis and fix
            claude_result = subprocess.run(
                ["claude", "--"],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=self.claude_timeout
            )
            
            if claude_result.returncode != 0:
                error_msg = f"Claude CLI error: {claude_result.stderr}"
                result["analysis"]["error"] = error_msg
                result["fix_suggestion"]["error"] = error_msg
                return result
            
            response = claude_result.stdout.strip()
            
            # Parse both analysis and fix from single response
            parsed_data = self._parse_unified_response(response)
            
            result["analysis"] = parsed_data["analysis"]
            result["fix_suggestion"] = parsed_data["fix_suggestion"]
            
            return result
            
        except subprocess.TimeoutExpired:
            error_msg = f"Claude CLI timeout after {self.claude_timeout} seconds"
            result["analysis"]["error"] = error_msg
            result["fix_suggestion"]["error"] = error_msg
            return result
        except Exception as e:
            error_msg = str(e)
            result["analysis"]["error"] = error_msg
            result["fix_suggestion"]["error"] = error_msg
            return result
    
    def _create_unified_prompt(self, test_name: str, failure_message: str, framework: str) -> str:
        """Create a unified prompt for both analysis and fix suggestion."""
        
        return f"""Analyze this test failure and provide code fix suggestions:

**TEST DETAILS:**
- Test Name: {test_name}
- Framework: {framework}
- Error: {failure_message}

Provide a comprehensive response with both analysis and fix suggestions in this format:

**ANALYSIS_ROOT_CAUSE:**
[Why did the test fail? Be specific about the underlying issue]

**ANALYSIS_SUGGESTED_FIX:**
[High-level approach to fix the issue]

**ANALYSIS_CONFIDENCE:**
[0.1 to 1.0]

**FIX_TYPE:**
[quick_fix|refactor|configuration|dependency|infrastructure|test_update]

**FIX_PRIORITY:**
[critical|high|medium|low]

**FIX_EFFORT:**
[minutes|hours|days]

**FIX_CODE_CHANGES:**
```language
// Show specific code changes needed
// Include before/after examples if helpful
```

**FIX_CONFIGURATION:**
```
// Any configuration file changes
```

**FIX_DEPENDENCIES:**
```
// New dependencies or version updates
```

**FIX_VALIDATION_STEPS:**
1. [Step to verify the fix]
2. [How to test the fix] 
3. [Expected outcome]

**FIX_PREVENTION:**
[How to prevent this issue in the future]

**FIX_IMPACT:**
[What other areas might be affected by this fix]"""

    def _parse_unified_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude response into analysis and fix suggestion data."""
        
        # Extract sections using regex
        sections = {}
        pattern = r'\*\*([^*]+):\*\*\s*(.*?)(?=\*\*[^*]+:\*\*|$)'
        
        for section_name, content in re.findall(pattern, response, re.DOTALL | re.IGNORECASE):
            section_key = section_name.strip().upper()
            sections[section_key] = content.strip()
        
        # Parse analysis data
        analysis = {
            "success": True,
            "root_cause": sections.get("ANALYSIS_ROOT_CAUSE", ""),
            "suggested_fix": sections.get("ANALYSIS_SUGGESTED_FIX", ""),
            "confidence_score": self._extract_confidence(sections.get("ANALYSIS_CONFIDENCE", "0.5"))
        }
        
        # Parse fix suggestion data
        fix_suggestion = {
            "success": True,
            "fix_type": sections.get("FIX_TYPE", "unknown").lower(),
            "priority": sections.get("FIX_PRIORITY", "medium").lower(),
            "estimated_effort": sections.get("FIX_EFFORT", "unknown").lower(),
            "code_changes": self._extract_code_block(sections.get("FIX_CODE_CHANGES", "")),
            "configuration_changes": self._extract_code_block(sections.get("FIX_CONFIGURATION", "")),
            "dependencies": self._extract_code_block(sections.get("FIX_DEPENDENCIES", "")),
            "validation_steps": self._parse_validation_steps(sections.get("FIX_VALIDATION_STEPS", "")),
            "prevention": sections.get("FIX_PREVENTION", ""),
            "impact_assessment": sections.get("FIX_IMPACT", ""),
            "raw_response": response
        }
        
        # Add error handling for empty responses
        if not analysis["root_cause"] and not fix_suggestion["code_changes"]:
            analysis["success"] = False
            analysis["error"] = "Failed to parse analysis from response"
            fix_suggestion["success"] = False
            fix_suggestion["error"] = "Failed to parse fix suggestion from response"
        
        return {
            "analysis": analysis,
            "fix_suggestion": fix_suggestion
        }
    
    def _extract_confidence(self, confidence_text: str) -> float:
        """Extract confidence score from text."""
        try:
            confidence = float(re.findall(r'[\d.]+', confidence_text)[0])
            return max(0.1, min(1.0, confidence))
        except:
            return 0.5
    
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
    
    def process_test_failures(self, input_file: str, output_file: str = None, 
                            framework: str = None, max_failures: int = None,
                            parallel: bool = True) -> Dict[str, Any]:
        """
        Process test failures from JSON file with unified analysis and fix suggestions.
        
        Args:
            input_file: Path to JSON file with test failures
            output_file: Output file path (defaults to unified_analysis.json)
            framework: Framework to apply to all tests
            max_failures: Maximum number of failures to process
            parallel: Whether to process in parallel
            
        Returns:
            Processing results dictionary
        """
        try:
            # Read input file
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Extract test cases
            test_cases = self._extract_test_cases(data)
            
            if not test_cases:
                return {"success": False, "error": "No test cases found in JSON file"}
            
            print(f"📖 Found {len(test_cases)} test cases")
            
            # Filter failed tests
            failed_tests = [tc for tc in test_cases if tc.get('status') == 'failed' or tc.get('failure_message')]
            
            if not failed_tests:
                return {"success": True, "message": "No failed tests found", "results": []}
            
            print(f"🔍 Found {len(failed_tests)} failed tests")
            
            # Limit processing if specified
            if max_failures and len(failed_tests) > max_failures:
                print(f"⚠️  Limiting analysis to first {max_failures} failures")
                failed_tests = failed_tests[:max_failures]
            
            # Process tests (parallel or sequential)
            if parallel and len(failed_tests) > 1:
                results = self._process_parallel(failed_tests, framework)
            else:
                results = self._process_sequential(failed_tests, framework)
            
            # Create comprehensive output
            successful_analyses = sum(1 for r in results if r["analysis"]["success"])
            successful_fixes = sum(1 for r in results if r["fix_suggestion"]["success"])
            
            output_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "input_file": input_file,
                    "total_tests": len(test_cases),
                    "failed_tests": len(failed_tests),
                    "processed_tests": len(results),
                    "successful_analyses": successful_analyses,
                    "successful_fixes": successful_fixes,
                    "processing_mode": "parallel" if parallel else "sequential"
                },
                "summary": {
                    "analysis_success_rate": round(successful_analyses / len(results), 2) if results else 0,
                    "fix_success_rate": round(successful_fixes / len(results), 2) if results else 0,
                    "average_confidence": round(sum(r["analysis"].get("confidence_score", 0) 
                                                  for r in results if r["analysis"]["success"]) / max(successful_analyses, 1), 2)
                },
                "test_results": results
            }
            
            # Save output
            output_filename = output_file or "unified_analysis.json"
            with open(output_filename, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n📁 Unified analysis saved to: {output_filename}")
            
            return {
                "success": True,
                "output_file": output_filename,
                "total_processed": len(results),
                "successful_analyses": successful_analyses,
                "successful_fixes": successful_fixes
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_test_cases(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract test cases from various JSON formats."""
        
        # Handle direct array
        if isinstance(data, list):
            return data
        
        # Handle object with test arrays
        for key in ['test_results', 'failed_tests', 'tests', 'failures', 'test_cases']:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # Handle single test case
        if 'name' in data or 'test_name' in data:
            return [data]
        
        return []
    
    def _process_sequential(self, failed_tests: List[Dict[str, Any]], framework: str) -> List[Dict[str, Any]]:
        """Process tests sequentially."""
        results = []
        
        for i, test_case in enumerate(failed_tests, 1):
            test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i}"
            print(f"\n🔬 Processing {i}/{len(failed_tests)}: {test_name}")
            
            result = self.analyze_and_suggest_fix(test_case, framework)
            results.append(result)
            
            # Show progress
            if result["analysis"]["success"] and result["fix_suggestion"]["success"]:
                print(f"✅ Complete analysis and fix generated")
            elif result["analysis"]["success"]:
                print(f"⚠️  Analysis completed, fix generation failed")
            else:
                print(f"❌ Analysis failed")
        
        return results
    
    def _process_parallel(self, failed_tests: List[Dict[str, Any]], framework: str) -> List[Dict[str, Any]]:
        """Process tests in parallel."""
        results = []
        
        print(f"\n🚀 Processing {len(failed_tests)} tests in parallel (max {self.max_workers} workers)")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_test = {
                executor.submit(self.analyze_and_suggest_fix, test_case, framework): (i, test_case)
                for i, test_case in enumerate(failed_tests)
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_test):
                i, test_case = future_to_test[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append((i, result))
                    
                    test_name = test_case.get('name') or test_case.get('test_name') or f"test_{i+1}"
                    if result["analysis"]["success"] and result["fix_suggestion"]["success"]:
                        print(f"✅ {completed}/{len(failed_tests)} - {test_name}: Complete")
                    else:
                        print(f"⚠️  {completed}/{len(failed_tests)} - {test_name}: Partial")
                        
                except Exception as e:
                    print(f"❌ {completed}/{len(failed_tests)} - Error: {e}")
                    results.append((i, {"error": str(e)}))
        
        # Sort results by original order
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]

def create_sample_file():
    """Create a sample JSON file for testing."""
    sample_data = [
        {
            "name": "test_user_authentication",
            "status": "failed",
            "failure_message": "AssertionError: Expected status code 200, but got 401\nResponse: {'error': 'Invalid authentication token'}",
            "framework": "pytest"
        },
        {
            "name": "test_database_connection",
            "status": "failed", 
            "failure_message": "psycopg2.OperationalError: could not connect to server: Connection refused\nIs the server running on host \"localhost\" (127.0.0.1) and accepting TCP/IP connections on port 5432?",
            "framework": "pytest"
        },
        {
            "name": "test_cypress_element_not_found",
            "status": "failed",
            "failure_message": "Timed out retrying after 4000ms: Expected to find element: `.submit-button`, but never found it.",
            "framework": "cypress"
        }
    ]
    
    with open('sample_test_failures.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📝 Sample test failures file created: sample_test_failures.json")

def main():
    parser = argparse.ArgumentParser(
        description="Unified Test Failure Analyzer - Analysis and Fix Suggestions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all failures (parallel processing)
  python unified_test_analyzer.py test_failures.json
  
  # Sequential processing with custom output
  python unified_test_analyzer.py input.json --output results.json --no-parallel
  
  # Limit processing and specify framework
  python unified_test_analyzer.py input.json --max-failures 5 --framework pytest
  
  # Create sample file for testing
  python unified_test_analyzer.py --sample
        """
    )
    
    parser.add_argument("input_file", nargs='?', help="JSON file with test failures")
    parser.add_argument("--output", "-o", help="Output file (default: unified_analysis.json)")
    parser.add_argument("--framework", help="Framework to apply to all tests")
    parser.add_argument("--max-failures", type=int, help="Maximum number of failures to process")
    parser.add_argument("--timeout", type=int, default=120, help="Claude CLI timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=3, help="Maximum parallel workers")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing")
    parser.add_argument("--sample", action="store_true", help="Create sample test failures file")
    
    args = parser.parse_args()
    
    try:
        if args.sample:
            create_sample_file()
            return 0
        
        if not args.input_file:
            parser.error("input_file is required (or use --sample)")
        
        print(f"🚀 Unified Test Failure Analysis")
        print(f"📁 Input: {args.input_file}")
        print("=" * 60)
        
        analyzer = UnifiedTestAnalyzer(
            claude_timeout=args.timeout,
            max_workers=args.max_workers
        )
        
        result = analyzer.process_test_failures(
            args.input_file,
            args.output,
            args.framework,
            args.max_failures,
            parallel=not args.no_parallel
        )
        
        if result["success"]:
            print(f"\n✅ Processing Complete!")
            print(f"📊 Summary:")
            print(f"  Total processed: {result['total_processed']}")
            print(f"  Successful analyses: {result['successful_analyses']}")
            print(f"  Successful fixes: {result['successful_fixes']}")
            print(f"  Output file: {result['output_file']}")
        else:
            print(f"❌ Processing failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())