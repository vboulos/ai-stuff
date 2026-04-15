# Setup Guide: Switching from Claude to Ollama

This guide explains how to set up and use Ollama for local test failure analysis and fix suggestions.

## Prerequisites

### 1. Install Ollama

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS (alternative with Homebrew):**
```bash
brew install ollama
```

**Windows:**
Download and install from [ollama.com/download](https://ollama.com/download)

### 2. Start Ollama Service

```bash
ollama serve
```

This will start the Ollama server on `http://localhost:11434`

### 3. Pull a Model

Choose one of these recommended models for code analysis:

**Llama 3.1 (recommended for general use):**
```bash
ollama pull llama3.1
```

**CodeLlama (optimized for code):**
```bash
ollama pull codellama
```

**Mistral (good balance of speed and quality):**
```bash
ollama pull mistral
```

**Llama 3.1 70B (best quality, requires more resources):**
```bash
ollama pull llama3.1:70b
```

To list all available models:
```bash
ollama list
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or install directly:
```bash
pip install ollama
```

## Usage

### Basic Usage

Use the default model (llama3.1):
```bash
python analyze_and_suggest_fixes.py test_failures.json
```

### Specify a Different Model

```bash
python analyze_and_suggest_fixes.py test_failures.json --model codellama
```

```bash
python analyze_and_suggest_fixes.py test_failures.json --model mistral
```

### Other Options

**Analysis only (skip fix suggestions):**
```bash
python analyze_and_suggest_fixes.py input.json --analysis-only
```

**Custom output file:**
```bash
python analyze_and_suggest_fixes.py input.json --output my_results.json
```

**Limit number of failures to process:**
```bash
python analyze_and_suggest_fixes.py input.json --max-failures 10
```

**Sequential processing (disable parallel):**
```bash
python analyze_and_suggest_fixes.py input.json --no-parallel
```

**Specify test framework:**
```bash
python analyze_and_suggest_fixes.py input.json --framework pytest
```

**Adjust timeout:**
```bash
python analyze_and_suggest_fixes.py input.json --timeout 180
```

**Create sample test file:**
```bash
python analyze_and_suggest_fixes.py --sample
```

## Model Recommendations

| Model | Speed | Quality | Use Case | Resource Usage |
|-------|-------|---------|----------|----------------|
| llama3.1 | Fast | Good | General purpose | ~4GB RAM |
| codellama | Fast | Very Good | Code-specific tasks | ~4GB RAM |
| mistral | Very Fast | Good | Quick analysis | ~4GB RAM |
| llama3.1:70b | Slow | Excellent | Critical analysis | ~40GB RAM |

## Troubleshooting

### "Connection refused" error

Make sure Ollama is running:
```bash
ollama serve
```

### Model not found

Pull the model first:
```bash
ollama pull llama3.1
```

### Out of memory errors

Try a smaller model:
```bash
python analyze_and_suggest_fixes.py input.json --model mistral
```

### Slow performance

- Use a smaller model (mistral)
- Reduce max_workers: `--max-workers 1`
- Process fewer failures: `--max-failures 5`

## Differences from Claude Version

| Feature | Claude CLI | Ollama |
|---------|-----------|--------|
| Location | Cloud-based | Local |
| Cost | Pay per use | Free |
| Privacy | Data sent to API | Fully local |
| Speed | Fast | Depends on hardware |
| Setup | CLI install | Install + model download |
| Internet | Required | Not required (after setup) |

## Advanced Configuration

### Custom Model Parameters

You can modify the temperature and other parameters in the source files:
- `analyze_failures.py` (line ~48)
- `fix_suggestor.py` (line ~51)

Example customization:
```python
response = ollama.chat(
    model=self.model,
    messages=[{'role': 'user', 'content': prompt}],
    options={
        'temperature': 0.1,    # Lower = more deterministic
        'top_p': 0.9,          # Nucleus sampling
        'top_k': 40,           # Top-k sampling
        'num_predict': 2048,   # Max tokens to generate
    }
)
```

### Using Custom/Fine-tuned Models

If you have a custom Ollama model:
```bash
python analyze_and_suggest_fixes.py input.json --model my-custom-model
```

## Performance Tips

1. **Keep Ollama running**: Don't restart between analyses
2. **Use SSD storage**: Model loading is much faster
3. **Allocate enough RAM**: 8GB+ recommended
4. **Close other applications**: Give Ollama maximum resources
5. **Use parallel processing**: Default max_workers=3 is good for most systems

## Next Steps

1. Verify Ollama is working:
   ```bash
   ollama run llama3.1 "Hello, how are you?"
   ```

2. Create a sample test file:
   ```bash
   python analyze_and_suggest_fixes.py --sample
   ```

3. Run your first analysis:
   ```bash
   python analyze_and_suggest_fixes.py sample_test_failures.json
   ```

## Support

For Ollama issues: https://github.com/ollama/ollama/issues
For script issues: Check the main README.md
