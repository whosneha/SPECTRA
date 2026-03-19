# SPECTRA

**SED Parameter Estimation Code for The Rubin Astronomy**e Response Analysis**

A flexible SED fitting pipeline for stellar populations using multi-wavelength photometry. Designed for Rubin/LSST with native support for PHANGS-HST star clusters and custom catalogs.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
- 🌟 **Multi-wavelength SED fitting** — UV to NIR photometry
--- **Rubin/LSST ready** — Direct TAP queries to Rubin Science Platform
- 📊 **PHANGS-HST support** — Built-in loader for PHANGS star cluster catalogs
## Featuresible models** — FSPS SSP models with Calzetti dust attenuation
- 🔥 **Fast ML or full MCMC** — Maximum likelihood for batches, MCMC for uncertainties
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
# 1. Clone repositorytly
git clone https://github.com/whosneha/SPECTRA.git
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
```bash
# Fit 10 clusters with MCMC
spectra --config config_phangs.yaml --method mcmc --max-rows 10
  author = {Your Name},
# Output: outputs/phangs_ic5332_top10_fsps/Fitting Pipeline},
#   - fit_summary.csv (all results)
#   - IC5332_cluster0001_row0000/sername/SPECTRA}
#       ├── sed_fit_*.png (SED plot)
#       ├── corner_plot.png (posteriors)
#       ├── trace_plot.png (convergence)
#       └── *_photometry.csv (data table)
```
MIT License — see [LICENSE](LICENSE)
### Example 2: Rubin/LSST Quick Query
## Contact
```bash
# Query single object by ID (requires RSP token)example.com](mailto:your.email@example.com)export RSP_TOKEN="your_token_here"spectra --rubin-id 1234567890 --token $RSP_TOKEN# Or with config filespectra --config config_rubin.yaml```### Example 3: Batch Processing Multiple Galaxies```bash# Process list of Rubin objectsspectra --config config_rubin_batch.yaml --method ml# Or cone search around coordinatesspectra --config config_rubin_cone_search.yaml```### Example 4: Custom FITS/CSV Catalog```bash# Single FITS filespectra --config config_single_fits.yaml# Directory of FITS filesspectra --config config_fits_batch.yaml```See **[docs/USAGE.md](docs/USAGE.md)** for detailed examples and **[docs/OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md)** for understanding results.---## ConfigurationSPECTRA uses YAML config files. Example configs provided:| Config File | Purpose | Input Type ||------------|---------|------------|| **`config_phangs.yaml`** | PHANGS-HST star clusters | FITS catalog || **`config_rubin.yaml`** | Rubin/LSST TAP query | Single object || **`config_rubin_batch.yaml`** | Multiple Rubin objects | List of IDs || **`config_rubin_cone_search.yaml`** | Spatial search | RA/Dec cone || **`config_single_fits.yaml`** | Single FITS table | FITS file || **`config_custom_plotting.yaml`** | Plot customization demo | Any |### Minimal Config Structure```yamlinput:  type: phangs_fits              # or: rubin_id, fits, csv, fits_batch  filepath: "catalog.fits"        # path to data file  max_rows: 10                    # process first 10 objectsssp_model:  type: fsps                      # or: mock (no FSPS needed)  imf: chabrier                   # or: salpeter, kroupa  dust_type: 2                    # 2=Calzetti, 1=Gordon, 3=MWfitting:  method: mcmc                    # or: ml (faster)  error_floor: 0.05               # 5% systematic error  parameters: [mass, age, metallicity, dust]  priors:    mass: [2.0, 7.0]              # log10(M/Msun) for clusters    age: [0.001, 1.0]             # Gyr    metallicity: [-1.5, 0.3]      # log10(Z/Zsun)    dust: [0.0, 1.5]              # E(B-V)mcmc:                             # only if method=mcmc  n_walkers: 64  n_steps: 3000  burn_in: 500plotting:  output_dir: "outputs/my_run"  save_plots: true  dpi: 300                        # high-res for publication```---## Supported Input Formats| Format | Description | Example Use Case ||--------|-------------|------------------|| **PHANGS FITS** | PHANGS-HST cluster catalogs | `type: phangs_fits` || **Fornax CSV** | Globular cluster photometry | `type: fornax_csv` || **Rubin TAP** | Query by object ID or coords | `type: rubin_id` or `rubin_tap` || **Generic FITS** | Single FITS binary table | `type: fits` || **Generic CSV** | Custom photometry tables | `type: csv` || **DAT files** | Legacy ASCII format | `type: dat` || **Batch FITS** | Directory of FITS files | `type: fits_batch` |**Required CSV/FITS columns**: `wavelength` (Å), `flux` (Jy), `flux_err` (Jy), `band` (optional)---## Output FilesSPECTRA generates per-object directories with:| File | Description | When Generated ||------|-------------|----------------|| **`fit_summary.csv`** | Combined results table (all objects) | Always || **`sed_fit_*.png`** | SED plot with model + residuals | Always || **`corner_plot.png`** | MCMC posterior distributions | MCMC only || **`trace_plot.png`** | Walker convergence diagnostics | MCMC only || **`residuals.png`** | Per-band χ residuals | Always || **`*_photometry.csv`** | Data table (obs + model flux) | If enabled || **`mcmc_samples.h5`** | Raw MCMC chain (HDF5) | MCMC only |Example directory structure:```outputs/phangs_ic5332_top10_fsps/├── fit_summary.csv├── IC5332_cluster0001_row0000/│   ├── sed_fit_IC5332_cluster0001_row0000.png│   ├── corner_plot.png│   ├── trace_plot.png│   └── IC5332_cluster0001_row0000_photometry.csv└── IC5332_cluster0002_row0001/    └── ...```See **[docs/OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md)** for complete output reference.---## Testing```bash# Install test dependenciespip install -e ".[test]"# Run all testspytest tests/ -v# Run fast tests onlypytest tests/ -m "not slow" -v# With coverage reportpytest tests/ --cov=src --cov-report=html```Try the **Jupyter tutorial** on Rubin Science Platform:```bashjupyter notebook notebooks/SPECTRA_RSP_Tutorial.ipynb```See **[docs/TESTING.md](docs/TESTING.md)** for testing guide.---## Documentation- **[INSTALL.md](docs/INSTALL.md)** — Installation instructions (simple wrapper, pip, FSPS setup)- **[USAGE.md](docs/USAGE.md)** — Detailed usage examples and config reference- **[OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md)** — Understanding all output files- **[TESTING.md](docs/TESTING.md)** — Running tests and Jupyter tutorial- **[EXAMPLE_MULTIBAND_CONFIG.md](docs/EXAMPLE_MULTIBAND_CONFIG.md)** — Rubin + GALEX + WISE example---## Science Use CasesSPECTRA has been tested on:- ✅ **PHANGS-HST star clusters** (5-band HST/UVIS photometry)- ✅ **Fornax globular clusters** (ugrizY optical photometry)- ✅ **Rubin/LSST DP0.2** (ugrizy photometry via TAP)- ✅ **Multi-wavelength galaxies** (GALEX + HST + Rubin + WISE)**Typical runtime**:- ML fitting: **~1 second per object** (good for 100+ objects)- MCMC fitting: **~2 minutes per object** (full posteriors + uncertainties)**Typical χ²/DOF**:- Star clusters (5 bands): **1.5–3.0** (acceptable)- Galaxies (12 bands): **1.0–2.0** (excellent)See chi-squared guide in **[docs/OUTPUTS_GUIDE.md](docs/OUTPUTS_GUIDE.md#are-my-chi-squared-values-bad)**.---## CitationIf you use SPECTRA in your research, please cite:```bibtex@software{spectra2024,  author = {Sneha Nair},  title = {SPECTRA: SED Parameter Estimation Code for The Rubin Astronomy},  year = {2024},  url = {https://github.com/whosneha/SPECTRA},  note = {Stellar population SED fitting pipeline for Rubin/LSST}}```---## ContributingContributions welcome! Please:1. Fork the repository2. Create a feature branch (`git checkout -b feature/new-model`)3. Add tests for new functionality (`tests/test_*.py`)4. Run tests (`pytest tests/ -v`)5. Submit a pull requestSee **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** for guidelines.---## LicenseMIT License — see [LICENSE](LICENSE)---## Contact**Sneha Nair**  GitHub: [@whosneha](https://github.com/whosneha)  Project: [github.com/whosneha/SPECTRA](https://github.com/whosneha/SPECTRA)Questions or bug reports? Open an issue: [Issues](https://github.com/whosneha/SPECTRA/issues)---## Acknowledgments- **FSPS**: Charlie Conroy ([github.com/cconroy20/fsps](https://github.com/cconroy20/fsps))- **emcee**: Dan Foreman-Mackey ([github.com/dfm/emcee](https://github.com/dfm/emcee))- **PHANGS-HST**: Lee et al. (2022), ApJS, 258, 10- **Rubin Observatory**: [www.lsst.org](https://www.lsst.org)Special thanks to the Rubin Science Platform team for DP0.2 data access.---**SPECTRA v1.0.0** — December 2024