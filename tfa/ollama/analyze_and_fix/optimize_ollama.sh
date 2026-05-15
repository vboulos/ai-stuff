#!/bin/bash
#
# Ollama Optimization Script for Kubernetes/CI
# Use this in your Jenkins pipeline before running analysis
#

set -e

echo "=========================================="
echo "🚀 Optimizing Ollama for CI/CD"
echo "=========================================="

# Set environment variables for optimal performance
export OLLAMA_NUM_PARALLEL=2        # Run 2 parallel requests (you have 4 CPUs)
export OLLAMA_MAX_LOADED_MODELS=1   # Keep only 1 model in memory at a time
export OLLAMA_KEEP_ALIVE=10m        # Keep model in memory for 10 minutes
export OLLAMA_NUM_THREAD=4          # Use all 4 CPUs

echo "✅ Environment variables set:"
echo "   OLLAMA_NUM_PARALLEL=$OLLAMA_NUM_PARALLEL"
echo "   OLLAMA_MAX_LOADED_MODELS=$OLLAMA_MAX_LOADED_MODELS"
echo "   OLLAMA_KEEP_ALIVE=$OLLAMA_KEEP_ALIVE"
echo "   OLLAMA_NUM_THREAD=$OLLAMA_NUM_THREAD"
echo ""

# Check system resources
echo "📊 System Resources:"
echo "   CPUs: $(nproc)"
echo "   Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "   Available Memory: $(free -h | grep Mem | awk '{print $7}')"
echo ""

# Start Ollama if not already running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🔌 Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama started (PID: $OLLAMA_PID)"
    else
        echo "❌ Failed to start Ollama"
        exit 1
    fi
else
    echo "✅ Ollama is already running"
fi

echo ""
echo "📦 Checking models..."
if ollama list | grep -q llama3.2; then
    echo "✅ llama3.2 is installed"
else
    echo "📥 Downloading llama3.2 (this will take a few minutes)..."
    ollama pull llama3.2
    echo "✅ llama3.2 downloaded"
fi

echo ""
echo "🧪 Testing model performance..."
python3 -c "
import ollama
import time

start = time.time()
response = ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Say OK'}],
    options={'num_predict': 5}
)
elapsed = time.time() - start
print(f'   Response time: {elapsed:.2f}s')
if elapsed < 5:
    print('   ✅ Performance is good')
elif elapsed < 15:
    print('   ⚠️  Performance is moderate')
else:
    print('   ❌ Performance is poor - check resources')
"

echo ""
echo "=========================================="
echo "✅ Ollama is ready!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  python3 analyze_and_suggest_fixes.py tests_analysis/grc_failed_tests.json \\"
echo "      --model llama3.2 \\"
echo "      --output tests_analysis/analysis_and_fixes.json \\"
echo "      --yes --skip-verify"
