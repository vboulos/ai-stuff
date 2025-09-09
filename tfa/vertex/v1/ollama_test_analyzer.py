#!/usr/bin/env python3
"""
Test Failure Analyzer using Ollama (local open-source models)
Analyzes test failures using locally running LLMs like Llama, CodeLlama, etc.
"""

import json
import os
import sys
import argparse
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TestFailure:
    """Represents a single test failure."""
    test_name: str
    failure_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class AnalysisResult:
    """Represents the analysis result for a test failure."""
    test_name: str
    failure_message: str
    root_cause: str
    suggested_fix: str
    confidence_score: float
    analysis_successful: bool = True
    error_message: Optional[str] = None


class OllamaTestAnalyzer:
    """Main class for analyzing test failures using Ollama."""
    
    def __init__(self, model_name: str = "llama3.2", 
                 ollama_url: str = "http://localhost:11434"):
        """
        Initialize the analyzer with Ollama configuration.
        
        Args:
            model_name: Ollama model to use (e.g., llama3.2, codellama, deepseek-coder)
            ollama_url: Ollama server URL
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
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
        Initialize Ollama connection and verify model availability.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code != 200:
                self.logger.error("Ollama server not responding")
                return False
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [model['name'].split(':')[0] for model in models]
            
            if self.model_name not in model_names:
                self.logger.warning(f"Model {self.model_name} not found locally")
                self.logger.info("Available models: " + ", ".join(model_names))
                self.logger.info(f"Pulling model {self.model_name}...")
                
                # Try to pull the model
                pull_response = requests.post(
                    f"{self.ollama_url}/api/pull",
                    json={"name": self.model_name},
                    timeout=300  # 5 minutes for model download
                )
                
                if pull_response.status_code != 200:
                    self.logger.error(f"Failed to pull model {self.model_name}")
                    return False
            
            self.logger.info(f"Ollama initialized successfully")
            self.logger.info(f"Model: {self.model_name}")
            self.logger.info(f"Server: {self.ollama_url}")
            
            return True
            
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to Ollama server. Is it running?")
            self.logger.info("Start Ollama with: ollama serve")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama: {e}")
            return False
    
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
            
            # Generate response using Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            analysis_text = result.get('response', '')
            
            # Parse the response
            analysis = self._parse_response(analysis_text)
            
            return AnalysisResult(
                test_name=test_failure.test_name,
                failure_message=test_failure.failure_message,
                root_cause=analysis.get('root_cause', 'Unable to determine root cause'),
                suggested_fix=analysis.get('suggested_fix', 'No specific fix suggested'),
                confidence_score=analysis.get('confidence_score', 0.5),
                analysis_successful=True
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing test failure {test_failure.test_name}: {e}")
            return AnalysisResult(
                test_name=test_failure.test_name,
                failure_message=test_failure.failure_message,
                root_cause=f"Analysis failed: {str(e)}",
                suggested_fix="Manual investigation required",
                confidence_score=0.0,
                analysis_successful=False,
                error_message=str(e)
            )
    
    def _create_analysis_prompt(self, test_failure: TestFailure) -> str:
        """Create a detailed prompt for test failure analysis."""
        prompt = f"""You are an expert software engineer and test analyst. Analyze the following test failure and provide detailed insights.

TEST INFORMATION:
- Test Name: {test_failure.test_name}
- File Path: {test_failure.file_path or 'Not specified'}
- Line Number: {test_failure.line_number or 'Not specified'}

FAILURE MESSAGE:
{test_failure.failure_message}

Please provide a comprehensive analysis in the following JSON format:

{{
    "root_cause": "Detailed explanation of what caused the test to fail",
    "suggested_fix": "Specific, actionable steps to fix the issue, including code examples if applicable",
    "confidence_score": 0.85,
    "additional_considerations": "Any other factors to consider or related issues to watch for"
}}

Guidelines for your analysis:
1. Focus on the most likely root cause based on the error message
2. Provide specific, actionable fix suggestions
3. Include code examples in your suggested fix when relevant
4. Set confidence_score between 0.0 and 1.0 based on how certain you are
5. Consider common patterns and anti-patterns in testing
6. If the error message is unclear, suggest debugging steps

Respond with valid JSON only, no additional text.
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from the AI model."""
        try:
            # Clean the response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
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
                # Fallback: try to parse the entire response
                parsed = json.loads(cleaned_text)
            
            # Validate required fields
            required_fields = ['root_cause', 'suggested_fix', 'confidence_score']
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = f"Field '{field}' not provided in analysis"
            
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
        
        root_cause = "Unable to parse detailed analysis"
        suggested_fix = "Manual analysis required"
        confidence_score = 0.3
        
        # Try to extract key information
        for line in lines:
            line_lower = line.lower()
            if 'cause' in line_lower or 'reason' in line_lower:
                root_cause = line.strip()
            elif 'fix' in line_lower or 'solution' in line_lower:
                suggested_fix = line.strip()
        
        return {
            'root_cause': root_cause,
            'suggested_fix': suggested_fix,
            'confidence_score': confidence_score
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
        self.logger.info(f"Analysis complete: {successful_analyses}/{total_failures} successful")
        
        return results
    
    def read_test_failures_from_json(self, file_path: str) -> List[TestFailure]:
        """Read test failures from a JSON file."""
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
                    line_number=test.get('line_number')
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
        """Save analysis results to a JSON file."""
        try:
            # Convert results to dictionaries
            results_dict = {
                'analysis_summary': {
                    'total_failures': len(results),
                    'successful_analyses': sum(1 for r in results if r.analysis_successful),
                    'average_confidence': sum(r.confidence_score for r in results if r.analysis_successful) / max(1, sum(1 for r in results if r.analysis_successful))
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
    """Command-line interface for the Ollama test analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Ollama (local open-source models)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with Llama
  python3 ollama_test_analyzer.py failures.json results.json
  
  # Use CodeLlama for better code analysis
  python3 ollama_test_analyzer.py --model codellama failures.json results.json
  
  # Use DeepSeek Coder (excellent for code)
  python3 ollama_test_analyzer.py --model deepseek-coder failures.json results.json
  
  # Analyze single test failure
  python3 ollama_test_analyzer.py --single "test_login" "AssertionError: Login failed"

Setup Requirements:
  1. Install Ollama: https://ollama.ai/
  2. Start Ollama: ollama serve
  3. Pull a model: ollama pull llama3.2

Popular Models:
  - llama3.2 (general purpose, good reasoning)
  - codellama (specialized for code)
  - deepseek-coder (excellent for programming tasks)
  - llama3.1 (larger, more capable)
        """
    )
    
    parser.add_argument("--model", default="llama3.2", help="Ollama model name (default: llama3.2)")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama server URL")
    parser.add_argument("--single", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), help="Analyze single test failure")
    parser.add_argument("input_file", nargs='?', help="JSON file containing test failures")
    parser.add_argument("output_file", nargs='?', help="Output file for analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = OllamaTestAnalyzer(
        model_name=args.model,
        ollama_url=args.url
    )
    
    if not analyzer.initialize():
        print("❌ Failed to initialize Ollama. Please check your setup.")
        print("\n🛠️  Setup Instructions:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Start server: ollama serve")
        print(f"3. Pull model: ollama pull {args.model}")
        sys.exit(1)
    
    try:
        if args.single:
            # Single test analysis
            test_name, error_msg = args.single
            failure = TestFailure(test_name=test_name, failure_message=error_msg)
            result = analyzer.analyze_failure(failure)
            
            print(f"\n🔍 Analysis Results for: {test_name}")
            print("=" * 60)
            print(f"Root Cause: {result.root_cause}")
            print(f"\nSuggested Fix: {result.suggested_fix}")
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
                print(f"\n✅ Analysis complete!")
                print(f"   Results: {successful}/{len(results)} successful")
                print(f"   Output saved to: {args.output_file}")
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