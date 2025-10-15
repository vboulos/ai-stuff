# Test Failure Analysis and Fix Suggestion Framework

A comprehensive Python framework for analyzing test failures and generating automated fix suggestions using Claude AI. This modular system processes test results, provides root cause analysis, and suggests specific code fixes.

## 🎯 Overview

This framework consists of three main components:

- **`analyze_failures.py`** - Analyzes test failures to identify root causes
- **`fix_suggestor.py`** - Generates specific code fixes and solutions
- **`analyze_and_suggest_fixes.py`** - Orchestrates the complete workflow

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  JSON Test      │    │   Failure        │    │  Fix           │
│  Results        │───▶│   Analyzer       │───▶│  Suggestor     │
│                 │    │                  │    │                │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Root Cause      │    │  Code Fixes &   │
                       │  Analysis        │    │  Suggestions    │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                └───────────▶┌──────────────────┐
                                             │ Comprehensive    │
                                             │ JSON Report      │
                                             └──────────────────┘
```

## 📦 Components

### 1. FailureAnalyzer (`analyze_failures.py`)

**Purpose**: Analyzes test failures using Claude AI to identify root causes.

**Key Features**:
- Root cause identification
- Confidence scoring (0.1-1.0)
- Error categorization (timeout, assertion, network, etc.)
- Severity assessment (critical, high, medium, low)
- Framework-specific analysis

**Example Usage**:
```python
from analyze_failures import FailureAnalyzer

analyzer = FailureAnalyzer(claude_timeout=120)
result = analyzer.analyze_failure(
    test_name="test_login",
    failure_message="AssertionError: Expected 200, got 401",
    framework="pytest"
)

print(f"Root Cause: {result['root_cause']}")
print(f"Confidence: {result['confidence_score']}")
```

### 2. FixSuggestor (`fix_suggestor.py`)

**Purpose**: Generates specific code fixes and implementation suggestions.

**Key Features**:
- Fix type classification (quick_fix, refactor, configuration, etc.)
- Priority assessment (critical, high, medium, low)
- Effort estimation (minutes, hours, days)
- Code examples and changes
- Validation steps
- Prevention strategies

**Example Usage**:
```python
from fix_suggestor import FixSuggestor

suggestor = FixSuggestor(claude_timeout=120)
result = suggestor.suggest_fix(
    test_name="test_login",
    failure_message="AssertionError: Expected 200, got 401",
    framework="pytest",
    analysis_data=previous_analysis
)

print(f"Fix Type: {result['fix_type']}")
print(f"Code Changes: {result['code_changes']}")
```

### 3. TestFailureOrchestrator (`analyze_and_suggest_fixes.py`)

**Purpose**: Orchestrates the complete workflow from test results to comprehensive analysis.

**Key Features**:
- Parallel and sequential processing
- Multiple input formats support
- Comprehensive JSON output
- Error handling and recovery
- Progress tracking and statistics

## 🚀 Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install requests

# Ensure Claude CLI is installed and configured
# Follow Claude CLI setup instructions
```

### Basic Usage

```bash
# Analyze test failures with fix suggestions
python analyze_and_suggest_fixes.py test_results.json

# Analysis only (skip fix suggestions)
python analyze_and_suggest_fixes.py test_results.json --analysis-only

# Custom output file with parallel processing
python analyze_and_suggest_fixes.py input.json --output results.json

# Sequential processing with limited failures
python analyze_and_suggest_fixes.py input.json --no-parallel --max-failures 5
```

### Input Format

The framework accepts various JSON formats:

**Direct Array**:
```json
[
  {
    "name": "test_user_authentication",
    "status": "failed",
    "failure_message": "AssertionError: Expected 200, got 401",
    "framework": "pytest"
  }
]
```

**Nested Object**:
```json
{
  "test_results": [
    {
      "test_name": "test_database_connection",
      "failure_message": "Connection refused",
      "framework": "pytest"
    }
  ]
}
```

## 📊 Output Format

The framework generates comprehensive JSON reports:

```json
{
  "metadata": {
    "generated_at": "2025-01-09T...",
    "total_tests": 10,
    "failed_tests": 3,
    "successful_analyses": 2,
    "successful_fixes": 2,
    "processing_mode": "analysis_and_fixes"
  },
  "statistics": {
    "processing_time_seconds": 45.2,
    "analysis_success_rate": 0.67,
    "fix_success_rate": 0.67,
    "average_confidence": 0.85
  },
  "test_results": [
    {
      "test_name": "test_login",
      "framework": "pytest",
      "original_test": { /* original test data */ },
      "analysis": {
        "success": true,
        "root_cause": "Authentication token validation failure",
        "suggested_fix": "Update token validation logic",
        "confidence_score": 0.8,
        "error_category": "authentication",
        "severity": "high"
      },
      "fix_suggestion": {
        "success": true,
        "fix_type": "quick_fix",
        "priority": "high",
        "estimated_effort": "minutes",
        "code_changes": "/* specific code fixes */",
        "validation_steps": ["step1", "step2"],
        "prevention": "prevention strategies"
      }
    }
  ]
}
```

## 🛠️ Advanced Usage

### Parallel Processing

```bash
# Use 5 parallel workers
python analyze_and_suggest_fixes.py input.json --max-workers 5

# Disable parallel processing
python analyze_and_suggest_fixes.py input.json --no-parallel
```

### Framework-Specific Analysis

```bash
# Apply framework to all tests
python analyze_and_suggest_fixes.py input.json --framework cypress

# Framework can also be specified per test in JSON
```

### Error Handling

```bash
# Increase timeout for complex analysis
python analyze_and_suggest_fixes.py input.json --timeout 180

# Limit processing for testing
python analyze_and_suggest_fixes.py input.json --max-failures 3
```

### Sample Data Generation

```bash
# Create sample test failures for testing
python analyze_and_suggest_fixes.py --sample
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Configure Claude CLI settings
export CLAUDE_API_KEY="your_api_key"
export CLAUDE_TIMEOUT="120"
```

### Command Line Options

```bash
python analyze_and_suggest_fixes.py --help
```

**Available Options**:
- `--output, -o`: Output file path
- `--framework`: Framework to apply to all tests
- `--max-failures`: Limit number of failures to process
- `--timeout`: Claude CLI timeout (default: 120s)
- `--max-workers`: Parallel workers (default: 3)
- `--no-parallel`: Disable parallel processing
- `--analysis-only`: Skip fix suggestions
- `--sample`: Create sample test file

## 📈 Performance

### Processing Speed
- **Parallel Mode**: ~3 tests analyzed simultaneously
- **Sequential Mode**: One test at a time
- **Average Time**: 30-60 seconds per test analysis
- **Timeout**: Configurable (default: 120 seconds)

### Scalability
- **Batch Processing**: Handles hundreds of test failures
- **Memory Efficient**: Processes results incrementally
- **Error Recovery**: Continues processing despite individual failures

## 🎯 Error Categories

The framework categorizes errors into:

- **timeout**: Test execution timeouts
- **assertion**: Assertion failures and unexpected values
- **network**: Network connectivity issues
- **configuration**: Configuration and setup problems
- **dependency**: Missing or incompatible dependencies
- **ui_interaction**: UI element interaction failures
- **database**: Database connection and query issues
- **authentication**: Authentication and authorization failures

## 🏷️ Fix Types

Generated fixes are classified as:

- **quick_fix**: Simple code changes (minutes)
- **refactor**: Code restructuring (hours)
- **configuration**: Config file changes (minutes)
- **dependency**: Package updates/additions (minutes)
- **infrastructure**: Environment setup (hours/days)
- **test_update**: Test code improvements (minutes/hours)

## 🔍 Use Cases

### Development Team
- **Daily Standup**: Quick overview of test failures
- **Sprint Planning**: Effort estimation for fixes
- **Code Review**: Understanding failure patterns

### QA Team
- **Test Analysis**: Root cause identification
- **Test Improvement**: Prevention strategies
- **Automation**: Automated failure triage

### DevOps Team
- **CI/CD Pipeline**: Automated failure analysis
- **Infrastructure Issues**: Environment-related failures
- **Monitoring**: Trend analysis and reporting

## 🛡️ Error Handling

### Graceful Degradation
- Continues processing if individual tests fail
- Provides partial results for successful analyses
- Detailed error reporting and logging

### Timeout Management
- Configurable timeouts per analysis
- Automatic retry logic for transient failures
- Progress tracking for long-running operations

### Validation
- Input format validation
- Output structure verification
- Error message sanitization

## 📚 Examples

### Example 1: Basic Analysis

```bash
# Analyze failed tests from CI/CD pipeline
python analyze_and_suggest_fixes.py ci_failures.json --output analysis_report.json
```

### Example 2: Framework-Specific Processing

```bash
# Process Cypress test failures
python analyze_and_suggest_fixes.py cypress_failures.json --framework cypress --max-workers 2
```

### Example 3: Quick Triage

```bash
# Quick analysis of top 5 failures
python analyze_and_suggest_fixes.py all_failures.json --max-failures 5 --analysis-only
```

### Example 4: Production Pipeline

```bash
# Full analysis with custom timeout
python analyze_and_suggest_fixes.py prod_failures.json \
  --output prod_analysis.json \
  --timeout 180 \
  --max-workers 5
```

## 🤝 Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Analyze Test Failures
  run: |
    python analyze_and_suggest_fixes.py test_failures.json --output analysis.json
    # Upload analysis.json as artifact
```

### Slack Integration

```python
# Send analysis summary to Slack
import json
import requests

with open('analysis.json') as f:
    data = json.load(f)
    
summary = data['statistics']
message = f"Test Analysis: {summary['successful_analyses']} analyses completed"
# Send to Slack webhook
```

## 🐛 Troubleshooting

### Common Issues

1. **Claude CLI Not Found**
   ```bash
   # Ensure Claude CLI is in PATH
   which claude
   ```

2. **Timeout Errors**
   ```bash
   # Increase timeout
   python analyze_and_suggest_fixes.py input.json --timeout 300
   ```

3. **Memory Issues**
   ```bash
   # Reduce parallel workers
   python analyze_and_suggest_fixes.py input.json --max-workers 1
   ```

4. **Invalid Input Format**
   ```bash
   # Validate JSON format
   python -m json.tool input.json
   ```

### Debug Mode

```bash
# Enable verbose logging
export PYTHONPATH=/path/to/modules
python -v analyze_and_suggest_fixes.py input.json
```

## 📄 License

This project is provided as-is for educational and development purposes.

## 🤖 AI Integration

This framework leverages Claude AI for:
- Natural language processing of error messages
- Pattern recognition in test failures
- Code generation for fixes
- Best practice recommendations

The quality of analysis depends on:
- Clear error messages in test results
- Sufficient context in failure descriptions
- Proper framework identification
- Network connectivity to Claude AI services


## Claude recommendation

Keep your current direct CLI approach for the main workflow because:
- It works well for your batch processing needs
- Performance is excellent for processing many failures
- Output is predictable and structured
- Easy to integrate into CI/CD pipelines

Consider adding subagent enhancement for:
- High-priority failures (critical/high severity)
- Low-confidence analyses (< 0.6 confidence score)
- Complex multi-component test failures
- When you need code context or research
