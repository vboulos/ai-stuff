#!/usr/bin/env python3
"""
JUnit XML to JSON Converter - Extracts failed test cases only
"""

import xml.etree.ElementTree as ET
import json
import sys
import argparse
import glob
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class JUnitXMLConverter:
    """
    Converts JUnit XML files to JSON format, including only failed test cases.
    """
    
    def __init__(self):
        self.failed_tests = []
        self.processed_files = []
        self.processing_errors = []
    
    def convert_xml_file(self, xml_file: str, framework: str = "junit") -> List[Dict[str, Any]]:
        """
        Convert a single JUnit XML file to JSON format.
        
        Args:
            xml_file: Path to the JUnit XML file
            framework: Testing framework name (default: "junit")
            
        Returns:
            List of failed test cases in JSON format
        """
        failed_tests = []
        
        try:
            print(f"📖 Processing: {xml_file}")
            
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Handle both testsuites and testsuite root elements
            if root.tag == 'testsuites':
                testsuites = root.findall('testsuite')
            else:
                testsuites = [root] if root.tag == 'testsuite' else []
            
            for testsuite in testsuites:
                suite_name = testsuite.get('name', 'Unknown Suite')
                
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
                        
                        # Create test data in specified format
                        test_data = {
                            "name": testcase.get('name', 'Unknown Test'),
                            "status": "failed",
                            "failure_message": failure_message.strip(),
                            "framework": framework
                        }
                        
                        # Optional: Add additional metadata
                        if testcase.get('classname'):
                            test_data["class_name"] = testcase.get('classname')
                        if testcase.get('time'):
                            test_data["execution_time"] = float(testcase.get('time', 0))
                        if suite_name != 'Unknown Suite':
                            test_data["suite_name"] = suite_name
                        
                        failed_tests.append(test_data)
            
            if failed_tests:
                print(f"✅ Found {len(failed_tests)} failed tests in {xml_file}")
            else:
                print(f"ℹ️  No failed tests found in {xml_file}")
            
            self.processed_files.append({
                "file": xml_file,
                "failed_tests": len(failed_tests),
                "status": "success"
            })
            
            return failed_tests
            
        except ET.ParseError as e:
            error_msg = f"XML parsing error in {xml_file}: {e}"
            print(f"❌ {error_msg}")
            self.processing_errors.append(error_msg)
            self.processed_files.append({
                "file": xml_file,
                "failed_tests": 0,
                "status": "parse_error",
                "error": str(e)
            })
            return []
        except FileNotFoundError:
            error_msg = f"File not found: {xml_file}"
            print(f"❌ {error_msg}")
            self.processing_errors.append(error_msg)
            self.processed_files.append({
                "file": xml_file,
                "failed_tests": 0,
                "status": "file_not_found"
            })
            return []
        except Exception as e:
            error_msg = f"Error processing {xml_file}: {e}"
            print(f"❌ {error_msg}")
            self.processing_errors.append(error_msg)
            self.processed_files.append({
                "file": xml_file,
                "failed_tests": 0,
                "status": "error",
                "error": str(e)
            })
            return []
    
    def convert_multiple_files(self, xml_files: List[str], framework: str = "junit") -> List[Dict[str, Any]]:
        """
        Convert multiple JUnit XML files to JSON format.
        
        Args:
            xml_files: List of paths to JUnit XML files
            framework: Testing framework name
            
        Returns:
            Combined list of failed test cases from all files
        """
        all_failed_tests = []
        
        for xml_file in xml_files:
            failed_tests = self.convert_xml_file(xml_file, framework)
            all_failed_tests.extend(failed_tests)
        
        return all_failed_tests
    
    def convert_from_pattern(self, pattern: str, framework: str = "junit") -> List[Dict[str, Any]]:
        """
        Convert JUnit XML files matching a glob pattern.
        
        Args:
            pattern: Glob pattern to match XML files (e.g., "*.xml", "test-results/**/*.xml")
            framework: Testing framework name
            
        Returns:
            Combined list of failed test cases from all matching files
        """
        xml_files = glob.glob(pattern, recursive=True)
        
        if not xml_files:
            print(f"⚠️  No XML files found matching pattern: {pattern}")
            return []
        
        print(f"📂 Found {len(xml_files)} XML files matching pattern: {pattern}")
        
        return self.convert_multiple_files(xml_files, framework)
    
    def save_to_json(self, failed_tests: List[Dict[str, Any]], output_file: str, 
                    include_metadata: bool = True) -> Dict[str, Any]:
        """
        Save failed test cases to JSON file.
        
        Args:
            failed_tests: List of failed test cases
            output_file: Output JSON file path
            include_metadata: Whether to include processing metadata
            
        Returns:
            Summary of the operation
        """
        try:
            if include_metadata:
                output_data = {
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "total_failed_tests": len(failed_tests),
                        "processed_files": len(self.processed_files),
                        "processing_errors": len(self.processing_errors),
                        "source_files": [f["file"] for f in self.processed_files if f["status"] == "success"]
                    },
                    "processing_summary": {
                        "successful_files": len([f for f in self.processed_files if f["status"] == "success"]),
                        "failed_files": len([f for f in self.processed_files if f["status"] != "success"]),
                        "files_processed": self.processed_files
                    },
                    "failed_tests": failed_tests
                }
                
                if self.processing_errors:
                    output_data["processing_errors"] = self.processing_errors
            else:
                # Simple format - just the failed tests array
                output_data = failed_tests
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            print(f"\n📁 Saved {len(failed_tests)} failed tests to: {output_file}")
            
            return {
                "success": True,
                "output_file": output_file,
                "total_failed_tests": len(failed_tests),
                "processed_files": len(self.processed_files)
            }
            
        except Exception as e:
            error_msg = f"Error saving to {output_file}: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        successful_files = [f for f in self.processed_files if f["status"] == "success"]
        failed_files = [f for f in self.processed_files if f["status"] != "success"]
        
        return {
            "total_files_processed": len(self.processed_files),
            "successful_files": len(successful_files),
            "failed_files": len(failed_files),
            "total_failed_tests": sum(f["failed_tests"] for f in successful_files),
            "processing_errors": len(self.processing_errors)
        }

def create_sample_junit_xml():
    """Create a sample JUnit XML file for testing."""
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite name="cypress_tests" tests="4" failures="2" errors="0" time="45.123">
        <testcase name="test_cypress_text_assertion" classname="cypress.text_tests" time="12.5">
            <failure message="Text assertion failed" type="AssertionError">
                Timed out retrying after 120000ms: expected '&lt;dd.pf-v5-c-description-list__description&gt;' to contain text 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name. Creates a velero Schedule', but the text was 'Policy is placed on hub or managed clusters with label acm-virt-config=acm-dr-virt-config-file-name.Creates a velero Schedule'
            </failure>
        </testcase>
        <testcase name="test_cypress_element_not_found" classname="cypress.element_tests" time="8.2">
            <failure message="Element not found" type="ElementNotFoundError">
                Timed out retrying after 4000ms: Expected to find element: `.submit-button`, but never found it.
            </failure>
        </testcase>
        <testcase name="test_cypress_successful" classname="cypress.success_tests" time="2.1">
            <!-- This test passed, so no failure element -->
        </testcase>
        <testcase name="test_cypress_another_success" classname="cypress.success_tests" time="1.8">
            <!-- This test also passed -->
        </testcase>
    </testsuite>
    <testsuite name="pytest_tests" tests="2" failures="1" errors="0" time="15.456">
        <testcase name="test_database_connection" classname="tests.db_tests" time="5.2">
            <failure message="Database connection failed" type="ConnectionError">
                psycopg2.OperationalError: could not connect to server: Connection refused
                Is the server running on host "localhost" (127.0.0.1) and accepting TCP/IP connections on port 5432?
            </failure>
        </testcase>
        <testcase name="test_api_success" classname="tests.api_tests" time="3.1">
            <!-- This test passed -->
        </testcase>
    </testsuite>
</testsuites>"""
    
    with open('sample_junit.xml', 'w') as f:
        f.write(sample_xml)
    
    print("📝 Sample JUnit XML file created: sample_junit.xml")

def main():
    parser = argparse.ArgumentParser(
        description="Convert JUnit XML files to JSON (failed tests only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single XML file
  python junit_xml_to_json.py test-results.xml
  
  # Convert multiple XML files
  python junit_xml_to_json.py file1.xml file2.xml file3.xml
  
  # Convert all XML files in directory (recursive)
  python junit_xml_to_json.py "test-results/**/*.xml"
  
  # Specify framework and output file
  python junit_xml_to_json.py results.xml --framework cypress --output failed_tests.json
  
  # Simple format without metadata
  python junit_xml_to_json.py results.xml --simple
  
  # Create sample XML file for testing
  python junit_xml_to_json.py --sample
        """
    )
    
    parser.add_argument("xml_files", nargs='*', help="JUnit XML file(s) or glob pattern")
    parser.add_argument("--output", "-o", default="failed_tests.json", help="Output JSON file (default: failed_tests.json)")
    parser.add_argument("--framework", "-f", default="junit", help="Testing framework name (default: junit)")
    parser.add_argument("--simple", action="store_true", help="Simple format without metadata")
    parser.add_argument("--sample", action="store_true", help="Create sample JUnit XML file")
    
    args = parser.parse_args()
    
    try:
        if args.sample:
            create_sample_junit_xml()
            return 0
        
        if not args.xml_files:
            parser.error("XML files are required (or use --sample)")
        
        print(f"🚀 JUnit XML to JSON Converter")
        print(f"📁 Framework: {args.framework}")
        print("=" * 60)
        
        converter = JUnitXMLConverter()
        
        # Handle single pattern vs multiple files
        if len(args.xml_files) == 1 and ('*' in args.xml_files[0] or '?' in args.xml_files[0]):
            # Treat as glob pattern
            failed_tests = converter.convert_from_pattern(args.xml_files[0], args.framework)
        else:
            # Treat as individual file paths
            failed_tests = converter.convert_multiple_files(args.xml_files, args.framework)
        
        # Save results
        result = converter.save_to_json(failed_tests, args.output, include_metadata=not args.simple)
        
        if result["success"]:
            summary = converter.get_summary()
            print(f"\n✅ Conversion Complete!")
            print(f"📊 Summary:")
            print(f"  Files processed: {summary['total_files_processed']}")
            print(f"  Successful: {summary['successful_files']}")
            print(f"  Failed: {summary['failed_files']}")
            print(f"  Total failed tests: {summary['total_failed_tests']}")
            print(f"  Output file: {args.output}")
            
            if summary['processing_errors'] > 0:
                print(f"  ⚠️  Processing errors: {summary['processing_errors']}")
        else:
            print(f"❌ Conversion failed: {result['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Conversion interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())