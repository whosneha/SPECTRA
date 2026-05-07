# MCMC Guide

MCMC is controlled by the `mcmc` section in your config.

## Key settings

- `n_walkers`
- `n_steps`
- `n_burnin`
- `thin`
- `n_threads`

## Good defaults

```yaml
mcmc:
  n_walkers: 32
  n_steps: 1000
  n_burnin: 300
  thin: 5
  n_threads: 4
```

## Output checks

After a run, inspect:

- `corner_plot.png`
- `trace_plot.png`
- `fit_summary.csv`
