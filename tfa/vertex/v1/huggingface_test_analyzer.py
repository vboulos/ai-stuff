#!/usr/bin/env python3
"""
Test Failure Analyzer using Hugging Face Transformers
Analyzes test failures using open-source models from Hugging Face.
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Install with: pip install transformers torch")
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


class HuggingFaceTestAnalyzer:
    """Main class for analyzing test failures using Hugging Face models."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", 
                 device: str = "auto"):
        """
        Initialize the analyzer with Hugging Face configuration.
        
        Args:
            model_name: HuggingFace model to use
            device: Device to run on ('cpu', 'cuda', or 'auto')
        """
        self.model_name = model_name
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.pipeline = None
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
        Initialize Hugging Face model and tokenizer.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Loading model: {self.model_name}")
            self.logger.info(f"Device: {self.device}")
            
            # Initialize tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Add pad token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Create text generation pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            self.logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize model: {e}")
            return False
    
    def analyze_failure(self, test_failure: TestFailure) -> AnalysisResult:
        """
        Analyze a single test failure and provide suggestions.
        
        Args:
            test_failure: TestFailure object containing failure details
            
        Returns:
            AnalysisResult object with analysis and suggestions
        """
        if not self.pipeline:
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
            
            # Generate response using the model
            response = self.pipeline(
                prompt,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            analysis_text = generated_text[len(prompt):].strip()
            
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
        prompt = f"""Analyze this test failure and provide insights:

Test: {test_failure.test_name}
Error: {test_failure.failure_message}

Analysis:
Root Cause: """
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the response from the model."""
        # Simple text-based parsing for models that don't return JSON
        lines = response_text.split('\n')
        
        root_cause = ""
        suggested_fix = ""
        confidence_score = 0.6
        
        current_section = ""
        
        for line in lines[:10]:  # Limit to first 10 lines
            line = line.strip()
            if not line:
                continue
                
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in ['root cause', 'cause:', 'reason:']):
                current_section = "root_cause"
                root_cause = line.split(':', 1)[-1].strip()
            elif any(keyword in line_lower for keyword in ['fix:', 'solution:', 'suggested fix']):
                current_section = "suggested_fix"
                suggested_fix = line.split(':', 1)[-1].strip()
            elif current_section == "root_cause" and not root_cause:
                root_cause = line
            elif current_section == "suggested_fix" and not suggested_fix:
                suggested_fix = line
        
        # Fallback if no structured response
        if not root_cause:
            root_cause = response_text[:200] + "..." if len(response_text) > 200 else response_text
        
        if not suggested_fix:
            suggested_fix = "Review the error message and check the test logic"
        
        return {
            'root_cause': root_cause or "Unable to determine root cause",
            'suggested_fix': suggested_fix or "Manual analysis required",
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
    """Command-line interface for the Hugging Face test analyzer."""
    parser = argparse.ArgumentParser(
        description="Analyze test failures using Hugging Face models",
        epilog="""
Examples:
  # Use CodeT5 for code analysis
  python3 huggingface_test_analyzer.py --model Salesforce/codet5-base failures.json results.json
  
  # Use CodeBERT
  python3 huggingface_test_analyzer.py --model microsoft/codebert-base failures.json results.json
  
  # Use on CPU only
  python3 huggingface_test_analyzer.py --device cpu failures.json results.json

Recommended Models:
  - Salesforce/codet5-base (code understanding)
  - microsoft/codebert-base (code analysis)
  - codellama/CodeLlama-7b-hf (if you have GPU)
        """
    )
    
    parser.add_argument("--model", default="microsoft/DialoGPT-medium", help="HuggingFace model name")
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Device to use")
    parser.add_argument("input_file", help="JSON file containing test failures")
    parser.add_argument("output_file", help="Output file for analysis results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = HuggingFaceTestAnalyzer(
        model_name=args.model,
        device=args.device
    )
    
    if not analyzer.initialize():
        print("❌ Failed to initialize model")
        sys.exit(1)
    
    try:
        if not os.path.exists(args.input_file):
            print(f"❌ Input file not found: {args.input_file}")
            sys.exit(1)
        
        # Read and analyze
        failures = analyzer.read_test_failures_from_json(args.input_file)
        if not failures:
            print("❌ No test failures found")
            sys.exit(1)
        
        results = analyzer.analyze_multiple_failures(failures)
        
        if analyzer.save_analysis_results(results, args.output_file):
            successful = sum(1 for r in results if r.analysis_successful)
            print(f"✅ Analysis complete: {successful}/{len(results)} successful")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()