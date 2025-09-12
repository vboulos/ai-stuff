#!/usr/bin/env python3
"""
JIRA Ticket Manager for Test Case Results
"""

import json
import re
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from jira import JIRA
from jira.exceptions import JIRAError
import os

class JIRATicketManager:
    """
    Manages JIRA tickets for test case failures.
    Creates new tickets or updates existing ones with analysis and fix suggestions.
    """
    
    def __init__(self, jira_url: str, username: str, api_token: str, project_key: str,
                 default_issue_type: str = 'Bug', default_labels: List[str] = None,
                 default_components: List[str] = None, default_fix_version: str = None,
                 custom_fields: Dict[str, Any] = None):
        """
        Initialize JIRA connection.
        
        Args:
            jira_url: JIRA server URL
            username: JIRA username/email
            api_token: JIRA API token
            project_key: JIRA project key (e.g., 'TEST', 'BUG')
            default_issue_type: Default issue type for new tickets (default: 'Bug')
            default_labels: Default labels to apply to all tickets
            default_components: Default components to apply to all tickets
            default_fix_version: Default fix version to apply to all tickets
            custom_fields: Custom field mappings {field_name: value}
        """
        self.jira_url = jira_url
        self.username = username
        self.project_key = project_key
        self.default_issue_type = default_issue_type
        self.default_labels = default_labels or []
        self.default_components = default_components or []
        self.default_fix_version = default_fix_version
        self.custom_fields = custom_fields or {}
        
        try:
            self.jira = JIRA(
                server=jira_url,
                basic_auth=(username, api_token)
            )
            print(f"✅ Connected to JIRA: {jira_url}")
        except Exception as e:
            raise Exception(f"Failed to connect to JIRA: {e}")
    
    def find_existing_ticket(self, test_name: str, framework: str = None) -> Optional[str]:
        """
        Find existing JIRA ticket for a test case.
        
        Args:
            test_name: Name of the test case
            framework: Testing framework (optional)
            
        Returns:
            JIRA ticket key if found, None otherwise
        """
        try:
            # Clean test name for search
            clean_test_name = self._clean_test_name(test_name)
            
            # Search queries to try
            search_queries = [
                f'project = {self.project_key} AND summary ~ "{clean_test_name}"',
                f'project = {self.project_key} AND summary ~ "{test_name[:50]}"',  # First 50 chars
                f'project = {self.project_key} AND text ~ "{clean_test_name}"'
            ]
            
            if framework:
                search_queries.append(
                    f'project = {self.project_key} AND summary ~ "{clean_test_name}" AND summary ~ "{framework}"'
                )
            
            for query in search_queries:
                try:
                    issues = self.jira.search_issues(query, maxResults=10)
                    
                    for issue in issues:
                        # Check if this is likely the same test
                        if self._is_same_test(test_name, issue.fields.summary, issue.fields.description):
                            print(f"🔍 Found existing ticket: {issue.key} - {issue.fields.summary}")
                            return issue.key
                            
                except JIRAError as e:
                    print(f"⚠️  Search query failed: {query} - {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ Error searching for existing ticket: {e}")
            return None
    
    def create_ticket(self, test_case_data: Dict[str, Any], 
                     custom_labels: List[str] = None,
                     custom_components: List[str] = None,
                     custom_fix_version: str = None,
                     custom_fields: Dict[str, Any] = None,
                     issue_type: str = None) -> Optional[str]:
        """
        Create a new JIRA ticket for a test case failure.
        
        Args:
            test_case_data: Test case data with analysis and fix suggestions
            custom_labels: Additional labels for this specific ticket
            custom_components: Additional components for this specific ticket
            custom_fix_version: Fix version for this specific ticket
            custom_fields: Additional custom fields for this specific ticket
            issue_type: Issue type for this specific ticket
            
        Returns:
            Created ticket key if successful, None otherwise
        """
        try:
            test_name = test_case_data.get("test_name", "Unknown Test")
            framework = test_case_data.get("framework", "Unknown")
            original_test = test_case_data.get("original_test", {})
            analysis = test_case_data.get("analysis", {})
            fix_suggestion = test_case_data.get("fix_suggestion", {})
            
            # Create ticket summary
            summary = f"Test Failure: {test_name[:80]}{'...' if len(test_name) > 80 else ''}"
            
            # Create detailed description
            description = self._create_ticket_description(
                test_case_data, is_new_ticket=True
            )
            
            # Determine priority based on analysis
            priority = self._determine_priority(analysis)
            
            # Create issue
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type or self.default_issue_type},
                'priority': {'name': priority}
            }
            
            # Build labels (combine defaults, auto-generated, and custom)
            labels = self.default_labels.copy()
            labels.extend(['test-failure', f'framework-{framework.lower()}'])
            
            # Add analysis-based labels
            if analysis.get("error_category"):
                labels.append(f'category-{analysis["error_category"]}')
            if analysis.get("severity"):
                labels.append(f'severity-{analysis["severity"]}')
            
            # Add custom labels
            if custom_labels:
                labels.extend(custom_labels)
            
            # Remove duplicates and set labels
            issue_dict['labels'] = list(set(labels))
            
            # Build components
            components = []
            
            # Add default components
            for comp_name in self.default_components:
                components.append({'name': comp_name})
            
            # Add suite-based component
            if original_test.get("suite_name"):
                components.append({'name': original_test['suite_name']})
            
            # Add custom components
            if custom_components:
                for comp_name in custom_components:
                    components.append({'name': comp_name})
            
            if components:
                issue_dict['components'] = components
            
            # Add fix version
            fix_version = custom_fix_version or self.default_fix_version
            if fix_version:
                issue_dict['fixVersions'] = [{'name': fix_version}]
            
            # Add custom fields
            all_custom_fields = self.custom_fields.copy()
            if custom_fields:
                all_custom_fields.update(custom_fields)
            
            # Apply custom fields to issue_dict
            for field_name, field_value in all_custom_fields.items():
                issue_dict[field_name] = field_value
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            print(f"✅ Created new ticket: {new_issue.key} - {summary}")
            return new_issue.key
            
        except JIRAError as e:
            print(f"❌ Failed to create JIRA ticket: {e}")
            return None
        except Exception as e:
            print(f"❌ Error creating ticket: {e}")
            return None
    
    def update_ticket(self, ticket_key: str, test_case_data: Dict[str, Any],
                     add_labels: List[str] = None,
                     add_components: List[str] = None,
                     update_fix_version: str = None,
                     update_custom_fields: Dict[str, Any] = None) -> bool:
        """
        Update existing JIRA ticket with new analysis and fix suggestions.
        
        Args:
            ticket_key: JIRA ticket key
            test_case_data: Test case data with analysis and fix suggestions
            add_labels: Additional labels to add to the ticket
            add_components: Additional components to add to the ticket
            update_fix_version: Fix version to set on the ticket
            update_custom_fields: Custom fields to update on the ticket
            
        Returns:
            True if successful, False otherwise
        """
        try:
            issue = self.jira.issue(ticket_key)
            
            # Create update description
            update_description = self._create_ticket_description(
                test_case_data, is_new_ticket=False
            )
            
            # Append to existing description
            current_description = issue.fields.description or ""
            separator = "\n\n" + "="*60 + "\n"
            updated_description = current_description + separator + update_description
            
            # Prepare update fields
            update_fields = {'description': updated_description}
            
            # Update labels if provided
            if add_labels:
                current_labels = set(issue.fields.labels or [])
                current_labels.update(add_labels)
                update_fields['labels'] = list(current_labels)
            
            # Update components if provided
            if add_components:
                current_components = [comp.name for comp in (issue.fields.components or [])]
                for comp_name in add_components:
                    if comp_name not in current_components:
                        current_components.append(comp_name)
                update_fields['components'] = [{'name': name} for name in current_components]
            
            # Update fix version if provided
            if update_fix_version:
                update_fields['fixVersions'] = [{'name': update_fix_version}]
            
            # Update custom fields if provided
            if update_custom_fields:
                update_fields.update(update_custom_fields)
            
            # Apply all updates
            issue.update(fields=update_fields)
            
            # Add comment
            analysis = test_case_data.get("analysis", {})
            if analysis.get("success"):
                comment = f"Updated with new analysis (Confidence: {analysis.get('confidence_score', 0):.2f})"
                self.jira.add_comment(issue, comment)
            
            print(f"✅ Updated ticket: {ticket_key}")
            return True
            
        except JIRAError as e:
            print(f"❌ Failed to update JIRA ticket {ticket_key}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error updating ticket {ticket_key}: {e}")
            return False
    
    def _clean_test_name(self, test_name: str) -> str:
        """Clean test name for searching."""
        # Remove special characters and extra spaces
        cleaned = re.sub(r'[^\w\s-]', ' ', test_name)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned[:100]  # Limit length
    
    def _is_same_test(self, test_name: str, summary: str, description: str) -> bool:
        """
        Determine if a JIRA issue is for the same test case.
        
        Args:
            test_name: Original test name
            summary: JIRA issue summary
            description: JIRA issue description
            
        Returns:
            True if likely the same test, False otherwise
        """
        # Simple heuristic - check if test name appears in summary or description
        test_name_clean = self._clean_test_name(test_name.lower())
        summary_clean = summary.lower() if summary else ""
        description_clean = description.lower() if description else ""
        
        # Check for significant overlap
        test_words = set(test_name_clean.split())
        summary_words = set(summary_clean.split())
        description_words = set(description_clean.split())
        
        # If test name is in summary or description, likely the same
        if test_name_clean in summary_clean or test_name_clean in description_clean:
            return True
        
        # Check word overlap
        all_issue_words = summary_words.union(description_words)
        overlap = len(test_words.intersection(all_issue_words))
        
        # If significant word overlap (>50% of test name words), consider it the same
        if len(test_words) > 0 and overlap / len(test_words) > 0.5:
            return True
        
        return False
    
    def _determine_priority(self, analysis: Dict[str, Any]) -> str:
        """Determine JIRA priority based on analysis."""
        severity = analysis.get("severity", "medium").lower()
        confidence = analysis.get("confidence_score", 0.5)
        
        # High confidence + critical/high severity = High priority
        if confidence >= 0.8 and severity in ["critical", "high"]:
            return "High"
        # Medium-high confidence + medium severity = Medium priority  
        elif confidence >= 0.6 and severity == "medium":
            return "Medium"
        # Low confidence or low severity = Low priority
        elif severity == "low" or confidence < 0.5:
            return "Low"
        else:
            return "Medium"
    
    def _create_ticket_description(self, test_case_data: Dict[str, Any], is_new_ticket: bool = True) -> str:
        """Create JIRA ticket description."""
        test_name = test_case_data.get("test_name", "Unknown Test")
        framework = test_case_data.get("framework", "Unknown")
        original_test = test_case_data.get("original_test", {})
        analysis = test_case_data.get("analysis", {})
        fix_suggestion = test_case_data.get("fix_suggestion", {})
        
        # Header
        if is_new_ticket:
            description = f"h2. Test Failure Report\n\n"
        else:
            description = f"h2. Updated Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Test details
        description += f"*Test Name:* {test_name}\n"
        description += f"*Framework:* {framework}\n"
        
        if original_test.get("suite_name"):
            description += f"*Test Suite:* {original_test['suite_name']}\n"
        if original_test.get("class_name"):
            description += f"*Test Class:* {original_test['class_name']}\n"
        if original_test.get("execution_time"):
            description += f"*Execution Time:* {original_test['execution_time']}s\n"
        
        description += "\n"
        
        # Failure message
        failure_message = original_test.get("failure_message", "No failure message available")
        description += f"h3. Failure Message\n"
        description += f"{{code}}\n{failure_message}\n{{code}}\n\n"
        
        # Analysis section
        if analysis.get("success"):
            description += f"h3. Root Cause Analysis\n"
            description += f"*Confidence Score:* {analysis.get('confidence_score', 0):.2f}\n"
            description += f"*Error Category:* {analysis.get('error_category', 'unknown')}\n"
            description += f"*Severity:* {analysis.get('severity', 'medium')}\n\n"
            
            description += f"*Root Cause:*\n{analysis.get('root_cause', 'No root cause provided')}\n\n"
            
            description += f"*Suggested Fix:*\n{analysis.get('suggested_fix', 'No suggested fix provided')}\n\n"
            
            if analysis.get("code_example"):
                description += f"*Code Example:*\n{{code:javascript}}\n{analysis['code_example']}\n{{code}}\n\n"
        else:
            description += f"h3. Analysis Status\n"
            description += f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}\n\n"
        
        # Fix suggestions
        if fix_suggestion.get("success"):
            description += f"h3. Detailed Fix Suggestions\n"
            description += f"*Fix Type:* {fix_suggestion.get('fix_type', 'unknown')}\n"
            description += f"*Priority:* {fix_suggestion.get('priority', 'medium')}\n"
            description += f"*Estimated Effort:* {fix_suggestion.get('estimated_effort', 'unknown')}\n\n"
            
            if fix_suggestion.get("code_changes"):
                description += f"*Code Changes:*\n{{code}}\n{fix_suggestion['code_changes']}\n{{code}}\n\n"
            
            if fix_suggestion.get("configuration_changes"):
                description += f"*Configuration Changes:*\n{{code}}\n{fix_suggestion['configuration_changes']}\n{{code}}\n\n"
            
            if fix_suggestion.get("validation_steps"):
                description += f"*Validation Steps:*\n"
                for i, step in enumerate(fix_suggestion['validation_steps'], 1):
                    description += f"# {step}\n"
                description += "\n"
            
            if fix_suggestion.get("prevention"):
                description += f"*Prevention:*\n{fix_suggestion['prevention']}\n\n"
        elif fix_suggestion:
            description += f"h3. Fix Suggestion Status\n"
            description += f"❌ Fix suggestion failed: {fix_suggestion.get('error', 'Unknown error')}\n\n"
        
        # Metadata
        description += f"h3. Metadata\n"
        if analysis.get("analyzed_at"):
            description += f"*Analyzed At:* {analysis['analyzed_at']}\n"
        if fix_suggestion.get("suggested_at"):
            description += f"*Fix Suggested At:* {fix_suggestion['suggested_at']}\n"
        
        return description

class TestCaseJIRAProcessor:
    """
    Processes JSON file with test case results and manages JIRA tickets.
    """
    
    def __init__(self, jira_manager: JIRATicketManager, 
                 ticket_config: Dict[str, Any] = None):
        """
        Initialize with JIRA manager and optional ticket configuration.
        
        Args:
            jira_manager: JIRATicketManager instance
            ticket_config: Configuration for ticket creation/updates
                          {
                              'labels': ['custom-label1', 'custom-label2'],
                              'components': ['component1', 'component2'],
                              'fix_version': 'v1.0.0',
                              'custom_fields': {'customfield_10001': 'value'},
                              'issue_type': 'Task'
                          }
        """
        self.jira_manager = jira_manager
        self.ticket_config = ticket_config or {}
        self.processed_tests = []
        self.created_tickets = []
        self.updated_tickets = []
        self.errors = []
    
    def process_json_file(self, json_file: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process JSON file with test case results.
        
        Args:
            json_file: Path to JSON file with test results
            dry_run: If True, only simulate without creating/updating tickets
            
        Returns:
            Processing summary
        """
        try:
            # Read JSON file
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract test results
            test_results = self._extract_test_results(data)
            
            if not test_results:
                return {"success": False, "error": "No test results found in JSON file"}
            
            print(f"📖 Found {len(test_results)} test results to process")
            
            if dry_run:
                print("🔍 DRY RUN MODE - No tickets will be created or updated")
            
            # Process each test result
            for i, test_result in enumerate(test_results, 1):
                test_name = test_result.get("test_name", f"test_{i}")
                framework = test_result.get("framework", "unknown")
                
                print(f"\n🔬 Processing {i}/{len(test_results)}: {test_name}")
                
                try:
                    # Check for existing ticket
                    existing_ticket = self.jira_manager.find_existing_ticket(test_name, framework)
                    
                    if existing_ticket:
                        print(f"📝 Found existing ticket: {existing_ticket}")
                        if not dry_run:
                            success = self.jira_manager.update_ticket(
                                existing_ticket,
                                test_result,
                                add_labels=self.ticket_config.get('labels'),
                                add_components=self.ticket_config.get('components'),
                                update_fix_version=self.ticket_config.get('fix_version'),
                                update_custom_fields=self.ticket_config.get('custom_fields')
                            )
                            if success:
                                self.updated_tickets.append(existing_ticket)
                            else:
                                self.errors.append(f"Failed to update ticket {existing_ticket}")
                        else:
                            print(f"🔍 [DRY RUN] Would update ticket: {existing_ticket}")
                    else:
                        print(f"📋 No existing ticket found, creating new one")
                        if not dry_run:
                            new_ticket = self.jira_manager.create_ticket(
                                test_result,
                                custom_labels=self.ticket_config.get('labels'),
                                custom_components=self.ticket_config.get('components'),
                                custom_fix_version=self.ticket_config.get('fix_version'),
                                custom_fields=self.ticket_config.get('custom_fields'),
                                issue_type=self.ticket_config.get('issue_type')
                            )
                            if new_ticket:
                                self.created_tickets.append(new_ticket)
                            else:
                                self.errors.append(f"Failed to create ticket for {test_name}")
                        else:
                            print(f"🔍 [DRY RUN] Would create new ticket for: {test_name}")
                    
                    self.processed_tests.append({
                        "test_name": test_name,
                        "existing_ticket": existing_ticket,
                        "action": "update" if existing_ticket else "create"
                    })
                    
                except Exception as e:
                    error_msg = f"Error processing {test_name}: {e}"
                    print(f"❌ {error_msg}")
                    self.errors.append(error_msg)
            
            # Summary
            summary = self._create_summary()
            print(f"\n✅ Processing Complete!")
            print(f"📊 Summary:")
            print(f"  Tests processed: {summary['total_processed']}")
            print(f"  Tickets created: {summary['tickets_created']}")
            print(f"  Tickets updated: {summary['tickets_updated']}")
            print(f"  Errors: {summary['errors']}")
            
            return summary
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_test_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract test results from various JSON formats."""
        
        # Handle direct array
        if isinstance(data, list):
            return data
        
        # Handle object with test arrays
        for key in ['test_results', 'failed_tests', 'tests', 'failures', 'test_cases']:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # Handle single test case
        if 'test_name' in data or 'name' in data:
            return [data]
        
        return []
    
    def _create_summary(self) -> Dict[str, Any]:
        """Create processing summary."""
        return {
            "success": True,
            "total_processed": len(self.processed_tests),
            "tickets_created": len(self.created_tickets),
            "tickets_updated": len(self.updated_tickets),
            "errors": len(self.errors),
            "created_tickets": self.created_tickets,
            "updated_tickets": self.updated_tickets,
            "error_details": self.errors
        }

def main():
    parser = argparse.ArgumentParser(
        description="Process test case results and manage JIRA tickets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  JIRA_URL       - JIRA server URL (e.g., https://company.atlassian.net)
  JIRA_USERNAME  - JIRA username/email
  JIRA_API_TOKEN - JIRA API token
  JIRA_PROJECT   - JIRA project key (e.g., 'TEST', 'BUG')

Examples:
  # Process test results and create/update JIRA tickets
  python jira_ticket_manager.py test_results.json
  
  # Dry run to see what would be created/updated
  python jira_ticket_manager.py test_results.json --dry-run
  
  # Override project key
  python jira_ticket_manager.py test_results.json --project BUGS
        """
    )
    
    parser.add_argument("json_file", help="JSON file with test case results")
    parser.add_argument("--project", help="JIRA project key (overrides JIRA_PROJECT env var)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without creating/updating tickets")
    parser.add_argument("--config", help="JSON configuration file for ticket customization")
    parser.add_argument("--labels", nargs="*", help="Custom labels to add to tickets")
    parser.add_argument("--components", nargs="*", help="Custom components to add to tickets")
    parser.add_argument("--fix-version", help="Fix version to set on tickets")
    parser.add_argument("--issue-type", default="Bug", help="Issue type for new tickets (default: Bug)")
    
    args = parser.parse_args()
    
    try:
        # Get JIRA configuration from environment
        jira_url = os.getenv("JIRA_URL")
        jira_username = os.getenv("JIRA_USERNAME")  
        jira_api_token = os.getenv("JIRA_API_TOKEN")
        jira_project = args.project or os.getenv("JIRA_PROJECT")
        
        if not all([jira_url, jira_username, jira_api_token, jira_project]):
            print("❌ Missing required JIRA configuration:")
            print("  Set environment variables: JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN, JIRA_PROJECT")
            print("  Or use --project to override project key")
            return 1
        
        print(f"🚀 JIRA Ticket Manager")
        print(f"📁 Input file: {args.json_file}")
        print(f"🏢 JIRA URL: {jira_url}")
        print(f"📋 Project: {jira_project}")
        print("=" * 60)
        
        # Load configuration from file if provided
        config_from_file = {}
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    config_from_file = json.load(f)
                print(f"📋 Loaded configuration from: {args.config}")
            except Exception as e:
                print(f"⚠️  Failed to load config file {args.config}: {e}")
        
        # Build ticket configuration from command line and config file
        ticket_config = {
            'labels': args.labels or config_from_file.get('labels', []),
            'components': args.components or config_from_file.get('components', []),
            'fix_version': args.fix_version or config_from_file.get('fix_version'),
            'issue_type': args.issue_type or config_from_file.get('issue_type', 'Bug'),
            'custom_fields': config_from_file.get('custom_fields', {})
        }
        
        # Initialize JIRA manager with defaults from config
        jira_manager = JIRATicketManager(
            jira_url, jira_username, jira_api_token, jira_project,
            default_issue_type=ticket_config['issue_type'],
            default_labels=config_from_file.get('default_labels', []),
            default_components=config_from_file.get('default_components', []),
            default_fix_version=config_from_file.get('default_fix_version'),
            custom_fields=config_from_file.get('default_custom_fields', {})
        )
        
        # Process test results
        processor = TestCaseJIRAProcessor(jira_manager, ticket_config)
        result = processor.process_json_file(args.json_file, args.dry_run)
        
        if not result["success"]:
            print(f"❌ Processing failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())