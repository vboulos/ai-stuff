#!/usr/bin/env python3
"""
Generates optimized prompts for Claude to analyze test failures.
No API required - just copy and paste the output into Claude.
"""

import xml.etree.ElementTree as ET
import json
import sys

class TestFailurePromptGenerator:
    """
    Generates Claude prompts for test failure analysis.
    """
    
    def parse_junit_xml(self, xml_file: str) -> list:
        """Parse JUnit XML and extract failures."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        failures = []
        test_id = 1
        
        # Handle both testsuites and testsuite root
        testsuites = root.findall('testsuite') if root.tag == 'testsuites' else [root]
        
        for testsuite in testsuites:
            for testcase in testsuite.findall('testcase'):
                failure = testcase.find('failure')
                if failure is not None:
                    failures.append({
                        'test_id': f"TC{test_id:03d}",
                        'test_name': testcase.get('name', 'Unknown Test'),
                        'suite_name': testsuite.get('name', 'Unknown Suite'),
                        'failure_message': failure.get('message', 'No message'),
                        'failure_details': failure.text or '',
                        'time_taken': testcase.get('time', '0')
                    })
                    test_id += 1
        
        return failures
    
    def generate_single_prompt(self, test_case: dict) -> str:
        """Generate a prompt for a single test failure."""
        
        prompt = f"""I need you to analyze this test failure and provide a structured response.

**TEST FAILURE ANALYSIS REQUEST**

Test Details:
- Test ID: {test_case['test_id']}
- Test Name: {test_case['test_name']}
- Test Suite: {test_case['suite_name']}
- Duration: {test_case['time_taken']}s

Error Message:
{test_case['failure_message']}

Full Error Details:
{test_case['failure_details']}

**PLEASE RESPOND IN THIS EXACT FORMAT:**

FAILURE_TYPE: [Choose ONE from: automation_bug, product_bug, assertion_error, timing_issue, environment_issue, configuration_issue, data_issue, network_issue, dependency_issue, flaky_test]

ROOT_CAUSE: [One clear sentence explaining what caused this failure]

FIX_SUGGESTION: [Detailed, actionable steps to fix this issue]

FIX_CODE: [Actual code to solve the problem - use proper syntax for the testing framework]

**ANALYSIS GUIDELINES:**
- If expected vs actual text differs only by spacing/formatting → assertion_error
- If timeout while waiting for elements/content → timing_issue  
- If element not found/wrong selector → automation_bug
- If API/network related → network_issue
- If environment/infrastructure issues → environment_issue
- If application logic is broken → product_bug

Focus on practical, implementable solutions. Be specific about what needs to be changed in the test code or application.
"""
        return prompt
    
    def generate_batch_prompt(self, failures: list) -> str:
        """Generate a prompt for multiple test failures."""
        
        prompt = "I need you to analyze these test failures and provide structured responses for each.\n\n"
        
        for i, test_case in enumerate(failures, 1):
            prompt += f"**TEST FAILURE #{i}**\n"
            prompt += f"Test ID: {test_case['test_id']}\n"
            prompt += f"Test Name: {test_case['test_name']}\n"
            prompt += f"Error: {test_case['failure_message']}\n"
            prompt += f"Details: {test_case['failure_details'][:300]}...\n\n"
        
        prompt += """**RESPONSE FORMAT REQUIRED:**

For each test failure, respond with:

TEST #{number}:
FAILURE_TYPE: [automation_bug/product_bug/assertion_error/timing_issue/environment_issue/configuration_issue/data_issue/network_issue/dependency_issue/flaky_test]
ROOT_CAUSE: [One sentence explanation]
FIX_SUGGESTION: [Detailed steps to fix]
FIX_CODE: [Actual code solution]

**ANALYSIS RULES:**
- Text mismatch (expected vs actual) = assertion_error
- Timeouts waiting for elements = timing_issue
- Wrong selectors/elements not found = automation_bug
- API/network issues = network_issue
- Application bugs = product_bug

Provide specific, actionable solutions for each failure.
"""
        return prompt
    
    def save_prompts_to_files(self, xml_file: str):
        """Parse XML and save prompts to files."""
        failures = self.parse_junit_xml(xml_file)
        
        if not failures:
            print("❌ No test failures found in XML file")
            return
        
        print(f"📋 Found {len(failures)} test failures")
        
        # Generate individual prompts
        for failure in failures:
            prompt = self.generate_single_prompt(failure)
            filename = f"prompt_{failure['test_id']}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            print(f"✅ Generated prompt: {filename}")
        
        # Generate batch prompt if multiple failures
        if len(failures) > 1:
            batch_prompt = self.generate_batch_prompt(failures)
            with open("prompt_batch_analysis.txt", 'w', encoding='utf-8') as f:
                f.write(batch_prompt)
            print(f"✅ Generated batch prompt: prompt_batch_analysis.txt")
        
        # Show sample prompt
        print(f"\n📝 === Sample Prompt (TC001) ===")
        print(self.generate_single_prompt(failures[0])[:500] + "...")
        
        print(f"\n🚀 === Next Steps ===")
        print("1. Open the generated .txt files")
        print("2. Copy the prompt text")
        print("3. Paste into Claude (web or app)")
        print("4. Get your analysis results!")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        # Create sample XML file
        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="Mocha Tests" time="194.6320" tests="2" failures="1">
  <testsuite name="GRC: Test export CSV functionality in GRC pages" timestamp="2025-09-04T02:24:43" tests="2" time="194.6080" failures="1">
    <testcase name="GRC: Test export CSV functionality in GRC pages RHACM4K-52041: GRC: Policies list can be exported as CSV file from UI" time="0.0000" classname="RHACM4K-52041: GRC: Policies list can be exported as CSV file from UI">
      <failure message="Timed out retrying after 120000ms: expected &lt;dd.pf-v5-c-description-list__description&gt; to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.'" type="AssertionError"><![CDATA[AssertionError: Timed out retrying after 120000ms: expected '<dd.pf-v5-c-description-list__description>' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule for all virtualmachines.kubevirt.io resources with a cluster.open-cluster-management.io/backup-vm label.'
    at eval (webpack://acmqe-grc-test/./tests/cypress/support/views.js:4742:80)
    at Array.forEach (<anonymous>)
    at Context.eval (webpack://acmqe-grc-test/./tests/cypress/support/views.js:4730:26)]]></failure>
    </testcase>
  </testsuite>
</testsuites>'''
        
        with open("sample_test_failure.xml", "w") as f:
            f.write(sample_xml)
        
        print("📝 Created sample XML file: sample_test_failure.xml")
        xml_file = "sample_test_failure.xml"
    else:
        xml_file = sys.argv[1]
    
    try:
        generator = TestFailurePromptGenerator()
        generator.save_prompts_to_files(xml_file)
        
    except FileNotFoundError:
        print(f"❌ File not found: {xml_file}")
        print("Usage: python prompt_generator.py <xml_file>")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()