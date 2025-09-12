# JIRA Ticket Manager for Test Case Results

Enhanced JIRA ticket manager with flexible configuration for labels, components, fix versions, and custom fields.

## Features

- ✅ **Flexible Configuration**: Support for labels, components, fix versions, and custom fields
- 🔍 **Smart Ticket Detection**: Finds existing tickets to avoid duplicates
- 📝 **Rich Ticket Content**: Detailed descriptions with analysis and fix suggestions
- 🛡️ **Error Handling**: Comprehensive error handling and dry-run mode
- ⚙️ **Multiple Configuration Methods**: Command line, environment variables, and config files

## Setup

```bash
pip install -r requirements.txt

# Set environment variables
export JIRA_URL="https://company.atlassian.net"
export JIRA_USERNAME="your-email@company.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT="TEST"
```

## Configuration Options

### 1. Command Line Arguments

```bash
# Basic usage
python jira_ticket_manager.py test_results.json

# With custom labels and components
python jira_ticket_manager.py test_results.json \
  --labels "priority-high" "team-qa" \
  --components "Web UI" "API" \
  --fix-version "v2.1.0" \
  --issue-type "Task"

# Dry run
python jira_ticket_manager.py test_results.json --dry-run
```

### 2. Configuration File

Create a JSON configuration file (see `config_example.json`):

```json
{
  "default_labels": ["automated-test", "qa"],
  "default_components": ["Testing"],
  "default_fix_version": "Next Release",
  "default_custom_fields": {
    "customfield_10001": "Test Automation"
  },
  "labels": ["test-failure-analysis"],
  "components": ["CI/CD"],
  "fix_version": "v2.1.0",
  "issue_type": "Bug",
  "custom_fields": {
    "customfield_10003": "Automated Analysis"
  }
}
```

Use with:
```bash
python jira_ticket_manager.py test_results.json --config config.json
```

### 3. Configuration Hierarchy

Configuration is applied in this order (later overrides earlier):
1. **Default Values** (`default_*` in config file)
2. **Config File Values** (specific values in config file)
3. **Command Line Arguments**

## Configuration Types

### Labels
- **Default Labels**: Applied to all tickets automatically
- **Custom Labels**: Added to specific tickets
- **Auto-generated Labels**: Based on test data (framework, category, severity)

### Components
- **Default Components**: Applied to all tickets
- **Suite Components**: Automatically added based on test suite name
- **Custom Components**: Added to specific tickets

### Fix Versions
- **Default Fix Version**: Applied to all tickets unless overridden
- **Custom Fix Version**: Set for specific processing runs

### Custom Fields
- **Default Custom Fields**: Applied to all tickets
- **Specific Custom Fields**: Added for specific processing runs

## Custom Field Examples

```json
{
  "custom_fields": {
    "customfield_10001": "Simple text value",
    "customfield_10002": {"value": "Option value"},
    "customfield_10003": {"id": "10001"},
    "customfield_10004": [{"value": "Multi-value 1"}, {"value": "Multi-value 2"}],
    "customfield_10005": {"name": "User Name"},
    "customfield_10006": {"key": "PROJECT-123"}
  }
}
```

## Usage Examples

### Basic Processing
```bash
python jira_ticket_manager.py test_results.json
```

### With Custom Configuration
```bash
python jira_ticket_manager.py test_results.json \
  --config production_config.json \
  --labels "release-blocker" \
  --fix-version "v2.1.1"
```

### Environment-Specific Configs

**Development:**
```json
{
  "default_labels": ["dev", "automated"],
  "default_components": ["Development"],
  "fix_version": "Development Sprint",
  "issue_type": "Task"
}
```

**Production:**
```json
{
  "default_labels": ["production", "critical"],
  "default_components": ["Production"],
  "fix_version": "Hotfix",
  "issue_type": "Bug",
  "custom_fields": {
    "customfield_10001": "Production Issue"
  }
}
```

## Ticket Structure

### New Tickets Include:
- **Summary**: Test name (truncated if needed)
- **Description**: Detailed failure information, analysis, and fix suggestions
- **Labels**: Framework, error category, severity, plus custom labels
- **Components**: Test suite, default components, plus custom components
- **Priority**: Auto-determined based on analysis confidence and severity
- **Fix Version**: As configured
- **Custom Fields**: As configured

### Updates Include:
- **Description**: Appended with new analysis data
- **Labels**: Additional labels added
- **Components**: Additional components added
- **Custom Fields**: Updated as specified
- **Comments**: Tracking analysis updates

## Error Handling

- **Duplicate Prevention**: Smart detection of existing tickets
- **Graceful Degradation**: Continues processing even if some tickets fail
- **Detailed Logging**: Clear error messages and processing summaries
- **Dry Run Mode**: Preview changes before applying

## Advanced Usage

### Programmatic Usage

```python
from jira_ticket_manager import JIRATicketManager, TestCaseJIRAProcessor

# Initialize with custom defaults
jira_manager = JIRATicketManager(
    jira_url, username, api_token, project_key,
    default_labels=['auto-generated', 'test-failure'],
    default_components=['QA'],
    default_fix_version='Next Release',
    custom_fields={'customfield_10001': 'Automated'}
)

# Process with specific configuration
ticket_config = {
    'labels': ['high-priority'],
    'components': ['Web UI'],
    'fix_version': 'v2.1.0',
    'custom_fields': {'customfield_10002': 'Critical'}
}

processor = TestCaseJIRAProcessor(jira_manager, ticket_config)
result = processor.process_json_file('test_results.json')
```

### Batch Processing with Different Configs

```bash
# Process different test suites with different configurations
python jira_ticket_manager.py ui_tests.json --config ui_config.json
python jira_ticket_manager.py api_tests.json --config api_config.json
python jira_ticket_manager.py integration_tests.json --config integration_config.json
```

## Troubleshooting

### Common Issues

1. **Custom Field Not Found**: Verify custom field IDs in JIRA admin
2. **Component Not Found**: Ensure components exist in the project
3. **Version Not Found**: Verify fix version exists in project settings
4. **Permission Denied**: Ensure API token has appropriate permissions

### Debug Mode

Use dry-run to test configuration:
```bash
python jira_ticket_manager.py test_results.json --config config.json --dry-run
```

This shows what would be created/updated without making changes.