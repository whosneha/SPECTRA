# Configuration Reference

All pipeline behaviour is controlled by a single `config.yaml` file.

---

## `input`

| Key | Type | Description |
|-----|------|-------------|
| `type` | str | Input format — see [Input Formats](inputs.md) |
| `filepath` | str | Path to file (for `fornax_csv`, `csv`, `fits`, `dat`) |
| `fits_dir` | str | Directory of FITS files (for `fits_batch`) |
| `file_pattern` | str | Glob pattern for FITS files |
| `max_rows_per_file` | int\|null | Max objects per FITS file |

---

## `ssp_model`

| Key | Default | Description |
|-----|---------|-------------|
| `type` | `fsps` | SSP library (only `fsps` currently supported) |
| `imf` | `kroupa` | IMF: `kroupa`, `chabrier`, `salpeter` |
| `dust_model` | `calzetti` | Attenuation law |
| `distance_mpc` | — | Physical distance in Mpc |
| `redshift` | `0.0` | Object redshift |

---

## `fitting`

| Key | Default | Description |
|-----|---------|-------------|
| `method` | `ml` | `ml` (max-likelihood) or `mcmc` |
| `parameters` | — | List of free parameters to fit |
| `priors` | — | `[min, max]` uniform prior for each parameter |
| `error_floor` | `0.05` | Fractional flux error floor added in quadrature |

### Free parameters

| Parameter | Units | Typical range |
|-----------|-------|---------------|
| `mass` | log(M☉) | [8, 14] |
| `age` | Gyr | [0.01, 13.5] |
| `metallicity` | [Z/H] | [-2.5, 0.5] |
| `dust` | E(B-V) | [0, 2] |

---

## `mcmc`

Only used when `fitting.method: mcmc`.

| Key | Default | Description |
|-----|---------|-------------|
| `n_walkers` | `32` | Number of emcee walkers |
| `n_steps` | `500` | Steps per walker |
| `n_burnin` | `200` | Burn-in steps (discarded) |
| `thin` | `3` | Thinning factor |
| `n_threads` | `4` | Parallel threads |

---

## `plotting`

| Key | Default | Description |
|-----|---------|-------------|
| `output_dir` | `outputs/` | Root output directory |
| `formats` | `[png]` | Output formats: `png`, `pdf`, `svg` |

---

## `output`

| Key | Default | Description |
|-----|---------|-------------|
| `save_photometry` | `false` | Save per-object flux table as CSV |
| `save_samples` | `false` | Save MCMC chain as HDF5 |
