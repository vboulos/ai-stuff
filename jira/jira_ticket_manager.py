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
    
    def __init__(self, jira_url: str, username: str = None, api_token: str = None, 
                 project_key: str = None, default_issue_type: str = 'Bug', 
                 default_labels: List[str] = None, default_components: List[str] = None, 
                 default_fix_version: str = None, custom_fields: Dict[str, Any] = None):
        """
        Initialize JIRA connection.
        
        Args:
            jira_url: JIRA server URL
            username: JIRA username/email (optional for token auth)
            api_token: JIRA API token or Personal Access Token
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
            # Personal Access Token authentication
            self.jira = JIRA(
                server=jira_url,
                token_auth=api_token
            )
            print(f"✅ Connected to JIRA using Personal Access Token: {jira_url}")
        except Exception as e:
            raise Exception(f"Failed to connect to JIRA: {e}")
    
    def find_existing_ticket(self, test_name: str, framework: str = None) -> Optional[str]:
        """
        Find existing JIRA ticket for a test case by searching for test name in summary.
        
        Args:
            test_name: Name of the test case
            framework: Testing framework (optional)
            
        Returns:
            JIRA ticket key if found, None otherwise
        """
        try:
            # Search for tickets with "Test Failure:" prefix and our test name
            # Use broader search terms to catch truncated summaries
            
            # Extract key identifying parts of the test name
            key_parts = self._extract_key_test_identifiers(test_name)
            
            # Build search queries with different strategies
            search_queries = []
            
            # Strategy 1: Search for tickets starting with "Test Failure:"
            search_queries.append(f'project = {self.project_key} AND summary ~ "Test Failure:"')
            
            # Strategy 2: Search for specific key parts if we have them
            for key_part in key_parts:
                if len(key_part) > 5:  # Only use meaningful parts
                    escaped_part = key_part.replace('"', '\\"')
                    search_queries.append(f'project = {self.project_key} AND summary ~ "{escaped_part}"')
            
            # Strategy 3: Search by the first few words of the test name (more specific)
            # For "GRC: Test export CSV functionality..." search for "GRC Test export"
            test_words = test_name.split()[:4]  # Take first 4 words
            if len(test_words) >= 3:
                search_phrase = ' '.join(test_words)
                escaped_phrase = search_phrase.replace('"', '\\"')
                search_queries.append(f'project = {self.project_key} AND summary ~ "{escaped_phrase}"')
            
            for query in search_queries:
                try:
                    print(f"🔍 Searching with query: {query}")
                    issues = self.jira.search_issues(query, maxResults=20)
                    
                    # Collect matching tickets
                    matching_tickets = []
                    for issue in issues:
                        # Debug: Show what we're comparing with status
                        status = getattr(issue.fields, 'status', None)
                        status_name = status.name if status else 'Unknown'
                        print(f"    Comparing with: {issue.key} - {issue.fields.summary} (Status: {status_name})")
                        
                        # Check if this matches our test
                        if self._is_same_test_ticket(test_name, issue.fields.summary, issue.fields.description):
                            matching_tickets.append((issue, status_name))
                            print(f"    ✓ Potential match: {issue.key} (Status: {status_name})")
                    
                    # If we found matches, prefer open tickets over closed ones
                    if matching_tickets:
                        # Define closed statuses
                        closed_statuses = {"Closed", "Done", "Resolved", "Fixed", "Cancelled", "Rejected", "Complete"}
                        
                        # First, try to find an open ticket
                        for issue, status_name in matching_tickets:
                            if status_name not in closed_statuses:
                                print(f"✅ Found existing open ticket: {issue.key} - {issue.fields.summary} (Status: {status_name})")
                                return issue.key
                        
                        # If no open ticket found, use the first closed one (but warn about it)
                        issue, status_name = matching_tickets[0]
                        print(f"⚠️  Found matching ticket but it's closed: {issue.key} - {issue.fields.summary} (Status: {status_name})")
                        print(f"    Will create a new ticket instead of updating closed one.")
                        # Don't return the closed ticket - let it create a new one
                        continue
                            
                except JIRAError as e:
                    print(f"⚠️  Search query failed: {query} - {e}")
                    continue
            
            print(f"📋 No existing ticket found for test: {test_name[:50]}...")
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
            custom_fix_version: Fix version for this specific ticket1
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
            
            # Determine priority based on analysis (validate it exists)
            priority = self._determine_priority(analysis)
            
            # Create issue
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type or self.default_issue_type}
            }
            
            # Add priority only if it's valid
            # try:
            #     valid_priorities = [p.name for p in self.jira.priorities()]
            #     if priority in valid_priorities:
            #         issue_dict['priority'] = {'name': priority}
            #     else:
            #         print(f"⚠️  Invalid priority '{priority}', using default")
            # except:
            #     print(f"⚠️  Could not validate priority, skipping")
            
            # Build labels only if any are defined
            labels = []
            
            # Add default labels if defined
            if self.default_labels:
                labels.extend(self.default_labels)
            
            # Add analysis-based labels if defined
            if analysis.get("error_category"):
                labels.append(f'category-{analysis["error_category"]}')
            if analysis.get("severity"):
                labels.append(f'severity-{analysis["severity"]}')
            
            # Add framework label
            if framework and framework.lower() != 'unknown':
                labels.append(f'framework-{framework.lower()}')
            
            # Add custom labels if provided
            if custom_labels:
                labels.extend(custom_labels)
            
            # Only add labels if we have any
            if labels:
                issue_dict['labels'] = list(set(labels))
            
            # Build components only if any are defined
            components = []
            
            # Only validate components if we might need them
            valid_components = []
            if self.default_components or custom_components or original_test.get("suite_name"):
                try:
                    valid_components = [comp.name for comp in self.jira.project_components(self.project_key)]
                except:
                    valid_components = []
            
            # Add default components only if defined
            if self.default_components:
                for comp_name in self.default_components:
                    if not valid_components or comp_name in valid_components:
                        components.append({'name': comp_name})
                    else:
                        print(f"⚠️  Skipping invalid default component: {comp_name}")
            
            # Add custom components only if provided
            if custom_components:
                for comp_name in custom_components:
                    if not valid_components or comp_name in valid_components:
                        components.append({'name': comp_name})
                    else:
                        print(f"⚠️  Skipping invalid custom component: {comp_name}")
            
            # Remove duplicates
            unique_components = []
            seen_names = set()
            for comp in components:
                if comp['name'] not in seen_names:
                    unique_components.append(comp)
                    seen_names.add(comp['name'])
            
            # Only add components if we have any
            if unique_components:
                issue_dict['components'] = unique_components
            
            # Add fix version only if specified
            fix_version = custom_fix_version or self.default_fix_version
            if fix_version:
                try:
                    project_versions = [v.name for v in self.jira.project_versions(self.project_key)]
                    if fix_version in project_versions:
                        issue_dict['fixVersions'] = [{'name': fix_version}]
                    else:
                        print(f"⚠️  Invalid fix version '{fix_version}', skipping")
                        print(f"Available versions: {project_versions[:5]}...")  # Show first 5
                except:
                    print(f"⚠️  Could not validate fix version, skipping")
            
            # Add custom fields only if any are defined
            all_custom_fields = {}
            if self.custom_fields:
                all_custom_fields.update(self.custom_fields)
            if custom_fields:
                all_custom_fields.update(custom_fields)
            
            # Apply custom fields to issue_dict only if we have any
            if all_custom_fields:
                for field_name, field_value in all_custom_fields.items():
                    issue_dict[field_name] = field_value
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            print(f"✅ Created new ticket: {new_issue.key} - {summary}")
            return new_issue.key
            
        except JIRAError as e:
            print(f"❌ Failed to create JIRA ticket: {e}")
            print(f"🔍 Request payload: {issue_dict}")
            if hasattr(e, 'response') and e.response:
                print(f"🔍 Response content: {e.response.text}")
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
            
            # Update fix version if provided (append to existing)
            if update_fix_version:
                current_fix_versions = [ver.name for ver in (issue.fields.fixVersions or [])]
                if update_fix_version not in current_fix_versions:
                    current_fix_versions.append(update_fix_version)
                update_fields['fixVersions'] = [{'name': name} for name in current_fix_versions]
            
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
    
    def _extract_key_test_identifiers(self, test_name: str) -> List[str]:
        """
        Extract key identifying parts from a test name.
        
        Args:
            test_name: Full test name
            
        Returns:
            List of key identifying strings
        """
        identifiers = []
        
        # Look for patterns like RHACM4K-52041, JIRA-123, etc.
        jira_pattern = re.findall(r'[A-Z]+-\d+', test_name)
        identifiers.extend(jira_pattern)
        
        # Extract meaningful words (longer than 3 chars, not common words)
        words = re.findall(r'\b\w{4,}\b', test_name)
        common_words = {'test', 'Test', 'functionality', 'pages', 'from', 'with', 'that', 'this'}
        meaningful_words = [w for w in words if w not in common_words]
        identifiers.extend(meaningful_words[:3])  # Take first 3 meaningful words
        
        return identifiers
    
    def _is_same_test_ticket(self, test_name: str, summary: str, description: str = None) -> bool:
        """
        Check if a JIRA ticket is for the same test, handling truncated summaries.
        
        Args:
            test_name: Original test name
            summary: JIRA issue summary
            description: JIRA issue description (optional)
            
        Returns:
            True if this is likely the same test
        """
        if not summary:
            return False
        
        # Remove "Test Failure: " prefix if present
        summary_clean = summary
        if summary_clean.startswith("Test Failure: "):
            summary_clean = summary_clean[14:]  # Remove "Test Failure: "
        
        print(f"      🔍 Comparing:")
        print(f"         Test: {test_name}")
        print(f"         Summary: {summary_clean}")
        
        # Check for exact match first
        if test_name == summary_clean:
            print(f"         ✅ Exact match!")
            return True
        
        # Handle truncated summaries (ending with "...")
        if summary_clean.endswith("..."):
            summary_truncated = summary_clean[:-3]
            print(f"         📏 Truncated summary: {summary_truncated}")
            # Check if test name starts with the truncated summary
            if test_name.startswith(summary_truncated) and len(summary_truncated) > 20:
                print(f"         ✅ Truncated match!")
                return True
        
        # Check if summary is truncated version of our test name (no ... at end)
        if len(summary_clean) < len(test_name) and test_name.startswith(summary_clean) and len(summary_clean) > 20:
            print(f"         ✅ Summary is truncated version of test!")
            return True
        
        # Extract key identifiers and see if they match
        test_identifiers = self._extract_key_test_identifiers(test_name)
        summary_identifiers = self._extract_key_test_identifiers(summary_clean)
        
        print(f"         🔑 Test identifiers: {test_identifiers}")
        print(f"         🔑 Summary identifiers: {summary_identifiers}")
        
        # If we have JIRA ticket numbers, they should match
        test_jira_ids = [id for id in test_identifiers if re.match(r'[A-Z]+-\d+', id)]
        summary_jira_ids = [id for id in summary_identifiers if re.match(r'[A-Z]+-\d+', id)]
        
        if test_jira_ids and summary_jira_ids:
            match = bool(set(test_jira_ids) & set(summary_jira_ids))
            if match:
                print(f"         ✅ JIRA ID match: {set(test_jira_ids) & set(summary_jira_ids)}")
                return True
        
        # Enhanced matching for the specific case - check if the beginning of both strings match significantly
        # For the case where test is "GRC: Test export CSV..." and summary is "GRC: Test export CSV..."
        # Get the first 50 characters and compare
        test_prefix = test_name[:50].lower()
        summary_prefix = summary_clean[:50].lower()
        
        if len(test_prefix) > 20 and len(summary_prefix) > 20:
            # Calculate similarity of the prefixes
            common_length = 0
            min_length = min(len(test_prefix), len(summary_prefix))
            for i in range(min_length):
                if test_prefix[i] == summary_prefix[i]:
                    common_length += 1
                else:
                    break
            
            # If at least 80% of the prefix matches and it's substantial
            if common_length >= min_length * 0.8 and common_length > 20:
                print(f"         ✅ Prefix match! ({common_length}/{min_length} chars)")
                return True
        
        # Check for significant word overlap
        if len(test_identifiers) >= 2 and len(summary_identifiers) >= 2:
            overlap = len(set(test_identifiers) & set(summary_identifiers))
            print(f"         📊 Word overlap: {overlap}/{len(test_identifiers)}")
            if overlap >= 2:
                print(f"         ✅ Significant word overlap!")
                return True
        
        # Check in description if available
        if description and test_name in description:
            print(f"         ✅ Found in description!")
            return True
        
        print(f"         ❌ No match")
        return False
    
    def _map_suite_to_component(self, suite_name: str, valid_components: List[str]) -> Optional[str]:
        """
        Map test suite names to valid JIRA components.
        
        Args:
            suite_name: Test suite name from the test data
            valid_components: List of valid component names in the project
            
        Returns:
            Mapped component name or None if no match found
        """
        suite_lower = suite_name.lower()
        
        # Direct mapping for common patterns
        mappings = {
            'grc': 'GRC',
            'governance': 'GRC', 
            'policy': 'GRC',
            'application': 'Application Lifecycle',
            'cluster': 'Cluster Lifecycle',
            'observability': 'Observability',
            'search': 'Search',
            'console': 'Console',
            'install': 'Installation',
            'upgrade': 'Upgrade'
        }
        
        # Try direct mapping first
        for keyword, component in mappings.items():
            if keyword in suite_lower and component in valid_components:
                return component
        
        # Try fuzzy matching with valid components
        for component in valid_components:
            component_lower = component.lower()
            # Check if any words from suite name appear in component name
            suite_words = suite_lower.split()
            for word in suite_words:
                if len(word) > 3 and word in component_lower:
                    return component
        
        # Default fallback - return first valid component if available
        if valid_components:
            return valid_components[0]
        
        return None
    
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
        jira_url = os.getenv("JIRA_URL", "https://issues.redhat.com")
        jira_username = os.getenv("JIRA_USERNAME")  # Optional for PAT
        jira_api_token = os.getenv("JIRA_API_TOKEN")
        jira_project = args.project or os.getenv("JIRA_PROJECT")
        
        # Validate required configuration
        if not jira_api_token:
            print("❌ Missing required JIRA API token:")
            print("  Set environment variable: JIRA_API_TOKEN")
            print("  Get your token from: https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens")
            return 1
        
        if not jira_project:
            print("❌ Missing required JIRA project key:")
            print("  Set environment variable: JIRA_PROJECT or use --project argument")
            print("  Example project keys: RHELPLAN, ACM, OCPBUGS")
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