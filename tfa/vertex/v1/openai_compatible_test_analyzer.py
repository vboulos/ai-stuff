#!/usr/bin/env python3
"""
Test Failure Analyzer using OpenAI-compatible APIs
Works with local/open-source models through vLLM, Text Generation Inference, or OpenAI-compatible APIs.
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Install with: pip install requests")
    sys.exit(1)


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


class OpenAICompatibleTestAnalyzer:
    """Main class for analyzing test failures using OpenAI-compatible APIs."""
    
    def __init__(self, base_url: str = "http://localhost:8000/v1", 
                 model_name: str = "llama-3.2-3b", 
                 api_key: str = "dummy"):
        """
        Initialize the analyzer with OpenAI-compatible API configuration.
        
        Args:
            base_url: Base URL for the API (e.g., vLLM, TGI, LM Studio)
            model_name: Model name to use
            api_key: API key (can be dummy for local servers)
        """
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.api_key = api_key
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
        Initialize and test the API connection.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Test connection by getting models list
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['id'] for model in models_data.get('data', [])]
                
                self.logger.info(f"API connection successful")
                self.logger.info(f"Base URL: {self.base_url}")
                self.logger.info(f"Model: {self.model_name}")
                self.logger.info(f"Available models: {', '.join(available_models)}")
                
                if self.model_name not in available_models and available_models:
                    self.logger.warning(f"Model {self.model_name} not in available models list")
                    self.logger.info(f"You may want to use one of: {', '.join(available_models)}")
                
                return True
            else:
                self.logger.error(f"API connection failed: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.error("Cannot connect to API server")
            self.logger.info("Make sure your model server is running")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize API: {e}")
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
            
            # Create chat completion request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert software engineer and test analyst. Analyze test failures and provide detailed insights in JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse the response
            analysis = self._parse_response(content)
            
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
        prompt = f"""Analyze the following test failure and provide detailed insights.

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

Respond with valid JSON only.
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
                # Try to parse the entire response
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
        """Analyze multiple test failures."""
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
                raise ValueError("Invalid JSON format")
            
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
            
        except Exception as e:
            self.logger.error(f"Error reading test failures from {file_path}: {e}")
            return []
    
    def save_analysis_results(self, results: List[AnalysisResult], output_path: str) -> bool:
        """Save analysis results to a JSON file."""
        try:
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
    """Command-line interface for the OpenAI-compatible test analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze test failures using OpenAI-compatible APIs (vLLM, TGI, LM Studio, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # vLLM server (default)
  python3 openai_compatible_test_analyzer.py failures.json results.json
  
  # Text Generation Inference
  python3 openai_compatible_test_analyzer.py --url http://localhost:8080/v1 failures.json results.json
  
  # LM Studio
  python3 openai_compatible_test_analyzer.py --url http://localhost:1234/v1 failures.json results.json
  
  # Custom model name
  python3 openai_compatible_test_analyzer.py --model codellama-7b failures.json results.json

Setup Examples:
  
  # vLLM (recommended for GPU)
  pip install vllm
  python -m vllm.entrypoints.openai.api_server --model microsoft/DialoGPT-medium --port 8000
  
  # Text Generation Inference (HuggingFace)
  docker run --gpus all --shm-size 1g -p 8080:80 -v $volume:/data ghcr.io/huggingface/text-generation-inference:1.1.0 --model-id microsoft/DialoGPT-medium
  
  # LM Studio (GUI tool)
  Download from https://lmstudio.ai/ and start local server
        """
    )
    
    parser.add_argument("--url", default="http://localhost:8000/v1", help="OpenAI-compatible API base URL")
    parser.add_argument("--model", default="llama-3.2-3b", help="Model name to use")
    parser.add_argument("--api-key", default="dummy", help="API key (dummy for local servers)")
    parser.add_argument("--single", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), help="Analyze single test failure")
    parser.add_argument("input_file", nargs='?', help="JSON file containing test failures")
    parser.add_argument("output_file", nargs='?', help="Output file for analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = OpenAICompatibleTestAnalyzer(
        base_url=args.url,
        model_name=args.model,
        api_key=args.api_key
    )
    
    if not analyzer.initialize():
        print("❌ Failed to initialize API connection")
        print("\n🛠️  Setup Options:")
        print("1. vLLM: python -m vllm.entrypoints.openai.api_server --model <model-name>")
        print("2. LM Studio: Download from https://lmstudio.ai/")
        print("3. Text Generation Inference: Use HuggingFace TGI Docker")
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