# Input Data

SPECTRA supports multiple input data formats and sources for flexibility in different workflows.

## Supported Input Types

| Type | Description | Use Case |
|------|-------------|----------|
| `dat` | ASCII text file | Simple photometry files |
| `csv` | Comma-separated values | Tabular data from catalogs |
| `fits` | FITS table (single row) | Individual object from catalog |
| `fits_batch` | FITS table (multiple rows) | Batch processing of catalogs |
| `rubin_id` | Query by object ID | Rubin Observatory specific object |
| `rubin_tap` | Query by coordinates | Rubin Observatory cone search |
| `file_list` | Multiple files | Process directory of files |

## Data Format Requirements

All input data must contain:

- **Wavelengths**: Observed wavelengths (micrometers or Angstroms)
- **Fluxes**: Observed flux densities (Jy or other units)
- **Errors**: Flux uncertainties (same units as flux)

### DAT Files

Plain text ASCII format with whitespace-separated columns:

```
# wavelength(microns)  flux(Jy)  flux_err(Jy)
0.445                  1.2e-5    1.5e-6
0.551                  2.3e-5    2.0e-6
0.658                  3.1e-5    2.5e-6
0.806                  3.8e-5    3.0e-6
0.965                  4.2e-5    3.5e-6
1.220                  4.5e-5    4.0e-6
1.630                  4.8e-5    4.5e-6
2.190                  5.0e-5    5.0e-6
```

**Configuration**:
```yaml
input:
  type: 'dat'
  filepath: './data/object.dat'
```

### CSV Files

Comma-separated format with header row:

```csv
wavelength,flux,flux_err
0.445,1.2e-5,1.5e-6
0.551,2.3e-5,2.0e-6
0.658,3.1e-5,2.5e-6
```

**Configuration**:
```yaml
input:
  type: 'csv'
  filepath: './data/object.csv'
```

### FITS Tables

Binary FITS tables with photometry columns:

**Single object**:
```yaml
input:
  type: 'fits'
  filepath: './catalogs/cluster_catalog.fits'
  row_index: 0  # Optional, defaults to 0
```

**Expected FITS structure**:
- HDU 1: Binary table with columns for each band
- Columns: `u_flux`, `g_flux`, `r_flux`, etc.
- Error columns: `u_err`, `g_err`, `r_err`, etc.

### FITS Batch Processing

Process multiple rows from FITS catalogs:

```yaml
input:
  type: 'fits_batch'
  fits_dir: './catalogs'
  file_pattern: '*.fits'
  max_rows_per_file: 100
  # OR
  row_indices: [0, 1, 2, 5, 10]  # Specific rows
```

See [Batch Processing Guide](batch-processing.md) for details.

## Rubin Observatory Data

### Query by Object ID

```yaml
input:
  type: 'rubin_id'
  rubin_id: 1234567890

rubin:
  rsp_token: "your-token"
  flux_type: "psfFlux"  # or "cModelFlux", "apFlux"
  bands: ["u", "g", "r", "i", "z", "y"]
```

### Query by Coordinates

Cone search around RA/Dec:

```yaml
input:
  type: 'rubin_tap'
  ra: 150.0  # degrees
  dec: 2.5   # degrees
  radius_arcsec: 10.0

rubin:
  rsp_token: "your-token"
  flux_type: "psfFlux"
  bands: ["u", "g", "r", "i", "z", "y"]
```

**Flux types**:
- `psfFlux`: PSF photometry
- `cModelFlux`: CModel photometry
- `apFlux`: Aperture photometry

See [Rubin Tutorial](../tutorials/rubin-data.md) for detailed examples.

## File Lists

Process multiple files from a directory:

```yaml
input:
  type: 'file_list'
  format: 'dat'
  photometry_dir: './data'
  file_pattern: '*.dat'
```

Or specify files explicitly:

```yaml
input:
  type: 'file_list'
  format: 'csv'
  photometry_files:
    - './data/object1.csv'
    - './data/object2.csv'
    - './data/object3.csv'
```

## Combining Data Sources

Merge multiple datasets for a single object:

```yaml
input:
  type: 'dat'
  filepath: './primary_photometry.dat'

additional_data:
  enabled: true
  files:
    - path: './infrared_photometry.csv'
      format: 'csv'
    - path: './uv_photometry.dat'
      format: 'dat'
```

This is useful for combining optical, infrared, and UV photometry.

## Data Validation

SPECTRA automatically validates input data:

- Removes invalid flux values (NaN, inf, negative)
- Flags suspicious error values
- Checks wavelength ordering
- Converts units if needed

**Validation warnings**:
```
[WARNING] Removed 2 invalid flux measurements
[WARNING] Error floor applied: minimum 10% uncertainty
```

## Unit Conversions

SPECTRA expects:
- **Wavelengths**: Micrometers (μm)
- **Fluxes**: Janskys (Jy)

If your data uses different units, convert before loading:

```python
# Angstroms to microns
wavelength_um = wavelength_angstrom / 10000.0

# mJy to Jy
flux_jy = flux_mjy / 1000.0

# AB magnitudes to Jy
flux_jy = 10**((8.9 - ab_mag) / 2.5) * 1e-23 * 3e8 / (wavelength_m**2)
```

## Custom Data Loaders

For custom formats, extend the `DataLoader` class:

```python
from src.data.data_loader import DataLoader

class CustomLoader(DataLoader):
    def load_custom_format(self, filepath):
        # Your loading logic
        return {
            'wavelength': wavelengths,
            'obs_flux': fluxes,
            'obs_err': errors
        }
```

See [Custom Models Tutorial](../tutorials/custom-models.md) for details.

## Best Practices

1. **Quality cuts**: Remove unreliable photometry before fitting
2. **Error floors**: Use reasonable minimum uncertainties (10-20%)
3. **Wavelength coverage**: More bands = better constraints
4. **Consistent units**: Verify all data uses the same unit system
5. **Metadata**: Include object IDs and redshifts in filenames

## Example Data

Sample datasets are available in the repository:

```
SPECTRA/
├── examples/
│   ├── sample_photometry.dat
│   ├── cluster_catalog.fits
│   └── multiband_data.csv
```

## Next Steps

- [Data Loaders API](data-loaders.md)
- [Configuration Guide](../getting-started/configuration.md)
- [FITS Batch Tutorial](../tutorials/fits-batch.md)
