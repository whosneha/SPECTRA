# SPECTRA

**SED Parameter Evaluation Code for The Rubin Alliance**

A flexible SED fitting pipeline for stellar populations using multi-wavelength photometry. Designed for Rubin/LSST with native support for PHANGS-HST star clusters and custom catalogs.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- 🌟 **Multi-wavelength SED fitting** — UV to NIR photometry
--- **Rubin/LSST ready** — Direct TAP queries to Rubin Science Platform
- 📊 **PHANGS-HST support** — Built-in loader for PHANGS star cluster catalogs
## Featuresible models** — FSPS SSP models with Calzetti dust attenuation
-  **Fast ML or full MCMC** — Maximum likelihood for batches, MCMC for uncertainties
- Multi-wavelength SED fitting — UV to mid-IR photometry (GALEX + HST + JWST + Rubin + WISE)
- Rubin/LSST ready — Direct TAP queries to Rubin Science Platform
- PHANGS-HST support — Native FITS loader for PHANGS star cluster catalogs
- Flexible SSP models — FSPS with Chabrier/Kroupa/Salpeter IMF + Calzetti dust
- Fast ML or full MCMC — Maximum likelihood (seconds) or Bayesian posteriors (minutes)
- Publication-quality plots — Customizable SED fits, corner plots, trace diagnostics
- Easy to use — Simple YAML configs + command-line interface
- Well-tested — Comprehensive pytest suite + Jupyter tutorial
cd SPECTRA
---ort PATH="$PWD/bin:$PATH"

## Quick Start(PHANGS-HST star clusters)
spectra --config config_phangs.yaml --max-rows 1 --method ml
```bash
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA

# 2. Add to PATH (makes 'spectra' command available)
export PATH="$PWD/bin:$PATH"
See **[docs/INSTALL.md](docs/INSTALL.md)** for full installation instructions.
# 3. Run example (PHANGS-HST cluster, fast ML fit)
spectra --config config_phangs.yaml --max-rows 1 --method ml
```bash
# Output: results in outputs/phangs_ic5332_top10_fsps/zshrc for permanent
```

---ional FSPS setup:
```bash
## Installation=/path/to/fsps
pip install fsps
### Option 1: Simple Wrapper (Recommended)
No pip installation needed — just add to PATH:
## Usage Examples
```bash
cd SPECTRAe 1: PHANGS Star Clusters
export PATH="$PWD/bin:$PATH"
spectra --config config_phangs.yaml --method mcmc --max-rows 10
# Make permanent by adding to shell config:
echo 'export PATH="/path/to/SPECTRA/bin:$PATH"' >> ~/.zshrc  # macOS
source ~/.zshrcRubin Quick Query
```bash
spectra --rubin-id 1234567890 --token $RSP_TOKEN
### Option 2: Python Module
Run directly without installation:
### Example 3: Custom FITS Catalog
```bash
cd SPECTRAconfig my_catalog.yaml --output results/run01
python run.py config_phangs.yaml
```
See **[docs/USAGE.md](docs/USAGE.md)** for detailed usage guide.
### Option 3: Pip Install (Developers)
Install as a package:

```bash configs provided:
cd SPECTRAg_phangs.yaml`** — PHANGS-HST star cluster catalogs
pip install -e .n.yaml`** — Rubin/LSST TAP queries
# 'spectra' command now available system-widecluster photometry
```
### Basic Config Structure
### Dependencies
```bash
pip install numpy scipy matplotlib astropy pyyaml pandas emcee corner h5py tqdm
```ype: phangs_fits
  filepath: "catalog.fits"
### Optional: FSPS (Real SSP Models)
For production use, install FSPS:
ssp_model:
```bash fsps
# Download and build FSPS
git clone https://github.com/cconroy20/fsps.git
cd fsps/src && make
fitting:
# Set environment variable
export SPS_HOME=/path/to/fspsallicity, dust]
echo 'export SPS_HOME=/path/to/fsps' >> ~/.zshrc
    mass: [3.0, 6.0]
# Install Python wrapper
pip install fsps [-1.5, 0.3]
``` dust: [0.0, 1.5]
```
**Without FSPS**: Pipeline uses physically-motivated mock SSP models (good for testing/development).
## Documentation
See **[docs/INSTALL.md](docs/INSTALL.md)** for full installation guide.
- **[Installation Guide](docs/INSTALL.md)** — Setup and dependencies
---*[Usage Guide](docs/USAGE.md)** — Detailed examples and config reference
- **[API Reference](docs/API.md)** — For developers
## Usage Examples
## Citation
### Example 1: PHANGS-HST Star Clusters (FITS Catalog)
If you use SPECTRA in your research, please cite:

```
Nair et al. (in prep), SPECTRA: Stellar Population Extractor for Clusters
via Template-fitted Resolved Aperture photometry
```