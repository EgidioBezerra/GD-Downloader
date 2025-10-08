#!/usr/bin/env python3
"""
Test runner script for GD-Downloader.

This script provides convenient ways to run tests with different configurations
and generates comprehensive reports.
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
    else:
        print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Please ensure pytest is installed: pip install -e .[test]")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-asyncio",
        "responses",
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def install_dependencies():
    """Install test dependencies."""
    print("📦 Installing test dependencies...")
    
    install_cmd = [sys.executable, "-m", "pip", "install", "-e", ".[test]"]
    return run_command(install_cmd, "Installing test dependencies")


def run_unit_tests(coverage=False, verbose=False):
    """Run unit tests only."""
    cmd = [sys.executable, "-m", "pytest", "tests/unit/"]
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-m", "not integration and not e2e"])
    
    return run_command(cmd, "Unit tests")


def run_integration_tests(coverage=False, verbose=False):
    """Run integration tests only."""
    cmd = [sys.executable, "-m", "pytest", "tests/integration/"]
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["-m", "integration"])
    
    return run_command(cmd, "Integration tests")


def run_critical_tests(verbose=False):
    """Run only critical tests."""
    cmd = [sys.executable, "-m", "pytest", "-m", "critical"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Critical tests only")


def run_fast_tests(verbose=False):
    """Run fast tests (exclude slow ones)."""
    cmd = [sys.executable, "-m", "pytest", "-m", "not slow"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Fast tests (exclude slow)")


def run_all_tests(coverage=False, verbose=False, parallel=False):
    """Run all tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if coverage:
        cmd.extend([
            "--cov=.", 
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--cov-fail-under=85"
        ])
    
    if verbose:
        cmd.append("-v")
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    return run_command(cmd, "All tests")


def run_specific_test(test_path, coverage=False, verbose=False):
    """Run specific test file or function."""
    cmd = [sys.executable, "-m", "pytest", test_path]
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Specific test: {test_path}")


def generate_coverage_report():
    """Generate detailed coverage report."""
    print("📊 Generating coverage report...")
    
    # Run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term",
        "tests/"
    ]
    
    success = run_command(cmd, "Coverage analysis")
    
    if success:
        print(f"\n📈 Coverage report generated:")
        print(f"  • HTML: htmlcov/index.html")
        print(f"  • XML: coverage.xml")
        
        if Path("htmlcov/index.html").exists():
            print(f"  • Open in browser: file://{Path.cwd() / 'htmlcov' / 'index.html'}")
    
    return success


def check_code_quality():
    """Run code quality checks."""
    print("🔧 Running code quality checks...")
    
    # Check imports
    imports_ok = run_command([
        sys.executable, "-c", 
        "import ast; ast.parse(open('main.py').read())"
    ], "Syntax check for main.py")
    
    # Check imports in key modules
    key_modules = ["validators", "errors", "config", "checkpoint", "i18n", "ui"]
    
    for module in key_modules:
        if not run_command([
            sys.executable, "-c", 
            f"import {module}"
        ], f"Import check for {module}"):
            imports_ok = False
    
    return imports_ok


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for GD-Downloader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --critical               # Run critical tests only
  python run_tests.py --coverage               # Run tests with coverage
  python run_tests.py --fast                   # Run fast tests (exclude slow)
  python run_tests.py tests/unit/test_validators.py  # Run specific test
        """
    )
    
    # Test selection options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--critical", action="store_true", help="Run critical tests only")
    parser.add_argument("--fast", action="store_true", help="Run fast tests (exclude slow)")
    
    # Test configuration options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    # Utility options
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    
    # Allow specific test path
    parser.add_argument("test_path", nargs="?", help="Specific test file or function to run")
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("GD-Downloader Test Runner")
    print(f"Working directory: {Path.cwd()}")
    
    # Check dependencies first
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        return
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
        return
    
    # Auto-check dependencies if not done
    if not args.check_deps and not args.install_deps:
        if not check_dependencies():
            print("\n❌ Dependencies missing. Run with --install-deps to install them.")
            sys.exit(1)
    
    success_count = 0
    total_runs = 0
    
    # Run code quality checks if requested
    if args.quality:
        total_runs += 1
        if check_code_quality():
            success_count += 1
    
    # Run specific test if provided
    if args.test_path:
        total_runs += 1
        if run_specific_test(args.test_path, args.coverage, args.verbose):
            success_count += 1
    
    # Run based on arguments
    elif args.all:
        total_runs += 1
        if run_all_tests(args.coverage, args.verbose, args.parallel):
            success_count += 1
    
    elif args.unit:
        total_runs += 1
        if run_unit_tests(args.coverage, args.verbose):
            success_count += 1
    
    elif args.integration:
        total_runs += 1
        if run_integration_tests(args.coverage, args.verbose):
            success_count += 1
    
    elif args.critical:
        total_runs += 1
        if run_critical_tests(args.verbose):
            success_count += 1
    
    elif args.fast:
        total_runs += 1
        if run_fast_tests(args.verbose):
            success_count += 1
    
    elif args.coverage:
        total_runs += 1
        if generate_coverage_report():
            success_count += 1
    
    else:
        # Default: run fast tests
        total_runs += 1
        if run_fast_tests(args.verbose):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📋 Test Run Summary")
    print(f"{'='*60}")
    print(f"Successful runs: {success_count}/{total_runs}")
    
    if success_count == total_runs:
        print("🎉 All test runs completed successfully!")
        return_code = 0
    else:
        print("💥 Some test runs failed!")
        return_code = 1
    
    # Show coverage info if generated
    if args.coverage and Path("htmlcov/index.html").exists():
        print(f"\n📊 Coverage report available at:")
        print(f"   file://{Path.cwd() / 'htmlcov' / 'index.html'}")
    
    print(f"\n💡 Tip: Run 'python run_tests.py --help' for more options")
    
    sys.exit(return_code)


if __name__ == "__main__":
    main()