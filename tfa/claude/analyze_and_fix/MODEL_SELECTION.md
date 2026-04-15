# Model Selection Guide

This guide shows you how to use any Ollama model with the test failure analyzer.

## Quick Start

### List Available Models

```bash
# See what models you have installed
python3 analyze_and_suggest_fixes.py --list-models

# Or use Ollama directly
ollama list
```

### Use Any Model

```bash
# Use the default model (llama3.1)
python3 analyze_and_suggest_fixes.py test_failures.json

# Use a specific model with --model or -m
python3 analyze_and_suggest_fixes.py test_failures.json --model mistral
python3 analyze_and_suggest_fixes.py test_failures.json -m codellama
python3 analyze_and_suggest_fixes.py test_failures.json -m qwen2.5-coder:7b
```

## Recommended Models for Code Analysis

### General Purpose Models

| Model | Pull Command | Size | Best For |
|-------|-------------|------|----------|
| **llama3.1** (default) | `ollama pull llama3.1` | 4.9GB | Balanced quality and speed |
| **llama3.1:70b** | `ollama pull llama3.1:70b` | 40GB | Best quality (needs powerful machine) |
| **mistral** | `ollama pull mistral` | 4.1GB | Fast and efficient |
| **mixtral** | `ollama pull mixtral` | 26GB | High quality, good reasoning |

### Code-Specific Models

| Model | Pull Command | Size | Best For |
|-------|-------------|------|----------|
| **codellama** | `ollama pull codellama` | 3.8GB | General code analysis |
| **codellama:13b** | `ollama pull codellama:13b` | 7.3GB | Better code understanding |
| **codellama:70b** | `ollama pull codellama:70b` | 39GB | Best code analysis |
| **qwen2.5-coder:7b** | `ollama pull qwen2.5-coder:7b` | 4.7GB | Excellent for debugging |
| **qwen2.5-coder:32b** | `ollama pull qwen2.5-coder:32b` | 19GB | Superior code reasoning |
| **deepseek-coder-v2** | `ollama pull deepseek-coder-v2` | 8.9GB | Strong code understanding |

### Lightweight/Fast Models

| Model | Pull Command | Size | Best For |
|-------|-------------|------|----------|
| **mistral:7b** | `ollama pull mistral:7b` | 4.1GB | Quick analysis |
| **phi3** | `ollama pull phi3` | 2.3GB | Very fast, lower quality |
| **llama3.2:3b** | `ollama pull llama3.2:3b` | 2.0GB | Lightweight option |

## Usage Examples

### Basic Usage with Different Models

```bash
# Llama 3.1 (default, good balance)
python3 analyze_and_suggest_fixes.py test_failures.json

# CodeLlama (optimized for code)
python3 analyze_and_suggest_fixes.py test_failures.json --model codellama

# Qwen Coder (excellent for debugging)
python3 analyze_and_suggest_fixes.py test_failures.json --model qwen2.5-coder:7b

# Mistral (faster, still good quality)
python3 analyze_and_suggest_fixes.py test_failures.json --model mistral

# Mixtral (high quality)
python3 analyze_and_suggest_fixes.py test_failures.json --model mixtral
```

### With Specific Model Tags

```bash
# Use specific version tags
python3 analyze_and_suggest_fixes.py test_failures.json -m llama3.1:latest
python3 analyze_and_suggest_fixes.py test_failures.json -m codellama:13b
python3 analyze_and_suggest_fixes.py test_failures.json -m qwen2.5-coder:32b
```

### Combined Options

```bash
# Use CodeLlama with analysis only (no fixes)
python3 analyze_and_suggest_fixes.py test_failures.json \
  --model codellama \
  --analysis-only

# Use Qwen Coder with limited failures and custom output
python3 analyze_and_suggest_fixes.py test_failures.json \
  --model qwen2.5-coder:7b \
  --max-failures 10 \
  --output results.json

# Use Mistral with sequential processing (slower but less resource intensive)
python3 analyze_and_suggest_fixes.py test_failures.json \
  --model mistral \
  --no-parallel \
  --max-workers 1
```

## Pulling New Models

### Pull Before Using

```bash
# Pull a model before using it
ollama pull qwen2.5-coder:7b

# Then use it
python3 analyze_and_suggest_fixes.py test_failures.json --model qwen2.5-coder:7b
```

### Auto-Continue Option

If you try to use a model that isn't installed, the script will:
1. Warn you that the model isn't found
2. Show you the pull command
3. List available models
4. Ask if you want to continue anyway

```bash
# Example: trying to use a model that isn't installed
$ python3 analyze_and_suggest_fixes.py test_failures.json --model codellama

⚠️  Warning: Model 'codellama' not found locally.
📥 Pull it first: ollama pull codellama

📦 Available Ollama Models:
============================================================
  • llama3.1:latest          (4.9 GB)
  • mistral:latest           (4.1 GB)
============================================================

Continue anyway? (y/N):
```

## Model Selection Tips

### Choose Based On Your Needs

**Speed Priority:**
- Use: `mistral`, `phi3`, or `llama3.2:3b`
- Best when: Processing many failures quickly

**Quality Priority:**
- Use: `llama3.1:70b`, `codellama:70b`, or `qwen2.5-coder:32b`
- Best when: Critical issues need careful analysis

**Code Specialization:**
- Use: `codellama`, `qwen2.5-coder`, or `deepseek-coder-v2`
- Best when: Analyzing programming errors

**Balanced:**
- Use: `llama3.1` (default), `codellama`, or `qwen2.5-coder:7b`
- Best when: Good mix of speed and quality

### Resource Considerations

| RAM Available | Recommended Models |
|---------------|-------------------|
| 8GB | phi3, llama3.2:3b, mistral |
| 16GB | llama3.1, codellama, qwen2.5-coder:7b, mistral |
| 32GB | codellama:13b, qwen2.5-coder:32b, mixtral |
| 64GB+ | llama3.1:70b, codellama:70b |

## Testing Different Models

Create a test script to compare models:

```bash
#!/bin/bash
# test_models.sh - Compare different models

MODELS=("llama3.1" "codellama" "qwen2.5-coder:7b" "mistral")
INPUT="test_failures.json"

for model in "${MODELS[@]}"; do
    echo "Testing model: $model"
    time python3 analyze_and_suggest_fixes.py "$INPUT" \
        --model "$model" \
        --max-failures 3 \
        --output "results_${model//:/_}.json"
    echo "---"
done
```

## Custom/Fine-tuned Models

You can use ANY Ollama model, including custom ones:

```bash
# Use a custom model you've imported
python3 analyze_and_suggest_fixes.py test_failures.json --model my-custom-model

# Use a quantized version
python3 analyze_and_suggest_fixes.py test_failures.json --model llama3.1:8b-q4_0
```

## Environment Variable (Alternative)

You can also set a default model via environment variable:

```bash
# In your .bashrc or .zshrc
export OLLAMA_MODEL=qwen2.5-coder:7b

# Then modify the script default or use it in your wrapper
python3 analyze_and_suggest_fixes.py test_failures.json
```

## Troubleshooting

### Model Not Found

```bash
# List what you have
ollama list

# Pull the model
ollama pull <model-name>

# Verify it's available
python3 analyze_and_suggest_fixes.py --list-models
```

### Out of Memory

```bash
# Use a smaller model
python3 analyze_and_suggest_fixes.py test_failures.json --model mistral

# Or reduce parallelism
python3 analyze_and_suggest_fixes.py test_failures.json --max-workers 1
```

### Slow Performance

```bash
# Use a faster model
python3 analyze_and_suggest_fixes.py test_failures.json --model mistral

# Or process fewer at once
python3 analyze_and_suggest_fixes.py test_failures.json --max-failures 5
```

## Model Performance Comparison

Based on typical test failure analysis:

| Model | Speed | Quality | Code Understanding | Memory |
|-------|-------|---------|-------------------|--------|
| llama3.1 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 5GB |
| codellama | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 4GB |
| qwen2.5-coder:7b | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 5GB |
| mistral | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 4GB |
| llama3.1:70b | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 40GB |
| phi3 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 2GB |

## Recommended Starting Points

**First Time User:**
```bash
ollama pull llama3.1
python3 analyze_and_suggest_fixes.py test_failures.json
```

**Code-Focused Analysis:**
```bash
ollama pull qwen2.5-coder:7b
python3 analyze_and_suggest_fixes.py test_failures.json --model qwen2.5-coder:7b
```

**Limited Resources:**
```bash
ollama pull mistral
python3 analyze_and_suggest_fixes.py test_failures.json --model mistral --no-parallel
```

**Best Quality (if you have resources):**
```bash
ollama pull llama3.1:70b
python3 analyze_and_suggest_fixes.py test_failures.json --model llama3.1:70b --max-workers 1
```
