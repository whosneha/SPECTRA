# SSP Models

The fitting engine uses SSP-driven model flux predictions.

## Config keys

```yaml
ssp_model:
  type: fsps
  redshift: 0.0
  imf: kroupa
```

## Fitted parameters

Typical fitted parameters are:

- `mass`
- `age`
- `metallicity`
- `dust`

Priors for these are set under `fitting.priors`.
