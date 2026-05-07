# Installation

## Requirements

- Python 3.9+
- pip

## Install from repository

```bash
git clone https://github.com/whosneha/SPECTRA.git
cd SPECTRA
pip install -r requirements.txt
```

## Verify installation

After installing, verify that all dependencies and modules are working correctly:

```bash
python tests/run_installation_tests.py
```

This runs a comprehensive smoke test suite that checks:
- All required packages are installed
- Core SPECTRA modules import correctly
- Configuration files are valid
- Data loaders work as expected

All tests should pass (34/34).

## Run without package install

```bash
./bin/spectra --help
```

If needed, use:

```bash
python run.py --help
```

## Optional FSPS setup

SPECTRA can run without FSPS (fallback/mock mode). If you want FSPS-backed models, install FSPS and set SPS_HOME.
