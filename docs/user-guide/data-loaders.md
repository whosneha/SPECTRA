# Data Loaders

The loader layer normalizes very different inputs into one internal structure:

- `wavelength`
- `obs_flux`
- `obs_err`
- optional metadata such as `object_id`, `bands`, `ra`, `dec`, and `redshift`

## Main entry points

- `src/data/data_loader.py`: generic CSV, DAT, FITS, and Rubin query integration
- `src/data/phangs_loader.py`: PHANGS-HST catalog handling
- `src/data/fornax_loader.py`: Fornax GC CSV loader
- `src/data/rubin_query.py`: TAP query and Rubin flux extraction logic

## Rubin loader behavior

- `rubin_id` fetches one object by `objectId`
- `rubin_tap` queries a sky position and, by default, keeps the brightest match
- `rubin_cone_search` returns multiple `(object_id, phot_data)` pairs
- fluxes are converted from Rubin `nJy` columns into `Jy`

## Generic CSV behavior

The CSV loader tries several common column names. If `flux_err` is missing, it falls back to a 10% fractional uncertainty. If `mod_flux` is missing, it initializes that array to zero.
