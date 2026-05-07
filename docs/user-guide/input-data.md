# Input Data Guide

SPECTRA expects photometry in wavelength-plus-flux form and supports both file-based and catalog/query workflows.

## Common requirements

- Reliable flux and error values
- Positive fluxes for fitting
- Wavelength coverage across multiple bands

## Recommended first workflow

1. Start with local CSV or DAT input
2. Validate config with `--validate`
3. Run ML first, then MCMC

For exact format definitions, see [Input Formats](../inputs.md).
