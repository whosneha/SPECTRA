# Batch Processing

## FITS batch mode

```yaml
input:
  type: fits_batch
  fits_dir: /path/to/fits
  file_pattern: "*.fits"
  max_rows_per_file: 10
```

Run:

```bash
./bin/spectra --config path/to/local_fits_batch.yaml
```

## Rubin batch mode

Use `rubin_batch_ids` or `rubin_from_csv` for object-list workflows.

## Best practice

Start with small caps (`max_rows`, `max_rows_per_file`) before full-scale runs.
