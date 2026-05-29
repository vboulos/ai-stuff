# Jenkins/Kubernetes Setup Guide

## Your Current Configuration ✅

```yaml
resources:
  limits:
    cpu: "4"       # Good for Ollama
    memory: 8Gi    # Enough for llama3.2
  requests:
    cpu: "1"
    memory: 6Gi
```

**This is perfect for llama3.2!**

## Recommended Jenkins Pipeline

### Complete Pipeline Example

```groovy
pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: ollama
    image: ollama/ollama:latest
    command:
    - cat
    tty: true
    env:
      - name: HOME
        value: '/home/jenkins'
      - name: OLLAMA_HOST
        value: '0.0.0.0:11434'
      - name: OLLAMA_NUM_PARALLEL
        value: '2'
      - name: OLLAMA_MAX_LOADED_MODELS
        value: '1'
      - name: OLLAMA_KEEP_ALIVE
        value: '10m'
      - name: OLLAMA_NUM_THREAD
        value: '4'
    resources:
      limits:
        cpu: "4"
        memory: 8Gi
      requests:
        cpu: "1"
        memory: 6Gi
"""
        }
    }
    
    stages {
        stage('Setup Ollama') {
            steps {
                container('ollama') {
                    sh '''
                        echo "Starting Ollama..."
                        ollama serve &
                        sleep 3
                        
                        echo "Checking if Ollama is running..."
                        curl -s localhost:11434/api/tags || exit 1
                        
                        echo "Pulling llama3.2 model..."
                        ollama pull llama3.2
                        
                        echo "✅ Ollama setup complete"
                    '''
                }
            }
        }
        
        stage('Analyze Test Failures') {
            steps {
                container('ollama') {
                    sh '''
                        # Install Python dependencies
                        pip3 install ollama
                        
                        # Run analysis
                        python3 analyze_and_suggest_fixes.py \
                            tests_analysis/grc_failed_tests.json \
                            --model llama3.2 \
                            --output tests_analysis/analysis_and_fixes.json \
                            --yes \
                            --skip-verify
                    '''
                }
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'tests_analysis/analysis_and_fixes.json'
            }
        }
    }
}
```

## Quick Start Script

For your current setup, create this script in your Jenkins job:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "🔬 Test Failure Analysis Pipeline"
echo "=========================================="

# 1. Start Ollama
echo "🔌 Starting Ollama..."
ollama serve &
sleep 3

# 2. Verify Ollama is running
if ! curl -s localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama failed to start"
    exit 1
fi
echo "✅ Ollama is running"

# 3. Download model (only downloads if not present)
echo "📥 Ensuring llama3.2 is available..."
ollama pull llama3.2

# 4. Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install ollama

# 5. Run analysis
echo "🔬 Running test failure analysis..."
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify

echo ""
echo "=========================================="
echo "✅ Analysis Complete!"
echo "=========================================="
echo "Results saved to: tests_analysis/analysis_and_fixes.json"

# 6. Show summary
if [ -f tests_analysis/analysis_and_fixes.json ]; then
    echo ""
    echo "📊 Summary:"
    python3 -c "
import json
with open('tests_analysis/analysis_and_fixes.json') as f:
    data = json.load(f)
    meta = data.get('metadata', {})
    print(f\"  Total tests: {meta.get('total_tests', 'N/A')}\")
    print(f\"  Successful analyses: {meta.get('successful_analyses', 'N/A')}\")
    if 'fix_summary' in meta:
        fix = meta['fix_summary']
        print(f\"  Successful fixes: {fix.get('successful_fixes', 'N/A')}\")
    "
fi
```

## Environment Variables (Recommended)

Add these to your Kubernetes pod spec for optimal performance:

```yaml
env:
  - name: HOME
    value: '/home/jenkins'
  - name: OLLAMA_HOST
    value: '0.0.0.0:11434'
  
  # Performance optimizations
  - name: OLLAMA_NUM_PARALLEL
    value: '2'              # Run 2 parallel requests
  - name: OLLAMA_MAX_LOADED_MODELS
    value: '1'              # Keep only 1 model in memory
  - name: OLLAMA_KEEP_ALIVE
    value: '10m'            # Keep model loaded for 10 minutes
  - name: OLLAMA_NUM_THREAD
    value: '4'              # Use all 4 CPUs
```

## Model Recommendations by Memory

| Memory Available | Recommended Model | Size | Speed |
|-----------------|------------------|------|-------|
| 2-4 Gi | llama3.2 | 1.88 GB | ⚡ Fast |
| 5-8 Gi | llama3.2 or llama3.1 | 1.88 / 4.58 GB | ⚡⚡ Faster |
| 8+ Gi | llama3.1 | 4.58 GB | ⚡⚡⚡ Fastest |

**For your 8Gi setup: Use llama3.2** (most reliable, avoids memory pressure)

## Optimization Tips

### 1. Use --analyze-only for faster results (2x faster)
```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --analyze-only \
    --output analysis_only.json \
    --yes --skip-verify
```

### 2. Use --limit for testing
```bash
# Test with just 3 tests first
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --limit 3 \
    --output test_run.json \
    --yes --skip-verify
```

### 3. Increase timeout for slow environments
```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --timeout 120 \
    --yes --skip-verify
```

## Troubleshooting

### Issue: "model requires more system memory"
**Solution:** Use llama3.2 instead of llama3.1
```bash
--model llama3.2  # Uses ~2GB instead of ~5GB
```

### Issue: "EOFError: EOF when reading a line"
**Solution:** Add --yes flag
```bash
--yes --skip-verify  # Skip interactive prompts
```

### Issue: Script hangs/takes forever
**Solutions:**
1. Verify you're using llama3.2 (not llama3.1)
2. Use --limit to test with fewer tests first
3. Check Ollama is running: `curl localhost:11434/api/tags`
4. Increase timeout: `--timeout 120`

### Issue: Model download is slow
**Solution:** Pre-pull in Dockerfile or init container
```dockerfile
FROM ollama/ollama:latest
RUN ollama serve & sleep 3 && ollama pull llama3.2
```

## Expected Performance (10 tests)

| Configuration | Time | Speed |
|---------------|------|-------|
| llama3.2 (analysis + fixes) | ~2-3 min | Normal |
| llama3.2 (--analyze-only) | ~1 min | 2x faster ⚡ |
| llama3.1 (if memory allows) | ~30 sec | 4x faster ⚡⚡ |

## Monitoring Commands

```bash
# Check Ollama status
curl localhost:11434/api/tags

# Check available models
ollama list

# Monitor memory usage
free -h

# Test model quickly
python3 debug_ollama.py --model llama3.2 --num-tests 10
```

## Summary

✅ **Your setup is good!** Just use:

```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify
```

This should complete in **2-3 minutes** for 10 tests.
