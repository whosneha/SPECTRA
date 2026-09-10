# External Sources

SPECTRA can add coordinate-matched photometry on top of a Rubin or FITS-like primary input.

## External catalog query mode

```yaml
external_sources:
  enabled: true
  sources: [galex, allwise, vista]
  radius_arcsec: 3.0
  prefer_primary: true
  min_wavelength_separation_um: 0.05
```

Implemented catalog handlers live in `src/data/external_sources.py`.

## Supported source names

- `galex`
- `allwise`
- `vista`
- `euclid`
- `roman`

`euclid` and `roman` are more placeholder-like than the GALEX, AllWISE, and VISTA paths, so expect the latter three to be the most practical today.

## Local supplemental files

If you already have matched photometry on disk, use:

```yaml
additional_data:
  enabled: true
  files:
    - path: data/jwst_nircam.csv
      format: csv
```

This path avoids live catalog queries and is often easier to reproduce in notebooks.
