#!/usr/bin/env python3
"""
JSONReportGenerator - Generates comprehensive JSON reports with test failures, analysis, and fix suggestions
"""

import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class JSONReportGenerator:
    """Generates structured JSON reports containing test failures, root cause analysis, and fix suggestions."""
    
    def __init__(self):
        self.report_version = "1.0"
        self.generator_info = {
            "tool_name": "Claude CLI Test Failure Analyzer",
            "version": self.report_version,
            "description": "Automated test failure analysis and fix suggestion tool"
        }
    
    def generate_comprehensive_report(self, 
                                    results_with_fixes: List[Dict[str, Any]],
                                    original_summary: Optional[Dict[str, int]] = None,
                                    analysis_summary: Optional[Dict[str, Any]] = None,
                                    fix_summary: Optional[Dict[str, Any]] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a comprehensive report with all analysis and fix data."""
        
        timestamp = datetime.datetime.now().isoformat()
        
        report = {
            "report_metadata": {
                "generated_at": timestamp,
                "generator": self.generator_info,
                "report_type": "comprehensive_test_failure_analysis",
                "total_failed_tests": len(results_with_fixes)
            },
            "execution_summary": {
                "original_test_summary": original_summary or {},
                "analysis_summary": analysis_summary or {},
                "fix_summary": fix_summary or {},
                "processing_metadata": metadata or {}
            },
            "failed_tests": []
        }
        
        # Process each failed test result
        for result in results_with_fixes:
            test_report = self._create_test_report(result)
            report["failed_tests"].append(test_report)
        
        # Add aggregate insights
        report["insights"] = self._generate_insights(results_with_fixes)
        
        return report
    
    def _create_test_report(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed report for a single test failure."""
        
        # Basic test information
        test_report = {
            "test_identification": {
                "test_name": result.get('test_name', 'Unknown'),
                "test_class": result.get('test_class', ''),
                "file_path": result.get('file_path', ''),
                "line_number": result.get('line_number'),
                "status": result.get('status', 'failed'),
                "duration": result.get('duration'),
                "original_index": result.get('original_index')
            },
            "failure_details": {
                "error_message": result.get('message', ''),
                "stack_trace": result.get('stack_trace', ''),
                "error_category": result.get('category', 'unknown')
            }
        }
        
        # Root cause analysis
        root_cause = result.get('root_cause_analysis', {})
        test_report["root_cause_analysis"] = {
            "primary_cause": root_cause.get('primary_root_cause', ''),
            "technical_details": root_cause.get('technical_details', ''),
            "impact_assessment": root_cause.get('impact_assessment', ''),
            "confidence_level": root_cause.get('confidence_level', 'Medium'),
            "analysis_successful": 'analysis_error' not in root_cause
        }
        
        # Fix suggestion
        fix_suggestion = result.get('fix_suggestion', {})
        test_report["fix_suggestion"] = {
            "approach": fix_suggestion.get('fix_approach', ''),
            "explanation": fix_suggestion.get('explanation', ''),
            "confidence": fix_suggestion.get('confidence', 'Medium'),
            "testing_notes": fix_suggestion.get('testing_notes', ''),
            "side_effects": fix_suggestion.get('side_effects', ''),
            "code_changes": self._format_code_changes(fix_suggestion.get('code_changes', [])),
            "fix_generation_successful": 'fix_error' not in fix_suggestion
        }
        
        # Quality indicators
        test_report["quality_indicators"] = {
            "analysis_confidence": root_cause.get('confidence_level', 'Medium'),
            "fix_confidence": fix_suggestion.get('confidence', 'Medium'),
            "has_code_changes": len(fix_suggestion.get('code_changes', [])) > 0,
            "actionable_fix": self._is_actionable_fix(fix_suggestion),
            "completeness_score": self._calculate_completeness_score(test_report)
        }
        
        return test_report
    
    def _format_code_changes(self, code_changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format code changes for better readability in the report."""
        
        formatted_changes = []
        
        for change in code_changes:
            formatted_change = {
                "change_type": change.get('type', 'unknown'),
                "description": change.get('description', ''),
                "line_number": change.get('line_number'),
                "before_code": change.get('before', ''),
                "after_code": change.get('after', ''),
                "code_block": change.get('code', ''),
                "is_actionable": bool(change.get('before') or change.get('after') or change.get('code'))
            }
            formatted_changes.append(formatted_change)
        
        return formatted_changes
    
    def _is_actionable_fix(self, fix_suggestion: Dict[str, Any]) -> bool:
        """Determine if the fix suggestion is actionable."""
        
        # Check if there are concrete code changes
        code_changes = fix_suggestion.get('code_changes', [])
        has_concrete_changes = any(
            change.get('before') or change.get('after') or change.get('code')
            for change in code_changes
        )
        
        # Check if approach is specific (not just error messages)
        approach = fix_suggestion.get('fix_approach', '').lower()
        is_specific_approach = (
            approach and 
            len(approach) > 50 and  # Reasonable length
            'error' not in approach and 
            'failed' not in approach
        )
        
        return has_concrete_changes or is_specific_approach
    
    def _calculate_completeness_score(self, test_report: Dict[str, Any]) -> float:
        """Calculate a completeness score for the test report (0-1)."""
        
        score = 0.0
        max_score = 10.0
        
        # Basic information (2 points)
        if test_report["test_identification"]["test_name"] != 'Unknown':
            score += 1.0
        if test_report["failure_details"]["error_message"]:
            score += 1.0
        
        # Root cause analysis (4 points)
        root_cause = test_report["root_cause_analysis"]
        if root_cause["primary_cause"]:
            score += 1.5
        if root_cause["technical_details"]:
            score += 1.0
        if root_cause["confidence_level"] in ['High', 'Medium']:
            score += 1.0
        if root_cause["analysis_successful"]:
            score += 0.5
        
        # Fix suggestion (4 points)
        fix_suggestion = test_report["fix_suggestion"]
        if fix_suggestion["approach"]:
            score += 1.5
        if fix_suggestion["code_changes"]:
            score += 1.5
        if fix_suggestion["confidence"] in ['High', 'Medium']:
            score += 0.5
        if fix_suggestion["fix_generation_successful"]:
            score += 0.5
        
        return round(score / max_score, 2)
    
    def _generate_insights(self, results_with_fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate aggregate insights from all test failures."""
        
        insights = {
            "failure_patterns": {},
            "common_root_causes": {},
            "fix_complexity_distribution": {"simple": 0, "moderate": 0, "complex": 0},
            "confidence_analysis": {
                "high_confidence_fixes": 0,
                "medium_confidence_fixes": 0,
                "low_confidence_fixes": 0
            },
            "actionable_fixes_count": 0,
            "recommendations": []
        }
        
        # Analyze patterns
        for result in results_with_fixes:
            # Count failure patterns
            error_msg = result.get('message', '').lower()
            error_type = self._categorize_error_type(error_msg)
            insights["failure_patterns"][error_type] = insights["failure_patterns"].get(error_type, 0) + 1
            
            # Count root causes
            root_cause = result.get('root_cause_analysis', {}).get('primary_root_cause', '')[:100]
            if root_cause:
                insights["common_root_causes"][root_cause] = insights["common_root_causes"].get(root_cause, 0) + 1
            
            # Analyze fix complexity
            fix_suggestion = result.get('fix_suggestion', {})
            complexity = self._assess_fix_complexity(fix_suggestion)
            insights["fix_complexity_distribution"][complexity] += 1
            
            # Count confidence levels
            fix_confidence = fix_suggestion.get('confidence', 'Medium').lower()
            if 'high' in fix_confidence:
                insights["confidence_analysis"]["high_confidence_fixes"] += 1
            elif 'low' in fix_confidence:
                insights["confidence_analysis"]["low_confidence_fixes"] += 1
            else:
                insights["confidence_analysis"]["medium_confidence_fixes"] += 1
            
            # Count actionable fixes
            if self._is_actionable_fix(fix_suggestion):
                insights["actionable_fixes_count"] += 1
        
        # Generate recommendations
        insights["recommendations"] = self._generate_recommendations(insights, len(results_with_fixes))
        
        return insights
    
    def _categorize_error_type(self, error_message: str) -> str:
        """Categorize error type from error message."""
        
        error_message = error_message.lower()
        
        if 'assertion' in error_message or 'assert' in error_message:
            return 'assertion_error'
        elif 'type' in error_message and 'error' in error_message:
            return 'type_error'
        elif 'attribute' in error_message:
            return 'attribute_error'
        elif 'import' in error_message or 'module' in error_message:
            return 'import_error'
        elif 'index' in error_message:
            return 'index_error'
        elif 'key' in error_message:
            return 'key_error'
        elif 'value' in error_message:
            return 'value_error'
        else:
            return 'other_error'
    
    def _assess_fix_complexity(self, fix_suggestion: Dict[str, Any]) -> str:
        """Assess the complexity of a fix suggestion."""
        
        code_changes = fix_suggestion.get('code_changes', [])
        approach = fix_suggestion.get('fix_approach', '')
        
        # Simple: single line change or simple replacement
        if len(code_changes) == 1 and ('replace' in approach.lower() or 'change' in approach.lower()):
            return 'simple'
        
        # Complex: multiple changes or architectural changes
        elif len(code_changes) > 2 or any(
            keyword in approach.lower() 
            for keyword in ['refactor', 'redesign', 'architecture', 'multiple']
        ):
            return 'complex'
        
        # Moderate: everything else
        else:
            return 'moderate'
    
    def _generate_recommendations(self, insights: Dict[str, Any], total_failures: int) -> List[str]:
        """Generate actionable recommendations based on insights."""
        
        recommendations = []
        
        # Failure pattern recommendations
        top_patterns = sorted(insights["failure_patterns"].items(), key=lambda x: x[1], reverse=True)
        if top_patterns:
            top_pattern = top_patterns[0]
            if top_pattern[1] > total_failures * 0.3:  # More than 30% of failures
                recommendations.append(
                    f"Focus on {top_pattern[0]} issues - they account for {top_pattern[1]} out of {total_failures} failures"
                )
        
        # Confidence recommendations
        low_confidence = insights["confidence_analysis"]["low_confidence_fixes"]
        if low_confidence > total_failures * 0.5:
            recommendations.append(
                "Many fixes have low confidence - consider manual code review for better analysis"
            )
        
        # Actionable fixes recommendations
        actionable_ratio = insights["actionable_fixes_count"] / total_failures if total_failures > 0 else 0
        if actionable_ratio < 0.5:
            recommendations.append(
                "Less than 50% of fixes are immediately actionable - consider providing more source code context"
            )
        
        # Complexity recommendations
        complex_fixes = insights["fix_complexity_distribution"]["complex"]
        if complex_fixes > total_failures * 0.4:
            recommendations.append(
                "Many fixes are complex - consider breaking down into smaller, incremental changes"
            )
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_path: str, 
                   pretty_print: bool = True) -> str:
        """Save the report to a JSON file."""
        
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(report, f, ensure_ascii=False)
            
            return str(path.absolute())
            
        except Exception as e:
            raise Exception(f"Failed to save report to {output_path}: {e}")
    
    def generate_summary_report(self, results_with_fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a concise summary report."""
        
        timestamp = datetime.datetime.now().isoformat()
        
        summary = {
            "report_metadata": {
                "generated_at": timestamp,
                "generator": self.generator_info,
                "report_type": "summary_test_failure_analysis"
            },
            "summary": {
                "total_failed_tests": len(results_with_fixes),
                "successfully_analyzed": sum(1 for r in results_with_fixes 
                                           if 'analysis_error' not in r.get('root_cause_analysis', {})),
                "fixes_generated": sum(1 for r in results_with_fixes 
                                     if 'fix_error' not in r.get('fix_suggestion', {})),
                "actionable_fixes": sum(1 for r in results_with_fixes 
                                      if self._is_actionable_fix(r.get('fix_suggestion', {})))
            },
            "top_issues": []
        }
        
        # Add top 5 most critical issues
        for i, result in enumerate(results_with_fixes[:5]):
            issue = {
                "rank": i + 1,
                "test_name": result.get('test_name', 'Unknown'),
                "error_summary": result.get('message', '')[:100] + '...' if len(result.get('message', '')) > 100 else result.get('message', ''),
                "root_cause": result.get('root_cause_analysis', {}).get('primary_root_cause', '')[:200] + '...',
                "fix_approach": result.get('fix_suggestion', {}).get('fix_approach', '')[:200] + '...'
            }
            summary["top_issues"].append(issue)
        
        return summary