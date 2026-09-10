# Rubin DP0.2 Tutorial

This repository is currently set up most directly for Rubin DP0.2/DC2 testing through `dp02_dc2_catalogs.Object`.

## CLI workflow

```bash
export PATH="$PWD/bin:$PATH"
export RSP_TOKEN="your_rsp_token"

spectra --validate --config example_configs/config_dp02_test.yaml
spectra --config example_configs/config_dp02_test.yaml --method ml
```

## Notebook workflow

For a short smoke test, open `notebooks/SPECTRA_DP02_Smoke_Test.ipynb` and run the cells in order. For the longer Rubin Science Platform workflow, use `notebooks/SPECTRA_RSP_Tutorial.ipynb`.

The smoke-test notebook:

- prompts for `RSP_TOKEN` if it is not already present
- copies the curated DP0.2 cone-search config into a notebook-local run config
- runs `main(config_path)`
- reads back `fit_summary.csv`

## Adapting to another Rubin data release

If you want to try a different Rubin table with the same flux-column naming scheme, override:

```yaml
rubin:
  catalog: your_release_schema.Object
```

If the new release changes column names, `src/data/rubin_query.py` will need a small schema update before the notebook can be reused unchanged.
