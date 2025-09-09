#!/usr/bin/env python3
"""
Test Failure Analyzer using Google Vertex AI
Analyzes test failures and provides fix suggestions using Vertex AI's Gemini models.
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Install with: pip install google-cloud-aiplatform")
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


class VertexAITestAnalyzer:
    """Main class for analyzing test failures using Vertex AI."""
    
    def __init__(self, project_id: str, location: str = "us-central1", 
                 model_name: str = "gemini-1.5-pro"):
        """
        Initialize the analyzer with Vertex AI configuration.
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location/region
            model_name: Gemini model to use
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.model = None
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
        Initialize Vertex AI and authenticate.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            
            # Initialize the model
            self.model = GenerativeModel(self.model_name)
            
            # Test authentication
            credentials, _ = default()
            
            self.logger.info(f"Vertex AI initialized successfully")
            self.logger.info(f"Project: {self.project_id}")
            self.logger.info(f"Location: {self.location}")
            self.logger.info(f"Model: {self.model_name}")
            
            return True
            
        except DefaultCredentialsError:
            self.logger.error("Authentication failed. Please run 'gcloud auth application-default login'")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI: {e}")
            return False
    
    def analyze_failure(self, test_failure: TestFailure) -> AnalysisResult:
        """
        Analyze a single test failure and provide suggestions.
        
        Args:
            test_failure: TestFailure object containing failure details
            
        Returns:
            AnalysisResult object with analysis and suggestions
        """
        if not self.model:
            return AnalysisResult(
                test_name=test_failure.test_name,
                failure_message=test_failure.failure_message,
                root_cause="Model not initialized",
                suggested_fix="Please initialize the analyzer first",
                confidence_score=0.0,
                analysis_successful=False,
                error_message="Model not initialized"
            )
        
        try:
            prompt = self._create_analysis_prompt(test_failure)
            
            self.logger.info(f"Analyzing test failure: {test_failure.test_name}")
            
            # Generate response using Vertex AI
            response = self.model.generate_content(prompt)
            
            # Parse the response
            analysis = self._parse_response(response.text)
            
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
        prompt = f"""
You are an expert software engineer and test analyst. Analyze the following test failure and provide detailed insights.

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
            
            # Parse JSON
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
            return {
                'root_cause': 'Failed to parse AI response',
                'suggested_fix': 'Manual analysis required',
                'confidence_score': 0.0
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
        """
        Read test failures from a JSON file.
        
        Expected JSON format:
        {
            "failed_tests": [
                {
                    "test_name": "test_example",
                    "failure_message": "AssertionError: ...",
                    "file_path": "test_file.py",
                    "line_number": 42
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
    """Command-line interface for the Vertex AI test analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Google Vertex AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python vertex_ai_test_analyzer.py --project my-project failures.json results.json
  
  # With custom model and location
  python vertex_ai_test_analyzer.py --project my-project --location europe-west1 --model gemini-1.5-flash failures.json results.json
  
  # Analyze single test failure
  python vertex_ai_test_analyzer.py --project my-project --single "test_login" "AssertionError: Login failed"

Setup Requirements:
  1. Install dependencies: pip install google-cloud-aiplatform
  2. Set up authentication: gcloud auth application-default login
  3. Ensure Vertex AI API is enabled in your Google Cloud project
        """
    )
    
    parser.add_argument("--project", required=True, help="Google Cloud project ID")
    parser.add_argument("--location", default="us-central1", help="Vertex AI location (default: us-central1)")
    parser.add_argument("--model", default="gemini-1.5-pro", help="Model name (default: gemini-1.5-pro)")
    parser.add_argument("--single", nargs=2, metavar=('TEST_NAME', 'ERROR_MSG'), help="Analyze single test failure")
    parser.add_argument("input_file", nargs='?', help="JSON file containing test failures")
    parser.add_argument("output_file", nargs='?', help="Output file for analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = VertexAITestAnalyzer(
        project_id=args.project,
        location=args.location,
        model_name=args.model
    )
    
    if not analyzer.initialize():
        print("❌ Failed to initialize Vertex AI. Please check your setup.")
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