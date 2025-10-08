# GD-Downloader Testing Guide

This comprehensive guide covers all aspects of testing the GD-Downloader project, including unit tests, integration tests, end-to-end tests, and the complete testing infrastructure.

## 🧪 Testing Overview

The GD-Downloader project uses a robust testing infrastructure designed to ensure reliability, performance, and maintainability. Our testing approach includes:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component interaction testing  
- **End-to-End Tests**: Full workflow testing
- **Performance Tests**: Load and stress testing
- **Validation Tests**: Configuration and dependency testing

## 📋 Test Structure

```
tests/
├── conftest.py              # Global test configuration and fixtures
├── unit/                    # Unit tests for individual modules
│   ├── test_basic_validation.py
│   ├── test_checkpoint.py
│   ├── test_config.py
│   ├── test_errors.py
│   ├── test_i18n.py
│   ├── test_ui.py
│   └── test_validators.py
├── integration/             # Integration tests for module interactions
├── e2e/                     # End-to-end tests for complete workflows
├── fixtures/                # Test data and mock factories
│   └── mock_data.py
└── utils/                   # Test utilities and helpers
    └── test_helpers.py
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- All project dependencies installed (`pip install -e .[test]`)
- Test configuration files in place

### Running Tests

#### 1. Quick Validation
```bash
# Run quick validation tests
python scripts/quick_test.py

# This script validates:
# - Python version compatibility
# - Required dependencies
# - Configuration files
# - Basic module imports
```

#### 2. Unit Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test file
python -m pytest tests/unit/test_validators.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=. --cov-report=html

# Run critical tests only
python -m pytest tests/unit/ -m "critical" -v
```

#### 3. Full Test Suite
```bash
# Run all tests with detailed output
python run_tests.py --all --verbose --coverage

# Run all tests silently (CI mode)
python run_tests.py --all --quiet

# Run specific test categories
python run_tests.py --unit --integration
python run_tests.py --e2e --performance
```

## 📊 Test Categories

### Unit Tests (tests/unit/)

#### test_validators.py
Tests input validation functions:
- URL validation
- File path validation
- Configuration parameter validation
- Google Drive URL parsing

```bash
# Run validator tests
python -m pytest tests/unit/test_validators.py -v
```

#### test_config.py
Tests configuration management:
- Default values
- Environment variable handling
- Configuration file loading
- Type validation

```bash
# Run config tests
python -m pytest tests/unit/test_config.py -v
```

#### test_checkpoint.py
Tests pause/resume functionality:
- Checkpoint creation
- State restoration
- File integrity validation
- Recovery from interruption

```bash
# Run checkpoint tests
python -m pytest tests/unit/test_checkpoint.py -v
```

#### test_i18n.py
Tests internationalization:
- Language file loading
- Translation functionality
- Fallback mechanisms
- RTL language support

```bash
# Run i18n tests
python -m pytest tests/unit/test_i18n.py -v
```

#### test_ui.py
Tests CLI interface:
- Progress display
- User interaction
- Error message formatting
- Theme handling

```bash
# Run UI tests
python -m pytest tests/unit/test_ui.py -v
```

#### test_errors.py
Tests error handling:
- Custom exception classes
- Error message formatting
- Logging integration
- Recovery mechanisms

```bash
# Run error tests
python -m pytest tests/unit/test_errors.py -v
```

### Integration Tests (tests/integration/)

Tests module interactions:
- Authentication + Downloader integration
- UI + Downloader coordination
- Checkpoint + Downloader integration
- I18n + UI integration

```bash
# Run integration tests
python -m pytest tests/integration/ -v
```

### End-to-End Tests (tests/e2e/)

Tests complete workflows:
- Full download process
- Pause/resume scenarios
- Error recovery workflows
- Multi-language scenarios

```bash
# Run e2e tests
python -m pytest tests/e2e/ -v
```

## 🔧 Test Configuration

### pytest.ini
Contains pytest configuration:
- Test discovery patterns
- Markers for test categorization
- Output formatting
- Timeout settings

### conftest.py
Global test fixtures and utilities:
- Mock Google Drive service
- Temporary directory management
- Test data factories
- Common test utilities

## 📈 Test Coverage

### Coverage Goals
- Unit tests: 90%+ line coverage
- Integration tests: 80%+ branch coverage
- E2E tests: Critical path coverage

### Running Coverage Reports
```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=. --cov-report=html

# Generate terminal coverage report
python -m pytest tests/ --cov=. --cov-report=term-missing

# Coverage for specific modules
python -m pytest tests/ --cov=downloader --cov=validators --cov-report=html
```

### Coverage Reports
- HTML report: `htmlcov/index.html`
- Terminal report: Command line output
- XML report: `coverage.xml` (for CI/CD)

## 🏷️ Test Markers

### Available Markers
- `@pytest.mark.critical`: Critical functionality tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.network`: Tests requiring network access

### Using Markers
```bash
# Run only critical tests
python -m pytest tests/ -m "critical" -v

# Run tests excluding slow ones
python -m pytest tests/ -m "not slow" -v

# Run integration and e2e tests
python -m pytest tests/ -m "integration or e2e" -v
```

## 🛠️ Test Utilities

### Test Helpers (tests/utils/test_helpers.py)
Common utilities for tests:
- Mock data generators
- File system utilities
- Test environment setup
- Assertion helpers

### Mock Data (tests/fixtures/mock_data.py)
Test data factories:
- Google Drive file mocks
- Configuration test data
- Error scenario data
- Performance test data

## 📝 Test Scripts

### quick_test.py
Quick validation script for development:
```bash
python scripts/quick_test.py
```

Features:
- Fast validation (< 10 seconds)
- Dependency checking
- Configuration validation
- Basic import testing

### test_functionality.py
Comprehensive functionality testing:
```bash
python scripts/test_functionality.py
```

Features:
- Module functionality validation
- Integration point testing
- Error scenario testing
- Performance benchmarking

### run_tests.py
Main test runner with options:
```bash
# Show help
python run_tests.py --help

# Run all tests with coverage
python run_tests.py --all --coverage

# Run specific categories
python run_tests.py --unit --integration
python run_tests.py --e2e --performance

# CI mode (quiet, exit on failure)
python run_tests.py --all --quiet --ci
```

## 🐛 Debugging Tests

### Running Tests in Debug Mode
```bash
# Run with pdb debugger
python -m pytest tests/unit/test_validators.py --pdb

# Run with verbose output
python -m pytest tests/unit/test_validators.py -v -s

# Stop on first failure
python -m pytest tests/ --maxfail=1

# Run specific test function
python -m pytest tests/unit/test_validators.py::test_validate_url -v
```

### Test Logging
```bash
# Enable test logging
python -m pytest tests/ --log-cli-level=DEBUG

# Capture log output
python -m pytest tests/ --capture=no --log-cli-level=INFO
```

## 🔄 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -e .[test]
      - name: Run tests
        run: |
          python run_tests.py --all --coverage --ci
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python -m pytest tests/unit/
        language: system
        pass_filenames: false
        always_run: true
```

## 📊 Test Reports

### HTML Reports
Generate comprehensive HTML reports:
```bash
# Generate HTML test report
python -m pytest tests/ --html=reports/test_report.html --self-contained-html

# Generate coverage HTML report
python -m pytest tests/ --cov=. --cov-report=html --html=reports/coverage_report.html
```

### JSON Reports
For CI/CD integration:
```bash
# Generate JSON report
python -m pytest tests/ --json-report --json-report-file=test_report.json

# Generate coverage JSON
python -m pytest tests/ --cov=. --cov-report=json
```

## 🎯 Best Practices

### Writing Tests
1. **Descriptive Names**: Use clear, descriptive test names
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Isolation**: Tests should be independent
4. **Mocking**: Use mocks for external dependencies
5. **Fixtures**: Use fixtures for reusable setup

### Test Data
1. **Minimal Data**: Use minimal test data
2. **Edge Cases**: Test edge cases and error conditions
3. **Cleanup**: Clean up temporary files and data
4. **Consistency**: Use consistent data formats

### Performance
1. **Fast Tests**: Keep unit tests fast (< 1 second)
2. **Markers**: Mark slow tests appropriately
3. **Parallel**: Run tests in parallel when possible
4. **Resources**: Monitor resource usage

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
Error: ModuleNotFoundError: No module named 'downloader'
Solution: Ensure you're in the project root and run: pip install -e .
```

#### 2. Permission Errors
```bash
Error: Permission denied when creating temp files
Solution: Check file permissions and disk space
```

#### 3. Network Tests Failing
```bash
Error: Network tests timeout
Solution: Run with --skip-network or check network connection
```

#### 4. Coverage Issues
```bash
Error: Coverage not generated
Solution: Ensure coverage is installed: pip install coverage
```

### Test Environment Issues

#### Virtual Environment
```bash
# Create clean environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate
pip install -e .[test]
python run_tests.py --all
```

#### Dependencies
```bash
# Check all dependencies are installed
pip install -e .[test,dev]
pip list | grep pytest
```

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)

### Tools
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-html**: HTML reports
- **pytest-xdist**: Parallel execution

### Plugins
```bash
# Install useful pytest plugins
pip install pytest-xdist  # Parallel execution
pip install pytest-html   # HTML reports
pip install pytest-mock   # Mocking utilities
pip install pytest-benchmark  # Performance testing
```

## 🚀 Performance Testing

### Benchmark Tests
```bash
# Run performance benchmarks
python -m pytest tests/ --benchmark-only

# Compare performance
python -m pytest tests/ --benchmark-only --benchmark-save=baseline
python -m pytest tests/ --benchmark-only --benchmark-compare=baseline
```

### Load Testing
For download performance testing:
```bash
# Run load tests (requires additional setup)
python -m pytest tests/e2e/test_performance.py -v
```

## 🔒 Security Testing

### Security Tests
```bash
# Run security-focused tests
python -m pytest tests/ -m "security" -v

# Check for common vulnerabilities
python -m pytest tests/ -m "security and critical" -v
```

## 📈 Test Metrics

### Key Metrics to Track
- **Test Execution Time**: How long tests take to run
- **Coverage Percentage**: Code coverage metrics
- **Pass Rate**: Percentage of tests passing
- **Flaky Tests**: Tests with inconsistent results
- **Performance Baselines**: Expected performance metrics

### Monitoring
Set up monitoring for:
- Test execution trends
- Coverage changes
- Performance regressions
- Test stability metrics

---

## 🤝 Contributing to Tests

When contributing new features:
1. Write tests for new functionality
2. Ensure existing tests still pass
3. Maintain or improve coverage
4. Add documentation for test changes
5. Update test fixtures if needed

### Test Review Checklist
- [ ] Tests cover happy path scenarios
- [ ] Tests cover error scenarios
- [ ] Tests are independent and isolated
- [ ] Tests have descriptive names
- [ ] Tests clean up after themselves
- [ ] Coverage metrics are maintained

---

**This testing guide ensures comprehensive test coverage and maintainability of the GD-Downloader project.**