# Test Failure Analysis with Claude CLI

A complete system for analyzing test failures using Claude CLI, providing root cause analysis and code fix suggestions.

## Features

- ✅ Reads JSON test results from various formats
- 🔍 Filters and extracts only failed tests
- 🧠 Analyzes failures using Claude CLI with fallback to direct API
- 🛠️ Provides specific code fix suggestions
- 📊 Generates comprehensive JSON reports with insights
- 🚀 Robust error handling and multiple setup options

## Files Overview

### Core Classes
- `complete_test_reader.py` - Reads and filters test results
- `complete_failure_analyzer.py` - Analyzes failures using Claude CLI/API
- `complete_report_generator.py` - Generates comprehensive reports
- `complete_test_analyzer.py` - Main orchestrator class

### Example Files
- `sample_test_results.json` - Sample test data
- `run_example.py` - Complete usage example
- `README.md` - This documentation

## Installation & Setup

### Option 1: Claude CLI (Recommended)
```bash
# Install Claude CLI
pip install claude-cli

# Authenticate
claude auth login
```

### Option 2: Direct API
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Option 3: Both (Best reliability)
Set up both CLI and API key for maximum reliability.

## Usage

### Basic Usage
```bash
python complete_test_analyzer.py sample_test_results.json analysis_report.json
```

### With Specific Model
```bash
python complete_test_analyzer.py sample_test_results.json report.json --model claude-3-sonnet-20240229
```

### With API Key
```bash
python complete_test_analyzer.py sample_test_results.json report.json --api-key sk-ant-...
```

### Quick Single Test Analysis
```bash
python complete_test_analyzer.py --quick "test_name" "error message"
```

### Run Complete Example
```bash
python run_example.py
```

## Input JSON Format

The system accepts flexible JSON formats:

```json
{
  "test_results": [
    {
      "test_name": "test_calculate_price",
      "status": "failed",
      "message": "AssertionError: assert 90.0 == 80.0"
    }
  ]
}
```

Alternative formats supported:
- `tests` instead of `test_results`
- `name` instead of `test_name`
- `error` instead of `message`
- Direct array of tests
- Single test object

## Output Report Structure

### Comprehensive Report
```json
{
  "metadata": {
    "generated_at": "2024-01-15T10:30:00",
    "total_failed_tests": 5
  },
  "summary": {
    "total_tests": 5,
    "successful_analyses": 4,
    "analysis_success_rate": 80.0
  },
  "failed_tests": [
    {
      "test_name": "test_calculate_price",
      "failure_message": "AssertionError: assert 90.0 == 80.0",
      "root_cause": "Discount calculation logic error",
      "code_fix": "Change discount calculation from subtraction to percentage"
    }
  ],
  "insights": {
    "recommendations": ["Review calculation logic", "Add input validation"],
    "patterns": {"assertion": 3, "type": 1},
    "fix_complexity": {"simple": 3, "moderate": 1, "complex": 1}
  }
}
```

### Simple Report
A simplified version is also generated with just the essential data.

## Error Handling

The system handles various error scenarios:

- **Claude CLI not found**: Automatically tries direct API if available
- **Model not found**: Suggests alternative models
- **Authentication errors**: Provides setup instructions
- **Rate limits**: Graceful handling with suggestions
- **Network issues**: Timeout handling and retries

## Troubleshooting

### Common Issues

1. **404 Model Error**
   ```bash
   # Try specific model
   python complete_test_analyzer.py input.json output.json --model claude-3-sonnet-20240229
   ```

2. **Authentication Failed**
   ```bash
   # Check CLI status
   claude auth status
   
   # Or use API key
   export ANTHROPIC_API_KEY="your-key"
   ```

3. **CLI Not Found**
   ```bash
   # Install Claude CLI
   pip install claude-cli
   ```

### Skip Validation
If you're having setup issues, you can skip validation:
```bash
python complete_test_analyzer.py input.json output.json --no-validate
```

## Examples

### Programmatic Usage
```python
from complete_test_analyzer import TestAnalyzer

# Create analyzer
analyzer = TestAnalyzer(
    claude_cli_path="claude",
    model="claude-3-sonnet-20240229",
    api_key="your-api-key"
)

# Analyze all failures
analyzer.analyze_test_failures("tests.json", "report.json")

# Quick single analysis
result = analyzer.quick_analyze("test_name", "error message")
print(result['root_cause'])
print(result['code_fix'])
```

### Individual Classes
```python
from complete_test_reader import TestReader
from complete_failure_analyzer import FailureAnalyzer
from complete_report_generator import ReportGenerator

# Use classes individually
reader = TestReader()
failed_tests = reader.read_failed_tests("tests.json")

analyzer = FailureAnalyzer()
for test in failed_tests:
    result = analyzer.analyze_failure(test['test_name'], test['failure_message'])
    print(result)
```

## Performance Tips

1. **Use API Key**: Direct API is often faster than CLI
2. **Batch Processing**: The system processes all tests efficiently
3. **Caching**: Results are cached to avoid duplicate analysis
4. **Specific Models**: Using specific model names avoids lookup overhead

## Support

If you encounter issues:
1. Check your Claude CLI setup: `claude auth status`
2. Verify your API key is valid
3. Try the `--no-validate` flag to skip setup checks
4. Use `--model claude-3-sonnet-20240229` for specific model
5. Check the generated error messages for specific guidance