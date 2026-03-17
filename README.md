# SPECTRA: Stellar Population & SED Fitting Tool for Resolved Clusters

**SPECTRA** (Stellar Population Extractor for Clusters via Template-fitted Resolved Aperture photometry) is a Python package for fitting spectral energy distributions (SEDs) of star clusters and galaxies using simple stellar population (SSP) models. It is designed to work out-of-the-box with LSST/Rubin Observatory photometry, PHANGS-HST catalogs, and user-supplied CSV/FITS data.

> For full documentation, tutorials, and API reference, see the [SPECTRA Docs](docs/) (ReadTheDocs link coming soon).

---

## Project Structure

```text
SPECTRA/
├── src/
│   └── spectra/               #  The actual source code
│       ├── __init__.py        #   - Exposes the public API
│       ├── cli.py             #   - Command-line interface entry point
│       ├── main.py            #   - Top-level pipeline orchestration
│       ├── fit.py             #   - SED fitter (maximum likelihood)
│       ├── likelihood.py      #   - Likelihood function
│       ├── io.py              #   - Generic photometry I/O
│       ├── models/
│       │   └── ssp_model.py   #   - SSP model wrapper (python-FSPS)
│       ├── mcmc/
│       │   └── mcmc_runner.py #   - MCMC fitting via emcee
│       ├── data/
│       │   ├── data_loader.py #   - Unified data loader (FITS/CSV/DAT)
│       │   ├── fornax_loader.py #  - Loader for Fornax GC CSV format
│       │   └── rubin_query.py #   - Rubin/LSST TAP query interface
│       └── utils/
│           └── plotting.py    #   - SED & corner plot generation
│
├── data/                      #  Sample & test datasets
│   └── fornax_gc_photometry.csv  # Fornax dSph GC photometry (LSST)
│
├── tests/                     #  Unit tests
│   ├── test_likelihood.py
│   ├── test_ssp_model.py
│   └── test_fornax_loader.py
│
├── docs/                      #  Documentation (Jupyter Book)
│   ├── intro.md
│   ├── installation.md
│   ├── configuration.md
│   ├── inputs.md
│   ├── outputs.md
│   └── tutorials/
│       └── fornax_gc_demo.ipynb
│
├── config.yaml                #  User configuration file
├── pyproject.toml             #  Build configuration & metadata
├── .pre-commit-config.yaml    #  Automated code quality hooks
└── README.md
```

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv spectra_venv
source spectra_venv/bin/activate   # Windows: spectra_venv\Scripts\activate
```

### 3. Install in editable mode

```bash
pip install -e .[dev]
```

### 4. Verify installation

```bash
spectra --help
```

---

## Quick Start

### Run on the included Fornax GC sample data

```bash
spectra run --config config.yaml
```

### Run with a custom config

```bash
spectra run --config path/to/my_config.yaml
```

### Run programmatically

```python
from spectra import run_pipeline
run_pipeline("config.yaml")
```

---

## Input Types

SPECTRA supports multiple input formats, selected via `input.type` in `config.yaml`:

| `type`        | Description                                      |
|---------------|--------------------------------------------------|
| `fornax_csv`  | Multi-band CSV (see `data/fornax_gc_photometry.csv`) |
| `fits_batch`  | Directory of FITS catalogs (e.g. PHANGS-HST)    |
| `fits`        | Single FITS file                                 |
| `csv`         | Generic single CSV file                          |
| `dat`         | Whitespace-delimited `.dat` file                 |
| `file_list`   | List of files in config                          |
| `rubin_id`    | Rubin/LSST TAP query by object ID                |
| `rubin_tap`   | Rubin/LSST TAP query by RA/Dec coordinates       |

See [`docs/inputs.md`](docs/inputs.md) for full details and column specifications.

---

## Fitting Methods

Set `fitting.method` in `config.yaml`:

| Method | Description |
|--------|-------------|
| `ml`   | Maximum likelihood via `scipy.optimize` |
| `mcmc` | MCMC posterior sampling via `emcee` |

---

## Output

All outputs are written to `plotting.output_dir` (default: `outputs/fornax_gc/`):

```text
outputs/fornax_gc/
├── NGC1049/
│   ├── sed_plot.png
│   └── NGC1049_photometry.csv
├── ESO356-SC001/
│   └── ...
└── fit_summary.csv        ← best-fit parameters for all objects
```

---

## Configuration Reference

Key sections in `config.yaml`:

```yaml
input:
  type: "fornax_csv"          # Input format (see table above)
  filepath: data/fornax_gc_photometry.csv

ssp_model:
  type: "fsps"                # SSP library
  imf: "kroupa"               # IMF: kroupa | chabrier | salpeter
  dust_model: "calzetti"      # Dust law
  distance_mpc: 1.48          # Physical distance in Mpc
  redshift: 0.00032           # Redshift

fitting:
  method: "ml"                # ml | mcmc
  parameters: [mass, age, metallicity, dust]
  priors:
    mass:        [8.0, 14.0]  # log(M/Msun)
    age:         [0.01, 13.5] # Gyr
    metallicity: [-2.5, 0.5]  # [Z/H]
    dust:        [0.0, 2.0]   # E(B-V)
  error_floor: 0.05           # Fractional flux error floor

plotting:
  output_dir: outputs/fornax_gc
  formats: [png]
```

See [`docs/configuration.md`](docs/configuration.md) for all options.

---

## Running Tests

```bash
pip install pytest
pytest tests/
```

---

## Development Tools

### Code quality

```bash
ruff check .
ruff format .
mypy src/
```

### Pre-commit hooks (run automatically on every commit)

```bash
pip install pre-commit
pre-commit install
```

### Build documentation locally

```bash
pip install jupyter-book
jupyter-book build docs/
```

---

## Citation

If you use SPECTRA in your research, please cite:

```
Nair et al. (in prep), SPECTRA: Stellar Population Extractor for Clusters
via Template-fitted Resolved Aperture photometry
```