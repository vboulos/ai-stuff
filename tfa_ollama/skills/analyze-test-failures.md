# Analyze Test Failures Skill

## Overview

Perform comprehensive analysis of test failures by scanning JUnit XML files, mapping failures to source code, conducting root cause analysis, and generating targeted fix suggestions. This skill provides structured JSON output with detailed failure mappings and automation bug detection.

## Metadata

- **Name**: analyze-test-failures
- **Description**: Comprehensive test failure analysis with JUnit scanning, code mapping, and automated fix suggestions
- **Category**: Testing
- **Author**: PICS Team
- **Version**: 3.0.0
- **Tools**: Jenkins REST API, JUnit XML Parser, GitHub API, Static Code Analysis

## Command Interface

```bash
/analyze-test-failures <pipeline_name> <build_number> [options]
```

## Required Parameters

- `pipeline_name` (string): Full Jenkins pipeline name (e.g., "CI-jobs/search_tests")
- `build_number` (integer): Build number to analyze

## Optional Parameters

- `github_repo` (string, optional): GitHub repository URL for source code analysis
- `test_directory` (string, optional): Directory path containing test files (default: auto-detect)
- `include_source_analysis` (boolean, optional): Enable source code analysis (default: true)
- `suggest_fixes` (boolean, optional): Generate automation fix suggestions (default: true)
- `max_failures` (integer, optional): Maximum number of failures to analyze in detail (default: 10)
- `filter_pattern` (string, optional): Filter test cases by pattern (default: "RHACM4K-" for Red Hat ACM Quality Engineering)

## Pipeline Mapping

This skill works with any Jenkins pipeline that produces:
- JUnit XML test results
- Console output logs
- Test artifacts

## Core Features

### 1. Identify Failures
- **JUnit XML Scanning**: Automatically scan specified directories for junit.xml files
- **Pattern Filtering**: Filter test cases matching specific patterns (e.g., RHACM4K- for ACM Quality Engineering)
- **Failure Extraction**: Parse XML files to extract all failed test cases with detailed metadata
- **Error Categorization**: Classify failures by type (assertion, timeout, exception, etc.)
- **Stack Trace Analysis**: Extract and parse complete stack traces for each failure
- **Structural Data Mapping**: Extract test source file paths and fix locations for each failure

### 2. Code Mapping  
- **Test Source File Location**: Locate and identify the full path and filename of source files hosting test cases
- **Fix Location Identification**: Pinpoint exact code blocks or files requiring modification to fix test failures
- **Framework vs Application Bug Detection**: Distinguish between test framework bugs and application bugs
- **Test Method Location**: Identify exact file paths and line numbers for failed test methods
- **Dependency Mapping**: Map test dependencies and helper functions
- **Test Data Analysis**: Identify test data files and configuration dependencies

### 3. Root Cause Analysis
- **Execution Log Analysis**: Parse console logs and execution traces to identify failure triggers
- **Pattern Recognition**: Detect common failure patterns (timing issues, data dependencies, environment)
- **Context Extraction**: Extract relevant log context before and after failure points
- **Infrastructure Analysis**: Identify infrastructure vs. code-related failures

### 4. Code Fix Suggestions
- **Automation Bug Detection**: Identify exact lines needing modification in test files
- **Targeted Fixes**: Generate specific code changes for identified automation bugs
- **Best Practice Recommendations**: Suggest improvements for test reliability
- **Confidence Scoring**: Provide confidence levels for each suggested fix

### 5. Structured JSON Output
- **Standardized Schema**: Generate JSON output with consistent structure for each failure
- **Machine Readable**: Enable automated processing and integration with CI/CD pipelines
- **Detailed Metadata**: Include comprehensive failure context and analysis results
- **Actionable Items**: Provide clear next steps for each identified issue

## Execution Steps

1. **Initialize Analysis Environment**
   - Retrieve build information and status via Jenkins API
   - Identify test artifacts and console log locations
   - Set up GitHub repository access for source code analysis

2. **Scan and Parse JUnit Files**
   - Recursively scan specified directories for junit.xml files
   - Parse XML files to extract test case results
   - Identify all failed test cases with failure messages and stack traces
   - Categorize failures by type and severity

3. **Map Failures to Source Code**
   - Search GitHub repository for test source files
   - Match failed test case names with actual test methods
   - Identify file paths, line numbers, and test implementations
   - Extract test dependencies and related helper functions

4. **Conduct Root Cause Analysis**
   - Analyze console logs for failure context
   - Parse stack traces to identify exact failure points
   - Correlate timing data with failure patterns
   - Identify environmental vs. code-related issues

5. **Generate Targeted Fix Suggestions**
   - Analyze test source code for automation bugs
   - Generate specific line-by-line fix recommendations
   - Provide confidence scores for each suggestion
   - Categorize fixes by impact and complexity

6. **Compile Structured JSON Report**
   - Generate standardized JSON output with failure mappings
   - Include detailed analysis results for each test case
   - Provide actionable recommendations and next steps
   - Export machine-readable format for automation integration

## Jenkins API Implementation

The skill uses Jenkins REST API with these endpoints:
- **Build Info**: `GET /job/{pipeline_path}/{build_number}/api/json`
- **Test Report**: `GET /job/{pipeline_path}/{build_number}/testReport/api/json`
- **JUnit XML Files**: `GET /job/{pipeline_path}/{build_number}/artifact/**/junit*.xml`
- **Console Output**: `GET /job/{pipeline_path}/{build_number}/consoleText`
- **Test Artifacts**: `GET /job/{pipeline_path}/{build_number}/artifact/**`
- **Workspace Files**: `GET /job/{pipeline_path}/{build_number}/artifact/results/**`

### JUnit XML Processing
- **Multiple File Support**: Scan for all junit*.xml files in build artifacts
- **XML Validation**: Validate XML structure and handle corrupted files gracefully
- **Batch Processing**: Process multiple XML files concurrently for faster analysis
- **Error Recovery**: Handle partial XML files and extract available failure data

## GitHub Integration

When `github_repo` is provided:
- **Repository Access**: Clone or access repository via GitHub API
- **Test File Discovery**: Search for test files matching failed test names
- **Source Code Mapping**: Extract test implementation code and map to failure points
- **Dependency Analysis**: Analyze test logic, imports, and dependencies
- **Change History**: Review recent commits that might have introduced failures
- **Pattern Matching**: Use intelligent pattern matching to handle test name variations

### Code Search Strategies
- **Exact Match**: Search for exact test method names
- **Fuzzy Matching**: Handle variations in test naming conventions
- **Class-Based Search**: Locate test classes containing failed methods
- **Package Structure**: Navigate test package hierarchies efficiently
- **Multi-Framework Support**: Handle different test frameworks (JUnit, TestNG, Cypress, etc.)

## RHACM4K Test Analysis Requirements

For test cases matching the pattern "RHACM4K-", extract and map the following structural data:

### Required Data Extraction
- **Test Source File**: Locate and print the full path and filename of the source file hosting the test case
- **Fix Location**: Pinpoint the exact code block or file requiring modification to fix the test failure
- **Bug Type Classification**: Distinguish between test framework bug, application bug, and automation bug
- **Pattern Matching**: Only process test cases containing the string pattern "RHACM4K-"

### Structural Mapping Output
For each RHACM4K test failure, provide:
```json
{
  "rhacmId": "RHACM4K-XXXXX",
  "testSourceFile": "full/path/to/test/source/file.js",
  "fixLocation": {
    "targetFile": "path/to/file/requiring/fix.js", 
    "targetLines": [123, 124, 125],
    "bugType": "test_framework|application|automation",
    "description": "Specific description of what needs to be fixed"
  }
}
```

## Failure Analysis Categories

### 1. Infrastructure Issues
- Resource constraints
- Network timeouts
- Environment setup failures
- Service unavailability

### 2. Automation Bugs
- Incorrect selectors
- Race conditions
- Timing issues
- Data dependency problems
- Flaky assertions

### 3. Product Issues
- Legitimate functional failures
- API changes
- UI changes
- Performance regressions

### 4. Test Environment Issues
- Data setup problems
- Configuration mismatches
- Dependency conflicts

## Structured JSON Output Schema

The skill generates a comprehensive JSON file with the following structure:

### Primary Output Schema
```json
{
  "analysisMetadata": {
    "pipeline": "string",
    "buildNumber": "integer",
    "analysisTimestamp": "ISO8601",
    "totalFailures": "integer",
    "processingTime": "string"
  },
  "failureAnalysis": [
    {
      "testCaseName": "string",
      "failureMessage": "string", 
      "rootCauseAnalysis": "string",
      "codeFixSuggestion": "string",
      "sourceCodeMapping": {
        "testSourceFile": "string",
        "fullPath": "string", 
        "filePath": "string",
        "lineNumber": "integer",
        "testMethod": "string",
        "testClass": "string",
        "fixLocation": {
          "targetFile": "string",
          "targetLines": ["integer"],
          "bugType": "test_framework|application|automation",
          "description": "string"
        }
      },
      "failureDetails": {
        "stackTrace": "string",
        "errorType": "string",
        "severity": "string",
        "category": "automation|infrastructure|product|environment"
      },
      "fixMetadata": {
        "confidenceScore": "float (0-1)",
        "automationBug": "boolean",
        "estimatedEffort": "string",
        "suggestedLines": ["string"]
      }
    }
  ],
  "summaryMetrics": {
    "automationBugs": "integer",
    "infrastructureIssues": "integer", 
    "productIssues": "integer",
    "environmentIssues": "integer"
  }
}
```

### Individual Test Failure Schema
Each failed test case includes these required keys:
- **testCaseName**: Full qualified test name from JUnit XML
- **failureMessage**: Original failure message from test execution  
- **rootCauseAnalysis**: Detailed analysis of the underlying cause
- **codeFixSuggestion**: Specific code changes needed (for automation bugs)

### Extended Metadata
Additional context provided for each failure:
- **Source location mapping** with exact file paths and line numbers
- **Confidence scoring** for fix suggestions (0.0 to 1.0 scale)
- **Automation bug detection** with boolean flag and detailed reasoning
- **Category classification** for prioritization and routing

## Usage Examples

### Basic JUnit Analysis
```bash
/analyze-test-failures "CI-jobs/search_tests" 456
```
*Scans build 456 for JUnit XML files and analyzes all failures*

### Comprehensive Analysis with GitHub Integration
```bash
/analyze-test-failures "qe-acm-automation-poc/dr4hub_backup_e2e_test_execution" 847 {
  "github_repo": "https://github.com/stolostron/e2e-tests",
  "test_directory": "cypress/tests",
  "include_source_analysis": true,
  "suggest_fixes": true
}
```
*Full analysis including source code mapping and automation fix suggestions*

### Targeted Analysis for Specific Directory
```bash
/analyze-test-failures "CI-jobs/ui_tests" 123 {
  "test_directory": "tests/integration",
  "max_failures": 5,
  "suggest_fixes": true
}
```
*Focuses analysis on specific test directory with limited failure count*

### Infrastructure-Only Analysis
```bash
/analyze-test-failures "CI-jobs/api_tests" 789 {
  "include_source_analysis": false,
  "suggest_fixes": false,
  "max_failures": 20
}
```
*Quick analysis without source code inspection for infrastructure issues*

## Sample Output

### Example JSON Output
```json
{
  "analysisMetadata": {
    "pipeline": "CI-jobs/search_tests", 
    "buildNumber": 279,
    "analysisTimestamp": "2024-03-15T10:30:00Z",
    "totalFailures": 3,
    "processingTime": "45s"
  },
  "failureAnalysis": [
    {
      "testCaseName": "RHACM4K-57212.should load and render the search page",
      "failureMessage": "Element not found: .pf-c-title",
      "rootCauseAnalysis": "CSS selector '.pf-c-title' not found due to page loading timeout. The search page skeleton loader is still visible, indicating the page has not fully rendered.",
      "codeFixSuggestion": "Add explicit wait for page load completion before assertion. Replace immediate selector check with cy.get('.pf-c-title', { timeout: 30000 }).should('exist') and ensure skeleton elements are not present.",
      "sourceCodeMapping": {
        "filePath": "tests/cypress/tests/search.spec.js",
        "lineNumber": 30,
        "testMethod": "should load and render the search page", 
        "testClass": "Search in Local Cluster"
      },
      "failureDetails": {
        "stackTrace": "CypressError: Timed out retrying after 4000ms...",
        "errorType": "ElementNotFound",
        "severity": "HIGH",
        "category": "automation"
      },
      "fixMetadata": {
        "confidenceScore": 0.9,
        "automationBug": true,
        "estimatedEffort": "5 minutes",
        "suggestedLines": [
          "cy.get(pf.skeleton.base).should('not.exist')",
          "cy.get(pf.title.h1, { timeout: 30000 }).filter(':contains(Search)').should('exist')"
        ]
      }
    }
  ],
  "summaryMetrics": {
    "automationBugs": 2,
    "infrastructureIssues": 1,
    "productIssues": 0,
    "environmentIssues": 0
  }
}
```

## Implementation Requirements

### Core Dependencies
- **Jenkins API Access**: Valid credentials with artifact download permissions
- **JUnit XML Parser**: XML parsing capabilities for multiple file formats
- **GitHub API Access**: Token with repository read permissions (for source analysis)
- **Static Code Analysis**: Pattern recognition for automation bug detection
- **JSON Schema Validation**: Ensure output adheres to specified schema

### Configuration Files
- `jenkins_credentials.json`: Jenkins authentication in project root
- `github_token.json`: GitHub access token for repository analysis (optional)
- `analysis_config.json`: Custom patterns and fix suggestions (optional)

### Processing Capabilities
- **Concurrent XML Processing**: Handle multiple JUnit files simultaneously
- **Large File Handling**: Process builds with hundreds of test results
- **Memory Management**: Efficient processing of large console logs and stack traces
- **Error Recovery**: Handle corrupted XML files and partial data gracefully

## Prerequisites Checklist

### Required Access
- [ ] **Jenkins Access**: Valid credentials with permissions to access build artifacts
- [ ] **JUnit Reports**: Target builds must produce JUnit XML test results  
- [ ] **Artifact Access**: Console logs and test artifacts must be available

### Optional Enhancements
- [ ] **GitHub Access**: Token with repository read permissions for source code mapping
- [ ] **Test Directory Access**: Repository structure knowledge for faster file location
- [ ] **Framework Knowledge**: Understanding of test frameworks used in the project

### Environment Setup
- [ ] **Network Access**: Ability to reach Jenkins and GitHub APIs
- [ ] **Processing Resources**: Sufficient memory/CPU for large builds analysis
- [ ] **Output Directory**: Writable location for JSON output files

## Advanced Features

### Pattern Recognition Engine
- **Common Error Patterns**: Database of known automation issues and fixes
- **Framework-Specific Logic**: Tailored analysis for different test frameworks
- **Historical Learning**: Improve suggestions based on previous successful fixes
- **Custom Rules**: Support for project-specific automation patterns

### Integration Capabilities  
- **CI/CD Pipeline Integration**: Direct integration with build systems
- **Slack/Teams Notifications**: Automated failure summaries to team channels
- **JIRA Integration**: Automatic ticket creation for identified automation bugs
- **Dashboard Export**: Metrics and trends for test reliability monitoring

### Performance Optimizations
- **Caching Layer**: Cache repository structures and common patterns
- **Parallel Processing**: Analyze multiple failures simultaneously
- **Incremental Updates**: Only reprocess changed test files
- **Smart Filtering**: Focus analysis on recent failures and high-impact tests