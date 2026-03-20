# SPECTRA

**SED Parameter Estimation Code for The Rubin Astronomy**

A flexible SED fitting pipeline for stellar populations using multi-wavelength photometry. Designed for Rubin/LSST with native support for PHANGS-HST star clusters and custom catalogs.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- Multi-wavelength SED fitting -- UV to mid-IR photometry (GALEX + HST + JWST + Rubin + WISE)
- Rubin/LSST ready -- Direct TAP queries to Rubin Science Platform
- PHANGS-HST support -- Native FITS loader for PHANGS star cluster catalogs
- Flexible SSP models -- FSPS with Chabrier/Kroupa/Salpeter IMF + Calzetti dust
- Fast ML or full MCMC -- Maximum likelihood (seconds) or Bayesian posteriors (minutes)
- Publication-quality plots -- Customizable SED fits, corner plots, trace diagnostics
- Easy to use -- Simple YAML configs + command-line interface
- Well-tested -- Comprehensive pytest suite + Jupyter tutorial

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/whosneha/SPECTRA.git
cd SPECTRA

# 2. Add to PATH (makes 'spectra' command available)
export PATH="$PWD/bin:$PATH"

# 3. Run example (PHANGS-HST cluster, fast ML fit)
spectra --config example_configs/config_phangs.yaml --max-rows 1 --method ml

# Output: results in outputs/phangs_ic5332_top10_fsps/
```

---

## Project Structure

```
SPECTRA/
├── src/                          # Source code
│   ├── models/
│   │   └── ssp_model.py         # SSP model wrapper (FSPS/mock)
│   ├── mcmc/
│   │   └── mcmc_runner.py       # MCMC via emcee
│   ├── data/
│   │   ├── data_loader.py       # Unified data loader
│   │   ├── phangs_loader.py     # PHANGS-HST FITS loader
│   │   └── rubin_query.py       # Rubin TAP interface
│   ├── utils/
│   │   └── plotting.py          # SED & corner plots
│   ├── cli.py                   # Command-line interface
│   ├── main.py                  # Pipeline orchestration
│   ├── fit.py                   # ML fitter
│   └── likelihood.py            # Likelihood computation
│
├── tests/                        # Unit & integration tests
│   ├── test_ssp_model.py
│   ├── test_likelihood.py
│   ├── test_fitter.py
│   ├── test_mcmc_runner.py
│   ├── test_plotting.py
│   ├── test_data_loaders.py
│   └── test_integration.py
│
├── example_configs/              # Example YAML configuration files
│   ├── config_phangs.yaml       # PHANGS-HST star clusters
│   ├── config_rubin.yaml        # Rubin single object
│   ├── config_rubin_batch.yaml  # Rubin batch processing
│   ├── config_rubin_cone_search.yaml
│   ├── config_rubin_galex.yaml  # Rubin + GALEX multi-wavelength
│   ├── config_rubin_from_csv.yaml
│   ├── config_single_fits.yaml  # Single FITS file
│   ├── config_custom_plotting.yaml
│   ├── config_minimal_plotting.yaml
│   └── config_presentation_plotting.yaml
│
├── docs/                         # Documentation
│   ├── INSTALL.md
│   ├── USAGE.md
│   ├── OUTPUTS_GUIDE.md
│   ├── TESTING.md
│   ├── QUICK_REFERENCE.md
│   └── EXAMPLE_MULTIBAND_CONFIG.md
│
├── notebooks/
│   └── SPECTRA_RSP_Tutorial.ipynb
│
├── bin/
│   └── spectra                  # Command-line wrapper
│
├── setup.py
├── pytest.ini
├── run.py
└── README.md
```

---

## Installation

### Option 1: Simple Wrapper (Recommended)

No pip installation needed -- just add to PATH:

```bash
cd SPECTRA
export PATH="$PWD/bin:$PATH"

# Make permanent:
echo 'export PATH="/path/to/SPECTRA/bin:$PATH"' >> ~/.zshrc  # macOS
source ~/.zshrc
```

### Option 2: Python Module

Run directly without installation:

```bash
cd SPECTRA
python run.py example_configs/config_phangs.yaml
```

### Option 3: Pip Install (Developers)

```bash
cd SPECTRA
pip install -e .
```

### Dependencies

```bash
pip install numpy scipy matplotlib astropy pyyaml pandas emcee corner h5py tqdm
```

### Optional: FSPS (Real SSP Models)

```bash
git clone https://github.com/cconroy20/fsps.git
cd fsps/src && make

export SPS_HOME=/path/to/fsps
echo 'export SPS_HOME=/path/to/fsps' >> ~/.zshrc

pip install fsps
```

**Without FSPS**: Pipeline uses physically-motivated mock SSP models (good for testing/development).

See **[docs/INSTALL.md](docs/INSTALL.md)** for full installation guide.

---

## Supported Input Types

| Input Type | Description | Example Config |
|------------|-------------|----------------|
| **phangs_fits** | PHANGS-HST cluster catalogs | `example_configs/config_phangs.yaml` |
| **rubin_id** | Query by Rubin object ID | `example_configs/config_rubin.yaml` |
| **rubin_tap** | Query by RA/Dec coordinates | `example_configs/config_rubin.yaml` |
| **rubin_batch_ids** | List of Rubin object IDs | `example_configs/config_rubin_batch.yaml` |
| **rubin_cone_search** | Spatial cone search | `example_configs/config_rubin_cone_search.yaml` |
| **rubin_from_csv** | Rubin IDs from CSV file | `example_configs/config_rubin_from_csv.yaml` |
| **fits** | Single FITS binary table | `example_configs/config_single_fits.yaml` |
| **fits_batch** | Directory of FITS files | -- |
| **csv** | Generic CSV photometry | -- |
| **dat** | ASCII whitespace-delimited | -- |
| **file_list** | List of files in config | -- |

**Required columns** (CSV/FITS): `wavelength` (Angstroms), `flux` (Jy), `flux_err` (Jy), `band` (optional)

---

## Usage Examples

### Example 1: PHANGS-HST Star Clusters

```bash
spectra --config example_configs/config_phangs.yaml --method mcmc --max-rows 10
```

**Config**:
```yaml
input:
  type: phangs_fits
  filepath: "path/to/phangs_catalog.fits"
  max_rows: 10
```

---

### Example 2: Rubin/LSST Single Object

```bash
export RSP_TOKEN="your_token_here"
spectra --rubin-id 1234567890 --token $RSP_TOKEN
```

**Config**:
```yaml
input:
  type: rubin_id
  rubin_id: 1234567890

rubin:
  rsp_token: YOUR_RSP_TOKEN_HERE
  flux_type: psfFlux
  bands: [u, g, r, i, z, y]
```

---

### Example 3: Batch Rubin Objects

```bash
spectra --config example_configs/config_rubin_batch.yaml --method ml
```

**Config**:
```yaml
input:
  type: rubin_batch_ids
  rubin_ids:
    - 1234567890
    - 9876543210
    - 5555555555
```

---

### Example 4: Rubin + GALEX Multi-Wavelength

Combine Rubin optical with external UV/IR data:

```bash
spectra --config example_configs/config_rubin_galex.yaml
```

**Config**:
```yaml
input:
  type: rubin_id
  rubin_id: 1234567890

additional_data:
  enabled: true
  files:
    - path: "data/galex_rubin_1234567890.csv"
      format: csv
    - path: "data/wise_rubin_1234567890.csv"
      format: csv
```

**GALEX CSV format** (`galex_rubin_1234567890.csv`):
```csv
wavelength,flux,flux_err,band
1528,1.23e-6,1.45e-7,GALEX_FUV
2271,2.34e-6,2.10e-7,GALEX_NUV
```

**WISE CSV format** (`wise_rubin_1234567890.csv`):
```csv
wavelength,flux,flux_err,band
33526,5.67e-5,3.21e-6,WISE_W1
46028,4.32e-5,2.87e-6,WISE_W2
```

See **[docs/EXAMPLE_MULTIBAND_CONFIG.md](docs/EXAMPLE_MULTIBAND_CONFIG.md)** for full tutorial.

---

### Example 5: Batch Rubin + Matched External Photometry

Process multiple Rubin objects with corresponding external photometry files per object.

**Step 1: Organize your data** with one file per object per survey:
```
data/
├── galex/
│   ├── rubin_1234567890.csv
│   ├── rubin_9876543210.csv
│   └── rubin_5555555555.csv
└── wise/
    ├── rubin_1234567890.csv
    ├── rubin_9876543210.csv
    └── rubin_5555555555.csv
```

**Step 2: Process one object at a time** using a shell loop:
```bash
for id in 1234567890 9876543210 5555555555; do
  cat > /tmp/spectra_temp.yaml << EOF
input:
  type: rubin_id
  rubin_id: $id

rubin:
  flux_type: psfFlux
  bands: [u, g, r, i, z, y]

additional_data:
  enabled: true
  files:
    - path: "data/galex/rubin_${id}.csv"
      format: csv
    - path: "data/wise/rubin_${id}.csv"
      format: csv

ssp_model:
  type: fsps
  imf: chabrier
  dust_type: 2

fitting:
  method: ml
  error_floor: 0.05
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 3.0]

plotting:
  output_dir: "outputs/rubin_multiband_batch"
  save_plots: true

output:
  save_photometry: true
EOF

  spectra --config /tmp/spectra_temp.yaml
done
```

**What this does for each object**:
1. Queries Rubin for 6-band optical photometry
2. Loads the matching GALEX CSV (2 UV bands)
3. Loads the matching WISE CSV (2-4 IR bands)
4. Combines into a single 10-12 band SED
5. Fits and generates plots

**Output structure**:
```
outputs/rubin_multiband_batch/
├── fit_summary.csv
├── rubin_1234567890/
│   ├── sed_fit_rubin_1234567890.png
│   ├── residuals.png
│   └── rubin_1234567890_photometry.csv
├── rubin_9876543210/
│   └── ...
└── rubin_5555555555/
    └── ...
```

---

### Example 6: Cone Search

Find and fit all objects within a region:

```bash
spectra --config example_configs/config_rubin_cone_search.yaml
```

**Config**:
```yaml
input:
  type: rubin_cone_search
  ra: 150.1234
  dec: 2.3456
  radius_arcsec: 60.0
  max_objects: 20
```

---

### Example 7: Rubin Objects from CSV List

```bash
spectra --config example_configs/config_rubin_from_csv.yaml
```

**Config**:
```yaml
input:
  type: rubin_from_csv
  filepath: "data/rubin_object_list.csv"
  id_column: "object_id"
  redshift_column: "redshift"
```

**CSV file** (`data/rubin_object_list.csv`):
```csv
object_id,redshift,comment
1234567890,0.05,Galaxy A
9876543210,0.12,Galaxy B
5555555555,0.08,Galaxy C
```

---

### Example 8: Custom FITS/CSV Catalog

```bash
spectra --config example_configs/config_single_fits.yaml
```

See **[docs/USAGE.md](docs/USAGE.md)** for all examples.

---

## Configuration

SPECTRA uses YAML config files. All examples are in the `example_configs/` directory:

| Config File | Purpose |
|------------|---------|
| `config_phangs.yaml` | PHANGS-HST star clusters |
| `config_rubin.yaml` | Rubin single object |
| `config_rubin_batch.yaml` | Multiple Rubin objects |
| `config_rubin_cone_search.yaml` | Spatial search |
| `config_rubin_galex.yaml` | Rubin + GALEX |
| `config_rubin_from_csv.yaml` | Rubin from CSV list |
| `config_single_fits.yaml` | Single FITS table |
| `config_custom_plotting.yaml` | Plot customization |
| `config_minimal_plotting.yaml` | Minimal plot style |
| `config_presentation_plotting.yaml` | Presentation style |

Copy and customize for your project:
```bash
cp example_configs/config_rubin.yaml my_project.yaml
# Edit my_project.yaml with your settings
spectra --config my_project.yaml
```

### Minimal Config

```yaml
input:
  type: phangs_fits
  filepath: "catalog.fits"
  max_rows: 10

ssp_model:
  type: fsps
  imf: chabrier
  dust_type: 2

fitting:
  method: mcmc
  error_floor: 0.05
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [2.0, 7.0]
    age: [0.001, 1.0]
    metallicity: [-1.5, 0.3]
    dust: [0.0, 1.5]

mcmc:
  n_walkers: 64
  n_steps: 3000
  burn_in: 500

plotting:
  output_dir: "outputs/my_run"
  dpi: 300
```

---

## Fitting Methods

| Method | Speed | Output | Use Case |
|--------|-------|--------|----------|
| **ml** | ~1 sec/object | Best-fit parameters | Quick analysis, large batches |
| **mcmc** | ~2 min/object | Full posteriors + uncertainties | Publication-quality fits |

**ML** uses `scipy.optimize.minimize` (L-BFGS-B).
**MCMC** uses `emcee` affine-invariant ensemble sampler (64 walkers default).

---

## Output Files

| File | Description | When Generated |
|------|-------------|----------------|
| `fit_summary.csv` | Combined results table (all objects) | Always |
| `sed_fit_*.png` | SED plot with model + residuals | Always |
| `residuals.png` | Per-band chi residual bar chart | Always |
| `corner_plot.png` | MCMC posterior distributions | MCMC only |
| `trace_plot.png` | Walker convergence diagnostics | MCMC only |
| `mcmc_samples.h5` | Raw MCMC chain (HDF5) | MCMC only |
| `*_photometry.csv` | Data table (obs + model flux) | If `save_photometry: true` |

**ML runs produce per object**:
```
IC5332_cluster0001_row0000/
├── sed_fit_IC5332_cluster0001_row0000.png
└── residuals.png
```

**MCMC runs produce per object**:
```
IC5332_cluster0001_row0000/
├── sed_fit_IC5332_cluster0001_row0000.png
├── residuals.png
├── corner_plot.png
├── trace_plot.png
└── mcmc_samples.h5
```

**Full output structure**:
```
outputs/phangs_ic5332_top10_fsps/
├── fit_summary.csv
├── IC5332_cluster0001_row0000/
│   ├── sed_fit_IC5332_cluster0001_row0000.png
│   ├── residuals.png
│   ├── corner_plot.png             # MCMC only
│   ├── trace_plot.png              # MCMC only
│   ├── mcmc_samples.h5             # MCMC only
│   └── IC5332_cluster0001_row0000_photometry.csv  # If enabled
└── IC5332_cluster0002_row0001/
    └── ...
```

See **[docs/OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md)** for complete output reference.

---

## Plot Customization

SPECTRA supports full plot customization via config. All options are optional with sensible defaults -- your existing configs work without changes.

```yaml
plotting:
  output_dir: "outputs/my_run"
  formats: [png, pdf]
  dpi: 300
  plot_style: publication
  figure_size: [14, 10]

  show_components: true
  show_error_bars: true
  show_residuals: true
  show_parameter_box: true
  show_grid: true

  color_scheme:
    observed: "#3498DB"
    model: "#E74C3C"
    unattenuated: "#F39C12"

  marker_size_obs: 14
  marker_size_model: 150
  line_width: 2.0
  legend_location: upper right
  legend_fontsize: 11
```

See `example_configs/config_custom_plotting.yaml`, `example_configs/config_minimal_plotting.yaml`, and `example_configs/config_presentation_plotting.yaml` for full examples.

---

## Testing

```bash
pip install -e ".[test]"

# Run all tests
pytest tests/ -v

# Fast tests only
pytest tests/ -m "not slow" -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

Jupyter tutorial for Rubin Science Platform:
```bash
jupyter notebook notebooks/SPECTRA_RSP_Tutorial.ipynb
```

See **[docs/TESTING.md](docs/TESTING.md)** for testing guide.

---

## Documentation

- **[INSTALL.md](docs/INSTALL.md)** -- Installation instructions
- **[USAGE.md](docs/USAGE.md)** -- Detailed usage examples
- **[OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md)** -- Understanding all output files
- **[TESTING.md](docs/TESTING.md)** -- Running tests + Jupyter tutorial
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** -- Command cheat sheet
- **[EXAMPLE_MULTIBAND_CONFIG.md](docs/EXAMPLE_MULTIBAND_CONFIG.md)** -- Multi-wavelength tutorial

---

## Science Use Cases

SPECTRA has been tested on:

- PHANGS-HST star clusters (5-band HST/UVIS photometry)
- Rubin/LSST DP0.2 (ugrizy photometry via TAP)
- Multi-wavelength galaxies (GALEX + HST + Rubin + WISE)

**Typical runtime**:
- ML fitting: ~1 second per object
- MCMC fitting: ~2 minutes per object

**Typical chi-squared/DOF**:
- Star clusters (5 bands): 1.5-3.0
- Galaxies (12 bands): 1.0-2.0

---

## Citation

If you use SPECTRA in your research, please cite:

```bibtex
@software{spectra2024,
  author = {Sneha Nair},
  title = {SPECTRA: SED Parameter Estimation Code for The Rubin Astronomy},
  year = {2024},
  url = {https://github.com/whosneha/SPECTRA},
  note = {Stellar population SED fitting pipeline for Rubin/LSST}
}
```

---

## Contributing

Contributions welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-model`)
3. Add tests for new functionality (`tests/test_*.py`)
4. Run tests (`pytest tests/ -v`)
5. Submit a pull request

---

## License

MIT License -- see [LICENSE](LICENSE)

---

## Contact

**Sneha Nair**
GitHub: [@whosneha](https://github.com/whosneha)
Project: [github.com/whosneha/SPECTRA](https://github.com/whosneha/SPECTRA)

Questions or bug reports? Open an issue: [Issues](https://github.com/whosneha/SPECTRA/issues)

---

## Acknowledgments

- **FSPS**: Charlie Conroy ([github.com/cconroy20/fsps](https://github.com/cconroy20/fsps))
- **emcee**: Dan Foreman-Mackey ([github.com/dfm/emcee](https://github.com/dfm/emcee))
- **PHANGS-HST**: Lee et al. (2022), ApJS, 258, 10
- **Rubin Observatory**: [www.lsst.org](https://www.lsst.org)

Special thanks to the Rubin Science Platform team for DP0.2 data access.

---

**SPECTRA v1.0.0** -- December 2024