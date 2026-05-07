# Testing Guide

Run tests from the repository root.

## Installation verification

Verify your SPECTRA installation is complete and working:

```bash
python tests/run_installation_tests.py
```

This runs a suite of checks:
- All required Python packages are installed
- SPECTRA core modules can be imported
- Example configs are valid
- Data loaders work
- A minimal ML fit runs successfully

## Run all tests

```bash
pytest tests/ -v
```

## Run specific test categories

Installation and imports only:
```bash
pytest tests/test_installation.py -v
```

Data loader tests:
```bash
pytest tests/test_data_loaders.py -v
```

Likelihood and fitting:
```bash
pytest tests/test_likelihood.py -v
pytest tests/test_fitter.py -v
```

Integration tests:
```bash
pytest tests/test_integration.py -v
```

## Run with coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Run one test module

```bash
pytest tests/test_fornax_loader.py -v
```

## Run by marker

Fast tests only (skip slow/integration tests):
```bash
pytest tests/ -m "not slow and not integration" -v
```

Installation checks only:
```bash
pytest tests/test_installation.py::TestDependencies -v
pytest tests/test_installation.py::TestCoreImports -v
```

