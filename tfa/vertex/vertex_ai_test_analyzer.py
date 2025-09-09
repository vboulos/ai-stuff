import json
import os
import re
from typing import List, Dict, Any
import anthropic

class VertexAITestFailureAnalyzer:
    """
    Analyzes test failures using Anthropic models via Google Cloud Vertex AI.
    """
    
    def __init__(self, project_id: str = None, region: str = None, model_name: str = "claude-3-5-sonnet@20241022"):
        """
        Initialize the analyzer with Vertex AI Anthropic client.
        
        Args:
            project_id: Google Cloud project ID. If None, will look for ANTHROPIC_VERTEX_PROJECT_ID env var.
            region: Google Cloud region. If None, will look for ANTHROPIC_VERTEX_REGION env var or default to us-central1.
            model_name: Anthropic model to use via Vertex AI
        """
        if project_id is None:
            project_id = os.getenv('ANTHROPIC_VERTEX_PROJECT_ID')
            if not project_id:
                raise ValueError("Project ID required. Set ANTHROPIC_VERTEX_PROJECT_ID environment variable or pass project_id parameter.")
        
        if region is None:
            region = os.getenv('ANTHROPIC_VERTEX_REGION', 'us-central1')
        
        try:
            # Initialize Vertex AI Anthropic client
            self.client = anthropic.AnthropicVertex(
                project_id=project_id,
                region=region
            )
            self.model_name = model_name
            print(f"✅ Vertex AI Anthropic client initialized (Project: {project_id}, Region: {region})")
        except Exception as e:
            raise Exception(f"Failed to initialize Vertex AI client: {str(e)}")
    
    def read_test_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read test case data from JSON file.
        
        Args:
            file_path: Path to JSON file containing test case data
            
        Returns:
            List of test case dictionaries
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
        Analyze a single test failure using Vertex AI Anthropic.
        
        Args:
            test_case: Dictionary with test case information
            
        Returns:
            Dictionary with analysis results
        """
        # Include additional context if available
        additional_context = ""
        if 'test_code' in test_case:
            additional_context += f"\n\nTest Code:\n```\n{test_case['test_code']}\n```"
        if 'stack_trace' in test_case:
            additional_context += f"\n\nStack Trace:\n{test_case['stack_trace']}"
        if 'environment' in test_case:
            additional_context += f"\n\nEnvironment: {test_case['environment']}"
        
#         prompt = f"""Analyze this test failure and provide a structured response:

# Test Case ID: {test_case['test_case_id']}
# Test Case Name: {test_case['test_case_name']}
# Failure Message: {test_case['failure_message']}{additional_context}

# Please respond in this EXACT format:

# FAILURE_TYPE: [Select ONE from the list below]
# - automation_bug: Test code errors, wrong assertions, incorrect selectors, test logic issues
# - product_bug: Application functionality broken, business logic errors, feature not working
# - network_issue: API timeouts, connection failures, DNS problems, service unreachable
# - configuration_issue: Wrong URLs, missing settings, environment configuration problems
# - data_issue: Missing test data, incorrect data format, database problems, data validation
# - environment_issue: Services not running, infrastructure problems, deployment issues
# - timing_issue: Race conditions, synchronization problems, timeouts, async issues
# - dependency_issue: Missing libraries, version conflicts, service dependencies unavailable
# - assertion_error: Expected vs actual value mismatches, comparison failures
# - infrastructure_issue: Hardware/platform related failures, resource constraints
# - unknown: Cannot determine root cause from available information

# FIX_SUGGESTION: [Provide specific, actionable steps to fix this issue. Be detailed and practical.]

# FIX_CODE: [If applicable, provide actual code to fix the issue. Use triple backticks for code blocks. Include both the problematic code and the corrected version when possible.]

# Example response:
# FAILURE_TYPE: automation_bug
# FIX_SUGGESTION: The test is using an incorrect element selector. The application UI has changed and the element ID 'login-button' no longer exists. It has been renamed to 'submit-btn'. Update the test selector to use the correct element ID.
# FIX_CODE:
# ```python
# # Before (incorrect)
# login_button = driver.find_element(By.ID, "login-button")

# # After (correct)
# login_button = driver.find_element(By.ID, "submit-btn")
# ```

# Now analyze the test failure above and provide your response in this exact format.
# """

# prompt = f"""Analyze the attached JSON test result. Generate a new JSON object that includes all the original data and adds two new keys: 'suggestedFix' and 'codeFix'. For 'suggestedFix', explain the common reasons and provide a code example showing how to fix it."""
        prompt = f""" 
        Analyze this test failure:

        # Test Case Name: {test_case['test_case_name']}
        # Failure Message: {test_case['failure_message']}{additional_context}

        Provide:
        1. ROOT CAUSE: What's causing this failure?
        2. CODE FIX: Specific code changes to fix it

        Format:
        ROOT CAUSE: [your analysis]
        CODE FIX: [your fix suggestion]
        """
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1500,
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
        Parse Anthropic's structured response.
        
        Args:
            response: Raw response from Anthropic via Vertex AI
            
        Returns:
            Dictionary with parsed failure_type, fix_suggestion, and fix_code
        """
        # Extract failure type
        failure_type_match = re.search(r'FAILURE_TYPE:\s*([^\n]+)', response, re.IGNORECASE)
        failure_type = failure_type_match.group(1).strip().lower() if failure_type_match else 'unknown'
        
        # Clean up failure type (extract just the type name)
        failure_type = failure_type.split(':')[0].split('-')[0].strip()
        
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
            print(f"🔍 Analyzing test case {i}/{total_cases}: {test_case['test_case_id']}")
            
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
            
            # Small delay to respect rate limits
            import time
            time.sleep(1)
            
            print(f"   ✅ Analysis complete - Type: {analysis['failure_type']}")
        
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
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            raise Exception(f"Error saving results: {str(e)}")
    
    def analyze_failures(self, input_file: str, output_file: str):
        """
        Main method to analyze test failures end-to-end using Vertex AI.
        
        Args:
            input_file: Path to input JSON file with test cases
            output_file: Path to output JSON file for results
        """
        print("🚀 Starting test failure analysis using Vertex AI Anthropic...")
        
        # Read test cases
        test_cases = self.read_test_cases(input_file)
        print(f"📋 Loaded {len(test_cases)} test cases")
        
        # Process test cases
        results = self.process_test_cases(test_cases)
        
        # Save results
        self.save_results(results, output_file)
        
        # Print summary
        self._print_summary(results)
        
        print("🎉 Analysis complete!")
        return results
    
    def _print_summary(self, results: List[Dict[str, Any]]):
        """Print analysis summary."""
        print("\n📊 === Analysis Summary ===")
        
        # Count failure types
        failure_counts = {}
        fix_code_count = 0
        
        for result in results:
            failure_type = result['failure_type']
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
            
            if result['fix_code'].strip():
                fix_code_count += 1
        
        print(f"📈 Total test cases analyzed: {len(results)}")
        print(f"🔧 Test cases with fix code: {fix_code_count}")
        
        print("\n🏷️ Failure type distribution:")
        for failure_type, count in sorted(failure_counts.items()):
            print(f"   {failure_type}: {count}")


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
            "test_case_name": "test_element_selector",
            "failure_message": "NoSuchElementException: Unable to locate element with id 'submit-button'",
            "test_code": "submit_btn = driver.find_element(By.ID, 'submit-button')\nsubmit_btn.click()"
        },
        {
            "test_case_id": "TC005",
            "test_case_name": "test_calculation_logic",
            "failure_message": "AssertionError: Expected total 100.0 but got 110.0",
            "test_code": "order = Order()\norder.add_item('Product', 100.0)\ntotal = order.calculate_total()\nassert total == 100.0"
        }
    ]
    
    with open("sample_test_failures.json", "w") as f:
        json.dump(sample_data, f, indent=2)
    
    return "sample_test_failures.json"


def main():
    """Example usage of the Vertex AI Test Failure Analyzer."""
    try:
        # Create sample input file
        input_file = create_sample_input()
        print(f"📝 Created sample input file: {input_file}")
        
        # Initialize analyzer
        analyzer = VertexAITestFailureAnalyzer()
        
        # Run analysis
        output_file = "vertex_ai_analysis_results.json"
        results = analyzer.analyze_failures(input_file, output_file)
        
        # Show sample results
        print("\n🔍 === Sample Results ===")
        for result in results[:2]:  # Show first 2 results
            print(f"\n🧪 Test: {result['test_case_id']} - {result['test_case_name']}")
            print(f"🏷️  Failure Type: {result['failure_type']}")
            print(f"💡 Fix Suggestion: {result['fix_suggestion'][:100]}...")
            if result['fix_code']:
                print(f"🔧 Fix Code: {len(result['fix_code'])} characters of code provided")
            else:
                print("🔧 Fix Code: No code provided")
        
        if len(results) > 2:
            print(f"\n📄 ... and {len(results) - 2} more results in {output_file}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n🛠️ Setup Instructions:")
        print("1. Install Anthropic SDK: pip install anthropic")
        print("2. Set up Google Cloud authentication: gcloud auth application-default login")
        print("3. Set environment variables:")
        print("   export ANTHROPIC_VERTEX_PROJECT_ID=your_project_id")
        print("   export ANTHROPIC_VERTEX_REGION=us-central1")
        print("4. Enable Vertex AI API and Anthropic models in your Google Cloud project")
        print("5. Run the script: python vertex_ai_test_analyzer.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()