#!/usr/bin/env python3
"""
JsonReportGenerator - Generates JSON reports with test failures, root causes, and fix suggestions
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from fix_suggester import CodeFixSuggestion


@dataclass
class TestFailureReport:
    """Complete test failure report with analysis and fix suggestions."""
    test_name: str
    failure_message: str
    root_cause: str
    suggested_fix: str
    code_example: Optional[str] = None
    framework_specific_advice: Optional[str] = None
    prevention_tips: Optional[str] = None
    confidence_score: float = 0.7
    effort_estimate: str = "medium"
    fix_category: str = "code_change"
    analysis_timestamp: str = ""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    framework: Optional[str] = None


class JsonReportGenerator:
    """Generates comprehensive JSON reports from test failure analysis."""
    
    def __init__(self):
        """Initialize the JSON report generator."""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def generate_report(self, fix_suggestions: List[CodeFixSuggestion], output_path: str) -> bool:
        """
        Generate a comprehensive JSON report from fix suggestions.
        
        Args:
            fix_suggestions: List of CodeFixSuggestion objects
            output_path: Path where to save the JSON report
            
        Returns:
            True if report generated successfully, False otherwise
        """
        try:
            # Convert fix suggestions to report format
            test_reports = []
            for fix in fix_suggestions:
                report = TestFailureReport(
                    test_name=fix.test_name,
                    failure_message=fix.original_failure,
                    root_cause=fix.root_cause,
                    suggested_fix=fix.fix_description,
                    code_example=fix.code_example,
                    framework_specific_advice=fix.framework_specific_advice,
                    prevention_tips=fix.prevention_tips,
                    confidence_score=fix.confidence_score,
                    effort_estimate=fix.estimated_effort,
                    fix_category=fix.fix_category,
                    analysis_timestamp=datetime.now().isoformat()
                )
                test_reports.append(report)
            
            # Generate comprehensive report
            report_data = self._create_comprehensive_report(test_reports)
            
            # Save to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return False
    
    def _create_comprehensive_report(self, test_reports: List[TestFailureReport]) -> Dict[str, Any]:
        """
        Create a comprehensive report structure.
        
        Args:
            test_reports: List of TestFailureReport objects
            
        Returns:
            Dictionary with complete report structure
        """
        # Generate summary statistics
        summary = self._generate_summary(test_reports)
        
        # Generate insights and recommendations
        insights = self._generate_insights(test_reports)
        
        # Create the complete report
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator': 'Claude CLI Test Failure Analyzer',
                'version': '1.0.0',
                'total_failures_analyzed': len(test_reports)
            },
            'executive_summary': summary,
            'insights_and_patterns': insights,
            'test_failure_details': [asdict(report) for report in test_reports],
            'recommendations': self._generate_recommendations(test_reports),
            'appendix': {
                'methodology': 'Test failures analyzed using Claude CLI for root cause analysis and fix suggestions',
                'confidence_scoring': 'Confidence scores range from 0.0 to 1.0, representing analysis certainty',
                'effort_estimates': {
                    'low': 'Quick fixes, typically 1-2 hours',
                    'medium': 'Moderate changes, typically 2-8 hours', 
                    'high': 'Complex changes, typically 1+ days'
                },
                'fix_categories': {
                    'code_change': 'Requires modifying test or application code',
                    'configuration': 'Requires configuration changes',
                    'environment': 'Requires environment setup or infrastructure changes'
                }
            }
        }
        
        return report
    
    def _generate_summary(self, test_reports: List[TestFailureReport]) -> Dict[str, Any]:
        """Generate executive summary statistics."""
        if not test_reports:
            return {}
        
        # Effort distribution
        effort_counts = {}
        category_counts = {}
        framework_counts = {}
        
        for report in test_reports:
            effort_counts[report.effort_estimate] = effort_counts.get(report.effort_estimate, 0) + 1
            category_counts[report.fix_category] = category_counts.get(report.fix_category, 0) + 1
            if report.framework:
                framework_counts[report.framework] = framework_counts.get(report.framework, 0) + 1
        
        # Confidence statistics
        confidences = [report.confidence_score for report in test_reports]
        avg_confidence = sum(confidences) / len(confidences)
        high_confidence = sum(1 for c in confidences if c >= 0.8)
        low_confidence = sum(1 for c in confidences if c < 0.5)
        
        # Additional metrics
        with_code_examples = sum(1 for r in test_reports if r.code_example)
        with_prevention_tips = sum(1 for r in test_reports if r.prevention_tips)
        
        return {
            'total_failures': len(test_reports),
            'average_confidence_score': round(avg_confidence, 2),
            'high_confidence_analyses': high_confidence,
            'low_confidence_analyses': low_confidence,
            'effort_distribution': effort_counts,
            'fix_category_distribution': category_counts,
            'framework_distribution': framework_counts,
            'reports_with_code_examples': with_code_examples,
            'reports_with_prevention_tips': with_prevention_tips,
            'quick_wins': effort_counts.get('low', 0),
            'complex_fixes': effort_counts.get('high', 0)
        }
    
    def _generate_insights(self, test_reports: List[TestFailureReport]) -> Dict[str, Any]:
        """Generate insights and patterns from the test failures."""
        insights = {
            'common_failure_patterns': [],
            'framework_specific_issues': {},
            'effort_vs_confidence_analysis': {},
            'top_prevention_strategies': []
        }
        
        # Analyze common failure patterns
        root_causes = [report.root_cause.lower() for report in test_reports]
        
        # Count common keywords in root causes
        common_keywords = {}
        for cause in root_causes:
            words = cause.split()
            for word in words:
                if len(word) > 4:  # Only consider meaningful words
                    common_keywords[word] = common_keywords.get(word, 0) + 1
        
        # Get top keywords
        top_keywords = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        insights['common_failure_patterns'] = [
            {'pattern': keyword, 'frequency': count} 
            for keyword, count in top_keywords if count > 1
        ]
        
        # Framework-specific analysis
        framework_issues = {}
        for report in test_reports:
            if report.framework:
                if report.framework not in framework_issues:
                    framework_issues[report.framework] = {
                        'total_failures': 0,
                        'avg_confidence': 0.0,
                        'common_categories': {}
                    }
                
                framework_issues[report.framework]['total_failures'] += 1
                framework_issues[report.framework]['avg_confidence'] += report.confidence_score
                
                category = report.fix_category
                if category not in framework_issues[report.framework]['common_categories']:
                    framework_issues[report.framework]['common_categories'][category] = 0
                framework_issues[report.framework]['common_categories'][category] += 1
        
        # Calculate averages
        for framework, data in framework_issues.items():
            if data['total_failures'] > 0:
                data['avg_confidence'] = round(data['avg_confidence'] / data['total_failures'], 2)
        
        insights['framework_specific_issues'] = framework_issues
        
        # Effort vs confidence analysis
        effort_confidence = {}
        for report in test_reports:
            effort = report.effort_estimate
            if effort not in effort_confidence:
                effort_confidence[effort] = {'scores': [], 'count': 0}
            effort_confidence[effort]['scores'].append(report.confidence_score)
            effort_confidence[effort]['count'] += 1
        
        for effort, data in effort_confidence.items():
            if data['scores']:
                data['avg_confidence'] = round(sum(data['scores']) / len(data['scores']), 2)
                del data['scores']  # Remove raw scores from output
        
        insights['effort_vs_confidence_analysis'] = effort_confidence
        
        # Top prevention strategies
        prevention_tips = []
        for report in test_reports:
            if report.prevention_tips:
                prevention_tips.append(report.prevention_tips)
        
        # Extract common prevention themes (simplified)
        if prevention_tips:
            insights['top_prevention_strategies'] = [
                'Implement proper test setup and teardown',
                'Add comprehensive error handling and logging',
                'Use framework-specific best practices',
                'Implement proper mocking and test data management',
                'Add timeout and retry mechanisms for flaky tests'
            ][:min(5, len(prevention_tips))]
        
        return insights
    
    def _generate_recommendations(self, test_reports: List[TestFailureReport]) -> Dict[str, Any]:
        """Generate actionable recommendations based on the analysis."""
        recommendations = {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_strategies': [],
            'priority_fixes': []
        }
        
        # Immediate actions (high confidence, low effort)
        immediate = [
            report for report in test_reports 
            if report.confidence_score >= 0.8 and report.effort_estimate == 'low'
        ]
        
        recommendations['immediate_actions'] = [
            {
                'test_name': report.test_name,
                'action': f"Fix {report.test_name}: {report.suggested_fix[:100]}...",
                'confidence': report.confidence_score,
                'effort': report.effort_estimate
            }
            for report in immediate[:5]  # Top 5 immediate actions
        ]
        
        # Short-term improvements (medium effort)
        short_term = [
            report for report in test_reports 
            if report.effort_estimate == 'medium' and report.confidence_score >= 0.6
        ]
        
        recommendations['short_term_improvements'] = [
            f"Address {report.test_name}: {report.root_cause[:80]}..."
            for report in short_term[:3]
        ]
        
        # Long-term strategies
        high_effort = [report for report in test_reports if report.effort_estimate == 'high']
        
        if high_effort:
            recommendations['long_term_strategies'] = [
                'Plan architecture changes for complex test failures',
                'Implement comprehensive test infrastructure improvements',
                'Consider framework upgrades or migrations where needed'
            ]
        
        # Priority fixes (high confidence regardless of effort)
        priority = sorted(
            test_reports, 
            key=lambda x: x.confidence_score, 
            reverse=True
        )[:3]
        
        recommendations['priority_fixes'] = [
            {
                'test_name': report.test_name,
                'priority_reason': f"High confidence ({report.confidence_score:.2f}) analysis available",
                'effort': report.effort_estimate
            }
            for report in priority
        ]
        
        return recommendations
    
    def generate_simple_report(self, fix_suggestions: List[CodeFixSuggestion], output_path: str) -> bool:
        """
        Generate a simplified JSON report with just the essential information.
        
        Args:
            fix_suggestions: List of CodeFixSuggestion objects
            output_path: Path where to save the simple JSON report
            
        Returns:
            True if report generated successfully, False otherwise
        """
        try:
            simple_report = {
                'generated_at': datetime.now().isoformat(),
                'total_failures': len(fix_suggestions),
                'test_failures': []
            }
            
            for fix in fix_suggestions:
                simple_failure = {
                    'test_name': fix.test_name,
                    'failure_message': fix.original_failure,
                    'root_cause': fix.root_cause,
                    'suggested_fix': fix.fix_description,
                    'confidence_score': fix.confidence_score,
                    'effort_estimate': fix.estimated_effort
                }
                
                # Add code example if available
                if fix.code_example:
                    simple_failure['code_example'] = fix.code_example
                
                simple_report['test_failures'].append(simple_failure)
            
            # Save simple report
            simple_output_path = output_path.replace('.json', '_simple.json')
            with open(simple_output_path, 'w', encoding='utf-8') as f:
                json.dump(simple_report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Simple report generated: {simple_output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating simple report: {e}")
            return False
    
    def validate_report(self, report_path: str) -> Dict[str, Any]:
        """
        Validate a generated report and return validation results.
        
        Args:
            report_path: Path to the JSON report file
            
        Returns:
            Dictionary with validation results
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            validation = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'statistics': {}
            }
            
            # Check required fields
            required_top_level = ['report_metadata', 'executive_summary', 'test_failure_details']
            for field in required_top_level:
                if field not in report:
                    validation['errors'].append(f"Missing required field: {field}")
                    validation['valid'] = False
            
            # Check test failure details
            if 'test_failure_details' in report:
                failures = report['test_failure_details']
                validation['statistics']['total_failures'] = len(failures)
                
                required_failure_fields = ['test_name', 'failure_message', 'root_cause', 'suggested_fix']
                for i, failure in enumerate(failures):
                    for field in required_failure_fields:
                        if field not in failure or not failure[field]:
                            validation['warnings'].append(f"Failure {i+1} missing or empty field: {field}")
            
            # Check confidence scores
            if 'test_failure_details' in report:
                scores = [f.get('confidence_score', 0) for f in report['test_failure_details']]
                if scores:
                    validation['statistics']['avg_confidence'] = sum(scores) / len(scores)
                    validation['statistics']['low_confidence_count'] = sum(1 for s in scores if s < 0.5)
            
            return validation
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Error validating report: {e}"],
                'warnings': [],
                'statistics': {}
            }


def main():
    """Example usage of JsonReportGenerator."""
    import sys
    from test_result_reader import TestResultReader
    from failure_filter import FailureFilter
    from failure_analyzer import FailureAnalyzer
    from fix_suggester import FixSuggester
    
    if len(sys.argv) < 3:
        print("Usage: python3 json_report_generator.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Full pipeline
    reader = TestResultReader()
    test_cases = reader.read_json_file(input_file)
    
    filter_obj = FailureFilter()
    failed_tests = filter_obj.extract_failed_tests(test_cases)
    
    if not failed_tests:
        print("🎉 No failed tests found!")
        sys.exit(0)
    
    analyzer = FailureAnalyzer()
    if not analyzer.test_connection():
        print("❌ Cannot connect to Claude CLI")
        sys.exit(1)
    
    # Process first few for demonstration
    sample_tests = failed_tests[:3]
    analysis_results = analyzer.analyze_multiple_failures(sample_tests)
    
    fix_suggester = FixSuggester()
    fix_suggestions = fix_suggester.generate_multiple_fixes(analysis_results)
    
    # Generate reports
    generator = JsonReportGenerator()
    
    if generator.generate_report(fix_suggestions, output_file):
        print(f"✅ Comprehensive report generated: {output_file}")
        
        # Generate simple report too
        generator.generate_simple_report(fix_suggestions, output_file)
        
        # Validate the report
        validation = generator.validate_report(output_file)
        if validation['valid']:
            print("✅ Report validation passed")
        else:
            print(f"⚠️  Report validation issues: {validation['errors']}")
    else:
        print("❌ Failed to generate report")


if __name__ == "__main__":
    main()