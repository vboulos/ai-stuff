# Prompt Templates

This directory contains the prompt templates used by the failure analysis and fix suggestion tools.

## Available Prompts

### 1. analysis_prompt.txt (Generic)
General-purpose prompt for analyzing test failures across any framework or technology.

**Use Case:** General test failure analysis

**Variables:**
- `{framework_info}` - Test framework information (e.g., "(Framework: pytest)")
- `{test_name}` - Name of the failed test
- `{failure_message}` - The error message or failure output

**Output Sections:**
- ROOT CAUSE - Why the test failed
- SUGGESTED FIX - High-level approach to fix
- CODE EXAMPLE - Specific code changes if applicable
- CONFIDENCE - Score from 0.1 to 1.0
- ERROR_CATEGORY - Type of error (timeout, assertion, network, etc.)
- SEVERITY - critical|high|medium|low

### 1b. analysis_prompt_openshift_acm.txt (Specialized)
Expert-level prompt specifically designed for OpenShift/Kubernetes and Advanced Cluster Management (ACM) QE analysis.

**Use Case:** OpenShift, Kubernetes, ACM, multi-cluster, operator, and distributed system test failures

**Variables:**
- `{framework_info}` - Test framework information
- `{test_name}` - Name of the failed test
- `{failure_message}` - The error message or failure output

**Output Sections:**
- ROOT CAUSE - Detailed analysis with OpenShift/K8s/ACM context
- SUGGESTED FIX - Specific to OpenShift/K8s resources and commands
- CODE EXAMPLE - YAML manifests, CLI commands (oc/kubectl), code snippets
- CONFIDENCE - Score from 0.1 to 1.0 with reasoning
- ERROR_CATEGORY - Includes specialized categories (rbac, operator, api_compatibility, resource_constraint, cluster_state, multi_cluster)
- SEVERITY - With specific impact descriptions
- ADDITIONAL_CONTEXT - Known issues, Jira tickets, investigation steps, environmental factors

**Expert Capabilities:**
- Deep understanding of OpenShift/Kubernetes architecture
- ACM multicluster operations expertise
- Distributed system failure pattern recognition
- Operator reconciliation loop analysis
- Multi-cluster communication debugging
- Resource constraint identification

### 2. fix_suggestion_prompt.txt
Used by `fix_suggestor.py` to generate detailed fix suggestions with code examples.

**Variables:**
- `{framework_info}` - Test framework information
- `{test_name}` - Name of the failed test
- `{failure_message}` - The error message or failure output
- `{analysis_context}` - Optional previous analysis data

**Output Sections:**
- FIX_TYPE - Type of fix needed
- PRIORITY - Fix priority level
- ESTIMATED_EFFORT - Time required (minutes|hours|days)
- CODE_CHANGES - Specific code modifications
- CONFIGURATION_CHANGES - Config file updates
- DEPENDENCIES - Package updates needed
- VALIDATION_STEPS - How to verify the fix
- PREVENTION - How to prevent in future
- IMPACT_ASSESSMENT - Areas affected by fix
- ROLLBACK_PLAN - How to revert if needed

## Usage Examples

### Using the Generic Analysis Prompt (Default)
```python
from analyze_failures import FailureAnalyzer

# Uses prompts/analysis_prompt.txt by default
analyzer = FailureAnalyzer(model="llama3.1")

result = analyzer.analyze_failure(
    test_name="test_api_endpoint",
    failure_message="Connection timeout after 30s",
    framework="pytest"
)
```

### Using the OpenShift/ACM Specialized Prompt
```python
from analyze_failures import FailureAnalyzer
import os

# Use the specialized OpenShift/ACM prompt
prompt_path = os.path.join(
    os.path.dirname(__file__),
    "prompts",
    "analysis_prompt_openshift_acm.txt"
)

analyzer = FailureAnalyzer(
    model="llama3.1",
    prompt_file=prompt_path
)

result = analyzer.analyze_failure(
    test_name="test_managed_cluster_registration",
    failure_message="ManagedCluster resource stuck in pending state for 10 minutes",
    framework="ginkgo"
)

# Check for OpenShift/ACM specific fields
if result["success"]:
    print("Root Cause:", result["root_cause"])
    print("Severity:", result["severity"])
    print("Category:", result["error_category"])
    if result["additional_context"]:
        print("Additional Context:", result["additional_context"])
```

### Using a Completely Custom Prompt
```python
analyzer = FailureAnalyzer(
    model="llama3.1",
    prompt_file="/path/to/custom_prompt.txt"
)
```

## Customizing Prompts

You can customize these prompts by:

1. **Editing the template files** - Modify the .txt files directly
2. **Creating new specialized prompts** - Copy and modify existing templates
3. **Using custom prompt files** - Pass `prompt_file` parameter when initializing:
   ```python
   analyzer = FailureAnalyzer(prompt_file="/path/to/custom_prompt.txt")
   suggestor = FixSuggestor(prompt_file="/path/to/custom_fix_prompt.txt")
   ```

## Format Requirements

- Use Python string formatting syntax: `{variable_name}`
- Keep section headers in `**SECTION_NAME:**` format
- The parsing logic expects these exact headers, so maintain structure when customizing

## Best Practices

1. **Be specific** - The more context you provide, the better the analysis
2. **Maintain structure** - The parsers rely on the section headers
3. **Test changes** - Verify custom prompts produce parseable output
4. **Version control** - Track changes to understand prompt evolution
5. **Model-specific tuning** - Different LLMs may respond better to different prompt styles
