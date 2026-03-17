# Data Loaders

The `DataLoader` class provides a unified interface for loading photometry from various sources.

## Overview

SPECTRA uses a modular data loading system that:

- Supports multiple file formats (DAT, CSV, FITS)
- Queries remote databases (Rubin Observatory)
- Validates and cleans input data
- Combines multiple data sources
- Handles unit conversions

## DataLoader Class

```python
from src.data.data_loader import DataLoader

loader = DataLoader(config)
phot_data = loader.load('dat', filepath='object.dat')
```

## Loading Methods

### `load(format, **kwargs)`

Universal loading method that dispatches to format-specific loaders.

**Parameters**:
- `format` (str): Data format ('dat', 'csv', 'fits', 'rubin_id', 'rubin_tap')
- `**kwargs`: Format-specific parameters

**Returns**: Dictionary with keys:
- `wavelength`: numpy array of wavelengths (μm)
- `obs_flux`: numpy array of flux densities (Jy)
- `obs_err`: numpy array of flux uncertainties (Jy)

### DAT Files

```python
phot_data = loader.load('dat', filepath='photometry.dat')
```

**Format**: Whitespace-separated ASCII with 3 columns
- Column 1: Wavelength (μm)
- Column 2: Flux (Jy)
- Column 3: Flux error (Jy)

### CSV Files

```python
phot_data = loader.load('csv', filepath='photometry.csv')
```

**Expected columns**:
- `wavelength`: Wavelength in μm
- `flux`: Flux in Jy
- `flux_err` or `error`: Flux uncertainty in Jy

### FITS Tables

```python
# Single row
phot_data = loader.load('fits', filepath='catalog.fits', row_index=0)

# Specific extensions
phot_data = loader.load('fits', filepath='catalog.fits', 
                       row_index=5, hdu=1)
```

**Expected structure**:
- Band-specific flux columns: `u_flux`, `g_flux`, `r_flux`, etc.
- Band-specific error columns: `u_err`, `g_err`, `r_err`, etc.
- Central wavelengths automatically assigned from band names

### Rubin Observatory (Object ID)

```python
phot_data = loader.load('rubin_id', 
                       object_id=1234567890,
                       token='your-rsp-token',
                       flux_type='psfFlux',
                       bands=['u', 'g', 'r', 'i', 'z', 'y'])
```

### Rubin Observatory (Coordinates)

```python
phot_data = loader.load('rubin_tap',
                       ra=150.0,
                       dec=2.5,
                       radius_arcsec=10.0,
                       token='your-rsp-token',
                       flux_type='psfFlux',
                       bands=['u', 'g', 'r', 'i', 'z', 'y'])
```

## Data Validation

All loaded data undergoes automatic validation:

### 1. Invalid Value Removal

```python
# Removes NaN, inf, negative values
valid_mask = np.isfinite(flux) & np.isfinite(errors) & (flux > 0)
```

### 2. Error Floor Application

Ensures minimum fractional uncertainty:

```python
error_floor = 0.1  # 10% minimum
errors = np.maximum(errors, error_floor * flux)
```

### 3. Wavelength Sorting

Data is sorted by wavelength:

```python
sort_idx = np.argsort(wavelength)
wavelength = wavelength[sort_idx]
flux = flux[sort_idx]
```

## Combining Datasets

Merge multiple data sources:

```python
datasets = [
    loader.load('dat', filepath='optical.dat'),
    loader.load('csv', filepath='infrared.csv'),
    loader.load('dat', filepath='uv.dat')
]

combined = loader.combine_datasets(datasets)
```

**Behavior**:
- Concatenates all wavelengths and fluxes
- Removes duplicate wavelengths
- Sorts by wavelength
- Re-validates combined data

## Custom Column Mapping

For non-standard CSV column names:

```python
# Create custom loader
class CustomCSVLoader(DataLoader):
    def load_csv(self, filepath):
        df = pd.read_csv(filepath)
        return {
            'wavelength': df['lambda'].values,  # Custom name
            'obs_flux': df['f_nu'].values,      # Custom name
            'obs_err': df['sigma_f'].values     # Custom name
        }
```

## Band-to-Wavelength Mapping

For FITS files, central wavelengths are assigned:

```python
BAND_WAVELENGTHS = {
    'u': 0.365,  # μm
    'g': 0.464,
    'r': 0.621,
    'i': 0.754,
    'z': 0.870,
    'y': 0.971,
    # JWST bands
    'F090W': 0.902,
    'F115W': 1.154,
    'F150W': 1.501,
    'F200W': 1.989,
    # More bands...
}
```

Extend for custom filters:

```python
loader.band_wavelengths.update({
    'custom_band': 1.25,  # μm
})
```

## Error Handling

```python
try:
    phot_data = loader.load('fits', filepath='catalog.fits')
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Invalid data: {e}")
except Exception as e:
    print(f"Loading failed: {e}")
```

## Performance Considerations

### Large FITS Catalogs

Load only needed rows:

```python
# Instead of loading entire catalog
for row_idx in range(100):
    phot_data = loader.load('fits', filepath='big_catalog.fits', 
                           row_index=row_idx)
    # Process immediately
```

### Caching

For repeated access to the same files:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_load(filepath):
    return loader.load('dat', filepath=filepath)
```

## Quality Control

Check loaded data quality:

```python
phot_data = loader.load('dat', filepath='object.dat')

# Check wavelength coverage
print(f"Coverage: {phot_data['wavelength'].min():.3f} - "
      f"{phot_data['wavelength'].max():.3f} μm")

# Check S/N
snr = phot_data['obs_flux'] / phot_data['obs_err']
print(f"Median S/N: {np.median(snr):.1f}")

# Check for gaps
wave_diff = np.diff(phot_data['wavelength'])
print(f"Largest gap: {wave_diff.max():.3f} μm")
```

## Integration with Main Pipeline

The `DataLoader` is automatically used by `get_input_data()`:

```python
from src.main import get_input_data

datasets = get_input_data(config)
for object_id, phot_data in datasets:
    # Data is already loaded and validated
    print(f"{object_id}: {len(phot_data['wavelength'])} bands")
```

## Examples

### Example 1: Simple Loading

```python
from src.data.data_loader import DataLoader

config = {'fitting': {'error_floor': 0.1}}
loader = DataLoader(config)

data = loader.load('dat', filepath='my_object.dat')
print(f"Loaded {len(data['wavelength'])} photometry points")
```

### Example 2: Multi-Source Combination

```python
optical = loader.load('csv', filepath='sdss_photometry.csv')
nir = loader.load('dat', filepath='2mass_photometry.dat')
mir = loader.load('csv', filepath='wise_photometry.csv')

full_sed = loader.combine_datasets([optical, nir, mir])
print(f"Combined SED: {full_sed['wavelength'].min():.2f} - "
      f"{full_sed['wavelength'].max():.2f} μm")
```

### Example 3: FITS Batch Loading

```python
import glob

fits_files = glob.glob('./catalogs/*.fits')
all_data = []

for fits_file in fits_files:
    from astropy.io import fits
    with fits.open(fits_file) as hdul:
        n_rows = len(hdul[1].data)
    
    for row in range(min(10, n_rows)):
        data = loader.load('fits', filepath=fits_file, row_index=row)
        all_data.append((f"{fits_file}_{row}", data))

print(f"Loaded {len(all_data)} objects")
```

## API Reference

See [Data Loading API](../api/data-loading.md) for complete API documentation.

## Next Steps

- [Input Data Guide](input-data.md)
- [Batch Processing](batch-processing.md)
- [Rubin Data Tutorial](../tutorials/rubin-data.md)
