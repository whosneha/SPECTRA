# SPECTRA Testing Guide

## Running Tests

### Install with test dependencies:
```bash
cd SPECTRA
pip install -e ".[test]"
```

### Run all tests:
```bash
pytest tests/ -v
```

### Run specific test categories:
```bash
# Fast tests only
pytest tests/ -m "not slow"

# Integration tests
pytest tests/ -m integration

# Skip RSP tests (require authentication)
pytest tests/ -m "not rsp"
```

### Run with coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Categories

### Unit Tests
- `test_ssp_model` — SSP model flux generation
- `test_likelihood` — Chi-squared computation
- `test_fitter` — ML optimization

### Integration Tests
- `test_full_pipeline` — End-to-end on synthetic data
- `test_data_loaders` — PHANGS/Fornax loaders

### RSP Tests (require token)
- `test_rubin_query` — TAP service queries

## Continuous Integration

Tests run automatically on:
- Every push to `main`
- Every pull request
- Nightly builds

## Jupyter Notebook Tutorial

Try the interactive RSP tutorial:
```bash
jupyter notebook notebooks/SPECTRA_RSP_Tutorial.ipynb
```

Requires:
- Jupyter: `pip install jupyter`
- RSP token: Set `RSP_TOKEN` environment variable
