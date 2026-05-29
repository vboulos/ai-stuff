# Test Failure Analysis with AI and Source Code Integration

This implementation provides enhanced AI-powered test failure analysis based on the `analyze-test-failures` skill. It supports multiple AI providers and includes **source code scanning** for more accurate analysis and fix suggestions.

## Features

- **Source Code Analysis**: Scans actual test files and matches failures to source code for precise fix suggestions
- **Multi-AI Support**: Works with Ollama (local), OpenAI, Claude, or any custom REST API
- **Test Framework Support**: Supports Python (pytest/unittest), JavaScript/TypeScript (Jest/Mocha/Cypress), Java (JUnit), and more
- **Jenkins Integration**: Fetches test results and build information from Jenkins
- **Intelligent Matching**: Fuzzy matching between test names and source code methods
- **Structured Analysis**: Generates detailed JSON reports with line-specific fix suggestions
- **CI/CD Ready**: Includes Jenkinsfile for automated analysis
- **Categorized Failures**: Classifies failures as automation bugs, infrastructure issues, product issues, or environment problems
- **Skill-Based Prompts**: Uses the analyze-test-failures.md skill specification to generate consistent, structured AI prompts

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

Edit `config.json` with your Jenkins, AI provider, and test source settings:

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
  }
}
```

### 3. Run Analysis

```bash
# Jenkins mode - analyze remote build failures
python3 analyze_test_failures.py jenkins "CI-jobs/search_tests" 123 --config config.json

# Local mode - analyze local JUnit XML files
python3 analyze_test_failures.py local ./target/surefire-reports/*.xml --config config-local.json

# Local mode with multiple directories
python3 analyze_test_failures.py local ./results ./build/test-results --test-dirs ./tests ./src/test

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
  }
}
```

## Usage Examples

### Command Line

```bash
# Jenkins mode - analyze remote build failures
python3 analyze_test_failures.py jenkins "CI-jobs/search_tests" 123

# Local mode - analyze local XML files  
python3 analyze_test_failures.py local ./target/surefire-reports/*.xml

# Local mode with source code analysis
python3 analyze_test_failures.py local ./build/test-results --test-dirs ./tests ./cypress/e2e ./src/test

# Limit failures and specify output (both modes)
python3 analyze_test_failures.py local ./results/*.xml --max-failures 5 --output local_analysis.json

# Use different AI provider (both modes)
python3 analyze_test_failures.py jenkins "integration-tests" 999 --config openai-config.json
python3 analyze_test_failures.py local ./junit-reports --config claude-config.json

# Use custom skill file for specialized analysis
python3 analyze_test_failures.py local ./results/*.xml --skill-file ./skills/cypress-focused-analysis.md
```

### Programmatic Usage

```python
from analyze_test_failures import TestFailureAnalyzer

# Jenkins mode
jenkins_config = {
    "jenkins": {
        "url": "https://jenkins.example.com",
        "user": "user",
        "token": "token"
    },
    "ai": {"provider": "ollama", "model": "llama3.2"},
    "test_source": {"directories": ["./tests", "./src/test"]},
    "skill": {"file_path": "./skills/analyze-test-failures.md"}
}

analyzer = TestFailureAnalyzer(jenkins_config)
result = analyzer.analyze_build_failures("CI-jobs/tests", 123, {"max_failures": 10})

# Local mode
local_config = {
    "ai": {"provider": "ollama", "model": "llama3.2"},
    "test_source": {"directories": ["./tests", "./src/test"]},
    "local_junit": {"xml_paths": ["./target/surefire-reports", "./results/*.xml"]},
    "skill": {"file_path": "./skills/analyze-test-failures.md"}
}

analyzer = TestFailureAnalyzer(local_config)
result = analyzer.analyze_build_failures(options={"max_failures": 10})

print(f"Found {result['analysisMetadata']['totalFailures']} failures")
print(f"Mode: {result['analysisMetadata']['analysisMode']}")
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

- `analyze_test_failures.py`: Main analysis script with dual-mode support
- `requirements.txt`: Python dependencies
- `config.json.template`: Full configuration template (Jenkins + Local)
- `config-local.json.template`: Local-only configuration template
- `config-examples.json`: Example configurations for all AI providers
- `Jenkinsfile`: CI/CD pipeline configuration
- `example_usage.py`: Usage examples and demos
- `skills/analyze-test-failures.md`: Original skill specification

## Support

This tool implements the analyze-test-failures skill specification with both Jenkins and local mode support. It provides structured JSON output compatible with downstream automation tools and CI/CD systems.