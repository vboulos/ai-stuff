# Analysis & Fix Runbook Usage Guide

## Overview

Both the `FailureAnalyzer` and `FixSuggestor` classes now support using external runbook template files for generating prompts, instead of having them hardcoded in the code. This makes it easier to:

- Customize prompts without modifying code
- Maintain different prompt templates for different scenarios
- Version control your prompt engineering separately
- Share and reuse prompt templates across teams

## Quick Start

### 1. Using Hardcoded Prompts (Default)

```python
from analyze_failures import FailureAnalyzer

# Default behavior - uses hardcoded prompt
analyzer = FailureAnalyzer()

result = analyzer.analyze_failure(
    "test_login",
    "AssertionError: Expected 200, got 401",
    "pytest"
)
```

### 2. Using Runbook Template

```python
from analyze_failures import FailureAnalyzer

# Use custom runbook template
analyzer = FailureAnalyzer(runbook_path="analysis_runbook.txt")

result = analyzer.analyze_failure(
    "test_database_connection",
    "TimeoutError: Connection timed out after 30s",
    "pytest"
)
```

## Creating Custom Runbook Templates

### Template Variables

Your runbook template file can use these placeholders:

| Variable | Description | Example |
|----------|-------------|---------|
| `{test_name}` | Name of the test | `test_login` |
| `{failure_message}` | Error/failure message | `AssertionError: Expected 200, got 401` |
| `{framework}` | Test framework or "Not specified" | `pytest`, `jest`, `cypress` |
| `{framework_info}` | Formatted framework string | ` (Framework: pytest)` or empty |

### Example Template

Create a file called `analysis_runbook.txt`:

```
Analyze this test failure{framework_info}:

Test: {test_name}
Error: {failure_message}

Provide analysis in this format:

**ROOT CAUSE:**
[Why did it fail? Be specific about the underlying issue]

**SUGGESTED FIX:**
[High-level approach to fix the issue]

**CODE EXAMPLE:**
[Code example if helpful - show specific changes needed]

**CONFIDENCE:**
[0.1 to 1.0 - how confident are you in this analysis]

**ERROR_CATEGORY:**
[timeout|assertion|network|configuration|dependency|ui_interaction|database|authentication]

**SEVERITY:**
[critical|high|medium|low]
```

### Advanced Template Example

Create a more detailed runbook for specific scenarios:

```
FAILURE ANALYSIS REQUEST
========================

Framework: {framework}
Test Name: {test_name}
Failure Message:
{failure_message}

ANALYSIS INSTRUCTIONS:
----------------------
Please analyze this test failure and provide a comprehensive diagnosis.

Consider the following aspects:
1. Root cause identification
2. Impact assessment
3. Remediation steps
4. Prevention strategies

OUTPUT FORMAT:
--------------

**ROOT CAUSE:**
Provide a detailed explanation of why the test failed.

**SUGGESTED FIX:**
Describe the high-level approach to fix this issue.

**CODE EXAMPLE:**
If applicable, provide code snippets showing the fix.

**CONFIDENCE:**
Rate your confidence level (0.1 to 1.0)

**ERROR_CATEGORY:**
Classify: timeout|assertion|network|configuration|dependency|ui_interaction|database|authentication

**SEVERITY:**
Rate severity: critical|high|medium|low

**PREVENTION:**
Suggest how to prevent similar failures in the future.
```

## Error Handling

The runbook feature includes automatic fallback:

1. **File Not Found**: Falls back to hardcoded prompt with a warning
2. **Missing Variables**: Falls back to hardcoded prompt with error message
3. **Read Errors**: Falls back to hardcoded prompt with error details

Example output when runbook is not found:
```
⚠️  Runbook not found at 'custom_runbook.txt', using default prompt
```

## Best Practices

### 1. Organize Runbooks by Use Case

```
runbooks/
  ├── default_analysis.txt
  ├── security_analysis.txt
  ├── performance_analysis.txt
  └── integration_test_analysis.txt
```

### 2. Version Control Your Runbooks

Keep runbook templates in version control alongside your code:

```bash
git add analysis_runbook.txt
git commit -m "Add custom analysis runbook template"
```

### 3. Use Descriptive File Names

```python
# Good
analyzer = FailureAnalyzer(runbook_path="runbooks/cypress_ui_analysis.txt")
analyzer = FailureAnalyzer(runbook_path="runbooks/api_integration_analysis.txt")

# Less clear
analyzer = FailureAnalyzer(runbook_path="template1.txt")
```

### 4. Test Your Templates

Always test your custom templates before using them in production:

```python
# Test with sample data
analyzer = FailureAnalyzer(runbook_path="my_custom_runbook.txt")
result = analyzer.analyze_failure(
    "test_example",
    "Sample error message",
    "pytest"
)

# Verify the prompt was generated correctly
print(result)
```

## Using with Multiple Failures

The `analyze_multiple_failures` method also supports runbooks:

```python
analyzer = FailureAnalyzer(runbook_path="analysis_runbook.txt")

test_cases = [
    {
        "name": "test_login",
        "failure_message": "AssertionError: Expected 200, got 401",
        "framework": "pytest"
    },
    {
        "name": "test_checkout",
        "failure_message": "TimeoutError: Element not found",
        "framework": "cypress"
    }
]

results = analyzer.analyze_multiple_failures(test_cases)
```

## API Reference

### FailureAnalyzer.__init__

```python
def __init__(self, claude_timeout: int = 120, runbook_path: str = None):
    """
    Initialize the FailureAnalyzer.
    
    Args:
        claude_timeout: Timeout for Claude CLI calls in seconds (default: 120)
        runbook_path: Optional path to runbook template file. If provided,
                     prompts will be read from this file instead of hardcoded.
    """
```

### _create_analysis_prompt_from_runbook

```python
def _create_analysis_prompt_from_runbook(
    self, 
    test_name: str, 
    failure_message: str,
    framework: str, 
    runbook_path: str = "analysis_runbook.txt"
) -> str:
    """
    Create a prompt for failure analysis from a runbook file.
    
    The runbook template can use these placeholders:
        {test_name} - The name of the test
        {failure_message} - The error/failure message
        {framework} - The test framework (or "Not specified")
        {framework_info} - Formatted framework info for display
    """
```

## Troubleshooting

### Issue: Variables Not Substituted

**Problem**: Template shows `{test_name}` instead of actual test name

**Solution**: Make sure you're using Python string formatting syntax with single braces `{}`, not double braces `{{}}` or other template engines.

### Issue: Unicode/Encoding Errors

**Problem**: Characters display incorrectly

**Solution**: Save your runbook file with UTF-8 encoding

### Issue: Runbook Not Found

**Problem**: Warning about runbook not found

**Solution**: 
- Check the file path is correct (relative or absolute)
- Verify the file exists in the expected location
- Use absolute paths if working directory is uncertain

```python
import os

# Use absolute path
runbook_path = os.path.join(os.path.dirname(__file__), "analysis_runbook.txt")
analyzer = FailureAnalyzer(runbook_path=runbook_path)
```

## Using Fix Suggester with Runbooks

### Basic Usage

```python
from fix_suggestor import FixSuggestor

# Use custom runbook template
suggestor = FixSuggestor(runbook_path="fix_runbook.txt")

result = suggestor.suggest_fix(
    "test_database_connection",
    "TimeoutError: Connection timed out after 30s",
    "pytest",
    analysis_data  # Optional: previous analysis
)
```

### Fix Runbook Template Variables

The fix runbook template supports these placeholders:

| Variable | Description | Example |
|----------|-------------|---------|
| `{test_name}` | Name of the test | `test_database_connection` |
| `{failure_message}` | Error/failure message | `TimeoutError: Connection timed out` |
| `{framework}` | Test framework or "Not specified" | `pytest`, `jest`, `cypress` |
| `{framework_info}` | Formatted framework string | ` (Framework: pytest)` or empty |
| `{analysis_context}` | Previous analysis data | Block with root cause, category, etc. |

### Example Fix Runbook Template

Create `fix_runbook.txt`:

```
Generate specific code fixes for this failed test{framework_info}:

**TEST DETAILS:**
- Test Name: {test_name}
- Error: {failure_message}{analysis_context}

Provide detailed fix suggestions in this format:

**FIX_TYPE:**
[quick_fix|refactor|configuration|dependency|infrastructure|test_update]

**PRIORITY:**
[critical|high|medium|low]

**ESTIMATED_EFFORT:**
[minutes|hours|days]

**CODE_CHANGES:**
```language
// Show specific code changes needed
```

**CONFIGURATION_CHANGES:**
```
// Any configuration file changes needed
```

**DEPENDENCIES:**
```
// New dependencies or version updates needed
```

**VALIDATION_STEPS:**
1. [Step to verify the fix]
2. [How to test the fix]
3. [Expected outcome]

**PREVENTION:**
[How to prevent this issue in the future]

**IMPACT_ASSESSMENT:**
[What other areas might be affected by this fix]

**ROLLBACK_PLAN:**
[How to rollback if the fix causes issues]
```

## Using with the Orchestrator

The `TestFailureOrchestrator` supports runbooks for both analysis and fix suggestions:

```bash
# Use both analysis and fix runbooks
python analyze_and_suggest_fixes.py test_failures.json \
  --analysis-runbook analysis_runbook.txt \
  --fix-runbook fix_runbook.txt

# Use only analysis runbook
python analyze_and_suggest_fixes.py test_failures.json \
  --analysis-runbook custom_analysis.txt

# Use only fix runbook
python analyze_and_suggest_fixes.py test_failures.json \
  --fix-runbook custom_fix.txt
```

### Python API with Orchestrator

```python
from analyze_and_suggest_fixes import TestFailureOrchestrator

orchestrator = TestFailureOrchestrator(
    claude_timeout=120,
    max_workers=3,
    analysis_runbook="analysis_runbook.txt",
    fix_runbook="fix_runbook.txt"
)

result = orchestrator.process_test_failures(
    "test_failures.json",
    output_file="results.json"
)
```

## Examples

See the `__main__` sections for working examples:

```bash
# Test analysis with runbooks
python analyze_failures.py

# Test fix suggestions with runbooks
python fix_suggestor.py

# Full orchestration with runbooks
python analyze_and_suggest_fixes.py --sample
python analyze_and_suggest_fixes.py sample_test_failures.json \
  --analysis-runbook analysis_runbook.txt \
  --fix-runbook fix_runbook.txt
```

This will demonstrate both hardcoded and runbook-based approaches.

