# Configuration Basics

Every run is driven by one YAML file. The sections below are the ones the current pipeline actually expects.

## Minimal Rubin DP0.2 example

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

ssp_model:
  type: fsps
  redshift: 0.0
  imf: chabrier

fitting:
  method: ml
  error_floor: 0.05
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [8.0, 13.0]
    age: [0.1, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 3.0]

plotting:
  output_dir: outputs/dp02_test
  formats: [png]
  dpi: 150

output:
  save_photometry: true
```

## Required sections

- `input`: where the photometry comes from
- `ssp_model`: model family and default redshift settings
- `fitting`: method, parameter list, priors, and error floor
- `plotting`: output directory and plot format settings

## Optional sections

- `rubin`: token, catalog, Rubin flux family, and selected bands
- `external_sources`: coordinate-based GALEX, AllWISE, or VISTA lookups
- `additional_data`: local supplemental CSV or FITS files to merge in
- `mcmc`: walker count, chain length, burn-in, thinning
- `output`: whether to save photometry tables and samples

## Local bundled-data example

```yaml
input:
  type: fornax_csv
  filepath: data/fornax_gc_photometry.csv

ssp_model:
  type: fsps
  redshift: 0.00032
  imf: chabrier

fitting:
  method: ml
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [8.0, 12.0]
    age: [0.1, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 2.0]

plotting:
  output_dir: outputs/fornax_example
  formats: [png]
```

For the full key list, use [Configuration Reference](../configuration.md).
