# External Photometry Sources

SPECTRA can automatically query and combine photometry from external catalogs to supplement your primary data.

## Supported Sources

| Source | Wavelength Coverage | Bands | Status |
|--------|-------------------|-------|--------|
| **GALEX** | UV (0.15-0.23 μm) | FUV, NUV | Available |
| **AllWISE** | Mid-IR (3.4-22 μm) | W1, W2, W3, W4 | Available |
| **VISTA** | NIR (0.88-2.15 μm) | Z, Y, J, H, Ks | Available |
| **Euclid** | Optical-NIR (0.7-1.65 μm) | VIS, Y, J, H | Coming soon |
| **Roman** | NIR (0.62-2.13 μm) | 8 bands | Future |

## Configuration

### Basic Setup

```yaml
external_sources:
  enabled: true
  sources:
    - 'galex'
    - 'allwise'
    - 'vista'
  radius_arcsec: 10.0
```

### With Rubin Data

```yaml
input:
  type: 'rubin_tap'
  ra: 150.0
  dec: 2.5
  radius_arcsec: 10.0

external_sources:
  enabled: true
  sources:
    - 'galex'      # Add UV coverage
    - 'allwise'    # Add mid-IR coverage
  radius_arcsec: 10.0
  prefer_primary: true  # Keep Rubin data when overlapping
```

### With FITS Catalog

```yaml
input:
  type: 'fits'
  filepath: './catalog.fits'
  row_index: 0

external_sources:
  enabled: true
  sources:
    - 'vista'      # Add NIR coverage
    - 'allwise'    # Add mid-IR coverage
  radius_arcsec: 5.0  # Smaller radius for precise matching
```

## Use Cases

### 1. UV Extension for Star Clusters

Add GALEX UV photometry to constrain young stellar populations:

```yaml
external_sources:
  enabled: true
  sources:
    - 'galex'
  radius_arcsec: 15.0  # Clusters may be extended
```

### 2. Mid-IR Extension

Add AllWISE to constrain dust emission:

```yaml
external_sources:
  enabled: true
  sources:
    - 'allwise'
  radius_arcsec: 10.0
```

### 3. Full Wavelength Coverage

Combine multiple sources for maximum coverage:

```yaml
external_sources:
  enabled: true
  sources:
    - 'galex'      # UV
    - 'vista'      # NIR
    - 'allwise'    # Mid-IR
  radius_arcsec: 10.0
```

## Data Quality Controls

### Overlap Handling

When external bands overlap with primary data:

```yaml
external_sources:
  prefer_primary: true  # Keep Rubin/FITS data
  min_wavelength_separation_um: 0.05  # 500 Angstroms minimum separation
```

### Quality Cuts

Filter out low-quality photometry:

```yaml
external_sources:
  max_magnitude: 25.0  # Reject faint detections
  min_snr: 3.0  # Minimum signal-to-noise
```

## Installation Requirements

Install astroquery for external catalog access:

```bash
pip install astroquery
```

## Examples

### Example 1: GALEX + Rubin + AllWISE

Complete UV to mid-IR SED:

```yaml
input:
  type: 'rubin_tap'
  ra: 53.1589
  dec: -27.7867
  radius_arcsec: 10.0

rubin:
  flux_type: 'psfFlux'
  bands: ['u', 'g', 'r', 'i', 'z', 'y']

external_sources:
  enabled: true
  sources:
    - 'galex'
    - 'allwise'
  radius_arcsec: 10.0
```

Result: ~12-14 photometric bands covering 0.15-22 μm

### Example 2: VISTA for NIR Enhancement

```yaml
input:
  type: 'dat'
  filepath: './optical_photometry.dat'

external_sources:
  enabled: true
  sources:
    - 'vista'
  radius_arcsec: 10.0
```

### Example 3: Batch Processing with External Data

```yaml
input:
  type: 'fits_batch'
  fits_dir: './catalogs'
  file_pattern: '*.fits'
  max_rows_per_file: 100

external_sources:
  enabled: true
  sources:
    - 'galex'
    - 'allwise'
  radius_arcsec: 10.0
```

## Cross-Matching

SPECTRA automatically cross-matches external sources to your targets:

1. **Positional matching**: Within specified radius
2. **Closest match**: Takes nearest source if multiple found
3. **Wavelength checking**: Avoids duplicate wavelength coverage
4. **Quality filtering**: Applies S/N and magnitude cuts

## Output

External photometry is seamlessly integrated:

```python
# In output photometry file
wavelength,flux,flux_err,source
0.152,1.2e-6,2.0e-7,galex    # GALEX FUV
0.227,2.3e-6,3.0e-7,galex    # GALEX NUV
0.464,5.1e-6,4.0e-7,primary  # Rubin g
0.621,7.2e-6,5.0e-7,primary  # Rubin r
...
3.4,1.8e-5,1.5e-6,allwise    # WISE W1
4.6,2.1e-5,1.8e-6,allwise    # WISE W2
```

## Troubleshooting

### No External Data Found

```
[EXTERNAL] No external photometry found
```

**Solutions**:
- Increase search radius
- Check if target is in survey footprint
- Verify RA/Dec are correct

### Query Timeouts

```
[WARNING] Failed to query galex: Timeout
```

**Solutions**:
- Check internet connection
- Try again later
- Reduce number of sources queried simultaneously

### Band Overlap Warnings

```
[COMBINE] Removed 2 external bands due to overlap with primary
```

**This is normal**: `prefer_primary: true` keeps primary data over external

## Best Practices

1. **Start with GALEX + AllWISE**: Most complementary to optical
2. **Adjust radius**: Smaller for point sources, larger for extended objects
3. **Check coverage**: Plot SED to verify external data quality
4. **Quality over quantity**: Filter low S/N detections
5. **Document sources**: Output includes source labels

## API Reference

See [External Sources API](../api/external-sources.md) for programmatic usage.

## Next Steps

- [Input Data Guide](input-data.md)
- [Data Loaders](data-loaders.md)
- [Batch Processing](batch-processing.md)
