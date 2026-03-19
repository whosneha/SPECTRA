# Example: Rubin/LSST + GALEX + WISE Multi-Wavelength SED Fitting

**Combining optical, UV, and infrared photometry for comprehensive stellar population analysis**

---

## Configuration File: `config_rubin_multiband.yaml`

```yaml
input:
  type: rubin_id
  rubin_id: 1234567890

rubin:
  rsp_token: YOUR_RSP_TOKEN_HERE
  flux_type: psfFlux
  bands: [u, g, r, i, z, y]

additional_data:
  enabled: true
  files:
    - path: "data/galex_rubin_1234567890.csv"
      format: csv
    
    - path: "data/wise_rubin_1234567890.csv"
      format: csv

ssp_model:
  type: fsps
  redshift: 0.05
  imf: chabrier
  sfh: 0
  dust_type: 2
  add_neb_emission: true
  distance_mpc: 250.0

fitting:
  method: mcmc
  error_floor: 0.05
  parameters: [mass, age, metallicity, dust]
  priors:
    mass:         [9.0,  12.0]
    age:          [0.1,  13.5]
    metallicity:  [-2.0,  0.5]
    dust:         [0.0,   2.0]

mcmc:
  n_walkers:  64
  n_steps:    3000
  burn_in:    500
  thin:       10

plotting:
  output_dir: "outputs/rubin_multiband"
  save_plots: true
  plot_format: png
  dpi: 300

output:
  save_photometry: true
```

---

## Supplemental Data Files

### GALEX UV Photometry (`galex_rubin_1234567890.csv`)

```csv
wavelength,flux,flux_err,band
1528,1.23e-6,1.45e-7,GALEX_FUV
2271,2.34e-6,2.10e-7,GALEX_NUV
```

### WISE Infrared Photometry (`wise_rubin_1234567890.csv`)

```csv
wavelength,flux,flux_err,band
33526,5.67e-5,3.21e-6,WISE_W1
46028,4.32e-5,2.87e-6,WISE_W2
115608,2.15e-5,1.92e-6,WISE_W3
220883,1.08e-5,1.12e-6,WISE_W4
```

---

## Wavelength Coverage: 0.15–22 μm

| Survey      | Bands | Wavelength Range | Physical Properties          |
|-------------|-------|------------------|------------------------------|
| **GALEX**   | 2     | 1528–2271 Å      | Young stars, UV continuum    |
| **Rubin**   | 6     | 3557–9712 Å      | Optical, Balmer break        |
| **WISE**    | 4     | 3.4–22 μm        | Old stars, dust emission     |
| **Total**   | **12**| **0.15–22 μm**   | Full SED + dust constraints  |

---

## Running the Pipeline

```bash
spectra --config config_rubin_multiband.yaml --validate
spectra --config config_rubin_multiband.yaml
```

**Runtime**: ~2 minutes (MCMC with 64 walkers × 3000 steps)

---

## Expected Output

```
BEST-FIT PARAMETERS
════════════════════════════════════════
  log(M/M☉)  = 10.45 ± 0.08
  Age [Gyr]  = 3.2 ± 0.6
  [Z/H]      = -0.15 ± 0.12
  E(B-V)     = 0.42 ± 0.05
════════════════════════════════════════
χ²/DOF = 1.34  ✓ Good fit
```

**Generated Files**:
- `sed_fit_rubin_1234567890.png` — SED with 12-band coverage
- `corner_plot.png` — MCMC posterior distributions
- `trace_plot.png` — Convergence diagnostics
- `residuals.png` — Per-band χ residuals
- `rubin_1234567890_photometry.csv` — Data table

---

## Key Advantages

| Multi-Wavelength Benefit      | How It Helps                           |
|-------------------------------|----------------------------------------|
| **Break Age-Dust Degeneracy** | UV constrains age, IR constrains dust  |
| **Robust Stellar Mass**       | NIR sensitive to old populations       |
| **Dust Attenuation**          | UV/optical slope vs. IR excess         |
| **Star Formation History**    | UV detects recent star formation       |
| **Model Validation**          | 12 bands > 6 bands for χ² discrimination |

---

**SPECTRA v1.0** — [github.com/yourusername/SPECTRA](https://github.com/yourusername/SPECTRA)
