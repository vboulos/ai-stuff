# Quick Reference Card

## ✅ The Command That Works (Copy & Paste)

```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify
```

**Time:** ~2-3 minutes for 10 tests
**Memory:** ~2 GB

---

## 🚀 Common Commands

### Test with 1 test first (recommended)
```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 --limit 1 \
    --output test_run.json --yes --skip-verify
```
**Time:** ~15 seconds

### Analysis only (2x faster, no fix suggestions)
```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 --analyze-only \
    --output analysis_only.json --yes --skip-verify
```
**Time:** ~1 minute for 10 tests

### Interactive mode (local development)
```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output analysis_and_fixes.json
```
**Time:** ~2-3 minutes (with prompts)

---

## 🛠️ Diagnostic Commands

### Check if Ollama is running
```bash
curl localhost:11434/api/tags
```

### List installed models
```bash
ollama list
```

### Test model performance
```bash
python3 debug_ollama.py --model llama3.2 --num-tests 10
```

### Quick model test
```bash
python3 -c "import ollama; print(ollama.chat(model='llama3.2', messages=[{'role':'user','content':'Say OK'}])['message']['content'])"
```

---

## 📦 Model Management

### Install llama3.2 (if not installed)
```bash
ollama pull llama3.2
```

### Check model size
```bash
ollama list | grep llama3.2
```

### Remove a model (free up space)
```bash
ollama rm llama3.1
```

---

## ⚙️ All Command-Line Options

```bash
python3 analyze_and_suggest_fixes.py INPUT_FILE [OPTIONS]

Required:
  INPUT_FILE              Path to JSON file with test failures

Model Options:
  --model MODEL           Ollama model (default: llama3.1)
                         Recommended: llama3.2 for CI/CD

Output Options:
  --output FILE           Output JSON file (default: analysis_and_fixes.json)

Analysis Options:
  --framework FRAMEWORK   Test framework (pytest, jest, etc.)
  --analyze-only         Only analyze, skip fix suggestions (2x faster)
  --limit N              Process only first N tests

CI/CD Options:
  --yes, -y              Skip confirmation prompts
  --skip-verify          Skip Ollama connection check
  --timeout SECONDS      Timeout per call (default: 60)

Other:
  --verbose              Show detailed progress
  --help                 Show full help
```

---

## 🔥 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "model requires more system memory" | Use `--model llama3.2` |
| "EOFError: EOF when reading a line" | Add `--yes --skip-verify` |
| Takes forever / hangs | Use `--model llama3.2` (not llama3.1) |
| "model 'X' not found" | Run `ollama pull X` first |
| Connection refused | Start Ollama: `ollama serve &` |

---

## 📊 Performance Comparison

| Model | Size | Memory | Time (10 tests) | Best For |
|-------|------|--------|----------------|----------|
| llama3.2 | 1.88 GB | ~2 GB | 2-3 min | **CI/CD** ✅ |
| llama3.1 | 4.58 GB | ~5 GB | 30 sec | Local with 8GB+ RAM |
| llama3 | 4.34 GB | ~5 GB | 45 sec | Alternative |

**Recommendation for your Jenkins (8Gi memory):** Use **llama3.2**

---

## 📁 Input File Format Examples

### Format 1: Simple array
```json
[
  {
    "name": "test_login",
    "failure_message": "AssertionError: Expected 200, got 401"
  }
]
```

### Format 2: Nested object
```json
{
  "tests": [
    {
      "test_name": "test_login",
      "error": "Timeout"
    }
  ]
}
```

---

## 🎯 Jenkins Pipeline Snippet

```groovy
stage('Analyze Failures') {
    steps {
        sh '''
            ollama serve &
            sleep 3
            ollama pull llama3.2
            
            python3 analyze_and_suggest_fixes.py \
                tests_analysis/grc_failed_tests.json \
                --model llama3.2 \
                --output tests_analysis/results.json \
                --yes --skip-verify
        '''
        archiveArtifacts 'tests_analysis/results.json'
    }
}
```

---

## 💡 Pro Tips

1. **Always test with --limit 1 first** to verify setup
2. **Use llama3.2 in CI/CD** (most reliable, lowest memory)
3. **Add --yes --skip-verify** for non-interactive environments
4. **Use --analyze-only** if you only need root cause analysis
5. **Pre-pull models** in your Dockerfile to save time

---

## 📞 Need Help?

1. Run diagnostics: `python3 debug_ollama.py --model llama3.2`
2. Check `USAGE.md` for detailed examples
3. Check `JENKINS_SETUP.md` for CI/CD configuration
4. Read logs carefully - errors are usually descriptive

---

## ✅ Success Checklist

- [ ] Ollama is running (`curl localhost:11434/api/tags`)
- [ ] llama3.2 is installed (`ollama list | grep llama3.2`)
- [ ] Model responds quickly (`python3 debug_ollama.py --model llama3.2`)
- [ ] Test with 1 test works (`--limit 1`)
- [ ] Full run completes in ~2-3 minutes

If all checked ✅, you're good to go! 🚀
