# Test Failure Analysis with Ollama

Automated test failure analysis and fix suggestions using local LLMs via Ollama.

## 🚀 Quick Start (TL;DR)

```bash
# 1. Start Ollama
ollama serve &

# 2. Install model
ollama pull llama3.2

# 3. Run analysis
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes \
    --skip-verify
```

**Expected time:** 2-3 minutes for 10 tests  
**Memory needed:** ~2 GB  

👉 **See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for more commands**

---

## 📋 What This Does

This tool analyzes test failures and provides:

1. **Root Cause Analysis** - Why did the test fail?
2. **Suggested Fixes** - How to fix it
3. **Code Examples** - Specific code changes needed
4. **Validation Steps** - How to verify the fix
5. **Priority & Effort** - How urgent and how much work

---

## 📚 Documentation

| Document | Description | When to Use |
|----------|-------------|-------------|
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Copy-paste commands | **Start here!** |
| **[USAGE.md](USAGE.md)** | Complete usage guide | Detailed examples |
| **[JENKINS_SETUP.md](JENKINS_SETUP.md)** | CI/CD setup | Jenkins/Kubernetes |
| **[RUNBOOK_USAGE.md](RUNBOOK_USAGE.md)** | Runbook (if exists) | Operational guide |

---

## 🎯 Common Use Cases

### For CI/CD (Jenkins, GitLab, GitHub Actions)
```bash
python3 analyze_and_suggest_fixes.py input.json \
    --model llama3.2 \
    --output results.json \
    --yes --skip-verify
```

### For Local Development
```bash
python3 analyze_and_suggest_fixes.py input.json \
    --model llama3.2 \
    --output results.json
```

### Quick Test (1 test only)
```bash
python3 analyze_and_suggest_fixes.py input.json \
    --model llama3.2 --limit 1 \
    --output test.json --yes --skip-verify
```

### Analysis Only (2x faster)
```bash
python3 analyze_and_suggest_fixes.py input.json \
    --model llama3.2 --analyze-only \
    --output analysis.json --yes --skip-verify
```

---

## 📦 Prerequisites

### 1. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Mac
brew install ollama

# Or download from https://ollama.com/download
```

### 2. Install Python Package
```bash
pip3 install ollama
```

### 3. Pull Model
```bash
ollama pull llama3.2
```

---

## 🔧 Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `analyze_and_suggest_fixes.py` | **Main script** - Full analysis + fixes | ⭐ Recommended |
| `analyze_failures.py` | Analysis only module | Can be imported |
| `fix_suggestor.py` | Fix suggestion module | Can be imported |
| `debug_ollama.py` | Diagnostic tool | Run first to test |
| `test_ollama.py` | Quick connection test | Troubleshooting |
| `optimize_ollama.sh` | Optimization script | CI/CD setup |

---

## 📊 Model Selection

| Model | Size | Memory | Speed | Best For |
|-------|------|--------|-------|----------|
| **llama3.2** ⭐ | 1.88 GB | ~2 GB | Medium | **CI/CD, Limited RAM** |
| llama3.1 | 4.58 GB | ~5 GB | Fast | Local, 8GB+ RAM |
| llama3 | 4.34 GB | ~5 GB | Medium | Alternative |

**Recommendation:** Use `llama3.2` for reliability and compatibility.

**Your Jenkins Setup (8Gi memory):** ✅ Use `llama3.2`

---

## 🛠️ Command-Line Options

```bash
python3 analyze_and_suggest_fixes.py INPUT_FILE [OPTIONS]

Required:
  INPUT_FILE              JSON file with test failures

Key Options:
  --model MODEL           Ollama model (default: llama3.1)
  --output FILE           Output file (default: analysis_and_fixes.json)
  --yes, -y              Skip prompts (for CI/CD)
  --skip-verify          Skip connection check
  --limit N              Process only N tests
  --analyze-only         Skip fix suggestions (2x faster)
  --timeout SECONDS      Timeout per API call (default: 60)
  --framework NAME       Test framework (pytest, jest, cypress)

See USAGE.md for all options
```

---

## 📥 Input Format

The script accepts JSON files in various formats:

### Simple Array
```json
[
  {
    "name": "test_login",
    "failure_message": "AssertionError: Expected 200, got 401",
    "framework": "pytest"
  }
]
```

### Nested Object
```json
{
  "tests": [
    {
      "test_name": "test_login",
      "error": "Timeout after 30s"
    }
  ]
}
```

See [USAGE.md](USAGE.md) for more examples.

---

## 📤 Output Format

```json
{
  "metadata": {
    "generated_at": "2026-04-15T10:30:00",
    "model": "llama3.2",
    "total_tests": 10,
    "successful_analyses": 9,
    "fix_summary": {
      "successful_fixes": 8,
      "fix_type_distribution": {...},
      "priority_distribution": {...}
    }
  },
  "results": [
    {
      "test_name": "test_login",
      "analysis": {
        "root_cause": "Authentication token validation failure",
        "suggested_fix": "Update token validation logic",
        "confidence_score": 0.85,
        "error_category": "authentication",
        "severity": "high"
      },
      "fix_suggestion": {
        "fix_type": "quick_fix",
        "priority": "high",
        "code_changes": "...",
        "validation_steps": [...]
      }
    }
  ]
}
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "model requires more system memory" | Use `--model llama3.2` |
| "EOFError: EOF when reading a line" | Add `--yes --skip-verify` |
| Takes forever / hangs | Use `--model llama3.2` (not llama3.1) |
| "model 'X' not found" | Run `ollama pull X` first |
| Connection refused | Start Ollama: `ollama serve &` |

### Diagnostic Steps

```bash
# 1. Check Ollama is running
curl localhost:11434/api/tags

# 2. List installed models
ollama list

# 3. Run diagnostics
python3 debug_ollama.py --model llama3.2 --num-tests 10

# 4. Test with 1 test
python3 analyze_and_suggest_fixes.py input.json --model llama3.2 --limit 1 --yes
```

---

## ⚡ Performance Tips

1. **Use llama3.2** - Most reliable for CI/CD environments
2. **Use --limit** - Test with fewer tests first (`--limit 3`)
3. **Use --analyze-only** - Skip fix suggestions (2x faster)
4. **Pre-pull models** - In Dockerfile or init stage
5. **Set environment variables** - See [JENKINS_SETUP.md](JENKINS_SETUP.md)

### Expected Performance (10 tests)

| Configuration | Time | Speed |
|---------------|------|-------|
| llama3.2 (full) | 2-3 min | Normal |
| llama3.2 (--analyze-only) | 1 min | 2x faster ⚡ |
| llama3.1 (if memory allows) | 30 sec | 4x faster ⚡⚡ |

---

## 🎓 Examples

### Example 1: CI/CD Pipeline (Jenkins)
```bash
#!/bin/bash
set -e

ollama serve &
sleep 3
ollama pull llama3.2

python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output results.json \
    --yes --skip-verify
```

### Example 2: Local Testing
```bash
# Test with 3 tests
python3 analyze_and_suggest_fixes.py \
    sample_failures.json \
    --model llama3.2 \
    --limit 3 \
    --output test_results.json
```

### Example 3: Quick Analysis Only
```bash
# Skip fix suggestions, just analyze
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --analyze-only \
    --output analysis_only.json \
    --yes --skip-verify
```

### Example 4: Kubernetes/Jenkins with 8Gi Memory
```bash
# Optimized for your setup
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUM_THREAD=4

python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes --skip-verify
```

---

## 🏗️ Architecture

```
analyze_and_suggest_fixes.py (Main CLI)
    ↓
    ├─→ analyze_failures.py (FailureAnalyzer class)
    │       ↓
    │       └─→ Ollama API → llama3.2 → Analysis
    │
    └─→ fix_suggestor.py (FixSuggestor class)
            ↓
            └─→ Ollama API → llama3.2 → Fix Suggestions
```

---

## 🎯 Error Categories

Errors are categorized as:

- **timeout** - Test execution timeouts
- **assertion** - Assertion failures
- **network** - Network connectivity issues
- **configuration** - Configuration problems
- **dependency** - Missing dependencies
- **ui_interaction** - UI element failures
- **database** - Database issues
- **authentication** - Auth failures

---

## 🏷️ Fix Types

Fixes are classified as:

- **quick_fix** - Simple changes (minutes)
- **refactor** - Code restructuring (hours)
- **configuration** - Config changes (minutes)
- **dependency** - Package updates (minutes)
- **infrastructure** - Environment setup (hours/days)
- **test_update** - Test improvements (minutes/hours)

---

## 📦 Requirements

```
Python 3.7+
ollama (pip package)
Ollama service running
```

Install requirements:
```bash
pip3 install ollama
# or
pip3 install -r requirements.txt
```

---

## 🤝 CI/CD Integration

### Jenkins (Kubernetes)

See [JENKINS_SETUP.md](JENKINS_SETUP.md) for complete setup.

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

### GitLab CI
```yaml
test-analysis:
  script:
    - ollama serve &
    - sleep 3
    - ollama pull llama3.2
    - python3 analyze_and_suggest_fixes.py input.json --model llama3.2 --yes --skip-verify
  artifacts:
    paths:
      - analysis_and_fixes.json
```

### GitHub Actions
```yaml
- name: Analyze Test Failures
  run: |
    ollama serve &
    sleep 3
    ollama pull llama3.2
    python3 analyze_and_suggest_fixes.py input.json --model llama3.2 --yes --skip-verify
```

---

## ✅ Success Checklist

Before running in production:

- [ ] Ollama is installed (`which ollama`)
- [ ] Ollama is running (`curl localhost:11434/api/tags`)
- [ ] llama3.2 is pulled (`ollama list | grep llama3.2`)
- [ ] Diagnostics pass (`python3 debug_ollama.py --model llama3.2`)
- [ ] Test run with --limit 1 works
- [ ] CI/CD pipeline includes `--yes --skip-verify`

---

## 📞 Support

- 📖 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
- 📖 [USAGE.md](USAGE.md) - Detailed examples
- 📖 [JENKINS_SETUP.md](JENKINS_SETUP.md) - CI/CD setup
- 🔍 `python3 debug_ollama.py` - Diagnostics

---

## 📄 License

MIT License (or your license here)

---

**Ready to go?** 🚀

```bash
python3 analyze_and_suggest_fixes.py \
    tests_analysis/grc_failed_tests.json \
    --model llama3.2 \
    --output tests_analysis/analysis_and_fixes.json \
    --yes --skip-verify
```

For more commands, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md)!
