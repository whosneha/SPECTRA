import os
import numpy as np
import pandas as pd
from typing import List, Union, Optional, Dict
import requests
import time

class RubinDataQuery:
    """Query Rubin/LSST data via TAP service."""
    
    # Rubin/LSST filter effective wavelengths in microns
    FILTER_WAVELENGTHS = {
        'u': 0.368,
        'g': 0.476,
        'r': 0.621,
        'i': 0.754,
        'z': 0.870,
        'y': 0.971
    }
    
    # Zero point for AB magnitudes (Jy)
    AB_ZEROPOINT_JY = 3631.0
    
    def __init__(self, config: dict = None, token: Optional[str] = None, tap_url: str = None):
        """
        Initialize Rubin data query.
        
        Args:
            config: Configuration dictionary (takes precedence)
            token: RSP authentication token (can also be set via RSP_TOKEN env var)
            tap_url: TAP service URL (defaults to Rubin Science Platform)
        """
        if config:
            rubin_config = config.get('rubin', {})
            self.token = rubin_config.get('rsp_token') or token or os.environ.get('RSP_TOKEN')
            self.tap_url = rubin_config.get('tap_url') or tap_url or "https://data.lsst.cloud/api/tap"
            self.catalog = rubin_config.get('catalog', 'dp02_dc2_catalogs.Object')
            self.flux_type = rubin_config.get('flux_type', 'cModelFlux')
            self.bands = rubin_config.get('bands', ['u', 'g', 'r', 'i', 'z', 'y'])
        else:
            self.token = token or os.environ.get('RSP_TOKEN')
            self.tap_url = tap_url or "https://data.lsst.cloud/api/tap"
            self.catalog = 'dp02_dc2_catalogs.Object'
            self.flux_type = 'cModelFlux'
            self.bands = ['u', 'g', 'r', 'i', 'z', 'y']
        
        self.tap_service = None
        
        if self.token:
            self._init_tap_service()
        else:
            print("[RUBIN QUERY] No token provided. Set RSP_TOKEN or pass token to constructor.")
            print("  You can still load local FITS files without authentication.")
    
    def _init_tap_service(self):
        """Initialize the TAP service with authentication - matching working code exactly."""
        try:
            import pyvo
            from requests import Session
            
            # Match working code exactly - no extra headers
            session = Session()
            session.headers.update({"Authorization": f"Bearer {self.token}"})
            
            self.tap_service = pyvo.dal.TAPService(self.tap_url, session=session)
            print(f"[RUBIN QUERY] TAP service initialized: {self.tap_url}")
            
        except ImportError:
            print("[RUBIN QUERY] pyvo not installed. Install with: pip install pyvo")
            self.tap_service = None
        except Exception as e:
            print(f"[RUBIN QUERY] Failed to initialize TAP service: {e}")
            self.tap_service = None
    
    def query_object(self, object_ids: Union[int, List[int]], 
                     catalog: str = None,
                     max_retries: int = 3,
                     retry_delay: float = 5.0) -> pd.DataFrame:
        """Query the DP0.2 Object catalog for specific objectIds."""
        if self.tap_service is None:
            raise RuntimeError("TAP service not initialized. Provide a valid token.")
        
        catalog = catalog or self.catalog
        
        if isinstance(object_ids, list):
            object_ids_str = ", ".join(map(str, object_ids))
        else:
            object_ids_str = str(object_ids)
        
        query = f"""
        SELECT *
        FROM {catalog}
        WHERE objectId IN ({object_ids_str})
        """
        
        print(f"[RUBIN QUERY] Querying object(s): {object_ids_str}")
        print(f"[RUBIN QUERY] Query:\n{query}")
        
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"[RUBIN QUERY] Retry attempt {attempt + 1}/{max_retries} after {retry_delay}s delay...")
                    time.sleep(retry_delay)
                
                result = self.tap_service.run_sync(query)
                df = result.to_table().to_pandas()
                
                if df.empty:
                    raise RuntimeError(f"No results found for objectIds: {object_ids_str}")
                
                print(f"[RUBIN QUERY] Retrieved {len(df)} row(s)")
                print(f"[RUBIN QUERY] Columns available: {len(df.columns)}")
                return df
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"[RUBIN QUERY] Query failed (attempt {attempt + 1}): {error_msg}")
                
                # Check for server-side errors that might be transient
                server_error = self._check_server_error()
                if server_error:
                    print(f"[RUBIN QUERY] Server error detected: {server_error}")
                    if "MERGE_ERROR" in server_error or "Couldn't resolve" in server_error:
                        print("[RUBIN QUERY] This appears to be a transient RSP backend issue.")
                        print("[RUBIN QUERY] The Rubin Science Platform may be experiencing problems.")
                        print("[RUBIN QUERY] You can:")
                        print("  1. Wait and try again later")
                        print("  2. Check RSP status at https://data.lsst.cloud/")
                        print("  3. Try a different objectId")
                        if attempt < max_retries - 1:
                            continue  # Retry
        
        raise RuntimeError(f"TAP query failed after {max_retries} attempts. Last error: {last_error}\n"
                          f"This may be a Rubin Science Platform backend issue. Please try again later.")
    
    def _check_server_error(self) -> Optional[str]:
        """Make a direct request to check what the server is returning."""
        try:
            from requests import Session
            session = Session()
            session.headers.update({"Authorization": f"Bearer {self.token}"})
            
            # Simple test query
            test_query = "SELECT TOP 1 objectId FROM dp02_dc2_catalogs.Object"
            sync_url = f"{self.tap_url}/sync"
            response = session.post(sync_url, data={
                "QUERY": test_query,
                "LANG": "ADQL",
                "FORMAT": "votable"
            })
            
            if response.status_code >= 500:
                return f"HTTP {response.status_code}: {response.text[:300]}"
            return None
        except Exception as e:
            return f"Check failed: {e}"
    
    def query_region(self, ra: float, dec: float, radius_arcsec: float = 10.0,
                     catalog: str = None, max_rows: int = 1000) -> pd.DataFrame:
        """Query objects within a circular region."""
        if self.tap_service is None:
            raise RuntimeError("TAP service not initialized. Provide a valid token.")
        
        catalog = catalog or self.catalog
        
        query = f"""
        SELECT TOP {max_rows} *
        FROM {catalog}
        WHERE CONTAINS(
            POINT('ICRS', coord_ra, coord_dec),
            CIRCLE('ICRS', {ra}, {dec}, {radius_arcsec/3600.0})
        ) = 1
        """
        
        print(f"[RUBIN QUERY] Searching region: RA={ra:.4f}, Dec={dec:.4f}, radius={radius_arcsec}\"")
        
        try:
            result = self.tap_service.run_sync(query)
            df = result.to_table().to_pandas()
        except Exception as e:
            raise RuntimeError(f"TAP query failed: {e}")
        
        print(f"[RUBIN QUERY] Found {len(df)} object(s)")
        return df
    
    def cone_search(self, ra, dec, radius_arcsec=60.0, flux_type='psfFlux', 
                    bands=None, max_objects=None):
        """
        Perform cone search around coordinates.
        
        Args:
            ra: Right ascension (degrees)
            dec: Declination (degrees)
            radius_arcsec: Search radius (arcseconds)
            flux_type: Flux measurement type
            bands: List of bands to retrieve
            max_objects: Maximum number of objects to return
        
        Returns:
            List of (object_id, phot_data) tuples
        """
        bands = bands or ['u', 'g', 'r', 'i', 'z', 'y']
        radius_deg = radius_arcsec / 3600.0
        
        # TAP query for cone search
        query = f"""
        SELECT objectId, coord_ra, coord_dec,
               {', '.join([f'{band}_{flux_type}' for band in bands])},
               {', '.join([f'{band}_{flux_type}Err' for band in bands])}
        FROM dp02_dc2_catalogs.Object
        WHERE CONTAINS(POINT('ICRS', coord_ra, coord_dec),
                      CIRCLE('ICRS', {ra}, {dec}, {radius_deg})) = 1
        """
        
        if max_objects:
            query += f" LIMIT {max_objects}"
        
        print(f"[RUBIN] Executing cone search query...")
        results = self._execute_tap_query(query)
        
        datasets = []
        for row in results:
            obj_id = row['objectId']
            
            phot_data = self._extract_photometry(row, flux_type, bands)
            phot_data['object_id'] = f"rubin_{obj_id}"
            phot_data['ra'] = row['coord_ra']
            phot_data['dec'] = row['coord_dec']
            
            datasets.append((f"rubin_{obj_id}", phot_data))
        
        return datasets
    
    def extract_photometry(self, df: pd.DataFrame, 
                          flux_type: str = None,
                          bands: List[str] = None) -> Dict:
        """Extract photometry from query results."""
        bands = bands or self.bands
        flux_type = flux_type or self.flux_type
        
        wavelengths = []
        fluxes = []
        flux_errs = []
        used_bands = []
        
        print(f"\n[RUBIN QUERY] Extracting {flux_type} photometry:")
        
        for band in bands:
            flux_candidates = [
                f"{band}_{flux_type}",
                f"{band}_psfFlux",
                f"{band}_calibFlux",
            ]
            
            flux_col = None
            flux_val = np.nan
            
            for candidate in flux_candidates:
                if candidate in df.columns:
                    val = df[candidate].values[0]
                    if pd.notna(val):
                        flux_col = candidate
                        flux_val = val
                        break
            
            if flux_col is None:
                print(f"  {band}: No flux column found (skipped)")
                continue
            
            err_candidates = [
                f"{flux_col}Err",
                f"{band}_{flux_type}Err",
                f"{band}_psfFluxErr",
                f"{band}_calibFluxErr",
            ]
            
            flux_err_val = np.nan
            for err_col in err_candidates:
                if err_col in df.columns:
                    err_val = df[err_col].values[0]
                    if pd.notna(err_val):
                        flux_err_val = err_val
                        break
            
            if pd.isna(flux_err_val):
                flux_err_val = 0.05 * flux_val
            
            if pd.notna(flux_val) and flux_val > 0:
                flux_jy = flux_val * 1e-9
                flux_err_jy = flux_err_val * 1e-9
                
                wavelengths.append(self.FILTER_WAVELENGTHS[band])
                fluxes.append(flux_jy)
                flux_errs.append(flux_err_jy)
                used_bands.append(band)
                
                print(f"  {band}: {flux_val:.3e} nJy = {flux_jy:.3e} Jy (from {flux_col})")
            else:
                print(f"  {band}: Invalid flux value (skipped)")
        
        if len(wavelengths) == 0:
            raise RuntimeError("No valid photometry found in query results")
        
        print(f"\n[RUBIN QUERY] Successfully extracted {len(wavelengths)} bands: {used_bands}")
        
        return {
            'wavelength': np.array(wavelengths),
            'obs_flux': np.array(fluxes),
            'obs_err': np.array(flux_errs),
            'mod_flux': np.zeros(len(fluxes)),
            'bands': used_bands
        }
    
    @staticmethod
    def flux_to_mag(flux_jy: float, flux_err_jy: float = None):
        """Convert flux in Jy to AB magnitude."""
        if flux_jy <= 0 or not np.isfinite(flux_jy):
            return (np.nan, np.nan) if flux_err_jy is not None else np.nan
        
        mag = -2.5 * np.log10(flux_jy / RubinDataQuery.AB_ZEROPOINT_JY)
        
        if flux_err_jy is not None:
            mag_err = 2.5 / np.log(10) * flux_err_jy / flux_jy
            return mag, mag_err
        return mag
    
    @staticmethod
    def mag_to_flux(mag: float, mag_err: float = None):
        """Convert AB magnitude to flux in Jy."""
        if not np.isfinite(mag):
            return (np.nan, np.nan) if mag_err is not None else np.nan
        
        flux_jy = RubinDataQuery.AB_ZEROPOINT_JY * 10**(-0.4 * mag)
        
        if mag_err is not None:
            flux_err_jy = flux_jy * mag_err * np.log(10) / 2.5
            return flux_jy, flux_err_jy
        return flux_jy