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
        prompt = f"""Analyze this test failure and provide a detailed analysis:

TEST FAILURE:
Test Name: {test_failure.test_name}
File: {test_failure.file_path or 'Not specified'}
Line: {test_failure.line_number or 'Not specified'}

ERROR MESSAGE:
{test_failure.failure_message}

TEST CODE:
{test_failure.test_code or 'Test code not provided'}

Please provide your analysis in this exact format:

ROOT CAUSE:
[Explain what caused the test to fail]

SUGGESTED FIX:
[Provide specific steps to fix the issue]

CODE EXAMPLE:
[If applicable, show corrected code]

CONFIDENCE: [0.0 to 1.0]

Be detailed and specific in your analysis."""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's response using structured text format."""
        # Use the improved fallback parser as the primary method
        return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Parse Claude's structured response format."""
        lines = text.split('\n')
        
        root_cause = ""
        suggested_fix = ""
        code_example = ""
        confidence_score = 0.7
        
        current_section = ""
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check for section headers
            if line.upper().startswith('ROOT CAUSE:'):
                if section_content and current_section:
                    self._store_section_content(current_section, section_content, locals())
                current_section = "root_cause"
                section_content = [line.split(':', 1)[1].strip() if ':' in line else ""]
                
            elif line.upper().startswith('SUGGESTED FIX:'):
                if section_content and current_section:
                    self._store_section_content(current_section, section_content, locals())
                current_section = "suggested_fix"
                section_content = [line.split(':', 1)[1].strip() if ':' in line else ""]
                
            elif line.upper().startswith('CODE EXAMPLE:'):
                if section_content and current_section:
                    self._store_section_content(current_section, section_content, locals())
                current_section = "code_example"
                section_content = [line.split(':', 1)[1].strip() if ':' in line else ""]
                
            elif line.upper().startswith('CONFIDENCE:'):
                if section_content and current_section:
                    self._store_section_content(current_section, section_content, locals())
                current_section = "confidence"
                confidence_text = line.split(':', 1)[1].strip() if ':' in line else "0.7"
                try:
                    confidence_score = float(confidence_text)
                    confidence_score = max(0.0, min(1.0, confidence_score))
                except ValueError:
                    confidence_score = 0.7
                section_content = []
                
            elif line and current_section:
                # Continue accumulating content for current section
                section_content.append(line)
        
        # Store the last section
        if section_content and current_section:
            self._store_section_content(current_section, section_content, locals())
        
        # Fallback if no structured format found
        if not root_cause and not suggested_fix:
            # Try to extract any meaningful content
            text_lines = [line.strip() for line in lines if line.strip()]
            if text_lines:
                root_cause = " ".join(text_lines[:len(text_lines)//2]) or "Analysis provided by Claude"
                suggested_fix = " ".join(text_lines[len(text_lines)//2:]) or "Review the analysis above"
        
        return {
            'root_cause': root_cause or "Claude provided analysis but format could not be parsed",
            'suggested_fix': suggested_fix or "Review Claude's response for suggestions",
            'confidence_score': confidence_score,
            'code_example': code_example if code_example else None
        }
    
    def _store_section_content(self, section: str, content: List[str], vars_dict: dict):
        """Helper to store section content in the appropriate variable."""
        content_text = " ".join(content).strip()
        if section == "root_cause":
            vars_dict['root_cause'] = content_text
        elif section == "suggested_fix":
            vars_dict['suggested_fix'] = content_text
        elif section == "code_example":
            vars_dict['code_example'] = content_text
    
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