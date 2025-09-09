#!/usr/bin/env python3
"""
Test Failure Analyzer using Claude CLI Sonnet 4
Analyzes test failures and provides root cause analysis with code fix suggestions.
"""

import json
import os
import sys
import argparse
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TestFailure:
    """Represents a single test failure."""
    test_name: str
    failure_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    test_code: Optional[str] = None


@dataclass
class AnalysisResult:
    """Represents the analysis result for a test failure."""
    test_name: str
    failure_message: str
    root_cause: str
    suggested_fix: str
    code_example: Optional[str]
    confidence_score: float
    analysis_successful: bool = True
    error_message: Optional[str] = None


class ClaudeCLITestAnalyzer:
    """Main class for analyzing test failures using Claude CLI Sonnet 4."""
    
    def __init__(self, claude_cli_path: str = "claude", model: str = "sonnet-4"):
        """
        Initialize the analyzer with Claude CLI configuration.
        
        Args:
            claude_cli_path: Path to Claude CLI executable
            model: Claude model to use (sonnet-4, opus-4, etc.)
        """
        self.claude_cli_path = claude_cli_path
        self.model = model
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> bool:
        """
        Initialize and test Claude CLI connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Test Claude CLI availability
            result = subprocess.run(
                [self.claude_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Claude CLI found: {result.stdout.strip()}")
                
                # Test model access with a simple query
                test_result = self._run_claude_query("Hello, are you working?", simple_test=True)
                
                if test_result and "error" not in test_result.lower():
                    self.logger.info(f"Claude CLI Sonnet 4 initialized successfully")
                    self.logger.info(f"Model: {self.model}")
                    return True
                else:
                    self.logger.error("Claude CLI test query failed")
                    return False
            else:
                self.logger.error(f"Claude CLI not found or not working: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.error("Claude CLI not found. Please install it first.")
            self.logger.info("Installation: npm install -g @anthropic/claude-cli")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Claude CLI timeout. Check your connection.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude CLI: {e}")
            return False
    
    def _run_claude_query(self, prompt: str, simple_test: bool = False) -> Optional[str]:
        """
        Run a query using Claude CLI.
        
        Args:
            prompt: The prompt to send to Claude
            simple_test: If True, use a simple test query
            
        Returns:
            Claude's response or None if failed
        """
        try:
            # Create a temporary file for the prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(prompt)
                temp_file_path = temp_file.name
            
            try:
                # Run Claude CLI with the prompt file
                cmd = [self.claude_cli_path]
                
                # Add model specification if not default (skip if having issues)
                # if self.model and self.model != "default":
                #     cmd.extend(["--model", self.model])
                
                # Add the prompt file
                cmd.append(temp_file_path)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120 if not simple_test else 30
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    self.logger.error(f"Claude CLI error: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except subprocess.TimeoutExpired:
            self.logger.error("Claude CLI query timeout")
            return None
        except Exception as e:
            self.logger.error(f"Error running Claude query: {e}")
            return None
    
    def analyze_failure(self, test_failure: TestFailure) -> AnalysisResult:
        """
        Analyze a single test failure and provide suggestions.
        
        Args:
            test_failure: TestFailure object containing failure details
            
        Returns:
            AnalysisResult object with analysis and suggestions
        """
        try:
            prompt = self._create_analysis_prompt(test_failure)
            
            self.logger.info(f"Analyzing test failure: {test_failure.test_name}")
            
            # Get analysis from Claude
            response = self._run_claude_query(prompt)
            
            if not response:
                raise Exception("No response from Claude CLI")
            
            # Parse the response
            analysis = self._parse_response(response)
            
            return AnalysisResult(
                test_name=test_failure.test_name,
                failure_message=test_failure.failure_message,
                root_cause=analysis.get('root_cause', 'Unable to determine root cause'),
                suggested_fix=analysis.get('suggested_fix', 'No specific fix suggested'),
                code_example=analysis.get('code_example'),
                confidence_score=analysis.get('confidence_score', 0.7),
                analysis_successful=True
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing test failure {test_failure.test_name}: {e}")
            return AnalysisResult(
                test_name=test_failure.test_name,
                failure_message=test_failure.failure_message,
                root_cause=f"Analysis failed: {str(e)}",
                suggested_fix="Manual investigation required",
                code_example=None,
                confidence_score=0.0,
                analysis_successful=False,
                error_message=str(e)
            )
    
    def _create_analysis_prompt(self, test_failure: TestFailure) -> str:
        """Create a detailed prompt for test failure analysis."""
        prompt = f"""You are an expert software engineer and test analyst. Analyze the following test failure and provide detailed insights with specific code fixes.

TEST FAILURE INFORMATION:
- Test Name: {test_failure.test_name}
- File Path: {test_failure.file_path or 'Not specified'}
- Line Number: {test_failure.line_number or 'Not specified'}

FAILURE MESSAGE:
{test_failure.failure_message}

TEST CODE (if available):
{test_failure.test_code or 'Test code not provided'}

Please analyze this test failure and provide a comprehensive response in the following JSON format:

{{
    "root_cause": "Detailed explanation of what caused the test to fail, including technical details",
    "suggested_fix": "Specific, actionable steps to fix the issue with clear instructions",
    "code_example": "Complete code example showing the fix (if applicable)",
    "confidence_score": 0.85,
    "debugging_steps": ["Step 1", "Step 2", "Step 3"],
    "prevention_tips": "How to prevent similar issues in the future"
}}

ANALYSIS GUIDELINES:
1. Focus on the most likely root cause based on the error message and patterns
2. Provide specific, actionable fix suggestions with concrete steps
3. Include a complete code example if the fix involves code changes
4. Set confidence_score between 0.0 and 1.0 based on how certain you are
5. Consider common testing patterns, anti-patterns, and best practices
6. If the error message is unclear, suggest specific debugging steps
7. Look for issues like:
   - Assertion failures and incorrect expected values
   - Setup/teardown problems
   - Race conditions and timing issues
   - Mock/stub configuration problems
   - Environment or dependency issues
   - Logic errors in test code

Respond with valid JSON only, no additional text before or after.
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from Claude."""
        try:
            # Clean the response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
                
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
                
            cleaned_text = cleaned_text.strip()
            
            # Find JSON content between first { and last }
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_content = cleaned_text[start_idx:end_idx+1]
                parsed = json.loads(json_content)
            else:
                # Try to parse the entire response
                parsed = json.loads(cleaned_text)
            
            # Validate and set defaults for required fields
            required_fields = {
                'root_cause': 'Unable to determine root cause',
                'suggested_fix': 'No specific fix suggested',
                'confidence_score': 0.5,
                'code_example': None
            }
            
            for field, default_value in required_fields.items():
                if field not in parsed or not parsed[field]:
                    parsed[field] = default_value
            
            # Ensure confidence score is valid
            if not isinstance(parsed.get('confidence_score'), (int, float)):
                parsed['confidence_score'] = 0.5
            else:
                parsed['confidence_score'] = max(0.0, min(1.0, float(parsed['confidence_score'])))
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            self.logger.debug(f"Raw response: {response_text}")
            
            # Fallback: extract information using simple text parsing
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails."""
        lines = text.split('\n')
        
        root_cause = "Unable to parse detailed analysis from Claude response"
        suggested_fix = "Manual analysis required - Claude response could not be parsed"
        confidence_score = 0.3
        code_example = None
        
        # Try to extract key information from text
        current_section = ""
        accumulated_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            # Detect sections
            if any(keyword in line_lower for keyword in ['root cause', 'cause:', 'problem:']):
                if accumulated_text and current_section == "root_cause":
                    root_cause = ' '.join(accumulated_text)
                current_section = "root_cause"
                accumulated_text = [line.split(':', 1)[-1].strip()]
            elif any(keyword in line_lower for keyword in ['fix:', 'solution:', 'suggested fix', 'recommendation:']):
                if accumulated_text and current_section == "root_cause":
                    root_cause = ' '.join(accumulated_text)
                current_section = "suggested_fix"
                accumulated_text = [line.split(':', 1)[-1].strip()]
            elif any(keyword in line_lower for keyword in ['code:', 'example:', '```']):
                if accumulated_text and current_section == "suggested_fix":
                    suggested_fix = ' '.join(accumulated_text)
                current_section = "code_example"
                accumulated_text = []
            else:
                # Continue accumulating text for current section
                if current_section and not line.startswith('#'):
                    accumulated_text.append(line)
        
        # Process final accumulated text
        if accumulated_text:
            if current_section == "root_cause":
                root_cause = ' '.join(accumulated_text)
            elif current_section == "suggested_fix":
                suggested_fix = ' '.join(accumulated_text)
            elif current_section == "code_example":
                code_example = ' '.join(accumulated_text)
        
        return {
            'root_cause': root_cause,
            'suggested_fix': suggested_fix,
            'confidence_score': confidence_score,
            'code_example': code_example
        }
    
    def analyze_multiple_failures(self, test_failures: List[TestFailure]) -> List[AnalysisResult]:
        """
        Analyze multiple test failures.
        
        Args:
            test_failures: List of TestFailure objects
            
        Returns:
            List of AnalysisResult objects
        """
        results = []
        total_failures = len(test_failures)
        
        self.logger.info(f"Starting analysis of {total_failures} test failures")
        
        for i, failure in enumerate(test_failures, 1):
            self.logger.info(f"Analyzing failure {i}/{total_failures}: {failure.test_name}")
            result = self.analyze_failure(failure)
            results.append(result)
        
        # Log summary
        successful_analyses = sum(1 for r in results if r.analysis_successful)
        avg_confidence = sum(r.confidence_score for r in results if r.analysis_successful) / max(1, successful_analyses)
        
        self.logger.info(f"Analysis complete: {successful_analyses}/{total_failures} successful")
        self.logger.info(f"Average confidence score: {avg_confidence:.2f}")
        
        return results
    
    def read_test_failures_from_json(self, file_path: str) -> List[TestFailure]:
        """
        Read test failures from a JSON file.
        
        Expected JSON format:
        {
            "failed_tests": [
                {
                    "test_name": "test_example",
                    "failure_message": "AssertionError: ...",
                    "file_path": "test_file.py",
                    "line_number": 42,
                    "test_code": "def test_example()..."
                }
            ]
        }
        
        Args:
            file_path: Path to JSON file containing test failures
            
        Returns:
            List of TestFailure objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            failures = []
            
            # Handle different JSON formats
            if 'failed_tests' in data:
                test_data = data['failed_tests']
            elif isinstance(data, list):
                test_data = data
            else:
                raise ValueError("Invalid JSON format. Expected 'failed_tests' key or array of test failures")
            
            for test in test_data:
                failure = TestFailure(
                    test_name=test.get('test_name', 'Unknown Test'),
                    failure_message=test.get('failure_message', 'No failure message provided'),
                    file_path=test.get('file_path'),
                    line_number=test.get('line_number'),
                    test_code=test.get('test_code')
                )
                failures.append(failure)
            
            self.logger.info(f"Loaded {len(failures)} test failures from {file_path}")
            return failures
            
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading test failures from {file_path}: {e}")
            return []
    
    def save_analysis_results(self, results: List[AnalysisResult], output_path: str) -> bool:
        """
        Save analysis results to a JSON file.
        
        Args:
            results: List of AnalysisResult objects
            output_path: Path where to save the results
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Convert results to dictionaries
            successful_results = [r for r in results if r.analysis_successful]
            
            results_dict = {
                'analysis_summary': {
                    'total_failures': len(results),
                    'successful_analyses': len(successful_results),
                    'failed_analyses': len(results) - len(successful_results),
                    'success_rate': len(successful_results) / len(results) if results else 0,
                    'average_confidence': sum(r.confidence_score for r in successful_results) / max(1, len(successful_results)),
                    'generated_by': 'Claude CLI Sonnet 4',
                    'timestamp': subprocess.run(['date'], capture_output=True, text=True).stdout.strip()
                },
                'results': [asdict(result) for result in results]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analysis results saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving results to {output_path}: {e}")
            return False


def main():
    """Command-line interface for the Claude CLI test analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Claude CLI Sonnet 4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python3 claude_cli_test_analyzer.py failures.json results.json
  
  # With custom Claude CLI path
  python3 claude_cli_test_analyzer.py --claude-cli /usr/local/bin/claude failures.json results.json
  
  # With specific model
  python3 claude_cli_test_analyzer.py --model opus-4 failures.json results.json
  
  # Analyze single test failure
  python3 claude_cli_test_analyzer.py --single "test_login" "AssertionError: Login failed"

Setup Requirements:
  1. Install Claude CLI: npm install -g @anthropic/claude-cli
  2. Authenticate: claude auth login
  3. Verify access: claude --version

Supported Models:
  - sonnet-4 (default, most balanced)
  - opus-4 (most capable, slower)
  - haiku-4 (fastest, less detailed)
        """
    )
    
    parser.add_argument("--claude-cli", default="claude", help="Path to Claude CLI executable")
    parser.add_argument("--model", default="sonnet-4", help="Claude model to use")
    parser.add_argument("--single", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), help="Analyze single test failure")
    parser.add_argument("input_file", nargs='?', help="JSON file containing test failures")
    parser.add_argument("output_file", nargs='?', help="Output file for analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = ClaudeCLITestAnalyzer(
        claude_cli_path=args.claude_cli,
        model=args.model
    )
    
    if not analyzer.initialize():
        print("❌ Failed to initialize Claude CLI. Please check your setup.")
        print("\n🛠️  Setup Instructions:")
        print("1. Install Claude CLI: npm install -g @anthropic/claude-cli")
        print("2. Authenticate: claude auth login")
        print("3. Test: claude --version")
        sys.exit(1)
    
    try:
        if args.single:
            # Single test analysis
            test_name, error_msg = args.single
            failure = TestFailure(test_name=test_name, failure_message=error_msg)
            result = analyzer.analyze_failure(failure)
            
            print(f"\n🔍 Analysis Results for: {test_name}")
            print("=" * 70)
            print(f"Root Cause:\n{result.root_cause}")
            print(f"\nSuggested Fix:\n{result.suggested_fix}")
            if result.code_example:
                print(f"\nCode Example:\n{result.code_example}")
            print(f"\nConfidence Score: {result.confidence_score:.2f}")
            
        else:
            # Batch analysis
            if not args.input_file or not args.output_file:
                parser.error("input_file and output_file are required for batch analysis")
            
            if not os.path.exists(args.input_file):
                print(f"❌ Input file not found: {args.input_file}")
                sys.exit(1)
            
            # Read test failures
            failures = analyzer.read_test_failures_from_json(args.input_file)
            if not failures:
                print("❌ No test failures found in input file")
                sys.exit(1)
            
            print(f"📊 Found {len(failures)} test failures to analyze")
            
            # Analyze failures
            results = analyzer.analyze_multiple_failures(failures)
            
            # Save results
            if analyzer.save_analysis_results(results, args.output_file):
                successful = sum(1 for r in results if r.analysis_successful)
                avg_confidence = sum(r.confidence_score for r in results if r.analysis_successful) / max(1, successful)
                
                print(f"\n✅ Analysis complete!")
                print(f"   Successful analyses: {successful}/{len(results)}")
                print(f"   Average confidence: {avg_confidence:.2f}")
                print(f"   Results saved to: {args.output_file}")
            else:
                print("❌ Failed to save results")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()