"""
Convert SPECTRA photometry outputs to CIGALE input format.

Usage:
    python scripts/prepare_cigale_input.py --source phangs
    python scripts/prepare_cigale_input.py --source highz
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# CIGALE filter names matching SPECTRA wavelengths
SPECTRA_TO_CIGALE_FILTER = {
    # PHANGS HST bands (Angstroms -> CIGALE filter name)
    2704: 'hst.wfc3.F275W',
    3355: 'hst.wfc3.F336W',
    4325: 'hst.acs.wfc.F438W',
    5308: 'hst.wfc3.F555W',
    8024: 'hst.acs.wfc.F814W',
    # Rubin bands
    3557: 'lsst.u',
    4825: 'lsst.g',
    6223: 'lsst.r',
    7546: 'lsst.i',
    8691: 'lsst.z',
    9712: 'lsst.y',
}


def phangs_to_cigale(phangs_fits_path, output_dir, max_rows=10):
    """Convert PHANGS FITS catalog to CIGALE input table."""
    from src.data.phangs_loader import load_phangs_fits

    print(f"Loading PHANGS data: {phangs_fits_path}")
    datasets = load_phangs_fits(phangs_fits_path, max_rows=max_rows, min_valid_bands=3)

    rows = []
    for obj_id, phot in datasets:
        row = {'id': obj_id, 'redshift': phot.get('redshift', 0.00184)}

        for wav_aa, flux_jy, err_jy in zip(
            phot['wavelength'], phot['obs_flux'], phot['obs_err']
        ):
            # Match wavelength to CIGALE filter
            wav_int = int(round(wav_aa))
            cigale_filter = None
            for ref_wav, filt in SPECTRA_TO_CIGALE_FILTER.items():
                if abs(wav_int - ref_wav) < 200:
                    cigale_filter = filt
                    break

            if cigale_filter:
                # CIGALE expects flux in mJy
                row[cigale_filter] = flux_jy * 1e3
                row[f'{cigale_filter}_err'] = err_jy * 1e3

        rows.append(row)

    df = pd.DataFrame(rows)
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'cigale_input_phangs.txt')
    df.to_csv(out_path, sep='\t', index=False, float_format='%.6e')
    print(f"Saved CIGALE input: {out_path}")
    print(f"  {len(df)} objects, columns: {list(df.columns)}")
    return out_path, df


def dat_to_cigale(dat_path, output_dir, redshift=4.59):
    """Convert .dat spectroscopic file to CIGALE input table."""
    data = np.loadtxt(dat_path, comments='#')
    wavelength = data[:, 0]
    obs_flux = data[:, 1]
    obs_err = data[:, 2]

    # Convert microns to Angstroms if needed
    if wavelength.max() < 100:
        wavelength = wavelength * 1e4

    # Filter SNR > 1
    snr = obs_flux / obs_err
    valid = (obs_flux > 0) & (snr >= 1.0) & np.isfinite(obs_flux) & np.isfinite(obs_err)
    wavelength = wavelength[valid]
    obs_flux = obs_flux[valid]
    obs_err = obs_err[valid]

    # For spectroscopic data, bin into pseudo-bands
    # CIGALE needs broadband-like filters — we create custom ones
    obj_id = Path(dat_path).stem.replace('_ObsSpec_model', '')

    row = {'id': obj_id, 'redshift': redshift}

    # Bin into 3 wavelength groups for CIGALE
    n = len(wavelength)
    thirds = n // 3
    for i, (label, sl) in enumerate([
        ('blue', slice(0, thirds)),
        ('green', slice(thirds, 2*thirds)),
        ('red', slice(2*thirds, None))
    ]):
        flux_mean = np.mean(obs_flux[sl])
        err_mean = np.sqrt(np.sum(obs_err[sl]**2)) / len(obs_err[sl])
        wav_mean = np.mean(wavelength[sl])
        row[f'custom_{label}_{wav_mean:.0f}A'] = flux_mean * 1e3  # Jy -> mJy
        row[f'custom_{label}_{wav_mean:.0f}A_err'] = err_mean * 1e3

    os.makedirs(output_dir, exist_ok=True)
    df = pd.DataFrame([row])
    out_path = os.path.join(output_dir, f'cigale_input_{obj_id}.txt')
    df.to_csv(out_path, sep='\t', index=False, float_format='%.6e')
    print(f"Saved CIGALE input: {out_path}")
    return out_path, df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=['phangs', 'highz'], default='phangs')
    parser.add_argument('--max-rows', type=int, default=5)
    args = parser.parse_args()

    if args.source == 'phangs':
        phangs_fits = ("/Users/snehanair/Downloads/catalogs 2/"
                       "hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits")
        phangs_to_cigale(phangs_fits, 'cigale_runs/phangs', max_rows=args.max_rows)

    elif args.source == 'highz':
        dat_file = "/Users/snehanair/Desktop/out/id_z4p59_ObsSpec_model.dat"
        dat_to_cigale(dat_file, 'cigale_runs/highz', redshift=4.59)
