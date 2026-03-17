"""
Loader for Fornax Globular Cluster photometry CSV data.
Converts nJy flux values to Jy and packages into pipeline-compatible phot_data dicts.
"""

import os
import numpy as np
import pandas as pd

# LSST/Rubin band central wavelengths in microns
BAND_WAVELENGTH_UM = {
    'u': 0.3671,
    'g': 0.4770,
    'r': 0.6231,
    'i': 0.7625,
    'z': 0.9134,
    'y': 0.9803,
}

NJY_TO_JY = 1e-9


def load_fornax_csv(filepath):
    """
    Load Fornax GC photometry CSV and return list of (object_id, phot_data) tuples.
    
    phot_data keys:
        wavelength  : np.ndarray of central wavelengths in microns
        obs_flux    : np.ndarray of fluxes in Jy
        obs_err     : np.ndarray of flux errors in Jy
        mag_AB      : np.ndarray of AB magnitudes
        mag_err     : np.ndarray of magnitude errors
        bands       : list of band names
        object_id   : str
        ra_deg      : float
        dec_deg     : float
        aperture_arcsec : float
        redshift    : float
    """
    df = pd.read_csv(filepath, comment='#')

    datasets = []

    for obj_id, group in df.groupby('object_id', sort=False):
        group = group.sort_values('wavelength_um')

        phot_data = {
            'object_id':        obj_id,
            'ra_deg':           float(group['ra_deg'].iloc[0]),
            'dec_deg':          float(group['dec_deg'].iloc[0]),
            'aperture_arcsec':  float(group['aperture_arcsec'].iloc[0]),
            'redshift':         float(group['redshift'].iloc[0]),
            'bands':            list(group['band']),
            'wavelength':       group['wavelength_um'].to_numpy(dtype=float),
            'obs_flux':         group['flux_nJy'].to_numpy(dtype=float) * NJY_TO_JY,
            'obs_err':          group['flux_err_nJy'].to_numpy(dtype=float) * NJY_TO_JY,
            'mag_AB':           group['mag_AB'].to_numpy(dtype=float),
            'mag_err':          group['mag_err'].to_numpy(dtype=float),
        }

        datasets.append((obj_id, phot_data))
        print(f"  [FornaxLoader] Loaded {obj_id}: {len(phot_data['bands'])} bands "
              f"({', '.join(phot_data['bands'])})")

    return datasets
