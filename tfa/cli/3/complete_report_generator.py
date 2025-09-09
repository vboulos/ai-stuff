#!/usr/bin/env python3
"""
Complete ReportGenerator - Generates comprehensive JSON reports with analysis results
"""

import json
import datetime
import os
from typing import List, Dict, Any
from pathlib import Path


class ReportGenerator:
    """Generates comprehensive JSON reports with test failure analysis results."""
    
    def generate_report(self, analyzed_tests: List[Dict[str, str]], output_file: str) -> str:
        """Generate and save comprehensive JSON report with analysis results."""
        
        # Create output directory if it doesn't exist
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate comprehensive report
        report = {
            'metadata': {
                'generated_at': datetime.datetime.now().isoformat(),
                'generator': 'Claude Test Failure Analyzer',
                'version': '1.0',
                'total_failed_tests': len(analyzed_tests)
            },
            'summary': self._generate_summary(analyzed_tests),
            'failed_tests': analyzed_tests,
            'insights': self._generate_insights(analyzed_tests)
        }
        
        # Save report
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Report saved to: {output_file}")
            self.print_summary(analyzed_tests)
            return output_file
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return ""
    
    def _generate_summary(self, analyzed_tests: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate summary statistics for the report."""
        
        if not analyzed_tests:
            return {'total': 0, 'analysis_success_rate': 0}
        
        # Count successful analyses (not error messages)
        successful_analyses = sum(1 for test in analyzed_tests 
                                if not self._is_error_analysis(test))
        
        # Categorize common error types
        error_categories = self._categorize_errors(analyzed_tests)
        
        return {
            'total_tests': len(analyzed_tests),
            'successful_analyses': successful_analyses,
            'analysis_success_rate': round(successful_analyses / len(analyzed_tests) * 100, 1),
            'error_categories': error_categories,
            'most_common_issues': self._get_common_issues(analyzed_tests)
        }
    
    def _generate_insights(self, analyzed_tests: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate insights and recommendations based on analysis results."""
        
        insights = {
            'recommendations': [],
            'patterns': {},
            'fix_complexity': {'simple': 0, 'moderate': 0, 'complex': 0}
        }
        
        if not analyzed_tests:
            return insights
        
        # Analyze patterns in root causes
        root_cause_keywords = {}
        for test in analyzed_tests:
            root_cause = test.get('root_cause', '').lower()
            for keyword in ['assertion', 'null', 'type', 'import', 'index', 'key', 'connection']:
                if keyword in root_cause:
                    root_cause_keywords[keyword] = root_cause_keywords.get(keyword, 0) + 1
        
        insights['patterns'] = root_cause_keywords
        
        # Analyze fix complexity
        for test in analyzed_tests:
            code_fix = test.get('code_fix', '').lower()
            if any(word in code_fix for word in ['add', 'check', 'validate', 'simple']):
                insights['fix_complexity']['simple'] += 1
            elif any(word in code_fix for word in ['refactor', 'redesign', 'rewrite']):
                insights['fix_complexity']['complex'] += 1
            else:
                insights['fix_complexity']['moderate'] += 1
        
        # Generate recommendations
        insights['recommendations'] = self._generate_recommendations(analyzed_tests, root_cause_keywords)
        
        return insights
    
    def _categorize_errors(self, analyzed_tests: List[Dict[str, str]]) -> Dict[str, int]:
        """Categorize errors by type."""
        
        categories = {
            'assertion_errors': 0,
            'type_errors': 0,
            'import_errors': 0,
            'null_pointer_errors': 0,
            'index_errors': 0,
            'other_errors': 0
        }
        
        for test in analyzed_tests:
            failure_msg = test.get('failure_message', '').lower()
            
            if 'assertion' in failure_msg or 'assert' in failure_msg:
                categories['assertion_errors'] += 1
            elif 'type' in failure_msg and 'error' in failure_msg:
                categories['type_errors'] += 1
            elif 'import' in failure_msg or 'module' in failure_msg:
                categories['import_errors'] += 1
            elif 'null' in failure_msg or 'none' in failure_msg:
                categories['null_pointer_errors'] += 1
            elif 'index' in failure_msg:
                categories['index_errors'] += 1
            else:
                categories['other_errors'] += 1
        
        return categories
    
    def _get_common_issues(self, analyzed_tests: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Identify most common issues across tests."""
        
        issue_counts = {}
        
        for test in analyzed_tests:
            # Extract key phrases from root causes
            root_cause = test.get('root_cause', '')
            if len(root_cause) > 50:  # Skip error messages
                key_phrase = root_cause[:100] + "..." if len(root_cause) > 100 else root_cause
                issue_counts[key_phrase] = issue_counts.get(key_phrase, 0) + 1
        
        # Sort by frequency and return top 5
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'issue': issue, 'count': count}
            for issue, count in sorted_issues[:5]
        ]
    
    def _generate_recommendations(self, analyzed_tests: List[Dict[str, str]], 
                                patterns: Dict[str, int]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        
        recommendations = []
        total_tests = len(analyzed_tests)
        
        # Pattern-based recommendations
        if patterns.get('assertion', 0) > total_tests * 0.3:
            recommendations.append("High number of assertion failures - review test expectations and business logic")
        
        if patterns.get('null', 0) > total_tests * 0.2:
            recommendations.append("Multiple null pointer issues - add null checks and validation")
        
        if patterns.get('type', 0) > total_tests * 0.2:
            recommendations.append("Type-related errors detected - improve type safety and validation")
        
        if patterns.get('import', 0) > 0:
            recommendations.append("Import/module errors found - check dependencies and environment setup")
        
        # General recommendations
        error_analyses = sum(1 for test in analyzed_tests if self._is_error_analysis(test))
        if error_analyses > total_tests * 0.5:
            recommendations.append("Many analysis errors occurred - check Claude CLI setup or provide more context")
        
        if not recommendations:
            recommendations.append("Review individual test failures and apply suggested fixes systematically")
        
        return recommendations
    
    def _is_error_analysis(self, test: Dict[str, str]) -> bool:
        """Check if the analysis result is an error rather than actual analysis."""
        root_cause = test.get('root_cause', '').lower()
        return any(keyword in root_cause for keyword in [
            'error analyzing', 'analysis failed', 'cli error', 'timeout', 'not found'
        ])
    
    def print_summary(self, analyzed_tests: List[Dict[str, str]]) -> None:
        """Print a formatted summary of the analysis results."""
        
        if not analyzed_tests:
            print("No test failures to analyze.")
            return
        
        print(f"\n📊 Analysis Summary:")
        print(f"   Total failed tests analyzed: {len(analyzed_tests)}")
        
        # Count successful analyses
        successful = sum(1 for test in analyzed_tests if not self._is_error_analysis(test))
        success_rate = (successful / len(analyzed_tests)) * 100
        print(f"   Successful analyses: {successful}/{len(analyzed_tests)} ({success_rate:.1f}%)")
        
        # Show sample results
        print(f"\n📋 Sample Results:")
        for i, test in enumerate(analyzed_tests[:3], 1):
            print(f"   {i}. {test['test_name']}")
            
            # Truncate long messages for display
            root_cause = test['root_cause']
            if len(root_cause) > 80:
                root_cause = root_cause[:80] + "..."
            print(f"      Root Cause: {root_cause}")
            
            code_fix = test['code_fix']
            if len(code_fix) > 80:
                code_fix = code_fix[:80] + "..."
            print(f"      Fix: {code_fix}")
            print()
        
        if len(analyzed_tests) > 3:
            print(f"   ... and {len(analyzed_tests) - 3} more tests")
        
        print(f"📄 Full details available in the generated report")
    
    def generate_simple_report(self, analyzed_tests: List[Dict[str, str]], output_file: str) -> str:
        """Generate a simple, flat JSON report for easy consumption."""
        
        simple_report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'total_tests': len(analyzed_tests),
            'tests': analyzed_tests
        }
        
        simple_output = output_file.replace('.json', '_simple.json')
        
        try:
            with open(simple_output, 'w', encoding='utf-8') as f:
                json.dump(simple_report, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Simple report also saved to: {simple_output}")
            return simple_output
            
        except Exception as e:
            print(f"❌ Error saving simple report: {e}")
            return ""