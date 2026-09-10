# Input Formats

## Rubin inputs

SPECTRA supports five Rubin entry points:

- `rubin_id`: one object ID
- `rubin_tap`: one coordinate target, choosing the brightest match when several are returned
- `rubin_batch_ids`: explicit list of Rubin object IDs in the YAML
- `rubin_cone_search`: a region query that returns multiple objects
- `rubin_from_csv`: object IDs loaded from a local CSV

Example:

```yaml
input:
  type: rubin_cone_search
  ra: 62.0
  dec: -37.0
  radius_arcsec: 30.0
  max_objects: 5

rubin:
  rsp_token: null
  catalog: dp02_dc2_catalogs.Object
  flux_type: cModelFlux
  bands: [u, g, r, i, z, y]
```

## Local single-file inputs

```yaml
input:
  type: csv
  filepath: /path/to/local_photometry.csv
```

`csv` and `dat` loaders expect wavelength and flux columns. For generic CSVs, the loader looks for common names such as `wavelength`, `flux`, `flux_err`, `obs_flux`, and `obs_err`.

## PHANGS and Fornax loaders

```yaml
input:
  type: phangs_fits
  filepath: /path/to/phangs_catalog.fits
  max_rows: 10
```

```yaml
input:
  type: fornax_csv
  filepath: data/fornax_gc_photometry.csv
```

## FITS batch mode

```yaml
input:
  type: fits_batch
  fits_dir: /path/to/catalogs
  file_pattern: "*.fits"
  max_rows_per_file: 20
```

## Supplemental data

To merge local files with a primary input:

```yaml
additional_data:
  enabled: true
  files:
    - path: data/jwst_nircam.csv
      format: csv
```

To augment coordinate-bearing inputs with external catalogs, use `external_sources`; see [External Sources](user-guide/external-sources.md).
