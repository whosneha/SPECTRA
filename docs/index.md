# SPECTRA Documentation

Welcome to the SPECTRA (Spectral Energy Distribution fitting with MCMC) documentation!

## Overview

SPECTRA is a Python package for fitting Spectral Energy Distributions (SEDs) of astronomical objects using Simple Stellar Population (SSP) models. It supports multiple data sources, fitting methods, and provides comprehensive visualization tools.

## Key Features

- **Multiple Data Sources**: Support for FITS files, CSV, DAT, and Rubin Observatory TAP queries
- **Flexible Fitting**: Maximum likelihood and MCMC (Markov Chain Monte Carlo) methods
- **SSP Models**: Integration with stellar population synthesis models
- **Batch Processing**: Process multiple objects efficiently
- **Rich Visualization**: Automatic generation of SED plots, corner plots, and diagnostics
- **Extensible**: Easy to add custom models and data loaders

## Quick Example

```python
import yaml
from src.main import get_input_data, process_single_object

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get data and process
datasets = get_input_data(config)
for object_id, phot_data in datasets:
    results = process_single_object(object_id, phot_data, config, config['ssp_model'])
```

## Installation

```bash
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA
pip install -r requirements.txt
```

## Getting Started

1. [Installation Guide](getting-started/installation.md)
2. [Quick Start Tutorial](getting-started/quickstart.md)
3. [Configuration Guide](getting-started/configuration.md)

## Support

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/yourusername/SPECTRA).
