#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import sys
import argparse

def convert_junit_to_json(xml_file, output_file=None, framework="junit"):
    """
    Convert JUnit XML file to JSON, including only failed test cases.
    Creates a JSON file with an array of failed tests.
    
    Args:
        xml_file (str): Path to the JUnit XML file
        output_file (str, optional): Path to output JSON file. If None, uses "failed_tests.json"
        framework (str): Testing framework name (default: "junit")
    
    Returns:
        list: JSON array of failed test cases
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"File not found: {xml_file}", file=sys.stderr)
        return None
    
    failed_tests = []
    
    # Handle both testsuites and testsuite root elements
    if root.tag == 'testsuites':
        testsuites = root.findall('testsuite')
    else:
        testsuites = [root] if root.tag == 'testsuite' else []
    
    for testsuite in testsuites:
        for testcase in testsuite.findall('testcase'):
            # Check if test case has failure or error elements
            failures = testcase.findall('failure')
            errors = testcase.findall('error')
            
            if failures or errors:
                # Get failure message from first failure or error
                failure_message = ""
                if failures:
                    failure = failures[0]
                    failure_message = failure.get('message', '') or failure.text or ''
                elif errors:
                    error = errors[0]
                    failure_message = error.get('message', '') or error.text or ''
                
                test_data = {
                    "name": testcase.get('name', 'Unknown Test'),
                    "status": "failed",
                    "failure_message": failure_message.strip(),
                    "framework": framework
                }
                
                failed_tests.append(test_data)
    
    # Always create JSON file with failed tests
    output_filename = output_file or "failed_tests.json"
    with open(output_filename, 'w') as f:
        json.dump(failed_tests, f, indent=2)
    print(f"Created {output_filename} with {len(failed_tests)} failed test cases")
    
    return failed_tests

def main():
    parser = argparse.ArgumentParser(description='Convert JUnit XML to JSON (failed tests only)')
    parser.add_argument('xml_file', help='Path to the JUnit XML file')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: failed_tests.json)')
    parser.add_argument('-f', '--framework', default='junit', help='Testing framework name (default: junit)')
    
    args = parser.parse_args()
    
    convert_junit_to_json(args.xml_file, args.output, args.framework)

if __name__ == '__main__':
    main()