# Test Failure Analyzer

A Python tool that uses Claude AI to analyze test failures and classify them by type with fix suggestions and code fixes.

## Features

- **Intelligent Classification**: Automatically categorizes failures into types (automation_bug, product_bug, network_issue, etc.)
- **Fix Suggestions**: Provides detailed, actionable steps to resolve issues
- **Code Fixes**: Generates actual code to fix the problems when possible
- **JSON Input/Output**: Simple JSON file format for easy integration

## Installation

```bash
pip install anthropic
```

## Setup

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

## Usage

### Quick Start

```bash
python run_analysis.py
```

This will:
1. Look for `test_failures.json` in the current directory
2. Create a sample file if it doesn't exist
3. Analyze the failures and save results to `analysis_results.json`

### Input Format

Create a JSON file with your test failures:

```json
[
  {
    "test_case_id": "TC001",
    "test_case_name": "test_user_login",
    "failure_message": "AssertionError: Expected status code 200, but got 401"
  },
  {
    "test_case_id": "TC002", 
    "test_case_name": "test_database_connection",
    "failure_message": "ConnectionError: could not connect to database server"
  }
]
```

### Output Format

The tool generates a JSON file with analysis results:

```json
[
  {
    "test_case_id": "TC001",
    "test_case_name": "test_user_login",
    "failure_message": "AssertionError: Expected status code 200, but got 401",
    "failure_type": "automation_bug",
    "fix_suggestion": "The test is using incorrect credentials or the wrong endpoint...",
    "fix_code": "response = client.post('/login', data={'username': 'valid_user', 'password': 'correct_password'})"
  }
]
```

### Programmatic Usage

```python
from test_failure_analyzer import TestFailureAnalyzer

# Initialize analyzer
analyzer = TestFailureAnalyzer()

# Analyze failures
results = analyzer.analyze_failures("input.json", "output.json")

# Access results
for result in results:
    print(f"Test: {result['test_case_id']}")
    print(f"Type: {result['failure_type']}")
    print(f"Fix: {result['fix_suggestion']}")
    if result['fix_code']:
        print(f"Code: {result['fix_code']}")
```

## Failure Types

The analyzer classifies failures into these categories:

- **automation_bug**: Test code errors, wrong assertions, incorrect selectors
- **product_bug**: Application functionality broken, business logic errors  
- **network_issue**: API timeouts, connection failures, DNS problems
- **configuration_issue**: Wrong URLs, missing settings, environment config
- **data_issue**: Missing test data, incorrect data format, database problems
- **environment_issue**: Services not running, infrastructure problems
- **timing_issue**: Race conditions, synchronization problems, timeouts
- **dependency_issue**: Missing libraries, version conflicts, service dependencies
- **assertion_error**: Expected vs actual value mismatches
- **infrastructure_issue**: Hardware/platform related failures
- **unknown**: Cannot determine cause from available information

## Files

- `test_failure_analyzer.py` - Main analyzer class
- `run_analysis.py` - Simple script for quick analysis
- `requirements.txt` - Python dependencies

## Examples

Run the built-in example:

```bash
python test_failure_analyzer.py
```

This creates sample test failures and analyzes them to show how the tool works.

## Error Handling

The tool handles common issues gracefully:

- Missing API key: Clear error message with setup instructions
- Invalid JSON: Detailed error information
- Network issues: Fallback error responses
- Missing required fields: Validation with helpful error messages

## Output

The tool provides:

1. **Progress indicators** during analysis
2. **Summary statistics** of failure types
3. **Sample results preview** 
4. **Detailed JSON output** file with all results

Perfect for integration into CI/CD pipelines, test reporting, or manual test failure investigation.