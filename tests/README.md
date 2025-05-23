# ProlabDep Tests

This directory contains tests for the ProlabDep package.

## Test Structure

The tests are organized according to the package structure:

- `test_core/`: Tests for the core module (database, config, models)
- `test_analytics/`: Tests for the analytics module (time series, statistics, mass flow)
- `test_processors/`: Tests for the processors module (CSV, Excel, validation)
- `test_api/`: Tests for the API module (client interface)
- `test_imports.py`: Basic tests to ensure modules can be imported

## Running Tests

### Prerequisites

Install pytest and other test dependencies:

```bash
pip install pytest pytest-cov
```

### Running all tests

From the package root directory, run:

```bash
pytest
```

### Running specific test modules

To run tests for a specific module:

```bash
pytest tests/test_core
pytest tests/test_analytics
pytest tests/test_processors
```

### Running tests with coverage

```bash
pytest --cov=prolabdep
```

### Using the run_tests.py script

Alternatively, you can use the provided `run_tests.py` script:

```bash
python tests/run_tests.py
```

## Test Coverage

The tests cover:

1. Core functionality (database operations, configuration)
2. Data processing (CSV/Excel parsing, validation)
3. Analytics (time series analysis, statistics, mass flow calculations)
4. API functionality (client interface)

## Writing New Tests

When adding new features to the package, please add corresponding tests. 
Follow these guidelines:

1. Create test files in the appropriate test directory
2. Use descriptive test names that clearly indicate what is being tested
3. Use pytest fixtures for reusable test data
4. Test both normal operation and error handling 