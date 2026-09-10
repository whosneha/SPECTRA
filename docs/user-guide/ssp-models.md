# SSP Models

The fitting engine uses SSP-driven model flux predictions.

## Supported models

| `type` | Status | Notes |
|--------|--------|-------|
| `fsps` | **Supported** | Requires `SPS_HOME` env var and `pip install fsps` |
| `bc03` | **Supported** | Requires `bc03_data_dir` pointing to `*.ised_ASCII` files |
| `mock` | Internal fallback | Used automatically when FSPS / BC03 files are unavailable |

> **BC03 note**: BC03 reads the six-metallicity `*.ised_ASCII` grid files from a local directory.
> If `bc03_data_dir` is missing or the files are not found, it falls back to mock mode with a
> `UserWarning`.

## Config keys

```yaml
ssp_model:
  type: fsps
  redshift: 0.0
  imf: kroupa
```

### BC03 example

```yaml
ssp_model:
  type: bc03
  redshift: 0.0
  imf: chabrier             # 'chabrier', 'kroupa', or 'salpeter'
  bc03_data_dir: /path/to/bc03_data   # directory with *.ised_ASCII files
  bc03_resolution: lr       # 'lr' (default) or 'hr'
```

The BC03 distribution provides one `*.ised_ASCII` file per metallicity bin
(`m22`–`m72`).  All six files must be present for the chosen IMF.

## Fitted parameters

Typical fitted parameters are:

- `mass`
- `age`
- `metallicity`
- `dust`

Priors for these are set under `fitting.priors`.
