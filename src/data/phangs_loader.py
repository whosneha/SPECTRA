"""
Loader for PHANGS-HST cluster catalogs (FITS binary tables).

Photometry bands used (in order of increasing wavelength):
  F275W  ~  2704 Å  (NUV)
  F336W  ~  3355 Å  (U)
  F438W  ~  4325 Å  (B)
  F555W  ~  5308 Å  (V)
  F814W  ~  8024 Å  (I)

Fluxes are already in mJy, MW-foreground-reddening and aperture corrected.
Missing / no-coverage values are set to -9999 in the catalog.
"""

import numpy as np
from astropy.io import fits

# Central wavelengths in Angstroms (vacuum)
BAND_WAVELENGTHS_AA = {
    "F275W": 2704.0,
    "F336W": 3355.0,
    "F438W": 4325.0,
    "F555W": 5308.0,
    "F814W": 8024.0,
}

# Catalog column names for flux [mJy] and error [mJy]
FLUX_COLS = {
    "F275W": ("PHANGS_F275W_mJy",      "PHANGS_F275W_mJy_ERR"),
    "F336W": ("PHANGS_F336W_mJy",      "PHANGS_F336W_mJy_ERR"),
    "F438W": ("PHANGS_F438W_mJy",      "PHANGS_F438W_mJy_ERR"),
    "F555W": ("PHANGS_F555W_mJy",      "PHANGS_F555W_mJy_TOT_ERR"),
    "F814W": ("PHANGS_F814W_mJy",      "PHANGS_F814W_mJy_TOT_ERR"),
}

# mJy → Jy
MJY_TO_JY = 1e-3

# Sentinel value used in catalog for missing data
MISSING_VALUE = -9999.0

# IC 5332 systemic redshift from NED (z = 0.00184, v_sys ~ 552 km/s)
IC5332_REDSHIFT = 0.00184


def load_phangs_fits(filepath, row_indices=None, max_rows=None,
                     min_valid_bands=3, error_floor_frac=0.05):
    """
    Load PHANGS-HST cluster photometry from a FITS binary table.

    Parameters
    ----------
    filepath : str
        Path to the FITS catalog file.
    row_indices : list[int] or None
        Specific row indices to load (0-based).  None = all rows.
    max_rows : int or None
        If row_indices is None, limit to the first max_rows rows.
    min_valid_bands : int
        Minimum number of bands with valid (non-missing, positive) flux.
        Rows with fewer valid bands are skipped.
    error_floor_frac : float
        Fractional error floor added in quadrature to each band error.

    Returns
    -------
    list of (object_id, phot_data) tuples
        phot_data keys: wavelength, obs_flux, obs_err, bands,
                        object_id, redshift, ra, dec, cluster_class
    """
    datasets = []

    with fits.open(filepath) as hdul:
        table = hdul[1].data
        n_total = len(table)

    # Determine rows to process
    if row_indices is not None:
        rows = [r for r in row_indices if r < n_total]
    elif max_rows is not None:
        rows = list(range(min(max_rows, n_total)))
    else:
        rows = list(range(n_total))

    print(f"[PHANGS] {n_total} rows in catalog; processing {len(rows)}")

    with fits.open(filepath) as hdul:
        table = hdul[1].data

        for row_idx in rows:
            row = table[row_idx]

            # --- Cluster metadata ---
            cluster_id    = int(row["ID_PHANGS_CLUSTER"])
            ra            = float(row["PHANGS_RA"])
            dec           = float(row["PHANGS_DEC"])

            # FITS_record has no .get(); check column names on the table instead
            if "PHANGS_CLUSTER_CLASS_HUMAN" in table.names:
                cluster_class = int(row["PHANGS_CLUSTER_CLASS_HUMAN"])
            else:
                cluster_class = 0

            cc_class  = str(row["CC_CLASS"]).strip() if "CC_CLASS" in table.names else "unknown"
            object_id = f"IC5332_cluster{cluster_id:04d}_row{row_idx:04d}"

            # --- Extract photometry ---
            wavelengths, fluxes_jy, errs_jy, band_names = [], [], [], []

            for band in ["F275W", "F336W", "F438W", "F555W", "F814W"]:
                flux_col, err_col = FLUX_COLS[band]

                # Some columns may not exist (e.g. F438W on ACS targets)
                if flux_col not in table.names:
                    continue

                flux_mjy = float(row[flux_col])
                err_mjy  = float(row[err_col]) if err_col in table.names else np.nan

                # Skip missing / negative / non-finite values
                if (flux_mjy <= MISSING_VALUE * 0.5 or
                        flux_mjy <= 0.0 or
                        not np.isfinite(flux_mjy)):
                    continue

                flux_jy = flux_mjy * MJY_TO_JY

                # Error handling
                if not np.isfinite(err_mjy) or err_mjy <= 0.0:
                    err_jy = error_floor_frac * flux_jy
                else:
                    err_jy = err_mjy * MJY_TO_JY
                    # Add error floor in quadrature
                    err_jy = np.sqrt(err_jy**2 + (error_floor_frac * flux_jy)**2)

                wavelengths.append(BAND_WAVELENGTHS_AA[band])
                fluxes_jy.append(flux_jy)
                errs_jy.append(err_jy)
                band_names.append(band)

            n_valid = len(band_names)
            if n_valid < min_valid_bands:
                print(f"  [SKIP] row {row_idx} (cluster {cluster_id}): "
                      f"only {n_valid} valid bands")
                continue

            phot_data = {
                "object_id":     object_id,
                "wavelength":    np.array(wavelengths),   # Angstroms
                "obs_flux":      np.array(fluxes_jy),     # Jy
                "obs_err":       np.array(errs_jy),       # Jy
                "bands":         band_names,
                "redshift":      IC5332_REDSHIFT,         # use known galaxy redshift
                "ra":            ra,
                "dec":           dec,
                "cluster_class": cluster_class,
                "cc_class":      cc_class,
                "row_index":     row_idx,
                "source_file":   filepath,
            }

            datasets.append((object_id, phot_data))
            print(f"  [OK] row {row_idx} | cluster {cluster_id} | "
                  f"{n_valid} bands | cc={cc_class} | "
                  f"F555W={row['PHANGS_F555W_mJy']:.4f} mJy")

    return datasets
