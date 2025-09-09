#!/usr/bin/env python3
"""
Simple Report Writer - Generates JSON reports with analysis results
"""

import json
import datetime
from typing import List, Dict, Any


class SimpleReportWriter:
    """Writes analysis results to JSON file."""
    
    def generate_report(self, analyzed_tests: List[Dict[str, Any]], output_file: str) -> str:
        """Generate and save JSON report with analysis results."""
        
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'total_failed_tests': len(analyzed_tests),
            'analyzed_tests': analyzed_tests
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file
    
    def print_summary(self, analyzed_tests: List[Dict[str, Any]]) -> None:
        """Print a summary of the analysis results."""
        
        print(f"\n📊 Analysis Summary:")
        print(f"   Total failed tests analyzed: {len(analyzed_tests)}")
        
        # Show sample results
        for i, test in enumerate(analyzed_tests[:3]):  # Show first 3
            print(f"\n   Test {i+1}: {test['test_name']}")
            print(f"   Root Cause: {test['root_cause'][:100]}...")
            print(f"   Fix: {test['code_fix'][:100]}...")
        
        if len(analyzed_tests) > 3:
            print(f"\n   ... and {len(analyzed_tests) - 3} more tests")
        
        print(f"\n✅ Full report saved")