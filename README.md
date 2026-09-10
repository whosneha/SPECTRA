# SPECTRA

SPECTRA is a photometry-driven SED fitting pipeline for Rubin-style workflows, local catalogs, and nearby-cluster test sets. The current Rubin query layer is wired to the DP0.2/DC2 object catalog by default, but you can point `rubin.catalog` at a different TAP table if the same column names are available.

## What works well

- Rubin object lookups, coordinate queries, cone searches, and CSV-driven batches
- Local CSV, DAT, FITS, PHANGS-HST, and Fornax GC inputs
- Fast maximum-likelihood fits plus optional `emcee` posteriors
- Plot outputs for SEDs, residuals, corner plots, and trace diagnostics
- Optional external catalog augmentation through GALEX, AllWISE, and VISTA

## Quick start

```bash
git clone https://github.com/whosneha/SPECTRA.git
cd SPECTRA

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PATH="$PWD/bin:$PATH"
spectra --config example_configs/config_phangs.yaml --max-rows 1 --method ml
```

## Rubin DP0.2 test run

```bash
export PATH="$PWD/bin:$PATH"
export RSP_TOKEN="your_rsp_token"

spectra --validate --config example_configs/config_dp02_test.yaml
spectra --config example_configs/config_dp02_test.yaml --method ml
```

Outputs are written under `plotting.output_dir`, usually as one folder per object plus a batch `fit_summary.csv`.

## Notebook path

Use [notebooks/SPECTRA_RSP_Tutorial.ipynb](notebooks/SPECTRA_RSP_Tutorial.ipynb) for an end-to-end Rubin Science Platform style workflow. It uses the same config keys as the CLI and is set up for the DP0.2/DC2 catalog out of the box.

## Key config sections

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
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [8.0, 13.0]
    age: [0.1, 13.5]
    metallicity: [-2.5, 0.5]
    dust: [0.0, 3.0]

plotting:
  output_dir: outputs/dp02_test
  formats: [png]
```

## Repo map

- `src/`: pipeline code
- `example_configs/`: runnable YAML examples
- `docs/`: markdown docs for install, config, inputs, outputs, and Rubin workflows
- `notebooks/`: notebook examples
- `tests/`: pytest suite

## Docs

- [docs/index.md](docs/index.md)
- [docs/getting-started/quickstart.md](docs/getting-started/quickstart.md)
- [docs/tutorials/rubin-dp02.md](docs/tutorials/rubin-dp02.md)
- [docs/outputs.md](docs/outputs.md)

## Notes

- `plotting.formats` is the preferred plot-output key. Legacy `plot_format` values are still accepted.
- `mcmc.n_burnin` is the canonical burn-in key. Legacy `burn_in` is also accepted.
- Generated outputs, caches, and notebook scratch files should stay out of version control.
