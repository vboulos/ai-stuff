#!/usr/bin/env python3
"""
Enhanced Test Failure Analysis with Source Code Scanning

This script implements the analyze-test-failures skill with source code analysis.
It scans test source files, matches failures to actual test code, and provides
detailed fix suggestions based on the actual implementation.
"""

import argparse
import json
import logging
import os
import sys
import time
import re
import fnmatch
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
import urllib.parse
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SkillPromptGenerator:
    """Generate AI prompts based on skill specification files"""
    
    def __init__(self, skill_file_path: str = None):
        self.skill_file_path = skill_file_path or os.path.join(os.path.dirname(__file__), 'skills', 'analyze-test-failures.md')
        self.skill_content = self._load_skill_file()
        self.schema_template = self._extract_json_schema()
        self.analysis_categories = self._extract_failure_categories()
        self.core_features = self._extract_core_features()
    
    def _load_skill_file(self) -> str:
        """Load the skill specification file"""
        try:
            with open(self.skill_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded skill specification from {self.skill_file_path}")
            return content
        except FileNotFoundError:
            logger.warning(f"Skill file not found at {self.skill_file_path}, using fallback prompts")
            return ""
        except Exception as e:
            logger.error(f"Failed to load skill file: {e}")
            return ""
    
    def _extract_json_schema(self) -> str:
        """Extract the JSON output schema from the skill file"""
        if not self.skill_content:
            return self._get_fallback_schema()
        
        # Find the JSON schema section
        start_marker = '```json'
        end_marker = '```'
        
        start_idx = self.skill_content.find(start_marker)
        if start_idx == -1:
            return self._get_fallback_schema()
        
        start_idx += len(start_marker)
        end_idx = self.skill_content.find(end_marker, start_idx)
        
        if end_idx == -1:
            return self._get_fallback_schema()
        
        schema = self.skill_content[start_idx:end_idx].strip()
        return schema
    
    def _extract_failure_categories(self) -> str:
        """Extract failure analysis categories from the skill file"""
        if not self.skill_content:
            return "automation|infrastructure|product|environment"
        
        # Find the failure categories section
        categories_section = ""
        lines = self.skill_content.split('\n')
        
        in_categories = False
        for line in lines:
            if '## Failure Analysis Categories' in line:
                in_categories = True
                continue
            elif in_categories and line.startswith('## '):
                break
            elif in_categories:
                categories_section += line + '\n'
        
        return categories_section.strip() if categories_section else "automation|infrastructure|product|environment"
    
    def _extract_core_features(self) -> str:
        """Extract core features description from the skill file"""
        if not self.skill_content:
            return "Analyze test failures and provide fix suggestions"
        
        # Find the core features section
        features_section = ""
        lines = self.skill_content.split('\n')
        
        in_features = False
        for line in lines:
            if '## Core Features' in line:
                in_features = True
                continue
            elif in_features and line.startswith('## '):
                break
            elif in_features:
                features_section += line + '\n'
        
        return features_section.strip() if features_section else "Analyze test failures and provide fix suggestions"
    
    def _get_fallback_schema(self) -> str:
        """Fallback JSON schema if skill file is not available"""
        return '''{
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
    "category": "string"
  },
  "fixMetadata": {
    "confidenceScore": "float",
    "automationBug": "boolean",
    "estimatedEffort": "string",
    "suggestedLines": ["string"]
  }
}'''
    
    def generate_analysis_prompt(self, failure: Dict, build_info: Dict, test_source_info: Optional[Dict], options: Dict) -> str:
        """Generate AI analysis prompt based on skill specification"""
        
        # Extract key sections from skill
        overview = self._extract_section('## Overview')
        core_features = self.core_features
        categories = self.analysis_categories
        
        # Build source code section
        source_code_section = ""
        if test_source_info:
            source_code_section = f"""
ACTUAL TEST SOURCE CODE:
File: {test_source_info.get('relative_path', 'Unknown')}
Line: {test_source_info.get('line_number', 0)}
Language: {test_source_info.get('language', 'Unknown')}

```{test_source_info.get('language', '')}
{test_source_info.get('source_code', 'Source code not available')}
```
"""
        else:
            source_code_section = """
SOURCE CODE: Not available - analysis based on failure information only
"""

        # Check if this is an RHACM4K test case
        is_rhacm_test = 'RHACM4K-' in failure['testCaseName']
        rhacm_section = ""
        
        if is_rhacm_test:
            rhacm_id = ""
            import re
            rhacm_match = re.search(r'RHACM4K-\d+', failure['testCaseName'])
            if rhacm_match:
                rhacm_id = rhacm_match.group(0)
            
            rhacm_section = f"""
## RHACM4K ANALYSIS REQUIREMENTS:
This is an RHACM4K test case ({rhacm_id}). You MUST provide DETAILED analysis including:

### ROOT CAUSE ANALYSIS:
1. **Technical Cause**: Detailed explanation of the technical root cause
2. **Failure Conditions**: Specific conditions that triggered the failure
3. **Underlying Issues**: Technical issues like timing, selectors, assertions, data dependencies
4. **Environmental Factors**: Environmental conditions affecting the test
5. **Code Logic Problems**: Problems in test logic or incorrect assumptions

### CODE FIX SUGGESTIONS:
1. **Exact Line Numbers**: Specify which lines need modification
2. **Current Code**: Show the current problematic code snippets
3. **Suggested Code**: Provide the exact replacement code
4. **Fix Explanation**: Explain why this change fixes the root cause
5. **Alternative Approaches**: Suggest other ways to fix the issue if applicable

### STRUCTURAL DATA REQUIREMENTS:
1. **Test Source File**: Full path and filename of the source file hosting this test case
2. **Fix Location**: Exact code block or file requiring modification to fix the failure  
3. **Bug Type**: Distinguish between test_framework, application, or automation bug
4. **Enhanced Mapping**: Include problematicLines, currentCode, and suggestedReplacements
"""

        prompt = f"""
You are an expert test automation engineer implementing the "analyze-test-failures" skill.

{overview if overview else "Perform comprehensive analysis of test failures with JUnit scanning, code mapping, and automated fix suggestions."}

## Your Capabilities:
{core_features}

## Analysis Categories:
{categories}

{rhacm_section}

TEST FAILURE TO ANALYZE:
- Test Name: {failure['testCaseName']}
- Test Class: {failure['className']}
- Suite: {failure['suiteName']}
- Duration: {failure['duration']}s  
- Failure Message: {failure['failureMessage']}
- Stack Trace: {failure['stackTrace']}

{source_code_section}

BUILD CONTEXT:
- Pipeline: {build_info.get('fullDisplayName', 'Unknown')}
- Result: {build_info.get('result', 'Unknown')}
- URL: {build_info.get('url', 'Unknown')}

INSTRUCTIONS:
Analyze this test failure following the skill specification above. Provide your analysis in this EXACT JSON format:

{self.schema_template}

FOCUS ON:
1. **Deep Root Cause Analysis**: 
   - Analyze the exact technical cause of the failure
   - Identify specific conditions that triggered the failure
   - Examine underlying issues (timing, selectors, assertions, data dependencies)
   - Consider environmental factors and code logic problems

2. **Specific Code Fix Suggestions**: 
   - Provide EXACT line numbers that need modification
   - Show the current problematic code snippets
   - Provide precise replacement code with full context
   - Explain WHY each change fixes the root cause
   - Suggest alternative fix approaches when applicable

3. **Enhanced Source Code Mapping**:
   - Map failure to exact file paths and line numbers
   - Identify problematic lines and current code
   - Provide suggested replacements with context
   - Include language-specific fix recommendations

4. **Automation Bug Detection**: Distinguish automation bugs from product issues
5. **Confidence Scoring**: Rate your confidence in the analysis (0.0 to 1.0)
6. **Categorization**: Classify as automation, infrastructure, product, or environment issue
{"7. **RHACM4K Requirements**: Include testSourceFile, fixLocation, and enhanced structural data" if is_rhacm_test else ""}

CRITICAL: If source code is available, you MUST provide line-specific fixes with exact code changes. If source code is not available, provide detailed guidance on where to look and what to fix.

Return ONLY the JSON structure, no additional text.
"""
        
        return prompt
    
    def _extract_section(self, section_header: str) -> str:
        """Extract a specific section from the skill file"""
        if not self.skill_content:
            return ""
        
        lines = self.skill_content.split('\n')
        section_content = ""
        in_section = False
        
        for line in lines:
            if line.strip() == section_header:
                in_section = True
                continue
            elif in_section and line.startswith('## '):
                break
            elif in_section:
                section_content += line + '\n'
        
        return section_content.strip()


class JUnitXMLParser:
    """Parse JUnit XML files to extract test failures"""
    
    def __init__(self, xml_paths: List[str]):
        self.xml_paths = xml_paths
    
    def extract_failures(self) -> List[Dict]:
        """Extract test failures from JUnit XML files"""
        failures = []
        xml_files = self._discover_xml_files()
        
        logger.info(f"Found {len(xml_files)} JUnit XML files to process")
        
        for xml_file in xml_files:
            try:
                logger.info(f"Processing XML file: {xml_file}")
                failures.extend(self._parse_xml_file(xml_file))
            except Exception as e:
                logger.error(f"Failed to parse XML file {xml_file}: {e}")
                continue
        
        logger.info(f"Extracted {len(failures)} test failures from XML files")
        return failures
    
    def _discover_xml_files(self) -> List[str]:
        """Discover all XML files from the provided paths"""
        xml_files = []
        
        for path in self.xml_paths:
            if os.path.isfile(path):
                xml_files.append(path)
            elif os.path.isdir(path):
                # Search for XML files in directory
                xml_pattern = os.path.join(path, '**/*.xml')
                xml_files.extend(glob.glob(xml_pattern, recursive=True))
                
                # Also search for common JUnit file patterns
                junit_patterns = [
                    'junit*.xml', 'TEST-*.xml', '*-results.xml', 
                    'surefire-reports/*.xml', 'test-results/*.xml'
                ]
                for pattern in junit_patterns:
                    pattern_path = os.path.join(path, '**', pattern)
                    xml_files.extend(glob.glob(pattern_path, recursive=True))
            else:
                # Treat as glob pattern
                xml_files.extend(glob.glob(path, recursive=True))
        
        # Remove duplicates and filter for actual XML files
        xml_files = list(set(xml_files))
        xml_files = [f for f in xml_files if self._is_junit_xml(f)]
        
        return xml_files
    
    def _is_junit_xml(self, file_path: str) -> bool:
        """Check if file is a JUnit XML file"""
        if not file_path.endswith('.xml'):
            return False
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Check for JUnit XML structure
            return root.tag in ['testsuites', 'testsuite'] or 'testsuite' in [child.tag for child in root]
        except Exception:
            return False
    
    def _parse_xml_file(self, xml_file: str) -> List[Dict]:
        """Parse a single JUnit XML file"""
        failures = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Handle different JUnit XML structures
            testsuites = []
            if root.tag == 'testsuites':
                testsuites = root.findall('testsuite')
            elif root.tag == 'testsuite':
                testsuites = [root]
            else:
                # Look for testsuite elements
                testsuites = root.findall('.//testsuite')
            
            for testsuite in testsuites:
                suite_name = testsuite.get('name', 'Unknown Suite')
                
                # Find failed test cases
                testcases = testsuite.findall('testcase')
                for testcase in testcases:
                    # Check for failures and errors
                    failure_elem = testcase.find('failure')
                    error_elem = testcase.find('error')
                    
                    if failure_elem is not None or error_elem is not None:
                        failure_info = self._extract_failure_info(testcase, testsuite, failure_elem, error_elem)
                        failure_info['sourceFile'] = xml_file
                        
                        # Filter for RHACM4K pattern
                        test_name = failure_info.get('testCaseName', '')
                        if 'RHACM4K-' in test_name:
                            failure_info['rhacmId'] = self._extract_rhacm_id(test_name)
                            failures.append(failure_info)
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {xml_file}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing {xml_file}: {e}")
        
        return failures
    
    def _extract_rhacm_id(self, test_name: str) -> str:
        """Extract RHACM4K ID from test name"""
        import re
        match = re.search(r'RHACM4K-\d+', test_name)
        return match.group(0) if match else ""
    
    def _extract_failure_info(self, testcase, testsuite, failure_elem, error_elem) -> Dict:
        """Extract failure information from XML elements"""
        test_name = testcase.get('name', '')
        class_name = testcase.get('classname', testsuite.get('name', ''))
        duration = float(testcase.get('time', '0'))
        
        # Get failure details
        if failure_elem is not None:
            failure_message = failure_elem.get('message', '')
            failure_type = failure_elem.get('type', 'Failure')
            stack_trace = failure_elem.text or ''
        elif error_elem is not None:
            failure_message = error_elem.get('message', '')
            failure_type = error_elem.get('type', 'Error')
            stack_trace = error_elem.text or ''
        else:
            failure_message = 'Unknown failure'
            failure_type = 'Unknown'
            stack_trace = ''
        
        return {
            'testCaseName': test_name,
            'className': class_name,
            'failureMessage': failure_message,
            'stackTrace': stack_trace,
            'duration': duration,
            'suiteName': testsuite.get('name', ''),
            'failureType': failure_type
        }


class TestFileParser:
    """Parse test files and extract test methods with their source code"""
    
    def __init__(self, test_directories: List[str]):
        self.test_directories = test_directories
        self.test_files_cache = {}
        self.supported_extensions = ['.py', '.js', '.ts', '.java', '.rb', '.go', '.cs', '.php']
    
    def discover_test_files(self) -> Dict[str, str]:
        """Discover all test files in the specified directories"""
        test_files = {}
        
        for test_dir in self.test_directories:
            if not os.path.exists(test_dir):
                logger.warning(f"Test directory does not exist: {test_dir}")
                continue
                
            logger.info(f"Scanning test directory: {test_dir}")
            
            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in self.supported_extensions):
                        if self._is_test_file(file):
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, test_dir)
                            test_files[relative_path] = full_path
        
        logger.info(f"Discovered {len(test_files)} test files")
        return test_files
    
    def _is_test_file(self, filename: str) -> bool:
        """Check if a file is likely a test file based on naming conventions"""
        test_patterns = [
            '*test*', '*spec*', '*Test*', '*Spec*', 
            'test_*', '*_test.*', '*_spec.*', '*.test.*', '*.spec.*'
        ]
        return any(fnmatch.fnmatch(filename, pattern) for pattern in test_patterns)
    
    def find_test_method(self, test_name: str, class_name: str = None) -> Optional[Dict[str, Any]]:
        """Find a specific test method in the test files with enhanced RHACM4K support"""
        
        if not self.test_files_cache:
            self._build_test_cache()
        
        # Try exact match first
        if test_name in self.test_files_cache:
            result = self.test_files_cache[test_name].copy()
            result.update(self._enhance_rhacm_mapping(test_name, result))
            return result
        
        # Try fuzzy matching
        for cached_test_name, test_info in self.test_files_cache.items():
            if self._fuzzy_match(test_name, cached_test_name, class_name, test_info.get('class_name')):
                result = test_info.copy()
                result.update(self._enhance_rhacm_mapping(test_name, result))
                return result
        
        logger.warning(f"Could not find test method: {test_name}")
        return None
    
    def _enhance_rhacm_mapping(self, test_name: str, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance test mapping with RHACM4K specific information"""
        enhancement = {}
        
        # Extract RHACM ID if present
        if 'RHACM4K-' in test_name:
            import re
            rhacm_match = re.search(r'RHACM4K-\d+', test_name)
            if rhacm_match:
                enhancement['rhacmId'] = rhacm_match.group(0)
        
        # Enhance with full path information
        if 'file_path' in test_info:
            enhancement['testSourceFile'] = test_info['file_path']
            enhancement['fullPath'] = os.path.abspath(test_info['file_path'])
        
        # Analyze fix location based on file content and test name
        enhancement['fixLocation'] = self._analyze_fix_location(test_name, test_info)
        
        return enhancement
    
    def _analyze_fix_location(self, test_name: str, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze where the fix should be applied"""
        fix_location = {
            'targetFile': test_info.get('file_path', 'Unknown'),
            'targetLines': [test_info.get('line_number', 0)],
            'bugType': 'automation',  # Default assumption for test failures
            'description': 'Test automation issue requiring investigation'
        }
        
        # Enhanced logic based on test content analysis
        source_code = test_info.get('source_code', '')
        if source_code:
            # Look for common patterns that indicate different bug types
            if 'cypress' in source_code.lower() or 'cy.' in source_code:
                fix_location['bugType'] = 'test_framework'
                fix_location['description'] = 'Cypress test framework issue'
            elif 'selenium' in source_code.lower() or 'driver.' in source_code:
                fix_location['bugType'] = 'test_framework' 
                fix_location['description'] = 'Selenium test framework issue'
            elif 'timeout' in test_name.lower() or 'wait' in source_code.lower():
                fix_location['bugType'] = 'automation'
                fix_location['description'] = 'Timing or wait condition issue'
            elif 'assert' in source_code.lower() or 'expect' in source_code.lower():
                fix_location['bugType'] = 'automation'
                fix_location['description'] = 'Assertion or expectation issue'
        
        return fix_location
    
    def _build_test_cache(self):
        """Build cache of all test methods with their source code"""
        test_files = self.discover_test_files()
        
        for relative_path, full_path in test_files.items():
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse based on file extension
                if full_path.endswith(('.py',)):
                    self._parse_python_tests(content, full_path, relative_path)
                elif full_path.endswith(('.js', '.ts')):
                    self._parse_javascript_tests(content, full_path, relative_path)
                elif full_path.endswith('.java'):
                    self._parse_java_tests(content, full_path, relative_path)
                # Add more parsers as needed
                
            except Exception as e:
                logger.warning(f"Failed to parse test file {full_path}: {e}")
    
    def _parse_python_tests(self, content: str, full_path: str, relative_path: str):
        """Parse Python test files (pytest, unittest)"""
        lines = content.split('\n')
        
        # Find test methods and classes
        current_class = None
        current_method = None
        method_start_line = None
        indent_level = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Class definition
            if stripped.startswith('class ') and ('Test' in stripped or 'Spec' in stripped):
                current_class = self._extract_class_name(stripped)
                continue
            
            # Test method definition
            if stripped.startswith('def test_') or stripped.startswith('def test '):
                current_method = self._extract_method_name(stripped)
                method_start_line = line_num
                indent_level = len(line) - len(line.lstrip())
                continue
            
            # End of method (dedent or next method/class)
            if (current_method and method_start_line and 
                (stripped.startswith('def ') or stripped.startswith('class ') or
                 (line.strip() and len(line) - len(line.lstrip()) <= indent_level and line_num > method_start_line + 1))):
                
                # Extract method source
                method_lines = lines[method_start_line-1:line_num-1]
                method_source = '\n'.join(method_lines)
                
                # Store in cache
                cache_key = current_method
                if current_class:
                    cache_key = f"{current_class}.{current_method}"
                
                self.test_files_cache[cache_key] = {
                    'method_name': current_method,
                    'class_name': current_class,
                    'file_path': full_path,
                    'relative_path': relative_path,
                    'line_number': method_start_line,
                    'source_code': method_source,
                    'language': 'python'
                }
                
                # Also store with just method name
                if current_method not in self.test_files_cache:
                    self.test_files_cache[current_method] = self.test_files_cache[cache_key]
                
                current_method = None
                method_start_line = None
        
        # Handle last method if file ends without dedent
        if current_method and method_start_line:
            method_lines = lines[method_start_line-1:]
            method_source = '\n'.join(method_lines)
            
            cache_key = current_method
            if current_class:
                cache_key = f"{current_class}.{current_method}"
            
            self.test_files_cache[cache_key] = {
                'method_name': current_method,
                'class_name': current_class,
                'file_path': full_path,
                'relative_path': relative_path,
                'line_number': method_start_line,
                'source_code': method_source,
                'language': 'python'
            }
    
    def _parse_javascript_tests(self, content: str, full_path: str, relative_path: str):
        """Parse JavaScript/TypeScript test files (Jest, Mocha, Cypress, etc.)"""
        lines = content.split('\n')
        
        # Common JS test patterns
        test_patterns = [
            r'^\s*(it|test)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'^\s*(describe)\s*\.\s*(skip|only)?\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'^\s*(cy)\s*\.\s*it\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        ]
        
        current_describe = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Find describe blocks
            describe_match = re.search(r'describe\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', stripped)
            if describe_match:
                current_describe = describe_match.group(1)
                continue
            
            # Find test cases
            for pattern in test_patterns:
                match = re.search(pattern, stripped)
                if match:
                    test_name = match.group(2) if len(match.groups()) >= 2 else match.group(1)
                    
                    # Find the full test function
                    method_source = self._extract_js_test_function(lines, line_num - 1)
                    
                    cache_key = test_name
                    if current_describe:
                        cache_key = f"{current_describe}.{test_name}"
                    
                    self.test_files_cache[cache_key] = {
                        'method_name': test_name,
                        'class_name': current_describe,
                        'file_path': full_path,
                        'relative_path': relative_path,
                        'line_number': line_num,
                        'source_code': method_source,
                        'language': 'javascript'
                    }
                    
                    # Also store with just test name
                    if test_name not in self.test_files_cache:
                        self.test_files_cache[test_name] = self.test_files_cache[cache_key]
                    
                    break
    
    def _parse_java_tests(self, content: str, full_path: str, relative_path: str):
        """Parse Java test files (JUnit, TestNG)"""
        lines = content.split('\n')
        
        current_class = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Find class
            if stripped.startswith('public class ') or stripped.startswith('class '):
                current_class = self._extract_class_name(stripped)
                continue
            
            # Find test methods (with @Test annotation)
            if '@Test' in stripped:
                # Look for method definition in next few lines
                for i in range(1, 5):
                    if line_num + i < len(lines):
                        method_line = lines[line_num + i - 1].strip()
                        if 'public void' in method_line or 'void' in method_line:
                            method_name = self._extract_method_name(method_line)
                            if method_name:
                                method_source = self._extract_java_method(lines, line_num + i - 1)
                                
                                cache_key = method_name
                                if current_class:
                                    cache_key = f"{current_class}.{method_name}"
                                
                                self.test_files_cache[cache_key] = {
                                    'method_name': method_name,
                                    'class_name': current_class,
                                    'file_path': full_path,
                                    'relative_path': relative_path,
                                    'line_number': line_num + i,
                                    'source_code': method_source,
                                    'language': 'java'
                                }
                                break
    
    def _extract_js_test_function(self, lines: List[str], start_line: int) -> str:
        """Extract a complete JavaScript test function"""
        brace_count = 0
        paren_count = 0
        in_function = False
        method_lines = []
        
        for i in range(start_line, min(len(lines), start_line + 50)):
            line = lines[i]
            method_lines.append(line)
            
            # Count braces and parentheses
            for char in line:
                if char == '(':
                    paren_count += 1
                    in_function = True
                elif char == ')':
                    paren_count -= 1
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and in_function:
                        return '\n'.join(method_lines)
        
        return '\n'.join(method_lines)
    
    def _extract_java_method(self, lines: List[str], start_line: int) -> str:
        """Extract a complete Java method"""
        brace_count = 0
        method_lines = []
        found_opening_brace = False
        
        for i in range(start_line, min(len(lines), start_line + 100)):
            line = lines[i]
            method_lines.append(line)
            
            for char in line:
                if char == '{':
                    brace_count += 1
                    found_opening_brace = True
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and found_opening_brace:
                        return '\n'.join(method_lines)
        
        return '\n'.join(method_lines)
    
    def _extract_class_name(self, line: str) -> str:
        """Extract class name from class definition line"""
        match = re.search(r'class\s+(\w+)', line)
        return match.group(1) if match else None
    
    def _extract_method_name(self, line: str) -> str:
        """Extract method name from method definition line"""
        # Python: def test_something(
        python_match = re.search(r'def\s+(\w+)', line)
        if python_match:
            return python_match.group(1)
        
        # Java: public void testSomething(
        java_match = re.search(r'void\s+(\w+)', line)
        if java_match:
            return java_match.group(1)
        
        return None
    
    def _fuzzy_match(self, test_name: str, cached_name: str, class_name: str = None, cached_class: str = None) -> bool:
        """Perform fuzzy matching between test names"""
        
        # Direct match
        if test_name == cached_name:
            return True
        
        # Match with class prefix
        if class_name and cached_class:
            if f"{class_name}.{test_name}" == cached_name:
                return True
            if f"{cached_class}.{cached_name}" == test_name:
                return True
        
        # Normalize and compare (remove underscores, case insensitive)
        normalized_test = re.sub(r'[_\s-]', '', test_name.lower())
        normalized_cached = re.sub(r'[_\s-]', '', cached_name.lower())
        
        if normalized_test == normalized_cached:
            return True
        
        # Partial match (one contains the other)
        if normalized_test in normalized_cached or normalized_cached in normalized_test:
            return True
        
        return False


class AIProvider:
    """Base class for AI providers"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def analyze_failure(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaProvider(AIProvider):
    """Ollama AI provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ImportError("ollama package not installed. Run: pip install ollama")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'llama3.2')
        try:
            response = self.ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are an expert test automation engineer. Analyze test failures and provide specific code fixes in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return ""


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'gpt-4')
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': 'You are an expert test automation engineer. Analyze test failures and provide specific code fixes in JSON format.'},
                    {'role': 'user', 'content': prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return ""


class ClaudeProvider(AIProvider):
    """Claude (Anthropic) API provider"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def analyze_failure(self, prompt: str) -> str:
        model = self.config.get('model', 'claude-3-haiku-20240307')
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=4000,
                system="You are an expert test automation engineer. Analyze test failures and provide specific code fixes in JSON format.",
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            return ""


class GenericAPIProvider(AIProvider):
    """Generic REST API provider for any AI service"""
    
    def analyze_failure(self, prompt: str) -> str:
        url = self.config.get('api_url')
        headers = self.config.get('headers', {})
        payload = self.config.get('payload_template', {})
        
        # Replace placeholders in payload
        payload_str = json.dumps(payload).replace('{{PROMPT}}', prompt)
        payload = json.loads(payload_str)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Extract response based on configuration
            response_data = response.json()
            response_path = self.config.get('response_path', 'response')
            
            # Navigate through nested response
            result = response_data
            for key in response_path.split('.'):
                result = result.get(key, '')
            
            return str(result)
        except Exception as e:
            logger.error(f"Generic API analysis failed: {e}")
            return ""


class TestFailureAnalyzer:
    """Main analyzer class with source code integration"""
    
    def __init__(self, config: Dict):
        self.jenkins_config = config.get('jenkins', {})
        self.ai_config = config.get('ai', {})
        self.test_config = config.get('test_source', {})
        self.local_config = config.get('local_junit', {})
        self.skill_config = config.get('skill', {})
        self.ai_provider = self._create_ai_provider()
        
        # Initialize skill-based prompt generator
        skill_file_path = self.skill_config.get('file_path')
        self.prompt_generator = SkillPromptGenerator(skill_file_path)
        
        # Initialize test file parser
        test_directories = self.test_config.get('directories', [])
        if test_directories:
            self.test_parser = TestFileParser(test_directories)
        else:
            self.test_parser = None
            logger.warning("No test directories configured - source code analysis will be limited")
        
        # Initialize JUnit XML parser if local mode
        xml_paths = self.local_config.get('xml_paths', [])
        if xml_paths:
            self.junit_parser = JUnitXMLParser(xml_paths)
        else:
            self.junit_parser = None
    
    def _create_ai_provider(self) -> AIProvider:
        """Create AI provider based on configuration"""
        provider_type = self.ai_config.get('provider', 'ollama').lower()
        
        if provider_type == 'ollama':
            return OllamaProvider(self.ai_config)
        elif provider_type == 'openai':
            return OpenAIProvider(self.ai_config)
        elif provider_type == 'claude':
            return ClaudeProvider(self.ai_config)
        elif provider_type == 'generic':
            return GenericAPIProvider(self.ai_config)
        else:
            raise ValueError(f"Unknown AI provider: {provider_type}")
    
    def analyze_build_failures(self, pipeline_name: str = None, build_number: int = None, options: Optional[Dict] = None) -> Dict[str, Any]:
        """Main analysis method with source code integration - supports both Jenkins and local modes"""
        start_time = time.time()
        options = options or {}
        
        # Determine mode - local or Jenkins
        is_local_mode = bool(self.junit_parser)
        
        if is_local_mode:
            logger.info("Starting enhanced local analysis of JUnit XML files")
            analysis_source = "Local JUnit XML"
        else:
            logger.info(f"Starting enhanced Jenkins analysis of {pipeline_name} build {build_number}")
            analysis_source = f"{pipeline_name} #{build_number}"
        
        # Enhanced result format with metadata and results structure
        result = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "input_file": analysis_source,
                "model": self.ai_config.get('model', 'unknown'),
                "framework": None,  # Will be detected during analysis
                "total_tests": 0,
                "successful_analyses": 0,
                "analyze_only": False,
                "fix_summary": {
                    "total_fixes": 0,
                    "successful_fixes": 0,
                    "failed_fixes": 0,
                    "success_rate": 0.0,
                    "fix_type_distribution": {},
                    "priority_distribution": {},
                    "effort_distribution": {}
                }
            },
            "results": [],
            # Keep legacy format for backward compatibility
            "analysisMetadata": {
                "pipeline": pipeline_name or "Local Analysis",
                "buildNumber": build_number or 0,
                "analysisTimestamp": datetime.utcnow().isoformat() + "Z",
                "totalFailures": 0,
                "processingTime": "",
                "aiProvider": self.ai_config.get('provider', 'unknown'),
                "sourceCodeAnalysis": bool(self.test_parser),
                "analysisMode": "local" if is_local_mode else "jenkins",
                "analysisSource": analysis_source
            },
            "failureAnalysis": [],
            "summaryMetrics": {
                "automationBugs": 0,
                "infrastructureIssues": 0,
                "productIssues": 0,
                "environmentIssues": 0
            }
        }
        
        try:
            # Get build information and test failures based on mode
            if is_local_mode:
                build_info = self._create_local_build_info()
                test_failures = self._extract_local_test_failures()
            else:
                if not pipeline_name or build_number is None:
                    raise ValueError("Pipeline name and build number required for Jenkins mode")
                build_info = self._get_build_info(pipeline_name, build_number)
                if not build_info:
                    logger.error("Failed to retrieve build information")
                    return result
                test_failures = self._extract_test_failures(pipeline_name, build_number)
            
            result["analysisMetadata"]["totalFailures"] = len(test_failures)
            result["metadata"]["total_tests"] = len(test_failures)
            
            if not test_failures:
                logger.info("No test failures found")
                return result
            
            # Analyze failures with source code context
            max_failures = options.get('max_failures', 10)
            successful_analyses = 0
            
            for i, failure in enumerate(test_failures[:max_failures]):
                logger.info(f"Analyzing failure {i+1}/{min(len(test_failures), max_failures)}: {failure['testCaseName']}")
                
                analysis = self._analyze_failure_with_source_code(failure, build_info, options)
                if analysis:
                    successful_analyses += 1
                    
                    # Legacy format
                    result["failureAnalysis"].append(analysis)
                    self._update_summary_metrics(analysis, result["summaryMetrics"])
                    
                    # Enhanced format
                    enhanced_result = self._create_enhanced_result_format(failure, analysis, build_info)
                    result["results"].append(enhanced_result)
                    
                    # Update fix summary
                    self._update_fix_summary(enhanced_result, result["metadata"]["fix_summary"])
            
            # Update metadata
            result["metadata"]["successful_analyses"] = successful_analyses
            
            processing_time = time.time() - start_time
            result["analysisMetadata"]["processingTime"] = f"{processing_time:.1f}s"
            
            mode_str = "local" if is_local_mode else "Jenkins"
            logger.info(f"Enhanced {mode_str} analysis completed in {processing_time:.1f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            result["analysisMetadata"]["processingTime"] = f"{time.time() - start_time:.1f}s"
            return result
    
    def _analyze_failure_with_source_code(self, failure: Dict, build_info: Dict, options: Dict) -> Optional[Dict]:
        """Analyze failure with actual source code context"""
        try:
            # Find the source code for this test
            test_source_info = None
            if self.test_parser:
                test_source_info = self.test_parser.find_test_method(
                    failure['testCaseName'], 
                    failure.get('className')
                )
            
            # Build enhanced analysis prompt with source code
            prompt = self._build_enhanced_analysis_prompt(failure, build_info, test_source_info, options)
            
            # Get AI analysis
            response = self.ai_provider.analyze_failure(prompt)
            
            if not response:
                return None
            
            # Parse AI response
            analysis_json = self._extract_json_from_response(response)
            if analysis_json:
                # Enhance with detailed source code mapping if available
                if test_source_info:
                    # Extract problematic lines from the AI response if present
                    problematic_lines = self._extract_problematic_lines(analysis_json, test_source_info)
                    current_code = self._extract_current_code(test_source_info, problematic_lines)
                    suggested_replacements = self._extract_suggested_code(analysis_json)
                    
                    analysis_json['sourceCodeMapping'] = {
                        'filePath': test_source_info.get('relative_path', 'Unknown'),
                        'fullPath': test_source_info.get('file_path', 'Unknown'),
                        'lineNumber': test_source_info.get('line_number', 0),
                        'testMethod': test_source_info.get('method_name', failure['testCaseName']),
                        'testClass': test_source_info.get('class_name', failure.get('className', 'Unknown')),
                        'language': test_source_info.get('language', 'unknown'),
                        'problematicLines': problematic_lines,
                        'currentCode': current_code,
                        'suggestedReplacements': suggested_replacements
                    }
                    
                    # Add enhanced fix location information
                    analysis_json['fixLocation'] = {
                        'targetFile': test_source_info.get('relative_path', 'Unknown'),
                        'targetLines': problematic_lines,
                        'bugType': self._determine_bug_type(analysis_json, failure),
                        'description': analysis_json.get('codeFixSuggestion', 'Fix needed based on analysis'),
                        'codeContext': current_code
                    }
                return analysis_json
            
            # Fallback analysis
            return self._create_fallback_analysis(failure, response, test_source_info)
            
        except Exception as e:
            logger.error(f"Source code analysis failed: {str(e)}")
            return None
    
    def _build_enhanced_analysis_prompt(self, failure: Dict, build_info: Dict, test_source_info: Optional[Dict], options: Dict) -> str:
        """Build enhanced analysis prompt using skill-based prompt generator"""
        return self.prompt_generator.generate_analysis_prompt(failure, build_info, test_source_info, options)
    
    def _get_build_info(self, pipeline_name: str, build_number: int) -> Optional[Dict]:
        """Fetch build information from Jenkins"""
        try:
            jenkins_url = self.jenkins_config.get('url', '').rstrip('/')
            jenkins_user = self.jenkins_config.get('user', '')
            jenkins_token = self.jenkins_config.get('token', '')
            
            if not all([jenkins_url, jenkins_user, jenkins_token]):
                raise ValueError("Jenkins credentials not configured")
            
            encoded_pipeline = urllib.parse.quote(pipeline_name, safe='')
            url = f"{jenkins_url}/job/{encoded_pipeline}/{build_number}/api/json"
            
            response = requests.get(url, auth=(jenkins_user, jenkins_token), timeout=30)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get build info: {str(e)}")
            return None
    
    def _extract_test_failures(self, pipeline_name: str, build_number: int) -> List[Dict]:
        """Extract test failures from Jenkins"""
        failures = []
        
        try:
            jenkins_url = self.jenkins_config.get('url', '').rstrip('/')
            jenkins_user = self.jenkins_config.get('user', '')
            jenkins_token = self.jenkins_config.get('token', '')
            
            encoded_pipeline = urllib.parse.quote(pipeline_name, safe='')
            url = f"{jenkins_url}/job/{encoded_pipeline}/{build_number}/testReport/api/json"
            
            response = requests.get(url, auth=(jenkins_user, jenkins_token), timeout=30)
            if response.status_code == 404:
                logger.warning("No test report found for this build")
                return failures
            
            response.raise_for_status()
            test_report = response.json()
            
            # Extract failures
            for suite in test_report.get('suites', []):
                for case in suite.get('cases', []):
                    if case.get('status') in ['FAILED', 'ERROR']:
                        failure = {
                            'testCaseName': case.get('name', ''),
                            'className': case.get('className', ''),
                            'failureMessage': case.get('errorDetails', ''),
                            'stackTrace': case.get('errorStackTrace', ''),
                            'duration': case.get('duration', 0),
                            'suiteName': suite.get('name', '')
                        }
                        failures.append(failure)
            
            logger.info(f"Found {len(failures)} test failures")
            return failures
            
        except Exception as e:
            logger.error(f"Failed to extract test failures: {str(e)}")
            return failures
    
    def _extract_local_test_failures(self) -> List[Dict]:
        """Extract test failures from local JUnit XML files"""
        if not self.junit_parser:
            logger.error("No JUnit XML parser configured for local mode")
            return []
        
        try:
            failures = self.junit_parser.extract_failures()
            logger.info(f"Found {len(failures)} test failures from local XML files")
            return failures
        except Exception as e:
            logger.error(f"Failed to extract local test failures: {str(e)}")
            return []
    
    def _create_local_build_info(self) -> Dict:
        """Create mock build info for local analysis"""
        xml_paths = self.local_config.get('xml_paths', [])
        return {
            'fullDisplayName': f"Local Analysis: {', '.join(xml_paths)}",
            'result': 'UNKNOWN',
            'url': 'file://local',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        try:
            # Find JSON boundaries
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        
        return None
    
    def _create_fallback_analysis(self, failure: Dict, response: str, test_source_info: Optional[Dict]) -> Dict:
        """Create fallback analysis structure"""
        source_mapping = {
            "filePath": "Unknown",
            "lineNumber": 0,
            "testMethod": failure['testCaseName'],
            "testClass": failure.get('className', 'Unknown')
        }
        
        if test_source_info:
            source_mapping.update({
                "filePath": test_source_info.get('relative_path', 'Unknown'),
                "lineNumber": test_source_info.get('line_number', 0),
                "testMethod": test_source_info.get('method_name', failure['testCaseName']),
                "testClass": test_source_info.get('class_name', failure.get('className', 'Unknown')),
                "language": test_source_info.get('language', 'unknown'),
                "fullPath": test_source_info.get('file_path', 'Unknown')
            })
        
        # Safely handle response which might not be a string
        safe_response = str(response) if response else "Analysis failed"
        
        return {
            "testCaseName": failure['testCaseName'],
            "failureMessage": str(failure['failureMessage'])[:200] + "...",
            "rootCauseAnalysis": safe_response[:500] + "...",
            "codeFixSuggestion": "See rootCauseAnalysis for details",
            "sourceCodeMapping": source_mapping,
            "failureDetails": {
                "stackTrace": str(failure.get('stackTrace', ''))[:500] + "...",
                "errorType": "Unknown",
                "severity": "MEDIUM",
                "category": "automation"
            },
            "fixMetadata": {
                "confidenceScore": 0.5,
                "automationBug": True,
                "estimatedEffort": "Unknown",
                "suggestedLines": []
            }
        }
    
    def _update_summary_metrics(self, analysis: Dict, metrics: Dict):
        """Update summary metrics"""
        category = analysis.get('failureDetails', {}).get('category', 'automation')
        metrics[f"{category}{'Bugs' if category == 'automation' else 'Issues'}"] += 1
    
    def _create_enhanced_result_format(self, failure: Dict, analysis: Dict, build_info: Dict) -> Dict:
        """Create enhanced result format matching the provided example"""
        rhacm_id = failure.get('rhacmId', '')
        test_name = failure.get('testCaseName', '')
        
        # Extract framework from source code mapping or guess from file extension
        framework = analysis.get('sourceCodeMapping', {}).get('language', 'junit')
        if framework == 'javascript':
            framework = 'jest'
        elif framework == 'python':
            framework = 'pytest'
        
        # Create the enhanced result
        enhanced_result = {
            "test_name": test_name,
            "framework": framework,
            "original_test": {
                "name": test_name,
                "status": "failed",
                "failure_message": failure.get('failureMessage', ''),
                "framework": framework,
                "class_name": failure.get('className', ''),
                "execution_time": float(failure.get('duration', 0)),
                "suite_name": failure.get('suiteName', '')
            },
            "analysis": {
                "success": True,
                "root_cause": self._safe_get_string(analysis, 'rootCauseAnalysis'),
                "suggested_fix": self._safe_get_string(analysis, 'codeFixSuggestion'), 
                "code_example": '',  # Could be enhanced with actual code snippets
                "confidence_score": analysis.get('fixMetadata', {}).get('confidenceScore', 0.5),
                "error_category": analysis.get('failureDetails', {}).get('category', 'automation'),
                "severity": analysis.get('failureDetails', {}).get('severity', 'medium'),
                "additional_context": '',
                "raw_response": self._safe_get_string(analysis, 'rootCauseAnalysis') + '\n\n' + self._safe_get_string(analysis, 'codeFixSuggestion'),
                "analyzed_at": datetime.utcnow().isoformat()
            }
        }
        
        # Add RHACM ID if present
        if rhacm_id:
            enhanced_result['rhacmId'] = rhacm_id
        
        # Add source code mapping if available
        if 'sourceCodeMapping' in analysis:
            enhanced_result['sourceCodeMapping'] = analysis['sourceCodeMapping']
        
        # Add fix location if available
        if 'fixLocation' in analysis:
            enhanced_result['fixLocation'] = analysis['fixLocation']
        else:
            # Create a basic fix location from available information
            enhanced_result['fixLocation'] = {
                "targetFile": analysis.get('sourceCodeMapping', {}).get('filePath', 'unknown'),
                "targetLines": analysis.get('sourceCodeMapping', {}).get('problematicLines', []),
                "bugType": "automation",  # Default for test failures
                "description": self._safe_get_string(analysis, 'codeFixSuggestion')
            }
        
        # Add fix suggestion in the new format
        enhanced_result['fix_suggestion'] = {
            "success": True,
            "fix_type": self._determine_fix_type(analysis),
            "priority": self._determine_priority(analysis),
            "estimated_effort": self._determine_effort(analysis),
            "code_changes": self._safe_get_string(analysis, 'codeFixSuggestion'),
            "configuration_changes": '',
            "dependencies": '',
            "validation_steps": [
                "Verify the fix addresses the root cause",
                "Run the affected test to ensure it passes",
                "Check for any regressions in related functionality"
            ],
            "prevention": "Consider adding additional test coverage for this scenario",
            "impact_assessment": "Low to medium impact on test reliability",
            "rollback_plan": "Revert the changes if issues arise",
            "raw_response": self._safe_get_string(analysis, 'codeFixSuggestion'),
            "suggested_at": datetime.utcnow().isoformat()
        }
        
        return enhanced_result
    
    def _determine_fix_type(self, analysis: Dict) -> str:
        """Determine fix type from analysis"""
        category = analysis.get('failureDetails', {}).get('category', 'automation')
        if category == 'automation':
            return 'configuration'
        elif category == 'infrastructure':
            return 'configuration'
        else:
            return 'refactor'
    
    def _determine_priority(self, analysis: Dict) -> str:
        """Determine priority from analysis"""
        severity = analysis.get('failureDetails', {}).get('severity', 'medium').lower()
        if severity in ['high', 'critical']:
            return 'high'
        elif severity in ['low']:
            return 'low'
        else:
            return 'medium'
    
    def _determine_effort(self, analysis: Dict) -> str:
        """Determine estimated effort from analysis"""
        effort = analysis.get('fixMetadata', {}).get('estimatedEffort', '30 minutes')
        if 'hour' in effort.lower() or 'hr' in effort.lower():
            return '2 hours'
        else:
            return '30 minutes'
    
    def _update_fix_summary(self, enhanced_result: Dict, fix_summary: Dict):
        """Update fix summary statistics"""
        fix_summary['total_fixes'] += 1
        
        if enhanced_result['fix_suggestion']['success']:
            fix_summary['successful_fixes'] += 1
        else:
            fix_summary['failed_fixes'] += 1
        
        # Update distributions
        fix_type = enhanced_result['fix_suggestion']['fix_type']
        priority = enhanced_result['fix_suggestion']['priority'] 
        effort = enhanced_result['fix_suggestion']['estimated_effort']
        
        if fix_type not in fix_summary['fix_type_distribution']:
            fix_summary['fix_type_distribution'][fix_type] = 0
        fix_summary['fix_type_distribution'][fix_type] += 1
        
        if priority not in fix_summary['priority_distribution']:
            fix_summary['priority_distribution'][priority] = 0
        fix_summary['priority_distribution'][priority] += 1
        
        if effort not in fix_summary['effort_distribution']:
            fix_summary['effort_distribution'][effort] = 0
        fix_summary['effort_distribution'][effort] += 1
        
        # Calculate success rate
        total = fix_summary['total_fixes']
        fix_summary['success_rate'] = fix_summary['successful_fixes'] / total if total > 0 else 0.0
    
    def _extract_problematic_lines(self, analysis_json: Dict, test_source_info: Dict) -> List[int]:
        """Extract problematic line numbers from analysis or source info"""
        # Try to get from AI analysis first
        if 'sourceCodeMapping' in analysis_json and 'problematicLines' in analysis_json['sourceCodeMapping']:
            return analysis_json['sourceCodeMapping']['problematicLines']
        
        # Try to get from fixMetadata
        if 'fixMetadata' in analysis_json and 'suggestedLines' in analysis_json['fixMetadata']:
            try:
                # Extract line numbers from suggested lines
                lines = []
                for line_ref in analysis_json['fixMetadata']['suggestedLines']:
                    if isinstance(line_ref, str) and 'line' in line_ref.lower():
                        import re
                        line_nums = re.findall(r'line\s*(\d+)', line_ref.lower())
                        lines.extend([int(n) for n in line_nums])
                return lines if lines else [test_source_info.get('line_number', 0)]
            except:
                pass
        
        # Default to the main method line number
        return [test_source_info.get('line_number', 0)]
    
    def _extract_current_code(self, test_source_info: Dict, problematic_lines: List[int]) -> List[str]:
        """Extract current code snippets for problematic lines"""
        source_code = test_source_info.get('source_code', '')
        if not source_code:
            return ['// Source code not available']
        
        lines = source_code.split('\n')
        current_code = []
        
        for line_num in problematic_lines:
            if line_num > 0 and line_num <= len(lines):
                # Add context: line before, problematic line, line after
                start_idx = max(0, line_num - 2)
                end_idx = min(len(lines), line_num + 1)
                
                for i in range(start_idx, end_idx):
                    marker = ">>> " if i == line_num - 1 else "    "
                    current_code.append(f"{marker}Line {i+1}: {lines[i]}")
        
        return current_code if current_code else [f"Line {problematic_lines[0] if problematic_lines else 1}: {lines[0] if lines else 'No code available'}"]
    
    def _extract_suggested_code(self, analysis_json: Dict) -> List[str]:
        """Extract suggested code replacements from AI analysis"""
        # Try to get from sourceCodeMapping first
        if 'sourceCodeMapping' in analysis_json and 'suggestedReplacements' in analysis_json['sourceCodeMapping']:
            return analysis_json['sourceCodeMapping']['suggestedReplacements']
        
        # Try to get from codeFixSuggestion
        fix_suggestion = analysis_json.get('codeFixSuggestion', '')
        if fix_suggestion and '```' in fix_suggestion:
            # Extract code blocks from fix suggestion
            import re
            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', fix_suggestion, re.DOTALL)
            if code_blocks:
                return [block.strip() for block in code_blocks]
        
        # Try to extract from fixMetadata suggestedLines
        if 'fixMetadata' in analysis_json and 'suggestedLines' in analysis_json['fixMetadata']:
            suggested_lines = analysis_json['fixMetadata']['suggestedLines']
            if isinstance(suggested_lines, list):
                return suggested_lines
        
        # Fallback to generic suggestion
        return ['// See codeFixSuggestion for details', fix_suggestion[:100] + '...' if len(fix_suggestion) > 100 else fix_suggestion]
    
    def _determine_bug_type(self, analysis_json: Dict, failure: Dict) -> str:
        """Determine the type of bug based on analysis"""
        # Check if AI provided explicit bug type
        if 'fixLocation' in analysis_json and 'bugType' in analysis_json['fixLocation']:
            return analysis_json['fixLocation']['bugType']
        
        # Analyze failure details to categorize
        category = analysis_json.get('failureDetails', {}).get('category', 'automation')
        
        # Map categories to bug types
        bug_type_mapping = {
            'automation': 'automation',
            'infrastructure': 'test_framework', 
            'product': 'application',
            'environment': 'test_framework'
        }
        
        return bug_type_mapping.get(category, 'automation')
    
    def _safe_get_string(self, data: Dict, key: str) -> str:
        """Safely extract string value from dictionary, handling dict/object values"""
        value = data.get(key, '')
        
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # If it's a dict, try to extract meaningful string representation
            if 'technicalCause' in value:
                return value.get('technicalCause', '')
            elif 'description' in value:
                return value.get('description', '')
            elif 'primaryFix' in value:
                fix = value.get('primaryFix', {})
                if isinstance(fix, dict):
                    return fix.get('description', '') or fix.get('explanation', '')
                return str(fix)
            else:
                # Convert dict to readable string
                return str(value)
        elif value is None:
            return ''
        else:
            # Convert other types to string
            return str(value)


def load_config(config_file: str = 'config.json') -> Dict:
    """Load configuration from file"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config: {e}")
    
    return {}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced Test Failure Analysis with Source Code - Jenkins or Local Mode')
    
    # Mode selection
    subparsers = parser.add_subparsers(dest='mode', help='Analysis mode')
    
    # Jenkins mode
    jenkins_parser = subparsers.add_parser('jenkins', help='Analyze failures from Jenkins build')
    jenkins_parser.add_argument('pipeline_name', help='Jenkins pipeline name')
    jenkins_parser.add_argument('build_number', type=int, help='Build number')
    jenkins_parser.add_argument('--config', default='config.json', help='Config file')
    jenkins_parser.add_argument('--output', help='Output JSON file')
    jenkins_parser.add_argument('--max-failures', type=int, default=10, help='Max failures to analyze')
    jenkins_parser.add_argument('--test-dirs', nargs='*', help='Test source directories to scan')
    jenkins_parser.add_argument('--skill-file', help='Custom skill file path for AI prompts')
    
    # Local mode
    local_parser = subparsers.add_parser('local', help='Analyze failures from local JUnit XML files')
    local_parser.add_argument('xml_paths', nargs='+', help='JUnit XML file paths or directories')
    local_parser.add_argument('--config', default='config.json', help='Config file')
    local_parser.add_argument('--output', help='Output JSON file')
    local_parser.add_argument('--max-failures', type=int, default=10, help='Max failures to analyze')
    local_parser.add_argument('--test-dirs', nargs='*', help='Test source directories to scan')
    local_parser.add_argument('--skill-file', help='Custom skill file path for AI prompts')
    
    # Legacy mode (backwards compatibility)
    parser.add_argument('pipeline_name', nargs='?', help='Jenkins pipeline name (legacy mode)')
    parser.add_argument('build_number', nargs='?', type=int, help='Build number (legacy mode)')
    parser.add_argument('--config', default='config.json', help='Config file')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--max-failures', type=int, default=10, help='Max failures to analyze')
    parser.add_argument('--test-dirs', nargs='*', help='Test source directories to scan')
    parser.add_argument('--xml-files', nargs='*', help='JUnit XML files for local analysis')
    parser.add_argument('--skill-file', help='Custom skill file path for AI prompts')
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.mode == 'jenkins':
        # Jenkins mode
        pipeline_name = args.pipeline_name
        build_number = args.build_number
        xml_paths = None
        mode = 'jenkins'
    elif args.mode == 'local':
        # Local mode
        pipeline_name = None
        build_number = None
        xml_paths = args.xml_paths
        mode = 'local'
    else:
        # Legacy mode - determine based on arguments
        if args.xml_files:
            # Local mode (using legacy --xml-files)
            pipeline_name = None
            build_number = None
            xml_paths = args.xml_files
            mode = 'local'
        elif args.pipeline_name and args.build_number is not None:
            # Jenkins mode (legacy)
            pipeline_name = args.pipeline_name
            build_number = args.build_number
            xml_paths = None
            mode = 'jenkins'
        else:
            parser.error("Either specify 'jenkins <pipeline> <build>' or 'local <xml_files>' or use --xml-files for local analysis")
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error(f"Configuration file {args.config} not found or invalid")
        sys.exit(1)
    
    # Add test directories from command line if provided
    if args.test_dirs:
        if 'test_source' not in config:
            config['test_source'] = {}
        config['test_source']['directories'] = args.test_dirs
    
    # Add skill file from command line if provided
    if hasattr(args, 'skill_file') and args.skill_file:
        if 'skill' not in config:
            config['skill'] = {}
        config['skill']['file_path'] = args.skill_file
    
    # Configure for local mode if needed
    if mode == 'local':
        if 'local_junit' not in config:
            config['local_junit'] = {}
        config['local_junit']['xml_paths'] = xml_paths
    
    # Initialize analyzer
    try:
        analyzer = TestFailureAnalyzer(config)
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        sys.exit(1)
    
    # Run analysis
    options = {'max_failures': args.max_failures}
    
    if mode == 'local':
        result = analyzer.analyze_build_failures(options=options)
        output_file = args.output or f"local_analysis_{int(time.time())}.json"
    else:
        result = analyzer.analyze_build_failures(pipeline_name, build_number, options)
        output_file = args.output or f"analysis_{pipeline_name.replace('/', '_')}_{build_number}.json"
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print(f"\n=== ENHANCED ANALYSIS SUMMARY ===")
    print(f"Mode: {result['analysisMetadata']['analysisMode']}")
    print(f"Source: {result['analysisMetadata']['analysisSource']}")
    print(f"AI Provider: {result['analysisMetadata']['aiProvider']}")
    print(f"Source Code Analysis: {result['analysisMetadata']['sourceCodeAnalysis']}")
    print(f"Total Failures: {result['analysisMetadata']['totalFailures']}")
    print(f"Processing Time: {result['analysisMetadata']['processingTime']}")
    print(f"Automation Bugs: {result['summaryMetrics']['automationBugs']}")
    print(f"Infrastructure Issues: {result['summaryMetrics']['infrastructureIssues']}")
    print(f"Product Issues: {result['summaryMetrics']['productIssues']}")
    print(f"Environment Issues: {result['summaryMetrics']['environmentIssues']}")
    print(f"\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()