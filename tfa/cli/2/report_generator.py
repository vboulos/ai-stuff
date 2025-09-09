#!/usr/bin/env python3
"""
ReportGenerator - Generates JSON reports with analysis results
"""

import json
import datetime
from typing import List, Dict


class ReportGenerator:
    """Generates JSON reports with test failure analysis results."""
    
    def generate_report(self, analyzed_tests: List[Dict[str, str]], output_file: str) -> None:
        """Generate and save JSON report with analysis results."""
        
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'total_failed_tests': len(analyzed_tests),
            'failed_tests': analyzed_tests
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {output_file}")
        print(f"Analyzed {len(analyzed_tests)} failed tests")