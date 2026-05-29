# Docker Quick Start Guide

This guide shows you how to build and use the RHEL9 container with Ollama for test failure analysis.

## Prerequisites

- Docker installed and running
- At least 8GB of available RAM (16GB recommended)
- 10GB of free disk space

## Quick Start

### Option 1: Automated Build and Run

```bash
# Make the script executable
chmod +x build-and-run.sh

# Build, run, and pull the default model (llama3.1)
./build-and-run.sh

# Or specify a different model
./build-and-run.sh codellama
./build-and-run.sh mistral
```

### Option 2: Manual Steps

#### 1. Build the Docker Image

```bash
docker build -t rhel9-ollama-analyzer .
```

#### 2. Run the Container

```bash
docker run -d \
  --name test-analyzer \
  -v $(pwd):/app \
  -p 11434:11434 \
  rhel9-ollama-analyzer
```

#### 3. Pull an Ollama Model

```bash
# Pull llama3.1 (recommended)
docker exec test-analyzer ollama pull llama3.1

# Or pull a different model
docker exec test-analyzer ollama pull codellama
docker exec test-analyzer ollama pull mistral
```

#### 4. Verify Installation

```bash
# Check Ollama is running
docker exec test-analyzer curl http://localhost:11434/api/tags

# List available models
docker exec test-analyzer ollama list

# Test the model interactively
docker exec -it test-analyzer ollama run llama3.1 "Hello, how are you?"
```

## Usage

### Create Sample Test Failures

```bash
docker exec test-analyzer python3 analyze_and_suggest_fixes.py --sample
```

### Run Analysis

```bash
# Basic analysis
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  sample_test_failures.json

# With specific model
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  sample_test_failures.json --model codellama

# Analysis only (no fix suggestions)
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  sample_test_failures.json --analysis-only

# Limit number of failures
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  sample_test_failures.json --max-failures 5
```

### Access the Container

```bash
# Interactive shell
docker exec -it test-analyzer bash

# Once inside, you can run commands directly:
python3 analyze_and_suggest_fixes.py --help
ollama list
ollama run llama3.1 "Explain this error: AssertionError"
```

### View Results

```bash
# View the generated analysis
docker exec test-analyzer cat comprehensive_analysis.json

# Copy results to your host
docker cp test-analyzer:/app/comprehensive_analysis.json ./results.json
```

## Using Your Own Test Data

### Method 1: Volume Mount (Already Configured)

The current directory is mounted to `/app` in the container, so any files you have locally are available:

```bash
# If you have test_failures.json in the current directory
docker exec test-analyzer python3 analyze_and_suggest_fixes.py test_failures.json
```

### Method 2: Copy Files into Container

```bash
# Copy your test file
docker cp my_test_failures.json test-analyzer:/app/

# Run analysis
docker exec test-analyzer python3 analyze_and_suggest_fixes.py my_test_failures.json
```

## Available Models

| Model | Size | Speed | Quality | RAM Required |
|-------|------|-------|---------|--------------|
| mistral | 7B | Fast | Good | 4GB |
| llama3.1 | 8B | Medium | Very Good | 5GB |
| codellama | 7B | Medium | Very Good (Code) | 4GB |
| llama3.1:70b | 70B | Slow | Excellent | 40GB |

To pull a model:
```bash
docker exec test-analyzer ollama pull <model-name>
```

## Container Management

### Check Status

```bash
# Container status
docker ps -a | grep test-analyzer

# View logs
docker logs test-analyzer

# View Ollama processes
docker exec test-analyzer ps aux | grep ollama
```

### Stop and Start

```bash
# Stop the container
docker stop test-analyzer

# Start the container
docker start test-analyzer

# Restart the container
docker restart test-analyzer
```

### Clean Up

```bash
# Stop and remove container
docker stop test-analyzer
docker rm test-analyzer

# Remove image (optional)
docker rmi rhel9-ollama-analyzer

# Remove all (container + image)
docker stop test-analyzer && docker rm test-analyzer && docker rmi rhel9-ollama-analyzer
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs test-analyzer

# Check if port 11434 is already in use
lsof -i :11434  # macOS/Linux
netstat -ano | findstr :11434  # Windows

# Use a different port
docker run -d --name test-analyzer -v $(pwd):/app -p 12434:11434 rhel9-ollama-analyzer
```

### Ollama Not Responding

```bash
# Check if Ollama is running
docker exec test-analyzer ps aux | grep ollama

# Restart Ollama inside container
docker exec test-analyzer bash -c "pkill ollama && ollama serve &"

# Or restart the entire container
docker restart test-analyzer
```

### Model Download Fails

```bash
# Check internet connectivity
docker exec test-analyzer ping -c 3 ollama.com

# Try pulling again
docker exec test-analyzer ollama pull llama3.1

# Check disk space
docker exec test-analyzer df -h
```

### Out of Memory

```bash
# Use a smaller model
docker exec test-analyzer ollama pull mistral

# Or limit parallel processing
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  input.json --max-workers 1 --no-parallel
```

### Python Module Not Found

```bash
# Install missing module
docker exec test-analyzer pip3 install ollama

# Or rebuild the image
docker build --no-cache -t rhel9-ollama-analyzer .
```

## Advanced Usage

### Run Analysis and Exit

For CI/CD pipelines or one-off analysis:

```bash
docker run --rm \
  -v $(pwd):/app \
  rhel9-ollama-analyzer \
  bash -c "ollama serve & sleep 10 && ollama pull llama3.1 && \
  python3 analyze_and_suggest_fixes.py test_failures.json"
```

### Custom Entrypoint

```bash
# Run with custom command
docker run -d \
  --name test-analyzer \
  -v $(pwd):/app \
  -p 11434:11434 \
  rhel9-ollama-analyzer \
  python3 -m http.server 8000
```

### Access Ollama from Host

While the container is running:

```bash
# Test from your host machine
curl http://localhost:11434/api/tags

# Use Python from host (if you have ollama module installed)
export OLLAMA_HOST=http://localhost:11434
python3 analyze_and_suggest_fixes.py test_failures.json
```

## Performance Tips

1. **First run is slow**: Model download and first inference take time
2. **Keep container running**: Avoid restarting to keep models loaded in memory
3. **Use appropriate model**: Start with smaller models (mistral, llama3.1)
4. **Monitor resources**: `docker stats test-analyzer`
5. **Persistent storage**: Models are stored in the container, will be lost if container is removed

## Example: Complete Workflow

```bash
# 1. Build and start
chmod +x build-and-run.sh
./build-and-run.sh llama3.1

# 2. Create sample data
docker exec test-analyzer python3 analyze_and_suggest_fixes.py --sample

# 3. Run analysis
docker exec test-analyzer python3 analyze_and_suggest_fixes.py \
  sample_test_failures.json --model llama3.1

# 4. View results
docker exec test-analyzer cat comprehensive_analysis.json | jq .

# 5. Copy results to host
docker cp test-analyzer:/app/comprehensive_analysis.json ./

# 6. Clean up when done
docker stop test-analyzer
docker rm test-analyzer
```

## Next Steps

- See `SETUP_OLLAMA.md` for detailed Ollama usage
- See `README.md` for script options and features
- Experiment with different models to find the best balance of speed and quality
