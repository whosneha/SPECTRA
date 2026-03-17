"""Test script to load and inspect PHANGS FITS catalog."""

from astropy.io import fits
from astropy.table import Table
import numpy as np

# Path to the FITS file
fits_path = "/Users/snehanair/Downloads/catalogs 2/hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits"

# HST filter wavelengths in microns
HST_WAVELENGTHS = {
    'F275W': 0.275,
    'F336W': 0.336,
    'F438W': 0.438,
    'F555W': 0.531,
    'F814W': 0.802
}

def load_phangs_fits(filepath, row_index=0):
    """Load photometry from PHANGS FITS catalog."""
    
    print(f"Loading FITS file: {filepath}")
    
    # Open and read the FITS file
    with fits.open(filepath) as hdul:
        print(f"\nHDU list: {[hdu.name for hdu in hdul]}")
        
        # Data is typically in extension 1 for binary tables
        data = Table.read(hdul[1])
    
    print(f"\nTotal rows: {len(data)}")
    print(f"\nColumn names:")
    for col in data.colnames:
        print(f"  {col}")
    
    # Extract photometry for a specific row
    row = data[row_index]
    
    print(f"\n--- Object at row {row_index} ---")
    print(f"Cluster ID: {row['ID_PHANGS_CLUSTER']}")
    print(f"RA: {row['PHANGS_RA']:.6f} deg")
    print(f"Dec: {row['PHANGS_DEC']:.6f} deg")
    print(f"Human class: {row['PHANGS_CLUSTER_CLASS_HUMAN']}")
    
    # Extract fluxes
    print(f"\nPhotometry (mJy):")
    wavelengths = []
    fluxes = []
    flux_errs = []
    bands = []
    
    flux_cols = {
        'F275W': ('PHANGS_F275W_mJy', 'PHANGS_F275W_mJy_ERR'),
        'F336W': ('PHANGS_F336W_mJy', 'PHANGS_F336W_mJy_ERR'),
        'F438W': ('PHANGS_F438W_mJy', 'PHANGS_F438W_mJy_ERR'),
        'F555W': ('PHANGS_F555W_mJy', 'PHANGS_F555W_mJy_TOT_ERR'),
        'F814W': ('PHANGS_F814W_mJy', 'PHANGS_F814W_mJy_TOT_ERR'),
    }
    
    for band, (flux_col, err_col) in flux_cols.items():
        flux_mjy = row[flux_col]
        err_mjy = row[err_col]
        
        # Skip invalid values (-9999 means no coverage)
        if flux_mjy > 0 and flux_mjy != -9999:
            flux_jy = flux_mjy * 1e-3  # mJy to Jy
            err_jy = err_mjy * 1e-3
            
            wavelengths.append(HST_WAVELENGTHS[band])
            fluxes.append(flux_jy)
            flux_errs.append(err_jy)
            bands.append(band)
            
            print(f"  {band}: {flux_mjy:.4e} mJy ± {err_mjy:.4e} mJy = {flux_jy:.4e} Jy")
        else:
            print(f"  {band}: INVALID ({flux_mjy})")
    
    # Return as dictionary matching SPECTRA format
    phot_data = {
        'wavelength': np.array(wavelengths),
        'obs_flux': np.array(fluxes),
        'obs_err': np.array(flux_errs),
        'mod_flux': np.zeros(len(fluxes)),
        'bands': bands,
        'object_id': row['ID_PHANGS_CLUSTER'],
        'ra': row['PHANGS_RA'],
        'dec': row['PHANGS_DEC']
    }
    
    print(f"\n--- Extracted photometry dictionary ---")
    print(f"Wavelengths (µm): {phot_data['wavelength']}")
    print(f"Fluxes (Jy): {phot_data['obs_flux']}")
    print(f"Errors (Jy): {phot_data['obs_err']}")
    print(f"Bands: {phot_data['bands']}")
    
    return phot_data


if __name__ == "__main__":
    # Test loading
    phot = load_phangs_fits(fits_path, row_index=0)
    
    print("\n" + "="*50)
    print("SUCCESS! FITS file loaded correctly.")
    print(f"Found {len(phot['bands'])} valid bands for SED fitting.")
