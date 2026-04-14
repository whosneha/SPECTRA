"""
Query DP0.2 for bright test objects and save photometry locally as CSV.

This lets you test SPECTRA without needing an RSP connection every time.

Usage:
    export RSP_TOKEN="your_token"
    python scripts/query_dp02_test_objects.py

Output:
    data/dp02_test_photometry.csv   — photometry for ~10 bright galaxies
    data/dp02_test_stars.csv        — photometry for ~10 bright stars
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TOKEN = os.environ.get("RSP_TOKEN")
if not TOKEN:
    print("ERROR: Set RSP_TOKEN environment variable first")
    print("  export RSP_TOKEN='your_token_here'")
    sys.exit(1)


def query_bright_galaxies(n=10):
    """Query bright extended sources (galaxies) from DP0.2."""
    try:
        import pyvo
        from requests import Session

        session = Session()
        session.headers.update({"Authorization": f"Bearer {TOKEN}"})
        tap = pyvo.dal.TAPService("https://data.lsst.cloud/api/tap", session=session)

        # Query bright galaxies in DC2 field
        # extendedness = 1 means extended source (galaxy)
        # i_cModelFlux > 1000 nJy ≈ i < 22.4 mag
        query = """
        SELECT TOP {n}
            objectId, coord_ra, coord_dec,
            refExtendedness,
            u_cModelFlux, u_cModelFluxErr,
            g_cModelFlux, g_cModelFluxErr,
            r_cModelFlux, r_cModelFluxErr,
            i_cModelFlux, i_cModelFluxErr,
            z_cModelFlux, z_cModelFluxErr,
            y_cModelFlux, y_cModelFluxErr
        FROM dp02_dc2_catalogs.Object
        WHERE coord_ra BETWEEN 55 AND 57
          AND coord_dec BETWEEN -33 AND -31
          AND refExtendedness = 1
          AND i_cModelFlux > 5000
          AND u_cModelFlux > 0
          AND g_cModelFlux > 0
          AND r_cModelFlux > 0
          AND z_cModelFlux > 0
          AND y_cModelFlux > 0
          AND i_cModelFluxErr > 0
        ORDER BY i_cModelFlux DESC
        """.format(n=n)

        print(f"Querying {n} bright galaxies from DP0.2...")
        result = tap.run_sync(query)
        df = result.to_table().to_pandas()
        print(f"Found {len(df)} galaxies")
        return df

    except Exception as e:
        print(f"Query failed: {e}")
        return None


def query_bright_stars(n=10):
    """Query bright point sources (stars) from DP0.2."""
    try:
        import pyvo
        from requests import Session

        session = Session()
        session.headers.update({"Authorization": f"Bearer {TOKEN}"})
        tap = pyvo.dal.TAPService("https://data.lsst.cloud/api/tap", session=session)

        # extendedness = 0 means point source (star)
        query = """
        SELECT TOP {n}
            objectId, coord_ra, coord_dec,
            refExtendedness,
            u_psfFlux, u_psfFluxErr,
            g_psfFlux, g_psfFluxErr,
            r_psfFlux, r_psfFluxErr,
            i_psfFlux, i_psfFluxErr,
            z_psfFlux, z_psfFluxErr,
            y_psfFlux, y_psfFluxErr
        FROM dp02_dc2_catalogs.Object
        WHERE coord_ra BETWEEN 55 AND 57
          AND coord_dec BETWEEN -33 AND -31
          AND refExtendedness = 0
          AND i_psfFlux > 10000
          AND u_psfFlux > 0
          AND g_psfFlux > 0
          AND r_psfFlux > 0
          AND z_psfFlux > 0
          AND y_psfFlux > 0
          AND i_psfFluxErr > 0
        ORDER BY i_psfFlux DESC
        """.format(n=n)

        print(f"Querying {n} bright stars from DP0.2...")
        result = tap.run_sync(query)
        df = result.to_table().to_pandas()
        print(f"Found {len(df)} stars")
        return df

    except Exception as e:
        print(f"Query failed: {e}")
        return None


def convert_to_spectra_csv(df, flux_type="cModelFlux", output_path=None):
    """Convert DP0.2 query results to SPECTRA-compatible CSV format."""
    bands = ['u', 'g', 'r', 'i', 'z', 'y']
    # Rubin effective wavelengths in Angstroms
    wavelengths = {
        'u': 3557, 'g': 4825, 'r': 6223,
        'i': 7546, 'z': 8691, 'y': 9712
    }

    rows = []
    for _, obj in df.iterrows():
        obj_id = int(obj['objectId'])

        for band in bands:
            flux_col = f"{band}_{flux_type}"
            err_col = f"{band}_{flux_type}Err"

            if flux_col not in obj.index:
                continue

            flux_njy = obj[flux_col]
            err_njy = obj[err_col] if err_col in obj.index else 0.05 * flux_njy

            if not np.isfinite(flux_njy) or flux_njy <= 0:
                continue

            rows.append({
                'object_id': obj_id,
                'ra': obj['coord_ra'],
                'dec': obj['coord_dec'],
                'band': band,
                'wavelength': wavelengths[band],
                'flux_jy': flux_njy * 1e-9,      # nJy -> Jy
                'flux_err_jy': err_njy * 1e-9,
                'flux_njy': flux_njy,
                'flux_err_njy': err_njy,
                'snr': flux_njy / err_njy if err_njy > 0 else 0,
            })

    result_df = pd.DataFrame(rows)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        result_df.to_csv(output_path, index=False)
        print(f"Saved {len(result_df)} rows to {output_path}")

        # Print summary
        obj_ids = result_df['object_id'].unique()
        print(f"\n{'='*60}")
        print(f"SUMMARY: {len(obj_ids)} objects, {len(result_df)} measurements")
        print(f"{'='*60}")
        for oid in obj_ids:
            obj_rows = result_df[result_df['object_id'] == oid]
            snr_min = obj_rows['snr'].min()
            snr_max = obj_rows['snr'].max()
            print(f"  objectId {oid}: {len(obj_rows)} bands, "
                  f"SNR {snr_min:.0f}-{snr_max:.0f}")
        print(f"{'='*60}")

    return result_df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    # Query galaxies
    gal_df = query_bright_galaxies(10)
    if gal_df is not None and len(gal_df) > 0:
        convert_to_spectra_csv(gal_df, flux_type="cModelFlux",
                               output_path="data/dp02_test_galaxies.csv")

    # Query stars
    star_df = query_bright_stars(10)
    if star_df is not None and len(star_df) > 0:
        convert_to_spectra_csv(star_df, flux_type="psfFlux",
                               output_path="data/dp02_test_stars.csv")

    # Print usage instructions
    print("\n" + "="*60)
    print("TO USE THE SAVED DATA:")
    print("="*60)
    print("""
# Run SPECTRA on saved galaxy photometry (no RSP needed):
spectra --config example_configs/config_dp02_test.yaml

# Or load in Python:
import pandas as pd
df = pd.read_csv('data/dp02_test_galaxies.csv')
object_ids = df['object_id'].unique()
print(f"Available objects: {object_ids}")
""")
