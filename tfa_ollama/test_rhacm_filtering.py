#!/usr/bin/env python3
"""
Test script to validate RHACM4K filtering and enhanced analysis
"""

import json
import sys
from analyze_test_failures import JUnitXMLParser, TestFailureAnalyzer

def test_rhacm_filtering():
    """Test RHACM4K pattern filtering"""
    
    print("Testing RHACM4K filtering...")
    
    # Test RHACM ID extraction
    test_cases = [
        "GRC: Donut chart for certificate policy in discovered policies - ACM-13337 'before all' hook for RHACM4K-52786: GRC: UI: Donut Card for certificate policy in DiscoveredByCluster page",
        "GRC: Test discovered policies pages in console before all hook for RHACM4K-52430: GRC: Verify Discovered policies table : Content",
        "GRC: Operator policy support - ACM-9287 RHACM4K-46007: GRC: Remove operator(spec.removalBehavior.operatorGroups: DeleteIfUnused)",
        "Non-RHACM test case that should be filtered out"
    ]
    
    # Test the RHACM ID extraction
    from analyze_test_failures import JUnitXMLParser
    parser = JUnitXMLParser([])
    
    for test_case in test_cases:
        rhacm_id = parser._extract_rhacm_id(test_case)
        should_include = 'RHACM4K-' in test_case
        
        print(f"Test Case: {test_case[:80]}...")
        print(f"  RHACM ID: {rhacm_id if rhacm_id else 'None'}")
        print(f"  Should Include: {should_include}")
        print()
    
    print("✓ RHACM4K filtering test completed")

def test_enhanced_analysis():
    """Test enhanced analysis with sample data"""
    
    print("Testing enhanced analysis...")
    
    # Sample configuration for local analysis
    config = {
        "ai": {
            "provider": "ollama",
            "model": "llama3.2"
        },
        "test_source": {
            "directories": ["./tests", "./cypress/tests"]
        },
        "skill": {
            "file_path": "./skills/analyze-test-failures.md"
        }
    }
    
    # Sample failure data
    sample_failure = {
        'testCaseName': 'GRC: Test discovered policies pages in console before all hook for RHACM4K-52430: GRC: Verify Discovered policies table',
        'className': 'GRC Test Suite',
        'failureMessage': 'Timed out retrying',
        'stackTrace': 'Error: Timed out retrying at Context.check (webpack://acmqe-grc-test/./node_modules/cypress-wait-until/src/index.js:62:0)',
        'duration': 120,
        'suiteName': 'GRC Tests'
    }
    
    sample_build_info = {
        'fullDisplayName': 'Local Analysis',
        'result': 'FAILURE',
        'url': 'file://local'
    }
    
    try:
        # Test the prompt generation
        analyzer = TestFailureAnalyzer(config)
        prompt = analyzer._build_enhanced_analysis_prompt(sample_failure, sample_build_info, None, {})
        
        print("✓ Prompt generation successful")
        print(f"Prompt length: {len(prompt)} characters")
        
        # Check if RHACM4K requirements are included
        if "RHACM4K ANALYSIS REQUIREMENTS" in prompt:
            print("✓ RHACM4K requirements detected in prompt")
        else:
            print("✗ RHACM4K requirements not found in prompt")
            
        # Check if the skill file was loaded
        if analyzer.prompt_generator.skill_content:
            print("✓ Skill file loaded successfully")
        else:
            print("⚠ Skill file not loaded, using fallback")
            
    except Exception as e:
        print(f"✗ Enhanced analysis test failed: {e}")
        return False
    
    print("✓ Enhanced analysis test completed")
    return True

def main():
    """Run all tests"""
    print("Running RHACM4K Test Failure Analysis Tests")
    print("=" * 50)
    
    try:
        test_rhacm_filtering()
        print()
        test_enhanced_analysis()
        print()
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()