# Input Formats

## Multi-Wavelength Workflows

**Primary use case**: Combine Rubin optical photometry with external UV/NIR/mid-IR sources.

### Simple approach: Rubin + local files

```yaml
input:
  type: rubin_tap
  query: "SELECT * FROM dp02.PhotoObj ..."

additional_data:
  enabled: true
  files:
    - path: data/galex_fuv_nuv.csv      # UV: 2 bands
      format: csv
    - path: data/allwise_w1_w2.csv      # Mid-IR: 2 bands
      format: csv
```

Result: Rubin 6 optical bands + GALEX 2 UV bands + AllWise 2 mid-IR bands = 10 bands total.

### Advanced: Query external catalogs automatically

```yaml
input:
  type: rubin_cone_search
  ra: 150.5
  dec: 2.3
  radius_arcmin: 0.5

external_sources:
  enabled: true
  sources: [galex, allwise, vista]  # Auto-query
  radius_arcsec: 3.0
```

Result: Rubin (6 bands) + GALEX (2 UV) + AllWise (4 mid-IR) + VISTA (5 NIR) = 17 bands.

---

## fornax_csv

Use long-format Fornax CSV files.

Required columns include:

- `object_id`, `band`, `wavelength_um`
- `flux_nJy`, `flux_err_nJy`
- `mag_AB`, `mag_err`
- `ra_deg`, `dec_deg`, `aperture_arcsec`, `redshift`

```yaml
input:
  type: fornax_csv
  filepath: data/fornax_gc_photometry.csv
```

## phangs_fits

```yaml
input:
  type: phangs_fits
  filepath: /path/to/phangs_catalog.fits
  max_rows: 10
```

## fits_batch

```yaml
input:
  type: fits_batch
  fits_dir: /path/to/catalogs
  file_pattern: "*.fits"
  max_rows_per_file: 20
```

## rubin modes

- `rubin_id`
- `rubin_tap`
- `rubin_batch_ids`
- `rubin_cone_search`
- `rubin_from_csv`

These require a Rubin token in config or environment.

## local single-file modes

```yaml
input:
  type: csv   # or dat or fits
  filepath: /path/to/file.csv
```
