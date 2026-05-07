# Tutorial: FITS Batch Processing

## Goal

Process multiple FITS catalogs and produce one summary table plus per-object plots.

## Example config

```yaml
input:
  type: fits_batch
  fits_dir: /path/to/catalogs
  file_pattern: "*.fits"
  max_rows_per_file: 20

fitting:
  method: ml
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 2.0]

plotting:
  output_dir: outputs/fits_batch
```

## Run

```bash
./bin/spectra --config config.yaml
```

## Validate run products

Check:

- `outputs/fits_batch/fit_summary.csv`
- per-object folders with SED and residual plots
