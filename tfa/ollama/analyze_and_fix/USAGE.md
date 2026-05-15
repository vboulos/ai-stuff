# Test Failure Analysis - Usage Guide

## Quick Start

### Basic Usage
```bash
python3 analyze_and_suggest_fixes.py <input_file.json> --model llama3.1 --output results.json
```

### For CI/CD (Jenkins, GitLab, etc.)
```bash
# Use --yes to skip interactive prompts and --skip-verify for faster startup
python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --model llama3.1 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify
```

## Command Line Options

### Required
- `input_file` - Path to JSON file containing test failures

### Model Configuration
- `--model MODEL` - Ollama model to use (default: llama3.1)
  - Examples: llama3.1, llama3.2, mistral, codellama
  - Must be installed via `ollama pull <model>`

### Output Options
- `--output FILE` - Output file path (default: analysis_and_fixes.json)
- `--verbose` - Show detailed progress and timing

### Analysis Options
- `--framework FRAMEWORK` - Test framework (pytest, jest, cypress, etc.)
  - Auto-detected from test data if not specified
- `--analyze-only` - Only analyze failures, skip fix suggestions
- `--limit N` - Process only first N tests (useful for testing)

### CI/CD Options
- `--yes` or `-y` - Skip confirmation prompts (for non-interactive environments)
- `--skip-verify` - Skip Ollama connection verification (faster startup)
- `--timeout SECONDS` - Timeout for Ollama calls (default: 60)

## Examples

### Test with sample data
```bash
# Process just 1 test to verify setup
python3 analyze_and_suggest_fixes.py sample_failures.json --model llama3.1 --limit 1
```

### Interactive mode (local development)
```bash
# Full interactive experience with confirmations
python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --model llama3.1 \
    --output tests_analysis/analysis_and_fixes.json
```

### CI/CD mode (Jenkins, GitLab, GitHub Actions)
```bash
# Non-interactive, no prompts, skip verification
python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --model llama3.1 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify
```

### Analysis only (faster)
```bash
# Only analyze failures, don't generate fix suggestions
python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --model llama3.1 \
    --output tests_analysis/analysis_only.json \
    --analyze-only \
    --yes
```

### Limited run for testing
```bash
# Process only first 5 tests
python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \
    --model llama3.1 \
    --limit 5 \
    --output tests_analysis/sample_results.json
```

## Input File Format

The script accepts JSON files in various formats:

### Format 1: Array of test objects
```json
[
  {
    "name": "test_login",
    "failure_message": "AssertionError: Expected 200, got 401",
    "framework": "pytest"
  },
  {
    "name": "test_signup",
    "error": "Timeout after 30s"
  }
]
```

### Format 2: Object with test array
```json
{
  "tests": [
    { "test_name": "test_login", "message": "Error message" }
  ]
}
```

### Format 3: Object with failures array
```json
{
  "failures": [
    { "name": "test_login", "failure_message": "Error" }
  ],
  "failed_tests": [...]
}
```

The script will auto-detect the format.

## Output Format

```json
{
  "metadata": {
    "generated_at": "2024-04-15T10:30:00",
    "input_file": "tests_analysis/grc_failed_tests.json",
    "model": "llama3.1",
    "total_tests": 10,
    "successful_analyses": 9,
    "fix_summary": {
      "total_fixes": 10,
      "successful_fixes": 8,
      "fix_type_distribution": {...},
      "priority_distribution": {...}
    }
  },
  "results": [
    {
      "test_name": "test_login",
      "framework": "pytest",
      "original_test": {...},
      "analysis": {
        "success": true,
        "root_cause": "...",
        "suggested_fix": "...",
        "confidence_score": 0.85,
        "error_category": "authentication",
        "severity": "high"
      },
      "fix_suggestion": {
        "success": true,
        "fix_type": "quick_fix",
        "priority": "high",
        "code_changes": "...",
        "validation_steps": [...]
      }
    }
  ]
}
```

## Testing Your Setup

Before running on production data, test your Ollama setup:

```bash
# Test Ollama connection and performance
python3 test_ollama.py --model llama3.1 --num-tests 10

# This will:
# - Verify Ollama is running
# - List available models
# - Test response time
# - Estimate total processing time
```

## Troubleshooting

### "Model not found" error
```bash
# Install the model first
ollama pull llama3.1
# or
ollama pull llama3.2
```

### "EOFError: EOF when reading a line" in Jenkins
```bash
# Use --yes flag to skip prompts
python3 analyze_and_suggest_fixes.py input.json --model llama3.1 --yes
```

### Script is too slow
```bash
# Use --limit to process fewer tests
python3 analyze_and_suggest_fixes.py input.json --model llama3.1 --limit 5

# Or use --analyze-only (skips fix suggestions, 2x faster)
python3 analyze_and_suggest_fixes.py input.json --model llama3.1 --analyze-only

# Or use a smaller/faster model
python3 analyze_and_suggest_fixes.py input.json --model llama3:latest
```

### Connection timeout
```bash
# Increase timeout (default is 60s)
python3 analyze_and_suggest_fixes.py input.json --model llama3.1 --timeout 120
```

## Individual Scripts

You can also run analysis and fix suggestion separately:

### Step 1: Analyze failures
```bash
python3 analyze_failures.py --model llama3.1 --input tests.json --output analysis.json
```

### Step 2: Generate fix suggestions
```bash
python3 fix_suggestor.py --model llama3.1 --input analysis.json --output fixes.json
```

## Performance Tips

1. **Use --limit for initial testing** - Process 1-5 tests first to verify setup
2. **Use --analyze-only** - Skip fix suggestions if you only need analysis (2x faster)
3. **Use a smaller model** - llama3:latest is faster than llama3.1
4. **Increase timeout for complex tests** - Use --timeout 120 for longer tests
5. **Run in CI with --yes --skip-verify** - Avoid interactive prompts and verification overhead
