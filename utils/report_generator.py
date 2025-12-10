import json
from datetime import datetime
from pathlib import Path


class ReportGenerator:
    """Generate detailed test execution reports"""
    
    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def start_test_run(self):
        """Mark start of test execution"""
        self.start_time = datetime.now()
    
    def end_test_run(self):
        """Mark end of test execution"""
        self.end_time = datetime.now()
    
    def add_test_result(self, test_name, status, duration, error=None, screenshot=None):
        """Add a test result"""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'duration': duration,
            'error': error,
            'screenshot': screenshot,
            'timestamp': datetime.now().isoformat()
        })
    
    def generate_summary(self):
        """Generate test summary"""
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed = len([r for r in self.test_results if r['status'] == 'FAILED'])
        skipped = len([r for r in self.test_results if r['status'] == 'SKIPPED'])
        
        total_duration = sum(r['duration'] for r in self.test_results)
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': f"{(passed/total*100):.2f}%" if total > 0 else "0%",
            'total_duration': f"{total_duration:.2f}s",
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }
    
    def save_json_report(self):
        """Save report as JSON"""
        report = {
            'summary': self.generate_summary(),
            'test_results': self.test_results
        }
        
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return filepath
    
    def generate_html_report(self):
        """Generate HTML report"""
        summary = self.generate_summary()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 15px; background: #ecf0f1; border-radius: 5px; min-width: 150px; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ font-size: 14px; color: #7f8c8d; margin-top: 5px; }}
        .passed {{ color: #27ae60; }}
        .failed {{ color: #e74c3c; }}
        .skipped {{ color: #f39c12; }}
        table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 5px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .status-badge {{ padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 12px; }}
        .badge-passed {{ background: #d4edda; color: #155724; }}
        .badge-failed {{ background: #f8d7da; color: #721c24; }}
        .badge-skipped {{ background: #fff3cd; color: #856404; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Automated Test Execution Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{summary['total_tests']}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value passed">{summary['passed']}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value failed">{summary['failed']}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value skipped">{summary['skipped']}</div>
                <div class="metric-label">Skipped</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['pass_rate']}</div>
                <div class="metric-label">Pass Rate</div>
            </div>
        </div>
    </div>
    
    <div class="summary">
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Case</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in self.test_results:
            status_class = f"badge-{result['status'].lower()}"
            error_msg = result['error'][:100] if result['error'] else "-"
            
            html += f"""
                <tr>
                    <td>{result['test_name']}</td>
                    <td><span class="status-badge {status_class}">{result['status']}</span></td>
                    <td>{result['duration']:.2f}s</td>
                    <td>{error_msg}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        filename = f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(html)
        
        return filepath


# ============================================
# FILE: run_all_tests.py (Enhanced version)
# ============================================
"""
Enhanced test runner with comprehensive reporting
"""
