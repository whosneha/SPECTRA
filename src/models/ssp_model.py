import numpy as np
import os
import sys


class SSPModel:
    """Simple Stellar Population model wrapper."""

    def __init__(self, config):
        self.model_type       = config.get('type', 'fsps')
        self.imf              = config.get('imf', 'kroupa')
        self.dust_model       = config.get('dust_model', 'calzetti')
        self.dust_type_int    = config.get('dust_type', None)   # integer override from config
        self.config_sfh       = config.get('sfh', 0)
        self.add_neb_emission = config.get('add_neb_emission', False)
        self.distance_mpc     = config.get('distance_mpc', 9.01)  # IC 5332 ~9 Mpc
        self.redshift         = config.get('redshift', 0.0)
        self.mock_mode        = True
        self.ssp              = None
        self.flux_calibration = None

        if self.model_type == 'fsps':
            self._init_fsps()
        elif self.model_type == 'bc03':
            self._init_bc03()

    def set_flux_calibration(self, obs_flux, wavelengths=None):
        """
        Anchor mock model to observed flux level at V-band (or median).
        
        Args:
            obs_flux: Array of observed flux values (Jy)
            wavelengths: Array of wavelengths (Angstroms), used to find V-band
        """
        if wavelengths is not None:
            # Anchor to the band closest to V (5500 Å)
            v_idx = np.argmin(np.abs(wavelengths - 5500.0))
            self.flux_calibration = obs_flux[v_idx]
            print(f"[SSP MODEL] Flux calibration set to {self.flux_calibration:.2e} Jy "
                  f"(V-band @ {wavelengths[v_idx]:.0f} Å)")
        else:
            self.flux_calibration = np.median(obs_flux)
            print(f"[SSP MODEL] Flux calibration set to {self.flux_calibration:.2e} Jy (median)")

    def _init_fsps(self):
        """Initialize FSPS model."""
        try:
            if 'SPS_HOME' not in os.environ:
                print("Warning: SPS_HOME not set — using mock mode.")
                print("  export SPS_HOME=/path/to/fsps")
                self.mock_mode = True
                return

            import fsps
            dust_code = (self.dust_type_int if self.dust_type_int is not None
                         else self._get_dust_code(self.dust_model))
            self.ssp = fsps.StellarPopulation(
                imf_type=self._get_imf_code(self.imf),
                dust_type=dust_code,
                sfh=self.config_sfh,
                add_neb_emission=self.add_neb_emission,
            )
            self.mock_mode = False
            print("✓ FSPS initialized successfully")

        except RuntimeError as e:
            print(f"FSPS initialization failed: {e}")
            self.mock_mode = True
        except ImportError as e:
            print(f"FSPS import failed: {e}")
            print("Install with: pip install fsps")
            self.mock_mode = True

    def _init_bc03(self):
        """Initialize BC03 model (placeholder)."""
        print("BC03 not yet implemented. Using mock mode.")
        self.mock_mode = True

    @staticmethod
    def _get_imf_code(imf_name):
        """Map IMF name or integer to FSPS code."""
        if isinstance(imf_name, int):
            return imf_name
        imf_map = {'salpeter': 0, 'chabrier': 1, 'kroupa': 2}
        return imf_map.get(imf_name.lower(), 2)

    @staticmethod
    def _get_dust_code(dust_name):
        """Map dust model name or integer to FSPS code."""
        if isinstance(dust_name, int):
            return dust_name
        dust_map = {'nodust': 0, 'calzetti': 1, 'mw': 3}
        return dust_map.get(dust_name.lower(), 1)

    def get_magnitudes(self, mass=4.5, age=0.5, metallicity=-0.5,
                       dust=0.0, wavelengths=None):
        """
        Return model fluxes in Jy.

        Parameters
        ----------
        mass        : log10(M/Msun)
        age         : Gyr
        metallicity : log10(Z/Zsun)
        dust        : E(B-V)
        wavelengths : array of wavelengths in Angstroms
        """
        if self.mock_mode:
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)
        else:
            return self._get_fsps_fluxes(mass, age, metallicity, dust, wavelengths)

    def _get_fsps_fluxes(self, mass, age, metallicity, dust=0.0, wavelengths=None):
        """Compute fluxes via FSPS."""
        try:
            mass_msun = 10 ** mass
            self.ssp.params['logzsol'] = metallicity
            self.ssp.params['dust2']   = dust

            # get_spectrum returns (wavelength_aa, L_sun_per_Hz)
            # L_sun_per_Hz is luminosity per Hz per solar mass of stars FORMED
            wav_aa_rest, spec_lsun_hz = self.ssp.get_spectrum(tage=age, peraa=False)
            wav_um_rest = wav_aa_rest / 1e4

            z           = self.redshift
            wav_um_obs  = wav_um_rest * (1 + z)

            # Convert L_sun/Hz (per Msun formed) → erg/s/Hz total
            Lsun_erg_s  = 3.828e33
            pc_cm       = 3.0857e18
            distance_cm = self.distance_mpc * 1e6 * pc_cm

            # spec_lsun_hz is already in Lsun/Hz per 1 Msun formed
            # Multiply by mass to get total luminosity
            lum_erg_s_hz      = spec_lsun_hz * mass_msun * Lsun_erg_s

            # Flux at observer
            flux_erg_s_cm2_hz = lum_erg_s_hz / (4.0 * np.pi * distance_cm**2)
            # Note: no extra (1+z) division for nearby sources (z~0.002)
            flux_jy           = flux_erg_s_cm2_hz * 1e23

            if wavelengths is not None:
                wav_um_input = wavelengths / 1e4          # Å → μm
                valid_idx    = (wav_um_obs > 0) & (flux_jy > 0) & np.isfinite(flux_jy)
                if np.any(valid_idx):
                    sort_idx    = np.argsort(wav_um_obs[valid_idx])
                    wav_sorted  = wav_um_obs[valid_idx][sort_idx]
                    flux_sorted = flux_jy[valid_idx][sort_idx]
                    flux_jy     = np.interp(wav_um_input, wav_sorted, flux_sorted)
                else:
                    flux_jy = np.zeros_like(wavelengths, dtype=float)

            return np.maximum(flux_jy, 1e-30)

        except Exception as e:
            print(f"Error in FSPS calculation: {e}")
            import traceback; traceback.print_exc()
            self.mock_mode = True
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)

    def _get_mock_fluxes(self, mass, age, metallicity, dust=0.0, wavelengths=None):
        """
        Physically motivated mock SSP fluxes for PHANGS HST bands.

        mass        : log10(M/Msun), prior [3, 6]
        age         : Gyr,           prior [0.001, 1.0]
        metallicity : log10(Z/Zsun), prior [-1.5, 0.3]
        dust        : E(B-V),        prior [0.0, 1.0]
        wavelengths : Angstroms
        """
        n_wavelengths = len(wavelengths) if wavelengths is not None else 5

        mass_msun = 10 ** mass
        mass_ref  = 10 ** 4.5       # prior midpoint [3,6]

        # ── Base flux anchored to observed median ──────────────────────────
        if self.flux_calibration is not None:
            base_flux = self.flux_calibration * (mass_msun / mass_ref)
        else:
            base_flux = 1e-6 * (mass_msun / mass_ref)

        # ── Age-dependent M/L scaling (M/L_V ∝ age^0.7) ──────────────────
        age_ml          = max(age, 0.001) ** 0.7
        age_ref_ml      = 0.5 ** 0.7                 # normalise at 500 Myr
        luminosity_factor = age_ref_ml / age_ml      # young clusters brighter

        # ── Metallicity (small effect) ─────────────────────────────────────
        z_factor = 1.0 + 0.05 * metallicity

        if wavelengths is not None:
            wav_um  = wavelengths / 1e4               # Å → μm
            wav_ref = 0.55                            # normalise at V-band

            # Age-dependent UV slope
            age_myr = age * 1e3
            if age_myr < 10:
                beta = -2.5
            elif age_myr < 100:
                beta = -2.5 + 1.0 * np.log10(age_myr / 10)
            else:
                beta = -1.5 + 1.0 * np.log10(age_myr / 100)
            beta = np.clip(beta, -3.0, 0.0)

            wav_factor = (wav_um / wav_ref) ** beta
            v_idx      = np.argmin(np.abs(wav_um - wav_ref))
            wav_factor = wav_factor / wav_factor[v_idx]  # V-band normalised to 1

            # ── Calzetti+00 dust attenuation ──────────────────────────────
            if dust > 0:
                Rv = 4.05
                k_lambda = np.where(
                    wav_um < 0.63,
                    2.659 * (-2.156 + 1.509/wav_um
                             - 0.198/wav_um**2
                             + 0.011/wav_um**3) + Rv,
                    2.659 * (-1.857 + 1.040/wav_um) + Rv
                )
                k_lambda    = np.maximum(k_lambda, 0.0)
                dust_factor = 10 ** (-0.4 * dust * k_lambda)
            else:
                dust_factor = np.ones(len(wavelengths))
        else:
            wav_factor  = np.ones(n_wavelengths)
            dust_factor = np.ones(n_wavelengths)

        fluxes = base_flux * luminosity_factor * z_factor * wav_factor * dust_factor
        return np.maximum(fluxes, 1e-30)