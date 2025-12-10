import sys
import os
import pytest
from datetime import datetime
from pathlib import Path


def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         EXECUTION          -       ISTQB PROJECT         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_test_suite(suite_name, browser='chrome', markers=''):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {suite_name}")
    print(f"{'='*60}\n")
    
    args = [
        f"tests/{suite_name}",
        "-v",
        f"--browser={browser}",
        "--tb=short",
    ]
    
    if markers:
        args.append(f"-m {markers}")
    
    result = pytest.main(args)
    return result


def run_all_tests():
    """Run complete test suite with detailed reporting"""
    print_banner()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"reports/complete_report_{timestamp}.html"
    
    # Ensure reports directory exists
    Path("reports").mkdir(exist_ok=True)
    Path("screenshots").mkdir(exist_ok=True)
    
    print("📋 Test Configuration:")
    print(f"   • Target: OpenCart Demo")
    print(f"   • Browser: Chrome (default)")
    print(f"   • Report: {report_file}")
    print(f"   • Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all tests with comprehensive reporting
    args = [
        "tests/",
        "-v",
        "--html=" + report_file,
        "--self-contained-html",
        "--tb=short",
        "--maxfail=10",
        "-ra",  # Show all test results summary
    ]
    
    print("🚀 Starting test execution...\n")
    exit_code = pytest.main(args)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ TEST EXECUTION COMPLETE")
    print("="*60)
    print(f"📊 Report generated: {report_file}")
    print(f"📸 Screenshots saved in: screenshots/")
    print(f"🕐 End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if exit_code == 0:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  Some tests failed (Exit code: {exit_code})")
        print("   Check the HTML report for details.")
    
    print("\n💡 Quick Commands:")
    print("   • View report: open " + report_file)
    print("   • Re-run failed: pytest --lf -v")
    print("   • Run specific suite: pytest tests/test_suite_1_functional.py -v")
    print("="*60 + "\n")
    
    return exit_code


def run_by_markers():
    """Run tests by markers (functional, performance, etc.)"""
    markers = {
        'functional': 'Functional tests',
        'performance': 'Performance tests',
        'crossbrowser': 'Cross-browser tests',
        'responsive': 'Responsive design tests'
    }
    
    print("\n📑 Available test categories:")
    for i, (marker, desc) in enumerate(markers.items(), 1):
        print(f"   {i}. {desc} (-m {marker})")
    
    print("\n   0. Run ALL tests")
    
    choice = input("\nSelect test category (0-4): ")
    
    if choice == '0':
        return run_all_tests()
    
    marker_list = list(markers.keys())
    if choice.isdigit() and 1 <= int(choice) <= len(marker_list):
        marker = marker_list[int(choice) - 1]
        print(f"\n🎯 Running {markers[marker]}...")
        return pytest.main(["tests/", "-v", "-m", marker])
    else:
        print("❌ Invalid choice")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            exit_code = run_by_markers()
        else:
            exit_code = run_all_tests()
    else:
        exit_code = run_all_tests()
    
    sys.exit(exit_code)


# ============================================
# FILE: generate_test_data.py
# ============================================
"""
Generate test data for data-driven testing
"""
from faker import Faker
import json
import random

fake = Faker()

def generate_user_data(count=10):
    """Generate random user test data"""
    users = []
    for _ in range(count):
        users.append({
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'password': fake.password(length=12),
            'phone': fake.phone_number(),
            'address': fake.address(),
            'city': fake.city(),
            'country': fake.country()
        })
    return users

def generate_product_searches():
    """Generate product search test data"""
    products = [
        "MacBook", "iPhone", "Canon", "Samsung", "Sony",
        "HP", "Palm", "Apple Cinema", "iPod"
    ]
    
    search_data = []
    for product in products:
        search_data.append({
            'search_term': product,
            'expected_results': True,
            'category': 'valid'
        })
    
    # Add invalid searches
    invalid_searches = [
        "XYZ999NonExistent", "!@#$%", "", "a"*200
    ]
    
    for search in invalid_searches:
        search_data.append({
            'search_term': search,
            'expected_results': False,
            'category': 'invalid'
        })
    
    return search_data

def save_test_data():
    """Save test data to JSON file"""
    test_data = {
        'users': generate_user_data(),
        'searches': generate_product_searches(),
        'generated_at': fake.iso8601()
    }
    
    with open('config/test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print("✅ Test data generated: config/test_data.json")

if __name__ == "__main__":
    save_test_data()


print("=" * 60)
print("✅ BONUS UTILITIES CREATED")
print("=" * 60)
print("\n📦 Additional files created:")
print("   • utils/helpers.py - Test helper functions")
print("   • utils/report_generator.py - Custom report generator")
print("   • run_all_tests.py - Enhanced test runner")
print("   • generate_test_data.py - Test data generator")
print("\n🚀 Usage:")
print("   python run_all_tests.py")
print("   python run_all_tests.py --interactive")
print("   python generate_test_data.py")