# Configuration Reference

## `input`

- `type`: `fornax_csv`, `phangs_fits`, `fits`, `fits_batch`, `csv`, `dat`, `rubin_id`, `rubin_tap`, `rubin_batch_ids`, `rubin_cone_search`, `rubin_from_csv`, or `file_list`
- `filepath`: used by `csv`, `dat`, `fits`, `fornax_csv`, `phangs_fits`, and `rubin_from_csv`
- `rubin_id`: required for `rubin_id`
- `ra`, `dec`: required for `rubin_tap` and `rubin_cone_search`
- `radius_arcsec`: search radius for Rubin coordinate lookups
- `max_objects`: limit for `rubin_cone_search`
- `rubin_ids`: list of object IDs for `rubin_batch_ids`
- `id_column`: object ID column for `rubin_from_csv`
- `redshift_column`: optional per-object redshift override for `rubin_from_csv`
- `fits_dir`, `file_pattern`, `max_rows_per_file`: batch FITS options
- `max_rows`, `row_indices`: row-selection options for supported table inputs

## `rubin`

- `rsp_token`: Rubin Science Platform token, or leave `null` and export `RSP_TOKEN`
- `tap_url`: optional TAP endpoint override
- `catalog`: default is `dp02_dc2_catalogs.Object`
- `flux_type`: typically `cModelFlux`, `psfFlux`, or another compatible Rubin flux family
- `bands`: any subset of `u`, `g`, `r`, `i`, `z`, `y`

## `external_sources`

- `enabled`: turn coordinate-based catalog augmentation on
- `sources`: any subset of `galex`, `allwise`, `vista`, `euclid`, `roman`
- `radius_arcsec`: cross-match radius
- `prefer_primary`: keep Rubin points when wavelengths overlap closely
- `min_wavelength_separation_um`: overlap tolerance during merge

## `additional_data`

- `enabled`
- `files`: list of `{path, format}` entries for supplemental local photometry

## `ssp_model`

- `type`: `fsps` or `bc03`; unsupported values fall back to mock mode
- `redshift`: default redshift when one is not supplied by the input data
- `imf`: `chabrier`, `kroupa`, or `salpeter`
- `distance_mpc`: optional distance override for some setups
- `dust_model` or `dust_type`: model-specific dust configuration

## `fitting`

- `method`: `ml`, `mcmc`, or `pdf_analysis`
- `parameters`: fitted parameter names
- `priors`: `[min, max]` bounds for every fitted parameter
- `error_floor`: fractional floor added in quadrature to photometric errors
- `pdf_grid`: optional grid settings for `pdf_analysis`

## `mcmc`

- `n_walkers`
- `n_steps`
- `n_burnin`
- `thin`
- `n_threads`
- `random_seed`
- `walker_init`

`burn_in` is still accepted as a legacy alias for `n_burnin`.

## `plotting`

- `output_dir`
- `formats`: list such as `[png]` or `[png, pdf]`
- `dpi`
- `figure_size`
- `plot_style`
- `show_components`
- `show_error_bars`
- `show_residuals`
- `show_parameter_box`
- `wavelength_range`
- `flux_range`
- `color_scheme`

`plot_format` is still accepted as a legacy alias for a single entry in `formats`.

## `output`

- `save_photometry`
- `save_samples`
- `photometry_format`
