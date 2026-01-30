import numpy as np
import os
import sys

class SSPModel:
    """Simple Stellar Population model wrapper."""
    
    def __init__(self, config):
        """
        Initialize SSP model.
        """
        self.model_type = config.get('type', 'fsps')
        self.imf = config.get('imf', 'kroupa')
        self.dust_model = config.get('dust_model', 'calzetti')
        self.distance_mpc = config.get('distance_mpc', 100.0)
        self.redshift = config.get('redshift', 0.0)
        self.mock_mode = True
        self.ssp = None
        
        # Calibration flux level (will be set from observed data)
        self.flux_calibration = None
        
        if self.model_type == 'fsps':
            self._init_fsps()
        elif self.model_type == 'bc03':
            self._init_bc03()
    
    def set_flux_calibration(self, obs_flux):
        """
        Set flux calibration based on observed data.
        This ensures the mock model produces fluxes in the correct range.
        
        Args:
            obs_flux: Array of observed flux values
        """
        # Use median of observed flux as reference
        self.flux_calibration = np.median(obs_flux)
        print(f"[SSP MODEL] Flux calibration set to {self.flux_calibration:.2e} Jy")
    
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
    
    def get_magnitudes(self, mass=1e10, age=1.0, metallicity=-0.5, dust=0.0, wavelengths=None):
        """
        Get model magnitudes/fluxes for given parameters.
        
        Args:
            mass: Stellar mass in log10 solar masses
            age: Age in Gyr
            metallicity: Metallicity in log10 Z/Zsun
            dust: E(B-V) dust attenuation
            wavelengths: Optional wavelength array (μm)
            
        Returns:
            array: Model fluxes in Jy
        """
        if self.mock_mode:
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)
        else:
            return self._get_fsps_fluxes(mass, age, metallicity, dust, wavelengths)
    
    def _get_fsps_fluxes(self, mass, age, metallicity, dust=0.0, wavelengths=None):
        """
        Get fluxes from FSPS with proper redshift handling and dust.
        """
        try:
            mass_msun = 10 ** mass
            self.ssp.params['logzsol'] = metallicity
            self.ssp.params['dust2'] = dust  # Set dust attenuation
            
            wav_aa_rest, lum_lsun_hz = self.ssp.get_spectrum(tage=age, peraa=False)
            wav_um_rest = wav_aa_rest / 1e4
            
            z = self.redshift
            wav_um_obs = wav_um_rest * (1 + z)
            
            Lsun_erg_s = 3.828e33
            pc_cm = 3.0857e18
            
            lum_erg_s_hz = lum_lsun_hz * mass_msun * Lsun_erg_s
            distance_cm = self.distance_mpc * 1e6 * pc_cm
            flux_erg_s_cm2_hz = lum_erg_s_hz / (4.0 * np.pi * distance_cm**2 * (1 + z))
            flux_jy = flux_erg_s_cm2_hz * 1e23
            
            if wavelengths is not None:
                valid_idx = (wav_um_obs > 0) & (flux_jy > 0) & np.isfinite(flux_jy)
                if np.any(valid_idx):
                    sort_idx = np.argsort(wav_um_obs[valid_idx])
                    wav_sorted = wav_um_obs[valid_idx][sort_idx]
                    flux_sorted = flux_jy[valid_idx][sort_idx]
                    flux_jy = np.interp(wavelengths, wav_sorted, flux_sorted)
                else:
                    flux_jy = np.zeros_like(wavelengths)
            
            return np.maximum(flux_jy, 1e-30)
            
        except Exception as e:
            print(f"Error in FSPS calculation: {e}")
            import traceback
            traceback.print_exc()
            self.mock_mode = True
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)
    
    def _get_mock_fluxes(self, mass, age, metallicity, dust=0.0, wavelengths=None):
        """
        Get synthetic mock fluxes for testing.
        Calibrated to produce realistic fluxes matching observed data.
        """
        n_wavelengths = len(wavelengths) if wavelengths is not None else 12
        
        # Convert mass from log to linear
        mass_msun = 10 ** mass
        
        # Reference mass for scaling (10^12 solar masses)
        mass_ref = 1e12
        
        # Base flux calibration
        # If we have a calibration from observed data, use it
        # Scale so that mass=12 (10^12 Msun) gives approximately the observed flux level
        if self.flux_calibration is not None:
            base_flux = self.flux_calibration * (mass_msun / mass_ref)
        else:
            # Default: 3e-5 Jy at mass = 10^12 Msun
            base_flux = 3e-5 * (mass_msun / mass_ref)
        
        # Age effect: younger populations are brighter
        # Very mild dependence - factor of ~2 across age range
        age_factor = (0.1 / max(age, 0.01)) ** 0.1
        
        # Metallicity effect (very minor)
        z_factor = 1.0 + 0.02 * metallicity
        
        if wavelengths is not None:
            # Simple SED shape - relatively flat in Fnu for young galaxies
            wav_ref = 0.65  # Reference wavelength in microns
            
            # Very mild wavelength dependence
            beta = -0.5 + age * 0.2
            wav_factor = (wavelengths / wav_ref) ** beta
            
            # Normalize so mean is ~1
            wav_factor = wav_factor / np.mean(wav_factor)
            
            # Apply dust attenuation (Calzetti-like)
            if dust > 0:
                Rv = 4.05
                k_lambda = np.where(
                    wavelengths < 0.63,
                    2.659 * (-2.156 + 1.509/wavelengths - 0.198/wavelengths**2 + 0.011/wavelengths**3) + Rv,
                    2.659 * (-1.857 + 1.040/wavelengths) + Rv
                )
                k_lambda = np.maximum(k_lambda, 0)
                A_lambda = dust * k_lambda
                dust_factor = 10 ** (-0.4 * A_lambda)
            else:
                dust_factor = np.ones_like(wavelengths)
        else:
            wav_factor = np.ones(n_wavelengths)
            dust_factor = np.ones(n_wavelengths)
        
        # Combine all factors
        fluxes = base_flux * age_factor * z_factor * wav_factor * dust_factor
        
        # Add small deterministic scatter
        n = len(fluxes)
        scatter = 1.0 + 0.02 * np.sin(np.arange(n) * 2.3)
        fluxes = fluxes * scatter
        
        return np.maximum(fluxes, 1e-15)