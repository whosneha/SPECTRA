# Outputs

All outputs are written to `plotting.output_dir`:

```text
outputs/fornax_gc/
├── NGC1049/
│   ├── sed_plot.png
│   └── NGC1049_photometry.csv   # if output.save_photometry: true
├── ESO356-SC001/
│   └── ...
└── fit_summary.csv              # best-fit parameters for all objects
```

| File | Description |
|------|-------------|
| `sed_plot.png` | Observed photometry + best-fit model SED |
| `corner_plot.png` | MCMC posterior corner plot (mcmc only) |
| `mcmc_samples.h5` | Raw MCMC chains (if `output.save_samples: true`) |
| `*_photometry.csv` | Per-object flux table with model fluxes |
| `fit_summary.csv` | One row per object with all best-fit parameters |
