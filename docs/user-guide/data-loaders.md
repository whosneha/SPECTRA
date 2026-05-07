# Data Loaders

The pipeline uses a unified loader layer under `src/data`.

## Main loaders

- `fornax_loader.py`: Fornax GC long-format CSV
- `phangs_loader.py`: PHANGS catalog FITS handling
- `data_loader.py`: Generic CSV/DAT/FITS and Rubin query interfaces

## Loader output shape

Loaders return a dictionary with at least:

- `wavelength`
- `obs_flux`
- `obs_err`

Optional metadata includes `object_id`, `bands`, and coordinates.
