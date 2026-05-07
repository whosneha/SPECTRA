# Gallery

This page summarizes common analysis scenarios.

## Scenario 1: Fornax CSV batch

- Input: `fornax_csv`
- Recommended first pass: ML
- Final pass: MCMC on selected targets

## Scenario 2: PHANGS FITS subset

- Input: `phangs_fits`
- Use `max_rows` during iteration
- Expand once priors and plotting look correct

## Scenario 3: Rubin object query

- Input: `rubin_id` or `rubin_tap`
- Requires Rubin token
- Useful for quick single-object checks
