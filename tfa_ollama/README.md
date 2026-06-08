# Test Failure Analysis with AI, Source Code Integration, and Memory Learning

This implementation provides enhanced AI-powered test failure analysis based on the `analyze-test-failures` skill. It supports multiple AI providers, includes **source code scanning** for more accurate analysis, and features a **memory system** that learns from past failures to provide increasingly better solutions over time.

## Features

- **🧠 Memory Learning System**: Learns from past failures and solutions to provide better analysis over time
- **📝 Source Code Analysis**: Scans actual test files and matches failures to source code for precise fix suggestions
- **🔍 Similar Failure Detection**: Automatically finds and references similar past failures in analysis
- **📚 Knowledge Accumulation**: Stores successful analyses and allows QE review feedback
- **🤖 Multi-AI Support**: Works with Ollama (local), OpenAI, Claude, or any custom REST API
- **🧪 Test Framework Support**: Supports Python (pytest/unittest), JavaScript/TypeScript (Jest/Mocha/Cypress), Java (JUnit), and more
- **🔗 Jenkins Integration**: Fetches test results and build information from Jenkins
- **🎯 Intelligent Matching**: Fuzzy matching between test names and source code methods
- **📊 Structured Analysis**: Generates detailed JSON reports with line-specific fix suggestions
- **🚀 CI/CD Ready**: Includes Jenkinsfile for automated analysis
- **🏷️ Categorized Failures**: Classifies failures as automation bugs, infrastructure issues, product issues, or environment problems
- **📋 Skill-Based Prompts**: Uses the analyze-test-failures.md skill specification to generate consistent, structured AI prompts

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Settings

Copy and edit the configuration template:

```bash
cp config.json.template config.json
```

Edit `config.json` with your Jenkins, AI provider, test source, and memory settings:

```json
{
  "jenkins": {
    "url": "https://your-jenkins-server.com",
    "user": "your-username", 
    "token": "your-api-token"
  },
  "ai": {
    "provider": "ollama",
    "model": "llama3.2"
  },
  "test_source": {
    "directories": [
      "./tests",
      "./cypress/tests",
      "./src/test",
      "./test"
    ]
  },
  "memory": {
    "use_mem0": false,
    "backend": "local",
    "storage_path": "failure_memory.json",
    "feedback_path": "qe_feedback.json"
  }
}
```

### 3. Run Analysis

```bash
# Jenkins mode with memory and source code analysis
python3 analyze_test_failures.py jenkins "CI-jobs/search_tests" 123 --config config.json --test-dirs ./tests

# Local mode with memory enabled
python3 analyze_test_failures.py local ./target/surefire-reports/*.xml --config config-local.json --memory-backend local

# Local mode with source code and mem0 backend
python3 analyze_test_failures.py local ./results ./build/test-results --test-dirs ./tests ./src/test --memory-backend mem0

# Disable memory for one-off analysis
python3 analyze_test_failures.py local ./junit-reports/*.xml --disable-memory

# Legacy mode (backwards compatible)
python3 analyze_test_failures.py "CI-jobs/tests" 456 --test-dirs ./tests ./cypress/tests
python3 analyze_test_failures.py --xml-files ./junit-reports/*.xml --config config-local.json
```

## Analysis Modes

The tool supports two analysis modes:

### 🔗 Jenkins Mode
Analyze test failures from a remote Jenkins build by connecting to Jenkins API.

**Requirements:**
- Jenkins server access with API token
- Build must have test results published

**Usage:**
```bash
# Standard Jenkins analysis
python3 analyze_test_failures.py jenkins "CI-jobs/ui_tests" 456

# With custom config
python3 analyze_test_failures.py jenkins "qe-automation/api_tests" 789 --config jenkins-config.json
```

### 📁 Local Mode
Analyze test failures from local JUnit XML files without requiring Jenkins access.

**Requirements:**
- JUnit XML files (from Maven Surefire, Gradle, pytest-junit, Jest, etc.)
- No Jenkins connection needed

**Usage:**
```bash
# Analyze specific XML files
python3 analyze_test_failures.py local ./target/surefire-reports/TEST-*.xml

# Analyze all XML files in directories
python3 analyze_test_failures.py local ./build/test-results ./reports

# With source code analysis
python3 analyze_test_failures.py local ./results/*.xml --test-dirs ./src/test ./tests
```

**Supported XML Sources:**
- Maven Surefire Reports (`target/surefire-reports/`)
- Gradle Test Results (`build/test-results/`)
- pytest JUnit XML (`--junit-xml=results.xml`)
- Jest XML Reports (`jest-junit` plugin)
- Cypress XML Reports
- Any standard JUnit XML format

## Memory Learning System

The tool includes a sophisticated memory system that learns from past failure analyses to provide increasingly better solutions over time.

### 🧠 **How Memory Works**

1. **Automatic Learning**: Each successful analysis is automatically stored in memory
2. **Similarity Detection**: When analyzing new failures, the system searches for similar past cases
3. **Enhanced Prompts**: Similar failures and their solutions are included in AI analysis prompts
4. **Continuous Improvement**: The system gets smarter with each analysis

### 🔍 **Similar Failure Detection**

The memory system uses intelligent similarity scoring based on:
- **Test name patterns** (weighted 30%)
- **Failure message content** (weighted 40%) 
- **Test framework** (weighted 15%)
- **Error category** (weighted 15%)

### 📚 **Memory Backends**

#### Local JSON Storage (Default)
- Stores memories in local `failure_memory.json` file
- No external dependencies
- Portable across environments
- Suitable for individual developers or small teams

```json
{
  "memory": {
    "use_mem0": false,
    "backend": "local",
    "storage_path": "failure_memory.json",
    "feedback_path": "qe_feedback.json"
  }
}
```

#### Mem0 Integration (Advanced)
- Uses [mem0](https://github.com/mem0ai/mem0) for advanced vector-based memory
- Better similarity detection with embeddings
- Scalable for large teams
- Requires `pip install mem0`

```json
{
  "memory": {
    "use_mem0": true,
    "backend": "mem0",
    "mem0_config": {
      "vector_store": {
        "provider": "qdrant",
        "config": {
          "host": "localhost",
          "port": 6333
        }
      }
    }
  }
}
```

### 🎯 **Memory Usage Examples**

```bash
# Use local memory (default)
python3 analyze_test_failures.py local ./test-results/*.xml --memory-backend local

# Use mem0 for advanced similarity detection
python3 analyze_test_failures.py local ./test-results/*.xml --memory-backend mem0

# Disable memory for one-time analysis
python3 analyze_test_failures.py local ./test-results/*.xml --disable-memory

# Memory works with all other features
python3 analyze_test_failures.py jenkins "CI/tests" 123 --test-dirs ./tests --memory-backend local
```

### 📊 **QE Review & Feedback**

Quality Engineers can provide feedback on analysis quality:

```python
from analyze_test_failures import TestFailureAnalyzer

analyzer = TestFailureAnalyzer(config)

# Store QE feedback for a memory item
feedback = {
    "accuracy": "high",
    "usefulness": "very_useful",
    "comments": "Solution worked perfectly, saved 2 hours of debugging",
    "reviewer": "qe-team@example.com"
}

success = analyzer.store_qe_feedback(memory_id="abc123", feedback=feedback)
```

### 🔄 **Memory Workflow Example**

1. **First Analysis**: 
   ```bash
   python3 analyze_test_failures.py local ./results.xml --test-dirs ./tests
   ```
   - New login timeout failure analyzed
   - Solution: increase wait time from 5s to 15s
   - Analysis stored in memory

2. **Similar Failure Later**:
   ```bash
   python3 analyze_test_failures.py local ./new-results.xml --test-dirs ./tests  
   ```
   - Another login timeout detected
   - Memory search finds previous similar case
   - AI gets historical context: "Previous timeout fixed by increasing wait time"
   - Better, more consistent solution provided

3. **Memory Statistics**:
   ```
   === MEMORY STATISTICS ===
   Backend: local
   Total Stored Memories: 45
   Categories: {'automation': 32, 'infrastructure': 8, 'environment': 5}
   Frameworks: {'cypress': 20, 'pytest': 15, 'jest': 10}
   ```

## Skill-Based Prompting

The tool uses the `skills/analyze-test-failures.md` specification to generate AI prompts automatically. This ensures consistent, structured analysis regardless of which AI provider you use.

### 🎯 **How It Works**

1. **Skill File Loading**: Automatically loads the skill specification from `skills/analyze-test-failures.md`
2. **Dynamic Prompt Generation**: Extracts key sections like overview, core features, and failure categories
3. **Schema Validation**: Uses the JSON schema from the skill file to structure AI responses
4. **Consistent Analysis**: Ensures all AI providers follow the same analysis framework

### 📝 **Customizing Skills**

You can customize the analysis by modifying the skill file or using a custom one:

```bash
# Use custom skill file
python3 analyze_test_failures.py local ./results/*.xml --skill-file ./my-custom-skill.md

# Configure in config file
{
  "skill": {
    "file_path": "./custom-skills/enhanced-analysis.md"
  }
}
```

### 🔧 **Benefits**

- **Consistency**: Same analysis quality across different AI providers
- **Maintainability**: Update prompts by editing the skill file, not code
- **Customization**: Adapt analysis focus for different projects or teams
- **Documentation**: Skill file serves as living documentation of the analysis process

## AI Provider Setup

### Ollama (Local AI)

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama service: `ollama serve`
4. Use config:
```json
{
  "ai": {
    "provider": "ollama",
    "model": "llama3.2"
  }
}
```

### OpenAI

1. Get API key from OpenAI
2. Set environment variable: `export OPENAI_API_KEY=your-key`
3. Use config:
```json
{
  "ai": {
    "provider": "openai", 
    "model": "gpt-4",
    "api_key": "your-api-key"
  }
}
```

### Claude (Anthropic)

1. Get API key from Anthropic
2. Set environment variable: `export ANTHROPIC_API_KEY=your-key`
3. Use config:
```json
{
  "ai": {
    "provider": "claude",
    "model": "claude-3-haiku-20240307",
    "api_key": "your-api-key"
  }
}
```

## Source Code Analysis Features

### Supported Test Frameworks

The tool automatically detects and parses test files from these frameworks:

- **Python**: pytest, unittest
  - Recognizes `test_*.py` files and `def test_*` methods
  - Extracts test classes and method implementations
- **JavaScript/TypeScript**: Jest, Mocha, Cypress
  - Recognizes `*.test.js`, `*.spec.ts`, `*.cy.js` files
  - Parses `describe()`, `it()`, `test()`, `cy.it()` blocks
- **Java**: JUnit, TestNG
  - Recognizes `*Test.java` files and `@Test` annotations
  - Extracts test class and method structures

### Test Discovery

The analyzer scans configured directories and automatically:

1. **Discovers test files** based on naming patterns
2. **Parses test methods** and extracts source code
3. **Matches test failures** to actual source code using fuzzy matching
4. **Provides exact line numbers** and file paths for fixes

### Enhanced Analysis with Source Code

When source code is available, the AI analysis includes:

- **Exact line identification** of problematic code
- **Context-aware fixes** based on actual implementation
- **Framework-specific suggestions** (e.g., Cypress selectors, pytest assertions)
- **Code replacement recommendations** with line numbers

### Configuration Examples

```json
{
  "test_source": {
    "directories": [
      "./tests",                    // Python pytest tests
      "./cypress/e2e",             // Cypress end-to-end tests
      "./cypress/component",       // Cypress component tests  
      "./src/test/java",           // Java JUnit tests
      "./src/__tests__",           // Jest tests
      "./test/unit",               // Unit tests
      "./test/integration"         // Integration tests
    ]
  },
  "memory": {
    "use_mem0": false,             // Use local storage instead of mem0
    "backend": "local",            // Memory backend type
    "storage_path": "team_memory.json",     // Custom memory file
    "feedback_path": "qe_reviews.json"     // QE feedback storage
  }
}
```

## Usage Examples

### Command Line

```bash
# Jenkins mode with memory and source code
python3 analyze_test_failures.py jenkins "CI-jobs/search_tests" 123 --test-dirs ./tests --memory-backend local

# Local mode with all features enabled
python3 analyze_test_failures.py local ./target/surefire-reports/*.xml --test-dirs ./tests --memory-backend local

# Local mode with advanced mem0 memory backend
python3 analyze_test_failures.py local ./build/test-results --test-dirs ./tests ./cypress/e2e ./src/test --memory-backend mem0

# Disable memory for one-time analysis
python3 analyze_test_failures.py local ./results/*.xml --test-dirs ./tests --disable-memory

# Limit failures and specify output with memory
python3 analyze_test_failures.py local ./results/*.xml --max-failures 5 --output local_analysis.json --memory-backend local

# Use different AI provider with memory
python3 analyze_test_failures.py jenkins "integration-tests" 999 --config openai-config.json --memory-backend local
python3 analyze_test_failures.py local ./junit-reports --config claude-config.json --memory-backend mem0

# Custom skill file with memory learning
python3 analyze_test_failures.py local ./results/*.xml --skill-file ./skills/cypress-focused-analysis.md --memory-backend local
```

### Programmatic Usage

```python
from analyze_test_failures import TestFailureAnalyzer

# Jenkins mode with memory
jenkins_config = {
    "jenkins": {
        "url": "https://jenkins.example.com",
        "user": "user",
        "token": "token"
    },
    "ai": {"provider": "ollama", "model": "llama3.2"},
    "test_source": {"directories": ["./tests", "./src/test"]},
    "skill": {"file_path": "./skills/analyze-test-failures.md"},
    "memory": {
        "use_mem0": False,
        "backend": "local",
        "storage_path": "jenkins_memory.json"
    }
}

analyzer = TestFailureAnalyzer(jenkins_config)
result = analyzer.analyze_build_failures("CI-jobs/tests", 123, {"max_failures": 10})

# Local mode with mem0 memory
local_config = {
    "ai": {"provider": "ollama", "model": "llama3.2"},
    "test_source": {"directories": ["./tests", "./src/test"]},
    "local_junit": {"xml_paths": ["./target/surefire-reports", "./results/*.xml"]},
    "skill": {"file_path": "./skills/analyze-test-failures.md"},
    "memory": {
        "use_mem0": True,
        "backend": "mem0",
        "mem0_config": {
            "vector_store": {"provider": "chroma"}
        }
    }
}

analyzer = TestFailureAnalyzer(local_config)
result = analyzer.analyze_build_failures(options={"max_failures": 10})

# Check results and memory stats
print(f"Found {result['analysisMetadata']['totalFailures']} failures")
print(f"Mode: {result['analysisMetadata']['analysisMode']}")

# Get memory statistics
memory_stats = analyzer.get_memory_stats()
print(f"Memory backend: {memory_stats['backend']}")
print(f"Stored memories: {memory_stats.get('total_memories', 0)}")

# Store QE feedback for a specific analysis
feedback = {
    "accuracy": "high",
    "usefulness": "very_useful", 
    "comments": "Great analysis, solution worked immediately",
    "reviewer": "qe-team@company.com"
}
analyzer.store_qe_feedback("memory_id_123", feedback)
```

## CI/CD Integration

### Jenkins Pipeline

Use the included `Jenkinsfile` to set up automated failure analysis:

1. Create a new Jenkins pipeline job
2. Point to this repository
3. Configure these credentials in Jenkins:
   - `jenkins-api-credentials`: Username/token for Jenkins API access
   - `openai-api-key`: OpenAI API key (if using OpenAI)
   - `anthropic-api-key`: Anthropic API key (if using Claude)

### Running the Pipeline

The pipeline accepts these parameters:
- `TARGET_PIPELINE`: Pipeline to analyze (e.g., "CI-jobs/search_tests")
- `TARGET_BUILD_NUMBER`: Build number to analyze
- `AI_PROVIDER`: Choose from ollama, openai, claude
- `MAX_FAILURES`: Maximum number of failures to analyze

## Output Format

The tool generates JSON reports with this structure:

```json
{
  "analysisMetadata": {
    "pipeline": "CI-jobs/search_tests",
    "buildNumber": 123,
    "analysisTimestamp": "2024-03-15T10:30:00Z",
    "totalFailures": 5,
    "processingTime": "45s",
    "aiProvider": "ollama",
    "sourceCodeAnalysis": true,
    "analysisMode": "jenkins",
    "analysisSource": "CI-jobs/search_tests #123"
  },
  "failureAnalysis": [
    {
      "testCaseName": "should load search page",
      "failureMessage": "Element not found: .search-input", 
      "rootCauseAnalysis": "CSS selector changed, test needs update",
      "codeFixSuggestion": "Update selector to .pf-c-search-input",
      "sourceCodeMapping": {
        "filePath": "tests/search.spec.js",
        "lineNumber": 25,
        "testMethod": "should load search page",
        "testClass": "SearchTests",
        "language": "javascript",
        "problematicLines": [25, 26],
        "suggestedReplacements": ["cy.get('.pf-c-search-input').should('exist')"]
      },
      "failureDetails": {
        "errorType": "ElementNotFound",
        "severity": "HIGH",
        "category": "automation"
      },
      "fixMetadata": {
        "confidenceScore": 0.9,
        "automationBug": true,
        "estimatedEffort": "5 minutes",
        "suggestedLines": ["cy.get('.pf-c-search-input').should('exist')"],
        "fixType": "SelectorFix"
      }
    }
  ],
  "summaryMetrics": {
    "automationBugs": 3,
    "infrastructureIssues": 1, 
    "productIssues": 1,
    "environmentIssues": 0
  }
}
```

## Configuration Options

See `config-examples.json` for complete configuration examples for all supported AI providers.

## Common Use Cases

### 🚀 Local Development
```bash
# After running tests locally, analyze failures quickly
mvn test || true  # Run tests, continue on failure
python3 analyze_test_failures.py local ./target/surefire-reports --test-dirs ./src/test
```

### 🔄 CI/CD Integration
```bash
# In your CI pipeline, analyze failures without Jenkins dependency  
gradle test || true  # Run tests, continue on failure
python3 analyze_test_failures.py local ./build/test-results --max-failures 20 --output ci_analysis.json
```

### 🏥 Post-Mortem Analysis
```bash
# Analyze test failures from archived XML files
python3 analyze_test_failures.py local /path/to/archived/test-results/*.xml --config production-config.json
```

## Files

- `analyze_test_failures.py`: Main analysis script with dual-mode support and memory integration
- `memory.py`: Memory system for learning from past failures and storing QE feedback
- `requirements.txt`: Python dependencies
- `config.json.template`: Full configuration template (Jenkins + Local + Memory)
- `config-local.json.template`: Local-only configuration template
- `config-examples.json`: Example configurations for all AI providers
- `Jenkinsfile`: CI/CD pipeline configuration
- `example_usage.py`: Usage examples and demos
- `skills/analyze-test-failures.md`: Original skill specification
- `failure_memory.json`: Local memory storage (generated automatically)
- `qe_feedback.json`: QE review feedback storage (generated automatically)

## Support

This tool implements the analyze-test-failures skill specification with comprehensive features:

- **📊 Dual Mode Support**: Both Jenkins and local analysis modes
- **🧠 Memory Learning**: Automatic learning from past failures with similarity detection
- **📝 Source Code Integration**: Deep analysis with actual test source code
- **🤖 Multi-AI Support**: Works with Ollama, OpenAI, Claude, and custom APIs
- **📚 Knowledge Management**: QE feedback system and continuous improvement
- **🔧 Enterprise Ready**: Structured JSON output compatible with CI/CD systems

The memory system enables the tool to become more intelligent over time, providing increasingly better solutions as it learns from your team's testing patterns and failure resolution strategies.