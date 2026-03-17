"""
External photometry data source queries for supplementing SED fitting.
Supports: Euclid, Roman, GALEX, AllWISE, VISTA Hemisphere Survey
"""

import numpy as np
import warnings
from astropy.coordinates import SkyCoord
from astropy import units as u

try:
    from astroquery.vizier import Vizier
    from astroquery.ipac.irsa import Irsa
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False
    warnings.warn("astroquery not available. External source queries will fail.")


class ExternalPhotometryQuery:
    """Query external photometry catalogs to supplement SED data."""
    
    def __init__(self, config=None):
        """
        Initialize external photometry query handler.
        
        Parameters
        ----------
        config : dict, optional
            Configuration dictionary with query parameters
        """
        self.config = config or {}
        
        # Band central wavelengths (micrometers)
        self.band_wavelengths = {
            # Euclid
            'euclid_vis': 0.7,
            'euclid_y': 1.08,
            'euclid_j': 1.26,
            'euclid_h': 1.65,
            
            # Roman (Nancy Grace Roman Space Telescope)
            'roman_f062': 0.62,
            'roman_f087': 0.87,
            'roman_f106': 1.06,
            'roman_f129': 1.29,
            'roman_f158': 1.58,
            'roman_f184': 1.84,
            'roman_f146': 1.46,
            'roman_f213': 2.13,
            
            # GALEX
            'galex_fuv': 0.152,
            'galex_nuv': 0.227,
            
            # AllWISE
            'wise_w1': 3.4,
            'wise_w2': 4.6,
            'wise_w3': 12.0,
            'wise_w4': 22.0,
            
            # VISTA Hemisphere Survey (VHS)
            'vista_z': 0.878,
            'vista_y': 1.021,
            'vista_j': 1.254,
            'vista_h': 1.646,
            'vista_ks': 2.149,
        }
    
    def query_all_sources(self, ra, dec, radius_arcsec=10.0, sources=None):
        """
        Query all available external sources for photometry.
        
        Parameters
        ----------
        ra : float
            Right Ascension in degrees
        dec : float
            Declination in degrees
        radius_arcsec : float, optional
            Search radius in arcseconds (default: 10.0)
        sources : list, optional
            List of sources to query. If None, queries all available.
            Options: ['euclid', 'roman', 'galex', 'allwise', 'vista']
        
        Returns
        -------
        dict
            Combined photometry dictionary with wavelength, flux, flux_err
        """
        if not ASTROQUERY_AVAILABLE:
            raise ImportError("astroquery is required for external source queries. "
                            "Install with: pip install astroquery")
        
        if sources is None:
            sources = ['galex', 'allwise', 'vista']  # Most commonly available
        
        all_wavelengths = []
        all_fluxes = []
        all_errors = []
        all_sources = []
        
        # Query each source
        for source in sources:
            try:
                if source.lower() == 'euclid':
                    data = self.query_euclid(ra, dec, radius_arcsec)
                elif source.lower() == 'roman':
                    data = self.query_roman(ra, dec, radius_arcsec)
                elif source.lower() == 'galex':
                    data = self.query_galex(ra, dec, radius_arcsec)
                elif source.lower() == 'allwise':
                    data = self.query_allwise(ra, dec, radius_arcsec)
                elif source.lower() == 'vista':
                    data = self.query_vista(ra, dec, radius_arcsec)
                else:
                    print(f"[WARNING] Unknown source: {source}")
                    continue
                
                if data is not None and len(data['wavelength']) > 0:
                    all_wavelengths.extend(data['wavelength'])
                    all_fluxes.extend(data['flux'])
                    all_errors.extend(data['flux_err'])
                    all_sources.extend([source] * len(data['wavelength']))
                    print(f"[EXTERNAL] Found {len(data['wavelength'])} bands from {source}")
                
            except Exception as e:
                print(f"[WARNING] Failed to query {source}: {e}")
                continue
        
        if len(all_wavelengths) == 0:
            print("[EXTERNAL] No external photometry found")
            return None
        
        # Sort by wavelength
        sort_idx = np.argsort(all_wavelengths)
        
        return {
            'wavelength': np.array(all_wavelengths)[sort_idx],
            'flux': np.array(all_fluxes)[sort_idx],
            'flux_err': np.array(all_errors)[sort_idx],
            'source': np.array(all_sources)[sort_idx]
        }
    
    def query_euclid(self, ra, dec, radius_arcsec=10.0):
        """
        Query Euclid photometry (VIS, Y, J, H bands).
        
        Note: Euclid is still ramping up. This queries VizieR for any
        available Euclid data releases.
        """
        print(f"[EUCLID] Querying at RA={ra:.4f}, Dec={dec:.4f}, r={radius_arcsec}\"")
        
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        # Euclid catalog (when available)
        # Update catalog ID when Euclid data is released
        v = Vizier(columns=['*'], row_limit=1)
        v.ROW_LIMIT = 1
        
        try:
            # Placeholder - update with actual Euclid catalog
            result = v.query_region(coord, radius=radius_arcsec*u.arcsec,
                                   catalog='II/371')  # Example catalog ID
            
            if len(result) == 0:
                print("[EUCLID] No matches found")
                return None
            
            table = result[0]
            
            wavelengths = []
            fluxes = []
            errors = []
            
            # VIS band
            if 'VIS_mag' in table.colnames:
                flux, err = self._mag_to_flux(table['VIS_mag'][0], 
                                             table.get('e_VIS_mag', [0.1])[0],
                                             self.band_wavelengths['euclid_vis'])
                wavelengths.append(self.band_wavelengths['euclid_vis'])
                fluxes.append(flux)
                errors.append(err)
            
            # NIR bands (Y, J, H)
            for band in ['Y', 'J', 'H']:
                col_name = f'{band}_mag'
                if col_name in table.colnames:
                    flux, err = self._mag_to_flux(table[col_name][0],
                                                 table.get(f'e_{col_name}', [0.1])[0],
                                                 self.band_wavelengths[f'euclid_{band.lower()}'])
                    wavelengths.append(self.band_wavelengths[f'euclid_{band.lower()}'])
                    fluxes.append(flux)
                    errors.append(err)
            
            return {
                'wavelength': np.array(wavelengths),
                'flux': np.array(fluxes),
                'flux_err': np.array(errors)
            }
            
        except Exception as e:
            print(f"[EUCLID] Query failed: {e}")
            return None
    
    def query_roman(self, ra, dec, radius_arcsec=10.0):
        """
        Query Roman Space Telescope photometry.
        
        Note: Roman is not yet operational. This is a placeholder for
        when data becomes available.
        """
        print(f"[ROMAN] Querying at RA={ra:.4f}, Dec={dec:.4f}, r={radius_arcsec}\"")
        print("[ROMAN] Roman Space Telescope data not yet available")
        return None
    
    def query_galex(self, ra, dec, radius_arcsec=10.0):
        """
        Query GALEX UV photometry (FUV, NUV bands).
        """
        print(f"[GALEX] Querying at RA={ra:.4f}, Dec={dec:.4f}, r={radius_arcsec}\"")
        
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        # GALEX AIS catalog (All-Sky Imaging Survey)
        v = Vizier(columns=['*'], row_limit=1)
        
        try:
            result = v.query_region(coord, radius=radius_arcsec*u.arcsec,
                                   catalog='II/335/galex_ais')  # GALEX-AIS
            
            if len(result) == 0:
                print("[GALEX] No matches found")
                return None
            
            table = result[0]
            
            wavelengths = []
            fluxes = []
            errors = []
            
            # FUV band
            if 'FUVmag' in table.colnames and not np.ma.is_masked(table['FUVmag'][0]):
                flux, err = self._mag_to_flux(table['FUVmag'][0],
                                             table.get('e_FUVmag', [0.1])[0],
                                             self.band_wavelengths['galex_fuv'])
                if flux > 0:
                    wavelengths.append(self.band_wavelengths['galex_fuv'])
                    fluxes.append(flux)
                    errors.append(err)
            
            # NUV band
            if 'NUVmag' in table.colnames and not np.ma.is_masked(table['NUVmag'][0]):
                flux, err = self._mag_to_flux(table['NUVmag'][0],
                                             table.get('e_NUVmag', [0.1])[0],
                                             self.band_wavelengths['galex_nuv'])
                if flux > 0:
                    wavelengths.append(self.band_wavelengths['galex_nuv'])
                    fluxes.append(flux)
                    errors.append(err)
            
            if len(wavelengths) == 0:
                return None
            
            return {
                'wavelength': np.array(wavelengths),
                'flux': np.array(fluxes),
                'flux_err': np.array(errors)
            }
            
        except Exception as e:
            print(f"[GALEX] Query failed: {e}")
            return None
    
    def query_allwise(self, ra, dec, radius_arcsec=10.0):
        """
        Query AllWISE infrared photometry (W1, W2, W3, W4 bands).
        """
        print(f"[AllWISE] Querying at RA={ra:.4f}, Dec={dec:.4f}, r={radius_arcsec}\"")
        
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        try:
            # Query via IRSA
            table = Irsa.query_region(coord, catalog='allwise_p3as_psd',
                                     spatial='Cone',
                                     radius=radius_arcsec*u.arcsec)
            
            if len(table) == 0:
                print("[AllWISE] No matches found")
                return None
            
            # Take closest match
            row = table[0]
            
            wavelengths = []
            fluxes = []
            errors = []
            
            # W1, W2, W3, W4 bands
            for i in range(1, 5):
                mag_col = f'w{i}mpro'  # Profile-fit magnitude
                err_col = f'w{i}sigmpro'
                
                if mag_col in table.colnames and not np.ma.is_masked(row[mag_col]):
                    mag = row[mag_col]
                    mag_err = row.get(err_col, 0.1) if err_col in table.colnames else 0.1
                    
                    flux, err = self._mag_to_flux(mag, mag_err,
                                                 self.band_wavelengths[f'wise_w{i}'])
                    if flux > 0:
                        wavelengths.append(self.band_wavelengths[f'wise_w{i}'])
                        fluxes.append(flux)
                        errors.append(err)
            
            if len(wavelengths) == 0:
                return None
            
            return {
                'wavelength': np.array(wavelengths),
                'flux': np.array(fluxes),
                'flux_err': np.array(errors)
            }
            
        except Exception as e:
            print(f"[AllWISE] Query failed: {e}")
            return None
    
    def query_vista(self, ra, dec, radius_arcsec=10.0):
        """
        Query VISTA Hemisphere Survey photometry (Z, Y, J, H, Ks bands).
        """
        print(f"[VISTA] Querying at RA={ra:.4f}, Dec={dec:.4f}, r={radius_arcsec}\"")
        
        coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
        
        # VISTA Hemisphere Survey (VHS) DR6
        v = Vizier(columns=['*'], row_limit=1)
        
        try:
            result = v.query_region(coord, radius=radius_arcsec*u.arcsec,
                                   catalog='II/367/vhs_dr5')  # VHS DR5
            
            if len(result) == 0:
                print("[VISTA] No matches found")
                return None
            
            table = result[0]
            
            wavelengths = []
            fluxes = []
            errors = []
            
            # Z, Y, J, H, Ks bands
            for band in ['Z', 'Y', 'J', 'H', 'Ks']:
                mag_col = f'{band}mag'
                err_col = f'e_{band}mag'
                
                if mag_col in table.colnames and not np.ma.is_masked(table[mag_col][0]):
                    mag = table[mag_col][0]
                    mag_err = table.get(err_col, [0.1])[0] if err_col in table.colnames else 0.1
                    
                    flux, err = self._mag_to_flux(mag, mag_err,
                                                 self.band_wavelengths[f'vista_{band.lower()}'])
                    if flux > 0:
                        wavelengths.append(self.band_wavelengths[f'vista_{band.lower()}'])
                        fluxes.append(flux)
                        errors.append(err)
            
            if len(wavelengths) == 0:
                return None
            
            return {
                'wavelength': np.array(wavelengths),
                'flux': np.array(fluxes),
                'flux_err': np.array(errors)
            }
            
        except Exception as e:
            print(f"[VISTA] Query failed: {e}")
            return None
    
    def _mag_to_flux(self, mag, mag_err, wavelength_um):
        """
        Convert AB magnitude to flux in Janskys.
        
        Parameters
        ----------
        mag : float
            AB magnitude
        mag_err : float
            Magnitude uncertainty
        wavelength_um : float
            Central wavelength in micrometers
        
        Returns
        -------
        flux : float
            Flux in Janskys
        flux_err : float
            Flux uncertainty in Janskys
        """
        if np.ma.is_masked(mag) or np.isnan(mag) or mag > 30:
            return 0.0, 0.0
        
        # AB magnitude to flux density (Jy)
        # F_nu [Jy] = 10^((8.9 - AB_mag) / 2.5) * 3631 Jy
        flux_jy = 3631 * 10**((mag - 8.9) / (-2.5))
        
        # Error propagation
        flux_err_jy = flux_jy * mag_err * np.log(10) / 2.5
        
        return flux_jy, flux_err_jy


class ExternalDataCombiner:
    """Combine external photometry with primary data sources."""
    
    @staticmethod
    def combine_with_external(primary_data, external_data, 
                             min_separation_um=0.05, prefer_primary=True):
        """
        Combine primary photometry with external sources.
        
        Parameters
        ----------
        primary_data : dict
            Primary photometry data (e.g., Rubin, FITS catalog)
        external_data : dict
            External photometry data
        min_separation_um : float, optional
            Minimum wavelength separation to keep both points (default: 0.05 um)
        prefer_primary : bool, optional
            If True, prefer primary data when bands overlap (default: True)
        
        Returns
        -------
        dict
            Combined photometry dictionary
        """
        if external_data is None or len(external_data['wavelength']) == 0:
            return primary_data
        
        primary_wave = np.array(primary_data['wavelength'])
        primary_flux = np.array(primary_data['flux'])
        primary_err = np.array(primary_data['flux_err'])
        
        external_wave = np.array(external_data['wavelength'])
        external_flux = np.array(external_data['flux'])
        external_err = np.array(external_data['flux_err'])
        
        # Check for overlapping bands
        combined_wave = []
        combined_flux = []
        combined_err = []
        combined_source = []
        
        # Add all primary data
        for i in range(len(primary_wave)):
            combined_wave.append(primary_wave[i])
            combined_flux.append(primary_flux[i])
            combined_err.append(primary_err[i])
            combined_source.append('primary')
        
        # Add external data, checking for overlaps
        for i in range(len(external_wave)):
            ext_wave = external_wave[i]
            
            # Check if any primary band is too close
            wave_diffs = np.abs(primary_wave - ext_wave)
            min_diff = np.min(wave_diffs)
            
            if min_diff > min_separation_um:
                # No overlap, add external point
                combined_wave.append(ext_wave)
                combined_flux.append(external_flux[i])
                combined_err.append(external_err[i])
                combined_source.append(external_data.get('source', ['external'])[i])
            elif not prefer_primary:
                # Overlap but prefer external
                overlap_idx = np.argmin(wave_diffs)
                combined_flux[overlap_idx] = external_flux[i]
                combined_err[overlap_idx] = external_err[i]
                combined_source[overlap_idx] = external_data.get('source', ['external'])[i]
        
        # Sort by wavelength
        sort_idx = np.argsort(combined_wave)
        
        result = {
            'wavelength': np.array(combined_wave)[sort_idx],
            'flux': np.array(combined_flux)[sort_idx],
            'flux_err': np.array(combined_err)[sort_idx],
            'source': np.array(combined_source)[sort_idx]
        }
        
        print(f"[COMBINE] Primary: {len(primary_wave)} bands, "
              f"External: {len(external_wave)} bands, "
              f"Combined: {len(result['wavelength'])} bands")
        
        return result
