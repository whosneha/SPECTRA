import os
import numpy as np
import pandas as pd
from typing import Dict, Optional, List, Union
from pathlib import Path
from astropy.io import fits
from astropy.table import Table
from src.data.external_sources import ExternalPhotometryQuery, ExternalDataCombiner

class DataLoader:
    """Unified data loader for various input formats."""
    
    # Standard filter wavelengths (microns)
    FILTER_WAVELENGTHS = {
        # Rubin/LSST
        'u': 0.368, 'g': 0.476, 'r': 0.621, 'i': 0.754, 'z': 0.870, 'y': 0.971,
        # HST/ACS
        'F435W': 0.433, 'F475W': 0.474, 'F555W': 0.531, 'F606W': 0.591,
        'F625W': 0.630, 'F775W': 0.769, 'F814W': 0.806, 'F850LP': 0.905,
        # HST/WFC3
        'F275W': 0.270, 'F336W': 0.335, 'F438W': 0.433, 'F547M': 0.545,
        'F110W': 1.153, 'F125W': 1.249, 'F140W': 1.392, 'F160W': 1.537,
        # JWST/NIRCam
        'F070W': 0.704, 'F090W': 0.902, 'F115W': 1.154, 'F150W': 1.501,
        'F200W': 1.989, 'F277W': 2.762, 'F356W': 3.568, 'F444W': 4.408,
    }
    
    def __init__(self, config: Dict = None):
        """Initialize data loader."""
        self.config = config or {}
        self.rubin_query = None
    
    def load(self, input_type: str = None, **kwargs):
        """Load data based on input type specified in config or parameter."""
        if input_type is None:
            input_type = self.config.get('input', {}).get('type', 'file')
        
        print(f"[INPUT] Loading data with type: {input_type}")
        
        if input_type == 'rubin_id':
            phot_data = self._load_rubin_id(**kwargs)
        elif input_type == 'fits':
            phot_data = self._load_fits(**kwargs)
        elif input_type == 'file' or input_type == 'csv':
            phot_data = self._load_file(**kwargs)
        elif input_type == 'dat':
            phot_data = self._load_dat(**kwargs)
        else:
            raise ValueError(f"Unknown input type: {input_type}")
        
        # Check if external sources should be queried
        if self.config.get('external_sources', {}).get('enabled', False):
            ra = kwargs.get('ra') or phot_data.get('ra')
            dec = kwargs.get('dec') or phot_data.get('dec')
            
            if ra is not None and dec is not None:
                external_data = self._query_external_sources(ra, dec)
                if external_data is not None:
                    phot_data = self._combine_with_external(phot_data, external_data)
        
        return phot_data
    
    def _query_external_sources(self, ra, dec):
        """Query external photometry sources."""
        ext_config = self.config.get('external_sources', {})
        
        sources = ext_config.get('sources', ['galex', 'allwise', 'vista'])
        radius_arcsec = ext_config.get('radius_arcsec', 10.0)
        
        print(f"\n[EXTERNAL] Querying external sources: {sources}")
        
        query = ExternalPhotometryQuery(self.config)
        external_data = query.query_all_sources(ra, dec, radius_arcsec, sources)
        
        return external_data
    
    def _combine_with_external(self, primary_data, external_data):
        """Combine primary data with external photometry."""
        combiner = ExternalDataCombiner()
        
        ext_config = self.config.get('external_sources', {})
        min_separation = ext_config.get('min_wavelength_separation_um', 0.05)
        prefer_primary = ext_config.get('prefer_primary', True)
        
        combined = combiner.combine_with_external(
            primary_data, external_data,
            min_separation_um=min_separation,
            prefer_primary=prefer_primary
        )
        
        return combined
    
    def _load_file(self, filepath: str = None, **kwargs) -> Dict:
        """Load photometry from a generic file (CSV, DAT, or FITS based on extension)."""
        input_config = self.config.get('input', {})
        filepath = filepath or input_config.get('filepath')
        
        if not filepath:
            raise ValueError("No filepath specified in config or kwargs")
        
        filepath = Path(filepath)
        ext = filepath.suffix.lower()
        
        print(f"[DATA LOADER] Loading file: {filepath}")
        
        if ext == '.fits' or ext == '.fit':
            return self._load_fits(filepath=str(filepath), **kwargs)
        elif ext == '.csv':
            return self._load_csv(str(filepath))
        elif ext == '.dat' or ext == '.txt':
            return self._load_dat(str(filepath))
        else:
            # Try CSV first
            try:
                return self._load_csv(str(filepath))
            except:
                return self._load_dat(str(filepath))
    
    def _load_rubin_id(self, object_id: Union[int, List[int]], 
                       token: str = None,
                       flux_type: str = "cModelFlux",
                       bands: List[str] = None) -> Dict:
        """Load data by querying Rubin TAP service with object ID."""
        from .rubin_query import RubinDataQuery
        
        # Always create fresh query with provided token
        self.rubin_query = RubinDataQuery(token=token)
        
        if self.rubin_query.tap_service is None:
            raise RuntimeError("Failed to initialize TAP service. Check your token.")
        
        df = self.rubin_query.query_object(object_id)
        phot_data = self.rubin_query.extract_photometry(df, flux_type=flux_type, bands=bands)
        
        # Add metadata
        phot_data['object_id'] = str(object_id)
        phot_data['source'] = 'rubin_tap'
        
        return phot_data
    
    def _load_rubin_tap(self, ra: float, dec: float, 
                        radius_arcsec: float = 10.0,
                        token: str = None,
                        flux_type: str = "cModelFlux",
                        bands: List[str] = None,
                        select_brightest: bool = True) -> Dict:
        """Load data by querying Rubin TAP service with coordinates."""
        from .rubin_query import RubinDataQuery
        
        # Always create fresh query with provided token
        self.rubin_query = RubinDataQuery(token=token)
        
        if self.rubin_query.tap_service is None:
            raise RuntimeError("Failed to initialize TAP service. Check your token.")
        
        df = self.rubin_query.query_region(ra, dec, radius_arcsec)
        
        if select_brightest and len(df) > 1:
            flux_col = f"r_{flux_type}" if f"r_{flux_type}" in df.columns else None
            if flux_col:
                df = df.loc[[df[flux_col].idxmax()]]
                print(f"[DATA LOADER] Selected brightest source from {len(df)} candidates")
        
        phot_data = self.rubin_query.extract_photometry(df, flux_type=flux_type, bands=bands)
        
        # Add metadata
        phot_data['object_id'] = f"ra{ra:.4f}_dec{dec:.4f}"
        phot_data['source'] = 'rubin_tap'
        phot_data['ra'] = ra
        phot_data['dec'] = dec
        
        return phot_data
    
    def _load_fits(self, **kwargs):
        """Load photometry from a FITS file (e.g., PHANGS catalogs)."""
        input_config = self.config.get('input', {})
        filepath = kwargs.get('filepath') or input_config.get('filepath')
        row_index = kwargs.get('row_index', input_config.get('row_index', 0))
        
        if not filepath:
            raise ValueError("No FITS filepath specified in config or kwargs")
        
        print(f"[FITS] Loading: {filepath}")
        print(f"[FITS] Row index: {row_index}")
        
        # Get column mapping from config
        column_mapping = input_config.get('column_mapping', {})
        flux_columns = column_mapping.get('flux_columns', {})
        error_columns = column_mapping.get('error_columns', {})
        flux_unit = input_config.get('flux_unit', 'mJy')
        
        # Get filter wavelengths from config
        filter_wavelengths = self.config.get('filters', {})
        
        # Open FITS file
        with fits.open(filepath) as hdul:
            # Data is typically in extension 1 for binary tables
            data = Table.read(hdul[1])
        
        print(f"[FITS] Total rows in catalog: {len(data)}")
        
        # Get the specific row
        if row_index is not None and row_index < len(data):
            row = data[row_index]
        else:
            raise ValueError(f"Row index {row_index} out of range (0-{len(data)-1})")
        
        # Extract metadata if available
        id_col = column_mapping.get('id', 'ID_PHANGS_CLUSTER')
        ra_col = column_mapping.get('ra', 'PHANGS_RA')
        dec_col = column_mapping.get('dec', 'PHANGS_DEC')
        
        object_id = row[id_col] if id_col in data.colnames else row_index
        ra = row[ra_col] if ra_col in data.colnames else None
        dec = row[dec_col] if dec_col in data.colnames else None
        
        print(f"[FITS] Object ID: {object_id}")
        if ra and dec:
            print(f"[FITS] Coordinates: RA={ra:.6f}, Dec={dec:.6f}")
        
        # Extract photometry
        wavelengths = []
        fluxes = []
        flux_errs = []
        bands = []
        
        # Unit conversion factor
        if flux_unit.lower() == 'mjy':
            unit_factor = 1e-3  # mJy to Jy
        elif flux_unit.lower() == 'ujy' or flux_unit.lower() == 'µjy':
            unit_factor = 1e-6  # µJy to Jy
        elif flux_unit.lower() == 'njy':
            unit_factor = 1e-9  # nJy to Jy
        else:
            unit_factor = 1.0  # Assume already in Jy
        
        print(f"\n[FITS] Extracting photometry ({flux_unit} -> Jy, factor={unit_factor}):")
        
        for band, flux_col in flux_columns.items():
            if flux_col not in data.colnames:
                print(f"  {band}: Column '{flux_col}' not found (skipped)")
                continue
            
            flux_val = row[flux_col]
            
            # Get error column
            err_col = error_columns.get(band)
            if err_col and err_col in data.colnames:
                err_val = row[err_col]
            else:
                err_val = 0.05 * abs(flux_val)  # 5% default error
            
            # Skip invalid values (-9999 typically means no coverage)
            if flux_val <= 0 or flux_val == -9999:
                print(f"  {band}: Invalid flux value {flux_val} (skipped)")
                continue
            
            # Get wavelength for this band
            if band in filter_wavelengths:
                wavelength = filter_wavelengths[band]
            else:
                print(f"  {band}: No wavelength defined in config (skipped)")
                continue
            
            # Convert to Jy
            flux_jy = flux_val * unit_factor
            err_jy = abs(err_val) * unit_factor
            
            wavelengths.append(wavelength)
            fluxes.append(flux_jy)
            flux_errs.append(err_jy)
            bands.append(band)
            
            print(f"  {band}: {flux_val:.4e} {flux_unit} = {flux_jy:.4e} Jy ± {err_jy:.4e} Jy")
        
        if len(wavelengths) == 0:
            raise RuntimeError("No valid photometry found in FITS file")
        
        print(f"\n[FITS] Successfully extracted {len(bands)} bands: {bands}")
        
        # Return in standard SPECTRA format
        return {
            'wavelength': np.array(wavelengths),
            'obs_flux': np.array(fluxes),
            'obs_err': np.array(flux_errs),
            'mod_flux': np.zeros(len(fluxes)),
            'bands': bands,
            'object_id': object_id,
            'ra': ra,
            'dec': dec,
            'source_file': filepath,
            'row_index': row_index
        }
    
    def _load_dat(self, filepath: str) -> Dict:
        """Load photometry from a .dat ASCII file."""
        print(f"[DATA LOADER] Loading DAT file: {filepath}")
        
        # Try to read with automatic column detection
        data = pd.read_csv(filepath, sep=r'\s+', comment='#',
                          names=['wavelength', 'obs_flux', 'obs_err', 'mod_flux'])
        
        return {
            'wavelength': data['wavelength'].values,
            'obs_flux': data['obs_flux'].values,
            'obs_err': data['obs_err'].values,
            'mod_flux': data['mod_flux'].values,
            'source': 'dat',
            'filepath': filepath
        }
    
    def _load_csv(self, filepath: str) -> Dict:
        """Load photometry from a CSV file."""
        print(f"[DATA LOADER] Loading CSV file: {filepath}")
        
        data = pd.read_csv(filepath)
        wavelength = self._find_column(data, None, ['wavelength', 'wave', 'lambda'])
        flux = self._find_column(data, None, ['obs_flux', 'flux', 'f_nu'])
        flux_err = self._find_column(data, None, ['obs_err', 'flux_err', 'error'])
        mod_flux = self._find_column(data, None, ['mod_flux', 'model_flux', 'model'])
        
        if wavelength is None or flux is None:
            raise ValueError(f"Could not identify required columns in {filepath}")
        
        if flux_err is None:
            flux_err = 0.1 * flux
        if mod_flux is None:
            mod_flux = np.zeros(len(flux))
            
        return {
            'wavelength': np.array(wavelength),
            'obs_flux': np.array(flux),
            'obs_err': np.array(flux_err),
            'mod_flux': np.array(mod_flux),
            'source': 'csv',
            'filepath': filepath
        }
    
    def _find_column(self, df: pd.DataFrame, specified: str, 
                     candidates: List[str]) -> Optional[np.ndarray]:
        """Find a column in the dataframe."""
        if specified and specified in df.columns:
            return df[specified].values
        
        for candidate in candidates:
            # Check exact match
            if candidate in df.columns:
                return df[candidate].values
            # Check case-insensitive match
            for col in df.columns:
                if col.lower() == candidate.lower():
                    return df[col].values
        
        return None
    
    def combine_datasets(self, datasets: List[Dict], 
                        sort_by_wavelength: bool = True) -> Dict:
        """
        Combine multiple photometry datasets (e.g., Rubin + HST).
        
        Args:
            datasets: List of photometry dictionaries
            sort_by_wavelength: Sort combined data by wavelength
        
        Returns:
            Combined photometry dictionary
        """
        wavelengths = []
        fluxes = []
        errors = []
        sources = []
        
        for data in datasets:
            wavelengths.extend(data['wavelength'])
            fluxes.extend(data['obs_flux'])
            errors.extend(data['obs_err'])
            sources.extend([data.get('source', 'unknown')] * len(data['wavelength']))
        
        wavelengths = np.array(wavelengths)
        fluxes = np.array(fluxes)
        errors = np.array(errors)
        
        if sort_by_wavelength:
            sort_idx = np.argsort(wavelengths)
            wavelengths = wavelengths[sort_idx]
            fluxes = fluxes[sort_idx]
            errors = errors[sort_idx]
            sources = [sources[i] for i in sort_idx]
        
        return {
            'wavelength': wavelengths,
            'obs_flux': fluxes,
            'obs_err': errors,
            'mod_flux': np.zeros(len(wavelengths)),
            'sources': sources,
            'n_datasets': len(datasets)
        }
    
    def _load_dat(self, filepath):
        """
        Load whitespace-delimited .dat file.

        Supports two wavelength formats:
          - Microns (values < 100) -- converted to Angstroms
          - Angstroms (values >= 100) -- used as-is

        Expected columns: wavelength  obs_flux  obs_err  [mod_flux]
        Lines starting with '#' are treated as comments.
        """
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"DAT file not found: {filepath}")

        data = np.loadtxt(filepath, comments='#')

        if data.ndim == 1:
            raise ValueError(f"DAT file has only 1 row: {filepath}")

        wavelength = data[:, 0]
        obs_flux = data[:, 1]
        obs_err = data[:, 2]

        # Auto-detect wavelength units: if max < 100, assume microns
        if wavelength.max() < 100.0:
            print(f"[DATA LOADER] Wavelengths appear to be in microns (max={wavelength.max():.4f})")
            print(f"[DATA LOADER] Converting to Angstroms (* 1e4)")
            wavelength = wavelength * 1e4  # microns -> Angstroms

        # Optional 4th column: model flux from file (for reference only)
        mod_flux_file = data[:, 3] if data.shape[1] >= 4 else None

        # Filter out rows with non-positive flux or non-finite errors
        valid = (obs_flux > 0) & np.isfinite(obs_flux) & np.isfinite(obs_err) & (obs_err > 0)
        
        # Also filter out very low SNR points (SNR < 1 = noise-dominated)
        snr = np.where(valid, obs_flux / obs_err, 0.0)
        min_snr = 1.0
        low_snr = valid & (snr < min_snr)
        if np.any(low_snr):
            n_low = np.sum(low_snr)
            print(f"[DATA LOADER] Filtering {n_low} low-SNR points (SNR < {min_snr})")
            for idx in np.where(low_snr)[0]:
                print(f"  Row {idx}: flux={obs_flux[idx]:.3e}, err={obs_err[idx]:.3e}, SNR={snr[idx]:.2f}")
            valid = valid & (snr >= min_snr)
        
        if not np.all(valid):
            n_bad = np.sum(~valid)
            print(f"[DATA LOADER] Total filtered: {n_bad} of {len(obs_flux)} rows")
            wavelength = wavelength[valid]
            obs_flux = obs_flux[valid]
            obs_err = obs_err[valid]
            if mod_flux_file is not None:
                mod_flux_file = mod_flux_file[valid]

        # Generate band names from wavelength
        bands = [f"{w:.0f}A" for w in wavelength]

        print(f"[DATA LOADER] Loaded {len(wavelength)} data points from {os.path.basename(filepath)}")
        print(f"[DATA LOADER] Wavelength range: {wavelength.min():.1f} - {wavelength.max():.1f} Angstroms")
        print(f"[DATA LOADER] Flux range: {obs_flux.min():.3e} - {obs_flux.max():.3e}")
        if len(obs_flux) > 0:
            snr_kept = obs_flux / obs_err
            print(f"[DATA LOADER] SNR range: {snr_kept.min():.1f} - {snr_kept.max():.1f}")

        result = {
            'wavelength': wavelength,
            'obs_flux': obs_flux,
            'obs_err': obs_err,
            'bands': bands,
        }

        if mod_flux_file is not None:
            result['mod_flux_file'] = mod_flux_file

        return result

    def _load_csv(self, filepath):
        """Load CSV photometry file."""
        import pandas as pd

        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        df = pd.read_csv(filepath)

        # Try standard column names
        wav_col = None
        for candidate in ['wavelength', 'wave', 'lambda', 'wav']:
            if candidate in df.columns:
                wav_col = candidate
                break
        if wav_col is None:
            raise ValueError(f"No wavelength column found in {filepath}. "
                             f"Expected one of: wavelength, wave, lambda, wav")

        flux_col = None
        for candidate in ['flux', 'obs_flux', 'f_nu']:
            if candidate in df.columns:
                flux_col = candidate
                break
        if flux_col is None:
            raise ValueError(f"No flux column found in {filepath}.")

        err_col = None
        for candidate in ['flux_err', 'obs_err', 'error', 'err', 'f_nu_err']:
            if candidate in df.columns:
                err_col = candidate
                break
        if err_col is None:
            raise ValueError(f"No error column found in {filepath}.")

        wavelength = df[wav_col].values.astype(float)
        obs_flux = df[flux_col].values.astype(float)
        obs_err = df[err_col].values.astype(float)

        # Auto-detect wavelength units
        if wavelength.max() < 100.0:
            wavelength = wavelength * 1e4

        bands = df['band'].tolist() if 'band' in df.columns else [f"{w:.0f}A" for w in wavelength]

        valid = (obs_flux > 0) & np.isfinite(obs_flux) & np.isfinite(obs_err) & (obs_err > 0)
        wavelength = wavelength[valid]
        obs_flux = obs_flux[valid]
        obs_err = obs_err[valid]
        bands = [b for b, v in zip(bands, valid) if v]

        print(f"[DATA LOADER] Loaded {len(wavelength)} bands from CSV: {os.path.basename(filepath)}")

        return {
            'wavelength': wavelength,
            'obs_flux': obs_flux,
            'obs_err': obs_err,
            'bands': bands,
        }

    def _load_fits(self, filepath, row_index=0):
        """Load FITS binary table."""
        from astropy.io import fits as pyfits

        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"FITS file not found: {filepath}")

        with pyfits.open(filepath) as hdul:
            table = hdul[1].data
            row = table[row_index]

            # Try to find wavelength/flux columns
            col_names = [c.lower() for c in table.names]

            result = {
                'object_id': row_index,
                'wavelength': np.array([]),
                'obs_flux': np.array([]),
                'obs_err': np.array([]),
                'bands': [],
            }

            # Generic approach: look for wavelength, flux, error columns
            for wav_name in ['wavelength', 'wave', 'lambda']:
                if wav_name in col_names:
                    idx = col_names.index(wav_name)
                    result['wavelength'] = np.array(table.names[idx])
                    break

        print(f"[DATA LOADER] Loaded FITS row {row_index} from {os.path.basename(filepath)}")
        return result

    def _load_rubin(self, input_type, **kwargs):
        """Load Rubin data via TAP query."""
        from src.data.rubin_query import RubinDataQuery

        token = kwargs.get('token')
        rubin = RubinDataQuery(token=token)

        if input_type == 'rubin_id':
            object_id = kwargs.get('object_id')
            df = rubin.query_object(object_id)
        elif input_type == 'rubin_tap':
            ra = kwargs.get('ra')
            dec = kwargs.get('dec')
            radius = kwargs.get('radius_arcsec', 10.0)
            df = rubin.query_region(ra, dec, radius)
        else:
            raise ValueError(f"Unknown Rubin input type: {input_type}")

        return rubin.extract_photometry(
            df,
            flux_type=kwargs.get('flux_type', 'psfFlux'),
            bands=kwargs.get('bands')
        )

    def combine_datasets(self, datasets):
        """
        Combine multiple photometry datasets into one.

        Args:
            datasets: List of phot_data dicts

        Returns:
            Combined phot_data dict sorted by wavelength
        """
        all_wav = []
        all_flux = []
        all_err = []
        all_bands = []

        for ds in datasets:
            all_wav.extend(ds['wavelength'])
            all_flux.extend(ds['obs_flux'])
            all_err.extend(ds['obs_err'])
            if 'bands' in ds:
                all_bands.extend(ds['bands'])
            else:
                all_bands.extend([f"{w:.0f}A" for w in ds['wavelength']])

        # Sort by wavelength
        sort_idx = np.argsort(all_wav)

        combined = {
            'wavelength': np.array(all_wav)[sort_idx],
            'obs_flux': np.array(all_flux)[sort_idx],
            'obs_err': np.array(all_err)[sort_idx],
            'bands': [all_bands[i] for i in sort_idx],
        }

        # Carry over metadata from first dataset
        for key in ['redshift', 'ra', 'dec', 'object_id']:
            if key in datasets[0]:
                combined[key] = datasets[0][key]

        print(f"[DATA LOADER] Combined {len(datasets)} datasets -> {len(combined['wavelength'])} bands")
        return combined