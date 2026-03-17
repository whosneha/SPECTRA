# Configuration Guide

SPECTRA uses a YAML configuration file (`config.yaml`) to control all aspects of the fitting process.

## Configuration Structure

```yaml
input:
  type: "fits_batch"  # Data source type
  # ... input-specific parameters

ssp_model:
  redshift: 0.0
  # ... model parameters

fitting:
  method: "mcmc"
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.0]
    metallicity: [-2.0, 0.5]
    dust: [0.0, 2.0]

plotting:
  output_dir: "./output"
  # ... plotting options
```

## Input Configuration

### FITS Batch Processing

```yaml
input:
  type: 'fits_batch'
  fits_dir: '/path/to/fits/files'
  file_pattern: '*.fits'
  max_rows_per_file: 10  # Optional
  row_indices: [0, 1, 2]  # Optional, specific rows
```

### Single FITS File

```yaml
input:
  type: 'fits'
  filepath: '/path/to/file.fits'
  row_index: 0  # Optional
```

### Rubin Observatory by Object ID

```yaml
input:
  type: 'rubin_id'
  rubin_id: 1234567890

rubin:
  rsp_token: "your-token"  # Or use RSP_TOKEN env var
  flux_type: "psfFlux"
  bands: ["u", "g", "r", "i", "z", "y"]
```

### Rubin Observatory by Coordinates

```yaml
input:
  type: 'rubin_tap'
  ra: 150.0
  dec: 2.5
  radius_arcsec: 10.0

rubin:
  rsp_token: "your-token"
  flux_type: "psfFlux"
```

## SSP Model Configuration

```yaml
ssp_model:
  redshift: 0.0  # Default redshift (can be overridden per object)
  model_type: 'bruzual_charlot'  # Model to use
  imf: 'chabrier'  # Initial mass function
```

## Fitting Configuration

### Maximum Likelihood

```yaml
fitting:
  method: 'ml'
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.0]
    metallicity: [-2.0, 0.5]
    dust: [0.0, 2.0]
  error_floor: 0.1  # Minimum fractional error
```

### MCMC Sampling

```yaml
fitting:
  method: 'mcmc'
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.0]
    metallicity: [-2.0, 0.5]
    dust: [0.0, 2.0]

mcmc:
  n_walkers: 32
  n_steps: 5000
  n_burn: 1000
  backend: 'samples.h5'  # Save chain to file
```

## Plotting Configuration

```yaml
plotting:
  output_dir: './output'
  save_format: 'png'
  dpi: 300
  show_plots: false
  
  sed_plot:
    figsize: [10, 6]
    show_errors: true
    
  corner_plot:
    figsize: [12, 12]
    show_titles: true
```

## Additional Data Sources

Combine multiple data sources:

```yaml
additional_data:
  enabled: true
  files:
    - path: '/path/to/additional_photometry.csv'
      format: 'csv'
    - path: '/path/to/more_data.dat'
      format: 'dat'
```

## Complete Example

See [Example Configs](../examples/configs.md) for complete working examples.
