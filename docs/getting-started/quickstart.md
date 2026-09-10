# Quick Start

## Fast local smoke test

```bash
export PATH="$PWD/bin:$PATH"
spectra --config example_configs/config_phangs.yaml --max-rows 1 --method ml
```

This is the quickest way to confirm the pipeline, plotting, and output writing all work in your environment.

## Rubin DP0.2 test run

```bash
export PATH="$PWD/bin:$PATH"
export RSP_TOKEN="your_rsp_token"

spectra --validate --config example_configs/config_dp02_test.yaml
spectra --config example_configs/config_dp02_test.yaml --method ml
```

That config performs a small cone search in the DP0.2/DC2 field and fits a few bright sources using Rubin `cModelFlux` photometry.

## MCMC follow-up

```bash
spectra --config example_configs/config_dp02_test.yaml --method mcmc
```

Use MCMC once the ML workflow is behaving well. The posterior products are described in [MCMC Guide](../user-guide/mcmc.md).
