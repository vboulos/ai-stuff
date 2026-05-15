# Prompt Templates

This directory contains the prompt templates used by the failure analysis and fix suggestion tools.

## Available Prompts

### 1. analysis_prompt.txt
Used by `analyze_failures.py` to analyze test failures and identify root causes.

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

## Customizing Prompts

You can customize these prompts by:

1. **Editing the template files** - Modify the .txt files directly
2. **Using custom prompt files** - Pass `prompt_file` parameter when initializing:
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
