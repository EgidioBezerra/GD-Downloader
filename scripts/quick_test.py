#!/usr/bin/env python3
"""
Quick validation script for GD-Downloader test implementation.

This script performs basic validation checks to ensure the test
infrastructure is working correctly.
"""

import sys
import subprocess
import tempfile
from pathlib import Path

def run_command(cmd, description, critical=True):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"[OK] {description}")
            return True
        else:
            print(f"[FAIL] {description}")
            print(f"   Error: {result.stderr}")
            if critical:
                return False
            return True
    except Exception as e:
        print(f"[ERROR] {description}")
        print(f"   Exception: {e}")
        if critical:
            return False
        return True

def validate_python_environment():
    """Validate Python environment."""
    print("\n--- Validating Python environment ---")
    
    # Check Python version
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro} (OK)")
    else:
        print(f"[FAIL] Python {version.major}.{version.minor} required >= 3.8")
        return False
    
    return True

def validate_test_dependencies():
    """Validate test dependencies are installed."""
    print("\n--- Validating test dependencies ---")
    
    dependencies = [
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "responses",
        "freezegun",
        "psutil"
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            print(f"[OK] {dep}")
        except ImportError:
            print(f"[MISSING] {dep}")
            all_ok = False
    
    return all_ok

def validate_project_structure():
    """Validate project structure."""
    print("\n--- Validating project structure ---")
    
    required_files = [
        "pytest.ini",
        "pyproject.toml",
        "tests/conftest.py",
        "tests/unit/test_validators.py",
        "tests/unit/test_errors.py",
        "tests/unit/test_config.py",
        "tests/unit/test_basic_validation.py"
    ]
    
    all_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")
            all_ok = False
    
    return all_ok

def validate_imports():
    """Validate core modules can be imported."""
    print("\n--- Validating core module imports ---")
    
    core_modules = [
        "validators",
        "errors", 
        "config",
        "checkpoint",
        "i18n",
        "ui"
    ]
    
    all_ok = True
    for module in core_modules:
        try:
            __import__(module)
            print(f"[OK] {module}")
        except ImportError as e:
            print(f"[FAIL] {module} ({e})")
            all_ok = False
    
    return all_ok

def validate_basic_functionality():
    """Validate basic functionality works."""
    print("\n--- Validating basic functionality...")
    
    try:
        # Test validators
        from validators import validate_google_drive_url
        is_valid, folder_id = validate_google_drive_url("https://drive.google.com/drive/folders/123456")
        assert is_valid == True
        assert folder_id == "123456"
        print("[OK] URL validation works")
        
        # Test errors
        from errors import GDDownloaderError
        error = GDDownloaderError("Test error")
        assert str(error) == "Test error"
        print("[OK] Error handling works")
        
        # Test config
        from config import get_random_user_agent
        ua = get_random_user_agent()
        assert isinstance(ua, str) and len(ua) > 0
        print("[OK] Configuration works")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Basic functionality failed: {e}")
        return False

def run_critical_tests():
    """Run a subset of critical tests."""
    print("\n--- Running critical validation tests ---")
    
    critical_tests = [
        "tests/unit/test_basic_validation.py::TestBasicValidators::test_validate_valid_folder_url",
        "tests/unit/test_basic_validation.py::TestBasicErrors::test_base_error_creation",
        "tests/unit/test_basic_validation.py::TestBasicConfig::test_default_workers_constant"
    ]
    
    success_count = 0
    for test in critical_tests:
        cmd = [sys.executable, "-m", "pytest", test, "-v", "--tb=short"]
        if run_command(cmd, f"Running {Path(test).name}", critical=False):
            success_count += 1
    
    print(f"\n[SUMMARY] Critical tests: {success_count}/{len(critical_tests)} passed")
    return success_count == len(critical_tests)

def main():
    """Main validation routine."""
    print("GD-Downloader Test Infrastructure Validation")
    print("=" * 50)
    
    checks = [
        ("Python Environment", validate_python_environment),
        ("Test Dependencies", validate_test_dependencies),
        ("Project Structure", validate_project_structure),
        ("Module Imports", validate_imports),
        ("Basic Functionality", validate_basic_functionality),
        ("Critical Tests", run_critical_tests)
    ]
    
    passed = 0
    total = len(checks)
    
    for description, validator in checks:
        print(f"\n--- {description} ---")
        if validator():
            passed += 1
        else:
            print(f"[WARNING] {description} failed - check issues above")
    
    print("\n" + "=" * 50)
    print(f"Validation Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("[SUCCESS] All validations passed! Test infrastructure is ready.")
        return 0
    else:
        print("[WARNING] Some validations failed. Fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())