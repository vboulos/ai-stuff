# Prompt Refactoring Summary

## Overview
Extracted hardcoded prompts from Python code into separate, editable template files for better maintainability and customization.

## Changes Made

### 1. Created Prompt Templates Directory
```
prompts/
├── analysis_prompt.txt          # Failure analysis prompt template
├── fix_suggestion_prompt.txt    # Fix suggestion prompt template
└── README.md                    # Prompt documentation
```

### 2. Modified Python Files

#### analyze_failures.py
- Added `os` import for file path handling
- Updated `__init__()` to accept optional `prompt_file` parameter
- Added `_load_prompt_template()` method to load prompts from files
- Modified `_create_analysis_prompt()` to use template formatting instead of f-strings
- Default prompt location: `prompts/analysis_prompt.txt`

#### fix_suggestor.py
- Added `os` import for file path handling
- Updated `__init__()` to accept optional `prompt_file` parameter
- Added `_load_prompt_template()` method to load prompts from files
- Modified `_create_fix_prompt()` to use template formatting instead of f-strings
- Default prompt location: `prompts/fix_suggestion_prompt.txt`

## Usage

### Default Usage (No Changes Required)
```python
# Uses default prompts from prompts/ directory
analyzer = FailureAnalyzer(model="llama3.1")
suggestor = FixSuggestor(model="llama3.1")
```

### Custom Prompt Files
```python
# Use custom prompt templates
analyzer = FailureAnalyzer(
    model="llama3.1",
    prompt_file="/path/to/custom_analysis_prompt.txt"
)

suggestor = FixSuggestor(
    model="llama3.1",
    prompt_file="/path/to/custom_fix_prompt.txt"
)
```

## Benefits

1. **Easy Customization** - Edit prompts without touching Python code
2. **Version Control** - Track prompt changes separately from code
3. **A/B Testing** - Test different prompt variations easily
4. **Model-Specific Prompts** - Create optimized prompts for different LLMs
5. **Collaboration** - Non-developers can improve prompts
6. **Reusability** - Share prompt templates across projects

## Prompt Template Variables

### analysis_prompt.txt
- `{framework_info}` - Test framework information
- `{test_name}` - Name of the failed test
- `{failure_message}` - Error message or failure output

### fix_suggestion_prompt.txt
- `{framework_info}` - Test framework information
- `{test_name}` - Name of the failed test
- `{failure_message}` - Error message or failure output
- `{analysis_context}` - Previous analysis data (optional)

## Testing

All prompt templates have been tested and validated:
```bash
cd /path/to/analyze_and_fix
python3 -c "import os; ..."  # See test script in commit
```

## Backward Compatibility

✅ **Fully backward compatible** - Existing code continues to work without modifications.
The default behavior loads prompts from `prompts/` directory automatically.

## Next Steps

1. **Experiment with prompts** - Edit the .txt files to improve analysis quality
2. **Add new templates** - Create specialized prompts for specific frameworks
3. **Track metrics** - Monitor how prompt changes affect analysis accuracy
4. **Document findings** - Keep notes on what works best for different models
