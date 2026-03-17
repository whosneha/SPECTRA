# Quick Start Guide

Get up and running with SPECTRA in 5 minutes!

## Installation

```bash
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA
pip install -r requirements.txt
```

## Your First SED Fit

### 1. Prepare Your Data

Create a simple photometry file `test_object.dat`:

```
# wavelength(microns)  flux(Jy)  flux_err(Jy)
0.445                  1.2e-5    1.5e-6
0.551                  2.3e-5    2.0e-6
0.658                  3.1e-5    2.5e-6
0.806                  3.8e-5    3.0e-6
0.965                  4.2e-5    3.5e-6
```

### 2. Create Configuration

Create `config.yaml`:

```yaml
input:
  type: 'dat'
  filepath: './test_object.dat'

ssp_model:
  redshift: 0.5
  model_type: 'bruzual_charlot'
  imf: 'chabrier'

fitting:
  method: 'ml'
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [9.0, 12.0]
    age: [0.01, 10.0]
    metallicity: [-1.5, 0.3]
    dust: [0.0, 1.5]
  error_floor: 0.1

plotting:
  output_dir: './output'
  save_format: 'png'
  dpi: 150
  show_plots: false
```

### 3. Run SPECTRA

```bash
python src/main.py
```

### 4. View Results

Check the output directory:

```
output/
├── test_object/
│   └── test_object_sed.png
└── fit_summary.csv
```

View the SED plot and check the fit parameters in `fit_summary.csv`:

```python
import pandas as pd
results = pd.read_csv('output/fit_summary.csv')
print(results)
```

## Next Steps

### Try MCMC Fitting

Modify `config.yaml`:

```yaml
fitting:
  method: 'mcmc'
  # ...existing parameters...

mcmc:
  n_walkers: 32
  n_steps: 2000
  n_burn: 500
```

This will generate corner plots showing parameter uncertainties.

### Process Multiple Objects

```yaml
input:
  type: 'file_list'
  format: 'dat'
  photometry_dir: './data'
  file_pattern: '*.dat'
```

### Query Rubin Observatory

```yaml
input:
  type: 'rubin_tap'
  ra: 150.0
  dec: 2.5
  radius_arcsec: 10.0

rubin:
  rsp_token: "your-token-here"
  flux_type: "psfFlux"
  bands: ["u", "g", "r", "i", "z", "y"]
```

## Common Use Cases

- **Single object ML fit**: [See above](#your-first-sed-fit)
- **MCMC uncertainty estimation**: [MCMC Tutorial](../tutorials/single-object.md)
- **Batch processing FITS catalogs**: [FITS Batch Tutorial](../tutorials/fits-batch.md)
- **Rubin Observatory queries**: [Rubin Tutorial](../tutorials/rubin-data.md)

## Troubleshooting

### Import Errors

```bash
# Make sure you're in the SPECTRA directory
cd /path/to/SPECTRA
python src/main.py
```

### No Output Generated

Check that your output directory is writable:

```yaml
plotting:
  output_dir: './output'  # Relative path
  # or
  output_dir: '/full/path/to/output'  # Absolute path
```

### Poor Fits

Try adjusting priors or increasing error floor:

```yaml
fitting:
  error_floor: 0.2  # Increase if errors are too small
```

## Learn More

- [Configuration Guide](configuration.md) - Detailed config options
- [User Guide](../user-guide/input-data.md) - In-depth documentation
- [Tutorials](../tutorials/single-object.md) - Step-by-step examples
