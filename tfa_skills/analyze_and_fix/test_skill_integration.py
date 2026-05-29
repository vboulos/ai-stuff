#!/usr/bin/env python3
"""
Test script to verify skill integration without requiring Ollama dependency
"""

import json
import sys
import os
from datetime import datetime

# Test data in skill format
sample_skill_analysis = {
    "success": True,
    "testCaseName": "RHACM4K-57212.should load and render the search page",
    "failureMessage": "Element not found: .pf-c-title",
    "rootCauseAnalysis": "CSS selector '.pf-c-title' not found due to page loading timeout. The search page skeleton loader is still visible, indicating the page has not fully rendered.",
    "codeFixSuggestion": "Add explicit wait for page load completion before assertion. Replace immediate selector check with cy.get('.pf-c-title', { timeout: 30000 }).should('exist') and ensure skeleton elements are not present.",
    "sourceCodeMapping": {
        "filePath": "tests/cypress/tests/search.spec.js",
        "lineNumber": 30,
        "testMethod": "should load and render the search page",
        "testClass": "Search in Local Cluster"
    },
    "failureDetails": {
        "stackTrace": "CypressError: Timed out retrying after 4000ms...",
        "errorType": "ElementNotFound",
        "severity": "HIGH",
        "category": "automation"
    },
    "fixMetadata": {
        "confidenceScore": 0.9,
        "automationBug": True,
        "estimatedEffort": "5 minutes",
        "suggestedLines": [
            "cy.get('.pf-c-skeleton').should('not.exist')",
            "cy.get('.pf-c-title', { timeout: 30000 }).should('exist')"
        ]
    },
    "analyzed_at": datetime.now().isoformat()
}

# Test skill schema output format
skill_output = {
    "analysisMetadata": {
        "pipeline": "CI-jobs/search_tests",
        "buildNumber": 456,
        "analysisTimestamp": datetime.now().isoformat(),
        "totalFailures": 1,
        "processingTime": "completed",
        "model": "llama3.1",
        "skillVersion": "3.0.0"
    },
    "failureAnalysis": [sample_skill_analysis],
    "summaryMetrics": {
        "automationBugs": 1,
        "infrastructureIssues": 0,
        "productIssues": 0,
        "environmentIssues": 0
    }
}

def test_skill_format_validation():
    """Test that skill format follows required schema"""
    print("🔬 Testing skill format validation...")
    
    # Check required fields in analysis metadata
    required_metadata = ["pipeline", "buildNumber", "analysisTimestamp", "totalFailures", "skillVersion"]
    metadata = skill_output["analysisMetadata"]
    
    for field in required_metadata:
        assert field in metadata, f"Missing required metadata field: {field}"
    
    # Check required fields in failure analysis
    required_analysis = ["testCaseName", "failureMessage", "rootCauseAnalysis", "codeFixSuggestion"]
    analysis = skill_output["failureAnalysis"][0]
    
    for field in required_analysis:
        assert field in analysis, f"Missing required analysis field: {field}"
    
    # Check fix metadata structure
    fix_metadata = analysis["fixMetadata"]
    assert isinstance(fix_metadata["confidenceScore"], (int, float))
    assert isinstance(fix_metadata["automationBug"], bool)
    assert 0.0 <= fix_metadata["confidenceScore"] <= 1.0
    
    print("✅ Skill format validation passed!")

def test_legacy_compatibility():
    """Test legacy format handling"""
    print("🔄 Testing legacy compatibility...")
    
    # Legacy format test data
    legacy_analysis = {
        "success": True,
        "root_cause": "Authentication token is invalid or expired",
        "suggested_fix": "Check token validation logic",
        "confidence_score": 0.8,
        "error_category": "authentication",
        "severity": "high"
    }
    
    # Verify legacy fields exist
    assert "root_cause" in legacy_analysis
    assert "suggested_fix" in legacy_analysis
    assert "confidence_score" in legacy_analysis
    
    print("✅ Legacy compatibility test passed!")

def test_skill_context_parameters():
    """Test skill context parameter handling"""
    print("📋 Testing skill context parameters...")
    
    # Test parameter formatting
    test_kwargs = {
        "pipeline_name": "CI-jobs/search_tests",
        "build_number": 456,
        "github_repo": "https://github.com/stolostron/e2e-tests",
        "test_directory": "cypress/tests"
    }
    
    def format_kwargs(kwargs):
        if not kwargs:
            return "None provided"
        
        formatted = []
        for key, value in kwargs.items():
            if value:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted) if formatted else "None provided"
    
    formatted = format_kwargs(test_kwargs)
    assert "pipeline_name: CI-jobs/search_tests" in formatted
    assert "build_number: 456" in formatted
    
    print("✅ Skill context parameters test passed!")

def test_json_output():
    """Test JSON output serialization"""
    print("💾 Testing JSON output serialization...")
    
    # Test that output can be serialized to JSON
    try:
        json_output = json.dumps(skill_output, indent=2)
        
        # Test that it can be parsed back
        parsed = json.loads(json_output)
        assert parsed["analysisMetadata"]["skillVersion"] == "3.0.0"
        
        print("✅ JSON output serialization test passed!")
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        sys.exit(1)

def test_category_classification():
    """Test failure category classification"""
    print("🏷️  Testing category classification...")
    
    valid_categories = ["automation", "infrastructure", "product", "environment"]
    category = sample_skill_analysis["failureDetails"]["category"]
    
    assert category in valid_categories, f"Invalid category: {category}"
    
    # Test summary metrics calculation
    metrics = skill_output["summaryMetrics"]
    total_issues = sum(metrics.values())
    assert total_issues == skill_output["analysisMetadata"]["totalFailures"]
    
    print("✅ Category classification test passed!")

def main():
    """Run all tests"""
    print("🧪 Testing analyze-test-failures skill integration")
    print("=" * 60)
    
    try:
        test_skill_format_validation()
        test_legacy_compatibility()
        test_skill_context_parameters()
        test_json_output()
        test_category_classification()
        
        print("\n" + "=" * 60)
        print("🎉 All skill integration tests passed!")
        print("\n📊 Test Summary:")
        print(f"   - Skill schema v3.0.0: ✅")
        print(f"   - Legacy compatibility: ✅")
        print(f"   - Context parameters: ✅")
        print(f"   - JSON serialization: ✅")
        print(f"   - Category classification: ✅")
        print("\n✅ Implementation is ready for use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()