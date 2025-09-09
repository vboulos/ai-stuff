# Vertex AI Test Failure Analyzer Setup

A Python tool that uses Anthropic models via Google Cloud Vertex AI to analyze test failures and classify them by type with fix suggestions and code fixes.

## 🚀 Quick Start

1. **Install dependencies**
2. **Set up Google Cloud authentication**
3. **Configure environment variables**
4. **Run analysis**

## 📋 Prerequisites

- Google Cloud Project with billing enabled
- Vertex AI API enabled
- Access to Anthropic models in Vertex AI
- Python 3.7+

## 🛠️ Detailed Setup

### 1. Install Dependencies

```bash
pip install anthropic
# or
pip install -r requirements_vertex.txt
```

### 2. Google Cloud Setup

**Install Google Cloud CLI:**
```bash
# macOS
brew install google-cloud-sdk

# Windows/Linux - download from:
# https://cloud.google.com/sdk/docs/install
```

**Authenticate:**
```bash
gcloud auth login
gcloud auth application-default login
```

**Set your project:**
```bash
gcloud config set project YOUR_PROJECT_ID
```

### 3. Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com
```

Or via Google Cloud Console:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Library
3. Search for "Vertex AI API"
4. Click Enable

### 4. Enable Anthropic Models

**Via Google Cloud Console:**
1. Go to Vertex AI > Model Garden
2. Search for "Claude" or "Anthropic"
3. Enable the models you want to use
4. Follow any additional setup instructions

**Available Models:**
- `claude-3-5-sonnet@20241022` (default)
- `claude-3-haiku@20240307`
- `claude-3-opus@20240229`

### 5. Set Environment Variables

```bash
export ANTHROPIC_VERTEX_PROJECT_ID=your-google-cloud-project-id
export ANTHROPIC_VERTEX_REGION=us-central1  # or your preferred region
```

**Permanent setup (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id' >> ~/.bashrc
echo 'export ANTHROPIC_VERTEX_REGION=us-central1' >> ~/.bashrc
source ~/.bashrc
```

### 6. Test Your Setup

```bash
python -c "
import anthropic
import os
client = anthropic.AnthropicVertex(
    project_id=os.getenv('ANTHROPIC_VERTEX_PROJECT_ID'),
    region=os.getenv('ANTHROPIC_VERTEX_REGION', 'us-central1')
)
print('✅ Vertex AI Anthropic client initialized successfully')
"
```

## 📁 Usage

### Simple Analysis

```bash
python run_vertex_ai_analysis.py
```

### Custom Analysis

```python
from vertex_ai_test_analyzer import VertexAITestFailureAnalyzer

# Initialize with custom settings
analyzer = VertexAITestFailureAnalyzer(
    project_id="your-project-id",
    region="us-central1",
    model_name="claude-3-5-sonnet@20241022"
)

# Run analysis
results = analyzer.analyze_failures("input.json", "output.json")
```

## 🌍 Supported Regions

Anthropic models are available in these Vertex AI regions:
- `us-central1` (Iowa) - **Recommended**
- `us-east5` (Columbus)
- `europe-west1` (Belgium)

Check current availability: [Vertex AI Locations](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/claude)

## 💰 Pricing

Vertex AI pricing for Anthropic models:
- **Input tokens**: ~$3.00 per 1M tokens
- **Output tokens**: ~$15.00 per 1M tokens

Estimate: ~$0.01-0.05 per test case analysis

## 🔧 Troubleshooting

### Common Issues

**❌ "Project not found" error:**
```bash
# Check your project ID
gcloud config get-value project
# Set correct project
gcloud config set project YOUR_CORRECT_PROJECT_ID
```

**❌ "Permission denied" error:**
```bash
# Check your authentication
gcloud auth list
# Re-authenticate if needed
gcloud auth application-default login
```

**❌ "Model not available" error:**
```bash
# Check if Vertex AI API is enabled
gcloud services list --enabled | grep aiplatform
# Enable if needed
gcloud services enable aiplatform.googleapis.com
```

**❌ "Anthropic models not found" error:**
1. Go to [Vertex AI Model Garden](https://console.cloud.google.com/vertex-ai/model-garden)
2. Search for "Claude" or "Anthropic"
3. Enable the models for your project
4. Wait a few minutes for activation

### Debug Your Setup

```bash
# Check environment variables
echo $ANTHROPIC_VERTEX_PROJECT_ID
echo $ANTHROPIC_VERTEX_REGION

# Test Google Cloud auth
gcloud auth application-default print-access-token

# List available models
gcloud ai models list --region=us-central1 --filter="displayName:claude"
```

## 🔒 Security Best Practices

1. **Use IAM roles**: Grant minimum required permissions
2. **Rotate credentials**: Regularly refresh authentication
3. **Monitor usage**: Track API calls and costs
4. **Secure env vars**: Don't commit credentials to code

**Recommended IAM roles:**
- `roles/aiplatform.user`
- `roles/ml.developer`

## 📊 Output Format

Same as other analyzers:

```json
[
  {
    "test_case_id": "TC001",
    "test_case_name": "test_user_login",
    "failure_message": "AssertionError: Expected 200, got 401",
    "failure_type": "automation_bug",
    "fix_suggestion": "The test is using incorrect credentials...",
    "fix_code": "response = client.post('/login', data={'username': 'valid_user'...})"
  }
]
```

## 🔄 Migration from Direct API

If migrating from direct Anthropic API:

**Before:**
```python
import anthropic
client = anthropic.Anthropic(api_key="sk-...")
```

**After:**
```python
import anthropic
client = anthropic.AnthropicVertex(
    project_id="your-project-id",
    region="us-central1"
)
```

## 📞 Support

- **Google Cloud Support**: [cloud.google.com/support](https://cloud.google.com/support)
- **Vertex AI Docs**: [cloud.google.com/vertex-ai/docs](https://cloud.google.com/vertex-ai/docs)
- **Anthropic Models**: [docs.anthropic.com](https://docs.anthropic.com)

## ✅ Quick Verification Checklist

- [ ] Google Cloud project created with billing enabled
- [ ] Vertex AI API enabled
- [ ] Google Cloud CLI installed and authenticated
- [ ] Environment variables set correctly
- [ ] Anthropic models enabled in Model Garden
- [ ] Test script runs without errors

You're ready to analyze test failures with Vertex AI! 🎉