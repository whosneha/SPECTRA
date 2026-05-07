# Configuration Basics

Every SPECTRA analysis starts with a single YAML config file.

## Most Common Use Case

**Rubin + external sources** (GALEX, AllWise, VISTA, Euclid, Roman):

```yaml
input:
  type: rubin_tap
  query: "SELECT * FROM dp02.PhotoObj WHERE ..."

external_sources:
  enabled: true
  sources: [galex, allwise, vista]
  radius_arcsec: 3.0

ssp_model:
  type: fsps
  imf: kroupa

fitting:
  method: ml
  parameters: [mass, age, metallicity, dust]
  
plotting:
  output_dir: outputs/rubin_galex
```

See [External Sources Guide](../user-guide/external-sources.md) for more details on combining data sources.

---

## Required Sections

- `input` – Where to load photometry
- `ssp_model` – SSP model configuration
- `fitting` – Fitting parameters and priors
- `plotting` – Output and visualization

## Minimal Example (Local CSV)

```yaml
input:
  type: fornax_csv
  filepath: data/fornax_gc_photometry.csv

ssp_model:
  type: fsps
  redshift: 0.0
  imf: kroupa

fitting:
  method: ml
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [6.0, 12.0]
    age: [0.001, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 2.0]
  error_floor: 0.05

plotting:
  output_dir: outputs/fornax_gc

output:
  save_photometry: true
  save_samples: false
```

For full key-by-key details, see [Configuration Reference](../configuration.md).
