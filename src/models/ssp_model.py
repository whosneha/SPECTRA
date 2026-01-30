import numpy as np
import os
import sys

class SSPModel:
    """Simple Stellar Population model wrapper."""
    
    def __init__(self, config):
        """
        Initialize SSP model.
        
        Args:
            config: Dict with type, imf, dust_model keys
        """
        self.model_type = config.get('type', 'fsps')
        self.imf = config.get('imf', 'kroupa')
        self.dust_model = config.get('dust_model', 'calzetti')
        self.distance_mpc = config.get('distance_mpc', 100.0)  # Default 100 Mpc
        self.mock_mode = True
        self.ssp = None
        
        # Try to initialize FSPS
        if self.model_type == 'fsps':
            self._init_fsps()
        elif self.model_type == 'bc03':
            self._init_bc03()
    
    def _init_fsps(self):
        """Initialize FSPS model."""
        try:
            # Check if SPS_HOME is set
            if 'SPS_HOME' not in os.environ:
                print("Warning: SPS_HOME environment variable not set.")
                print("FSPS requires the SPS_HOME to point to your FSPS installation.")
                print("Using mock mode for now.")
                print("\nTo set up FSPS:")
                print("  1. Clone FSPS: git clone https://github.com/cconroy20/fsps.git")
                print("  2. Build it: cd fsps/src && make")
                print("  3. Set SPS_HOME: export SPS_HOME=/path/to/fsps")
                print("  4. Install python-fsps: pip install fsps")
                self.mock_mode = True
                return
            
            import fsps
            self.ssp = fsps.StellarPopulation(
                imf_type=self._get_imf_code(self.imf),
                dust_type=self._get_dust_code(self.dust_model)
            )
            self.mock_mode = False
            print("✓ FSPS initialized successfully")
            
        except RuntimeError as e:
            print(f"FSPS initialization failed: {e}")
            print("Using mock mode for now.")
            self.mock_mode = True
        except ImportError as e:
            print(f"FSPS import failed: {e}")
            print("Install with: pip install fsps (requires SPS_HOME set)")
            self.mock_mode = True
    
    def _init_bc03(self):
        """Initialize BC03 model (placeholder)."""
        print("BC03 not yet implemented. Using mock mode.")
        self.mock_mode = True
    
    @staticmethod
    def _get_imf_code(imf_name):
        """Map IMF name to FSPS code."""
        imf_map = {
            'kroupa': 2,
            'salpeter': 0,
            'chabrier': 1,
        }
        return imf_map.get(imf_name.lower(), 2)
    
    @staticmethod
    def _get_dust_code(dust_name):
        """Map dust model name to FSPS code."""
        dust_map = {
            'calzetti': 1,
            'mw': 3,
            'nodust': 0,
        }
        return dust_map.get(dust_name.lower(), 1)
    
    def get_magnitudes(self, mass=1e10, age=1.0, metallicity=-0.5, wavelengths=None):
        """
        Get model magnitudes/fluxes for given parameters.
        
        Args:
            mass: Stellar mass in log10 solar masses
            age: Age in Gyr
            metallicity: Metallicity in log10 Z/Zsun
            wavelengths: Optional wavelength array (μm)
            
        Returns:
            array: Model fluxes in Jy
        """
        if self.mock_mode:
            return self._get_mock_fluxes(mass, age, metallicity, wavelengths)
        else:
            return self._get_fsps_fluxes(mass, age, metallicity, wavelengths)
    
    def _get_fsps_fluxes(self, mass, age, metallicity, wavelengths=None):
        """
        Get fluxes from FSPS.
        
        Args:
            mass: log10 stellar mass (solar masses)
            age: Age in Gyr
            metallicity: log10 Z/Zsun
            wavelengths: Wavelength array in μm (optional)
            
        Returns:
            array: Fluxes in Jy
        """
        try:
            # Convert mass from log10 to linear (solar masses)
            mass_msun = 10 ** mass
            
            # Set FSPS parameters
            self.ssp.params['logzsol'] = metallicity
            
            # Get SED at specified age (age in Gyr)
            wav_aa, spec_lsun_hz = self.ssp.get_spectrum(tage=age, peraa=False)
            
            # Convert wavelength from Angstrom to micron
            wav_um = wav_aa / 1e4
            
            # Constants
            Lsun_erg = 3.828e33  # erg/s
            pc_cm = 3.086e18     # cm
            Mpc_cm = 3.086e24    # cm
            
            # Use actual distance to galaxy (in Mpc)
            distance_cm = self.distance_mpc * Mpc_cm
            
            # Convert from Lsun/Hz to erg/s/Hz
            spec_erg_hz = spec_lsun_hz * Lsun_erg
            
            # Then divide by 4π*d^2 to get flux at distance
            flux_cgs_hz = spec_erg_hz / (4 * np.pi * distance_cm**2)
            flux_jy = flux_cgs_hz * 1e23  # Convert to Jy
            
            # Scale by mass
            flux_jy *= mass_msun
            
            # Interpolate to requested wavelengths if provided
            if wavelengths is not None:
                valid_idx = (wav_um > 0) & (flux_jy > 0)
                if np.any(valid_idx):
                    flux_jy = np.interp(wavelengths, wav_um[valid_idx], flux_jy[valid_idx])
            
            print(f"[FSPS DEBUG] mass={mass} (log10), mass_msun={mass_msun:.2e}")
            print(f"[FSPS DEBUG] age={age} Gyr, metallicity={metallicity}")
            print(f"[FSPS DEBUG] distance={self.distance_mpc} Mpc")
            print(f"[FSPS DEBUG] Converted flux range: {flux_jy.min():.2e} to {flux_jy.max():.2e} Jy")
            
            return np.maximum(flux_jy, 1e-10)
            
        except Exception as e:
            print(f"Error in FSPS calculation: {e}")
            import traceback
            traceback.print_exc()
            print("Falling back to mock mode")
            self.mock_mode = True
            return self._get_mock_fluxes(mass, age, metallicity, wavelengths)
    
    def _get_mock_fluxes(self, mass, age, metallicity, wavelengths=None):
        """
        Get synthetic mock fluxes for testing.
        Produces fluxes in Jy with realistic scaling.
        
        Args:
            mass: log10 stellar mass
            age: Age in Gyr
            metallicity: log10 Z/Zsun
            wavelengths: Optional wavelength array to match
            
        Returns:
            array: Mock fluxes in Jy
        """
        n_wavelengths = len(wavelengths) if wavelengths is not None else 12
        
        # Base flux scales with mass (in Jy)
        # For a 1e10 solar mass star at optical wavelengths: ~3e-5 Jy
        mass_msun = 10 ** mass
        base_flux = 3e-5 * (mass_msun / 1e10)
        
        # Age factor: older stars are fainter
        age_factor = np.exp(-age / 10.0)
        
        # Metallicity factor: affects colors and luminosity
        z_factor = 1.0 + metallicity * 0.2
        
        # Add wavelength dependence (redder at longer wavelengths)
        if wavelengths is not None:
            wav_factor = (0.6 / wavelengths) ** 0.3
        else:
            wav_factor = np.ones(n_wavelengths)
        
        # Realistic noise
        np.random.seed(42)
        noise = np.random.normal(1.0, 0.08, n_wavelengths)
        
        # Combine all factors
        fluxes = base_flux * age_factor * z_factor * wav_factor * noise
        
        return np.maximum(fluxes, 1e-6)