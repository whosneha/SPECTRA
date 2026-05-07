# External Sources & Multi-Wavelength Workflows

SPECTRA's primary use case is **combining Rubin optical photometry with external multi-wavelength sources** to build complete UV-to-mid-IR SEDs. Three methods are available:

## Typical Workflow: Rubin + External Sources

The most common approach:

1. Query Rubin photometry (optical: u,g,r,i,z,y bands)
2. Supplement with external catalogs (UV, NIR, mid-IR)
3. Combine and fit the full SED

Example configuration:

```yaml
# Start with Rubin query
input:
  type: rubin_tap
  query: "SELECT * FROM dp02.PhotoObj WHERE ra BETWEEN 0 AND 10 AND dec BETWEEN 0 AND 10"
  max_rows: 100

# Supplement with external sources
external_sources:
  enabled: true
  sources: [galex, allwise, vista]  # UV, mid-IR, near-IR
  radius_arcsec: 3.0

# Optional: add local files (e.g., JWST NIRCam, Spitzer)
additional_data:
  enabled: true
  files:
    - path: data/jwst_nircam.csv
      format: csv
```

This produces complete SEDs spanning ~0.15 µm (GALEX FUV) to ~22 µm (AllWise W4).

## Method 1: Local supplemental files

Load extra FITS or CSV files to merge with primary photometry:

```yaml
additional_data:
  enabled: true
  files:
    - path: data/galex_uv.csv         # UV bands
      format: csv
    - path: data/jwst_nircam.fits     # JWST photometry
      format: fits
```

Each file must contain: `wavelength`, `flux`, `flux_err` columns (or with object IDs for batch).

## Method 2: Catalog queries (GALEX, AllWise, VISTA, Euclid, Roman)

Automatically query coordinate-based catalogs:

```yaml
external_sources:
  enabled: true
  sources: [galex, allwise, vista, euclid, roman]  # Query all available
  radius_arcsec: 3.0  # Search radius
```

Supported catalogs:
- **GALEX**: FUV (0.152 µm), NUV (0.227 µm) -- UV
- **AllWise**: W1-W4 (3.4-22 µm) -- Mid-IR
- **VISTA**: Z, Y, J, H, Ks (0.88-2.15 µm) -- Near-IR  
- **Euclid**: VIS, Y, J, H (0.7-1.65 µm) -- Optical/NIR
- **Roman**: F062 to F213 (0.62-2.13 µm) -- Optical/NIR

## Combining All Three Methods

For maximum wavelength coverage on important targets:

```yaml
input:
  type: rubin_tap
  query: "SELECT * FROM dp02.PhotoObj WHERE ..."

external_sources:
  enabled: true
  sources: [galex, allwise, vista]
  radius_arcsec: 3.0

additional_data:
  enabled: true
  files:
    - path: data/jwst_ers_nircam.fits
      format: fits
    - path: data/spitzer_irac.csv
      format: csv
```

Final SED will contain all bands: Rubin (optical) + GALEX (UV) + VISTA (NIR) + AllWise (mid-IR) + JWST (NIR) + Spitzer (mid-IR) = 15+ bands for precise fitting.

## When to Use

- **Always for objects z < 1**: UV, optical, NIR, mid-IR coverage improves stellar mass + age estimates
- **Essential for z > 0.5**: Broader wavelength coverage compensates for age/dust degeneracies
- **Recommended for high-z (z > 2)**: See [Science Use Cases](science-use-cases.md) for limitations

## Data Format Requirements

Local files must include for each object:
- `wavelength`: Angstroms or microns (specified in config)
- `flux`: Jy or erg/s/cm²/Å  
- `flux_err`: Same units as flux
- `object_id` (optional, for batch matching)

See [Input Formats](../inputs.md) for examples.
