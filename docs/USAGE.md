# SPECTRA Usage Guide

## Basic Usage

### 1. Run with Config File
```bash
spectra --config config_phangs.yaml
```

### 2. Quick Rubin Query
```bash
# Query single object by ID
spectra --rubin-id 1234567890 --token YOUR_TOKEN

# Uses default ML fitting, creates output in outputs/rubin_1234567890/
```

### 3. Batch Processing
```bash
# Process first 10 clusters from PHANGS catalog
spectra --config config_phangs.yaml --max-rows 10
```

### 4. Override Settings
```bash
# Use MCMC instead of ML
spectra --config config.yaml --method mcmc

# Custom output directory
spectra --config config.yaml --output results/my_run

# Combine overrides
spectra --config config.yaml --method mcmc --max-rows 5 --output test_run
```

### 5. Alternative Ways to Run

If the `spectra` command doesn't work, use these alternatives:

```bash
# From repo directory
cd /path/to/SPECTRA
python run.py config_phangs.yaml

# As Python module
python -m src.main config_phangs.yaml

# Direct wrapper script
./bin/spectra --config config_phangs.yaml
```

## Input Data Formats

...existing code from USAGE.md...
