# Outputs

All run products are written under `plotting.output_dir`.

## Typical layout

```text
outputs/dp02_test/
  fit_summary.csv
  rubin_1651281746966115584/
    sed_fit_rubin_1651281746966115584.png
    residuals.png
    rubin_1651281746966115584_photometry.csv
```

MCMC runs add:

- `corner_plot.<fmt>`
- `trace_plot.<fmt>`
- `mcmc_samples.h5`

## Main files

- `fit_summary.csv`: one row per object with best-fit parameters, log-likelihood, `chi2`, and `chi2_red`
- `sed_fit_<object>.<fmt>`: observed photometry, best-fit model points, and optional smooth SED context
- `residuals.<fmt>`: per-band residuals
- `<object>_photometry.csv`: saved observed and model flux table
- `corner_plot.<fmt>`: posterior covariance view for MCMC runs
- `trace_plot.<fmt>`: walker traces with the burn-in marker
- `mcmc_samples.h5`: raw posterior samples

## What to inspect first

For a Rubin test run, the fastest sanity checks are:

1. `fit_summary.csv` for `chi2_red`
2. the SED plot for obviously bad bands or scaling problems
3. `residuals.png` for systematic offsets

If the run used external catalogs, compare the console readout and residuals panel to see whether the added bands improved or destabilized the fit.
