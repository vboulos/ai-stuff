# Vertex AI Test Failure Analyzer

A Python tool that analyzes test failures and provides intelligent fix suggestions using Google Vertex AI's Gemini models.

## Features

- **Intelligent Analysis**: Uses Google's Gemini models to analyze test failure patterns
- **Detailed Suggestions**: Provides specific, actionable fix recommendations
- **Batch Processing**: Analyze multiple test failures at once
- **Confidence Scoring**: Each analysis includes a confidence score
- **Flexible Input**: Supports various JSON input formats
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with Vertex AI API enabled
2. **Authentication**: Set up Google Cloud authentication
3. **Python Dependencies**: Install required packages

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_vertex.txt
```

Or install manually:
```bash
pip install google-cloud-aiplatform google-auth
```

### 2. Set up Google Cloud Authentication

```bash
# Install Google Cloud CLI if not already installed
# Then authenticate:
gcloud auth application-default login

# Or set environment variable with service account key:
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

### 3. Enable Vertex AI API

Make sure Vertex AI API is enabled in your Google Cloud project:
```bash
gcloud services enable aiplatform.googleapis.com --project YOUR_PROJECT_ID
```

## Usage

### Basic Usage (Batch Analysis)

```bash
python3 vertex_ai_test_analyzer.py --project YOUR_PROJECT_ID input_failures.json results.json
```

### Single Test Analysis

```bash
python3 vertex_ai_test_analyzer.py --project YOUR_PROJECT_ID --single "test_login" "AssertionError: Login failed"
```

### Advanced Options

```bash
# Use different model and location
python3 vertex_ai_test_analyzer.py \
  --project YOUR_PROJECT_ID \
  --location europe-west1 \
  --model gemini-1.5-flash \
  failures.json results.json

# Enable verbose logging
python3 vertex_ai_test_analyzer.py --project YOUR_PROJECT_ID --verbose failures.json results.json
```

## Input Format

The tool expects a JSON file with test failures in this format:

```json
{
  "failed_tests": [
    {
      "test_name": "test_user_authentication",
      "failure_message": "AssertionError: Expected status code 200, but got 401",
      "file_path": "tests/test_auth.py",
      "line_number": 45
    }
  ]
}
```

Alternative format (direct array):
```json
[
  {
    "test_name": "test_example",
    "failure_message": "Error message here",
    "file_path": "test_file.py",
    "line_number": 42
  }
]
```

## Output Format

The tool generates a detailed JSON report:

```json
{
  "analysis_summary": {
    "total_failures": 3,
    "successful_analyses": 3,
    "average_confidence": 0.85
  },
  "results": [
    {
      "test_name": "test_user_authentication",
      "failure_message": "AssertionError: Expected status code 200, but got 401",
      "root_cause": "The test is using an invalid authentication token...",
      "suggested_fix": "Update the test to use a valid token or mock the authentication...",
      "confidence_score": 0.9,
      "analysis_successful": true,
      "error_message": null
    }
  ]
}
```

## Available Models

- `gemini-1.5-pro` (default) - Most capable, higher cost
- `gemini-1.5-flash` - Faster, lower cost
- `gemini-1.0-pro` - Previous generation

## Example Workflow

1. **Run your tests** and capture failures in JSON format
2. **Analyze failures** using the tool:
   ```bash
   python3 vertex_ai_test_analyzer.py --project my-project test_failures.json analysis_results.json
   ```
3. **Review results** in the generated JSON file
4. **Apply suggested fixes** to your test code
5. **Re-run tests** to verify fixes

## Error Handling

The tool includes comprehensive error handling:

- **Authentication errors**: Clear guidance on setup
- **Network timeouts**: Retry logic for API calls
- **Invalid JSON**: Detailed parsing error messages
- **Missing dependencies**: Installation instructions
- **Rate limiting**: Automatic backoff and retry

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Solution: Run 'gcloud auth application-default login'
   ```

2. **Project Not Found**
   ```
   Solution: Verify project ID and ensure Vertex AI API is enabled
   ```

3. **Import Error**
   ```
   Solution: Install dependencies with 'pip install google-cloud-aiplatform'
   ```

4. **Permission Denied**
   ```
   Solution: Ensure your account has Vertex AI User role
   ```

## Cost Considerations

- Gemini models charge per token
- Pro models are more expensive but more capable
- Flash models are cheaper and faster
- Monitor usage in Google Cloud Console

## Integration Examples

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Analyze Test Failures
  if: failure()
  run: |
    python3 vertex_ai_test_analyzer.py \
      --project ${{ secrets.GCP_PROJECT_ID }} \
      test_failures.json analysis_results.json
    cat analysis_results.json
```

### Pytest Integration

```python
# Custom pytest plugin to generate failure JSON
def pytest_runtest_logreport(report):
    if report.failed:
        # Generate JSON format for vertex_ai_test_analyzer.py
        pass
```

## License

This tool is provided as-is for educational and development purposes.