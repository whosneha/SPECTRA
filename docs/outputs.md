# Outputs

All run products are written under `plotting.output_dir`.

## Typical layout

```text
outputs/fornax_gc/
  fit_summary.csv
  NGC1049/
    sed_fit_NGC1049.png
    residuals.png
    NGC1049_photometry.csv
```

MCMC runs add files such as:

- `corner_plot.png`
- `trace_plot.png`
- `mcmc_samples.h5` (if enabled)

## Summary table

`fit_summary.csv` contains one row per object with fitted parameters and fit diagnostics.
