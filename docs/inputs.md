# Input Formats

Set `input.type` in `config.yaml` to one of the following:

## `fornax_csv`
A multi-band long-format CSV. Each row is one band measurement for one object.

**Required columns:**
| Column | Description |
|--------|-------------|
| `object_id` | Unique cluster identifier |
| `band` | Filter name (`g`, `r`, `i`, …) |
| `wavelength_um` | Central wavelength in microns |
| `flux_nJy` | Flux density in nanojansky |
| `flux_err_nJy` | 1-sigma flux error in nanojansky |
| `mag_AB` | AB magnitude |
| `mag_err` | Magnitude error |
| `redshift` | Object redshift |
| `ra_deg`, `dec_deg` | Coordinates in decimal degrees |
| `aperture_arcsec` | Photometric aperture radius |

```yaml
input:
  type: fornax_csv
  filepath: data/fornax_gc_photometry.csv
```

---

## `fits_batch`
Process all FITS files in a directory (e.g. PHANGS-HST catalogs).

```yaml
input:
  type: fits_batch
  fits_dir: /path/to/catalogs
  file_pattern: "hlsp_phangs-cat_*.fits"
  max_rows_per_file: 10   # null = all rows
```

---

## `rubin_tap`
Query the Rubin/LSST Science Platform by sky coordinates.

```yaml
input:
  type: rubin_tap
  ra: 39.9507
  dec: -34.2584
  radius_arcsec: 10.0
rubin:
  rsp_token: "YOUR_TOKEN"
  flux_type: cModelFlux
  bands: [g, r, i]
```

---

## `rubin_id`
Query a single Rubin object by its catalog ID.

```yaml
input:
  type: rubin_id
  rubin_id: 1234567890
```

---

## `fits` / `csv` / `dat`
Single-file inputs.

```yaml
input:
  type: csv
  filepath: my_photometry.csv
```
