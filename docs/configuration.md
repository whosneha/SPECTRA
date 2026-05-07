# Configuration Reference

## input

- `type`: one of `fornax_csv`, `phangs_fits`, `fits`, `fits_batch`, `csv`, `dat`, `rubin_id`, `rubin_tap`, `rubin_batch_ids`, `rubin_cone_search`, `rubin_from_csv`, `file_list`
- `filepath`: required for single-file inputs
- `max_rows`: optional row cap for supported inputs
- `row_indices`: optional explicit rows for FITS-style inputs

## ssp_model

- `type`: usually `fsps`
- `redshift`: default redshift
- `imf`: e.g. `kroupa`, `chabrier`, `salpeter`
- `distance_mpc`: optional, useful for some setups

## fitting

- `method`: `ml` or `mcmc`
- `parameters`: fitted parameters
- `priors`: `[min, max]` bounds per parameter
- `error_floor`: fractional floor on photometric errors

## mcmc

Used only when `fitting.method: mcmc`.

- `n_walkers`
- `n_steps`
- `n_burnin`
- `thin`
- `n_threads`

## plotting

- `output_dir`
- `show_plots`
- `save_plots`
- `plot_format`
- `dpi`

## output

- `save_photometry`
- `save_samples`
- `photometry_format`
