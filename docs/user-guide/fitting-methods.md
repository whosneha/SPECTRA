# Fitting Methods

## ML mode

`ml` is fast and useful for configuration checks and large batches.

```bash
./bin/spectra --config config.yaml --method ml
```

## MCMC mode

`mcmc` returns posterior-driven uncertainty estimates and diagnostic plots.

```bash
./bin/spectra --config config.yaml --method mcmc
```

## Practical recommendation

- Use ML to confirm data and priors
- Switch to MCMC for final parameter reporting
