import json
import os
import re
from typing import List, Dict, Any, Tuple
from anthropic import Anthropic

class TestFailureAnalyzer:
    """
    Analyzes test failures using Claude AI and classifies them by failure type.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the analyzer with Claude AI client.
        
        Args:
            api_key: Anthropic API key. If None, will look for ANTHROPIC_API_KEY env var.
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        self.client = Anthropic(api_key=api_key)
    
    def read_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read test case data from JSON file.
        
        Args:
            file_path: Path to JSON file containing test case data
            
        Returns:
            List of test case dictionaries
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Validate required fields
            required_fields = ['test_case_id', 'test_case_name', 'failure_message']
            for i, test_case in enumerate(data):
                for field in required_fields:
                    if field not in test_case:
                        raise ValueError(f"Missing required field '{field}' in test case {i}")
            
            return data
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def analyze_test_failure(self, test_case: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze a single test failure using Claude AI.
        
        Args:
            test_case: Dictionary with test case information
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
Analyze this test failure and provide a structured response:

Test Case ID: {test_case['test_case_id']}
Test Case Name: {test_case['test_case_name']}
Failure Message: {test_case['failure_message']}

Please respond in this exact format:

FAILURE_TYPE: [Select ONE: automation_bug, product_bug, network_issue, configuration_issue, data_issue, environment_issue, timing_issue, dependency_issue, assertion_error, infrastructure_issue, or unknown]

FIX_SUGGESTION: [Provide specific steps to fix this issue]

FIX_CODE: [If applicable, provide actual code to fix the issue. Use ``` code blocks]

Classification Guide:
- automation_bug: Test code errors, wrong selectors, incorrect assertions
- product_bug: Application functionality broken, business logic errors
- network_issue: API timeouts, connection failures, DNS problems
- configuration_issue: Wrong URLs, missing settings, environment config
- data_issue: Missing test data, incorrect data format, database problems
- environment_issue: Services not running, infrastructure problems
- timing_issue: Race conditions, synchronization problems, timeouts
- dependency_issue: Missing libraries, version conflicts, service dependencies
- assertion_error: Expected vs actual value mismatches
- infrastructure_issue: Hardware/platform related failures
- unknown: Cannot determine cause from available information
"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_response(response.content[0].text)
            
        except Exception as e:
            return {
                'failure_type': 'unknown',
                'fix_suggestion': f'Error analyzing test case: {str(e)}',
                'fix_code': ''
            }
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        Parse Claude's structured response.
        
        Args:
            response: Raw response from Claude AI
            
        Returns:
            Dictionary with parsed failure_type, fix_suggestion, and fix_code
        """
        # Extract failure type
        failure_type_match = re.search(r'FAILURE_TYPE:\s*([^\n]+)', response, re.IGNORECASE)
        failure_type = failure_type_match.group(1).strip().lower() if failure_type_match else 'unknown'
        
        # Validate failure type
        valid_types = [
            'automation_bug', 'product_bug', 'network_issue', 'configuration_issue',
            'data_issue', 'environment_issue', 'timing_issue', 'dependency_issue',
            'assertion_error', 'infrastructure_issue', 'unknown'
        ]
        if failure_type not in valid_types:
            failure_type = 'unknown'
        
        # Extract fix suggestion
        fix_suggestion_match = re.search(
            r'FIX_SUGGESTION:\s*(.*?)(?=FIX_CODE:|$)', 
            response, 
            re.IGNORECASE | re.DOTALL
        )
        fix_suggestion = fix_suggestion_match.group(1).strip() if fix_suggestion_match else 'No fix suggestion provided'
        
        # Extract code blocks
        code_pattern = r'```(?:\w+)?\n([\s\S]*?)```'
        code_matches = re.findall(code_pattern, response)
        fix_code = '\n\n'.join(code_matches) if code_matches else ''
        
        return {
            'failure_type': failure_type,
            'fix_suggestion': fix_suggestion,
            'fix_code': fix_code
        }
    
    def process_test_cases(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all test cases and generate analysis results.
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            List of dictionaries with analysis results
        """
        results = []
        total_cases = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Analyzing test case {i}/{total_cases}: {test_case['test_case_id']}")
            
            # Analyze the test failure
            analysis = self.analyze_test_failure(test_case)
            
            # Create result dictionary
            result = {
                'test_case_id': test_case['test_case_id'],
                'test_case_name': test_case['test_case_name'],
                'failure_message': test_case['failure_message'],
                'failure_type': analysis['failure_type'],
                'fix_suggestion': analysis['fix_suggestion'],
                'fix_code': analysis['fix_code']
            }
            
            results.append(result)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save analysis results to JSON file.
        
        Args:
            results: List of analysis results
            output_file: Path to output JSON file
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(results, file, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_file}")
        except Exception as e:
            raise Exception(f"Error saving results: {str(e)}")
    
    def analyze_failures(self, input_file: str, output_file: str):
        """
        Main method to analyze test failures end-to-end.
        
        Args:
            input_file: Path to input JSON file with test cases
            output_file: Path to output JSON file for results
        """
        print("Starting test failure analysis...")
        
        # Read test cases
        test_cases = self.read_test_cases(input_file)
        print(f"Loaded {len(test_cases)} test cases")
        
        # Process test cases
        results = self.process_test_cases(test_cases)
        
        # Save results
        self.save_results(results, output_file)
        
        # Print summary
        self._print_summary(results)
        
        print("Analysis complete!")
        return results
    
    def _print_summary(self, results: List[Dict[str, Any]]):
        """Print analysis summary."""
        print("\n=== Analysis Summary ===")
        
        # Count failure types
        failure_counts = {}
        fix_code_count = 0
        
        for result in results:
            failure_type = result['failure_type']
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
            
            if result['fix_code'].strip():
                fix_code_count += 1
        
        print(f"Total test cases analyzed: {len(results)}")
        print(f"Test cases with fix code: {fix_code_count}")
        
        print("\nFailure type distribution:")
        for failure_type, count in sorted(failure_counts.items()):
            print(f"  {failure_type}: {count}")


def create_sample_input():
    """Create sample input file for demonstration."""
    sample_data = [
        {
            "test_case_id": "TC001",
            "test_case_name": "test_user_login_authentication",
            "failure_message": "AssertionError: Expected status code 200, but got 401 Unauthorized"
        },
        {
            "test_case_id": "TC002",
            "test_case_name": "test_database_connection",
            "failure_message": "ConnectionError: could not connect to server: Connection refused"
        },
        {
            "test_case_id": "TC003",
            "test_case_name": "test_api_response_timeout",
            "failure_message": "TimeoutError: Request timed out after 30 seconds"
        },
        {
            "test_case_id": "TC004",
            "test_case_name": "test_null_pointer_validation",
            "failure_message": "NullPointerException: Cannot invoke method 'getName' on null object"
        },
        {
            "test_case_id": "TC005",
            "test_case_name": "test_element_not_found",
            "failure_message": "NoSuchElementException: Unable to locate element with id 'submit-button'"
        },
        {
            "test_case_id": "TC006",
            "test_case_name": "test_calculation_mismatch",
            "failure_message": "AssertionError: Expected total 100.0 but got 110.0"
        }
    ]
    
    with open("sample_test_failures.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    return "sample_test_failures.json"


def main():
    """Example usage of the TestFailureAnalyzer."""
    try:
        # Create sample input file
        input_file = create_sample_input()
        print(f"Created sample input file: {input_file}")
        
        # Initialize analyzer
        analyzer = TestFailureAnalyzer()
        
        # Run analysis
        output_file = "test_failure_analysis_results.json"
        results = analyzer.analyze_failures(input_file, output_file)
        
        # Show sample results
        print("\n=== Sample Results ===")
        for result in results[:3]:  # Show first 3 results
            print(f"\nTest: {result['test_case_id']} - {result['test_case_name']}")
            print(f"Failure Type: {result['failure_type']}")
            print(f"Fix Suggestion: {result['fix_suggestion'][:100]}...")
            if result['fix_code']:
                print(f"Fix Code: {len(result['fix_code'])} characters of code provided")
            else:
                print("Fix Code: No code provided")
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use this analyzer:")
        print("1. Set your API key: export ANTHROPIC_API_KEY=your_key_here")
        print("2. Install dependencies: pip install anthropic")
        print("3. Run the script: python test_failure_analyzer.py")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()