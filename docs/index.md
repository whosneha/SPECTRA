# SPECTRA Documentation

SPECTRA is a Python pipeline for fitting spectral energy distributions (SEDs) from multi-band photometry.

## Main Use Case

**Rubin/LSST multi-wavelength SED fitting** -- Combine Rubin optical photometry with external sources (GALEX UV, AllWise mid-IR, VISTA near-IR, future missions like Euclid and Roman) to fit galaxy and star cluster SEDs across wavelengths from UV to mid-IR, suitable for z < 1 objects.

## What SPECTRA supports

- **Rubin data sources**: Direct TAP queries, single object by ID, cone searches, batch from CSV
- **External catalogs**: GALEX (UV), AllWise (mid-IR), VISTA (near-IR), Euclid, Roman
- **File inputs**: CSV, DAT, FITS (single or batch), with optional local supplemental files
- **Catalog loaders**: PHANGS-HST FITS and Fornax GC CSV
- **Fitting modes**: Maximum-likelihood (fast, seconds) and MCMC (full posteriors, minutes)
- **Batch processing** and per-object output folders

## Start here

1. Installation: [Getting Started / Installation](getting-started/installation.md)
2. First run: [Getting Started / Quick Start](getting-started/quickstart.md)
3. Config basics: [Getting Started / Configuration](getting-started/configuration.md)

## Core references

- Inputs: [Input Formats](inputs.md)
- Config keys: [Configuration Reference](configuration.md)
- Outputs: [Outputs](outputs.md)
