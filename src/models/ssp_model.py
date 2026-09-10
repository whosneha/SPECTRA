import numpy as np
import os
import sys
import warnings
import gzip


class SSPModel:
    """Simple Stellar Population model wrapper."""

    def __init__(self, config):
        self.config           = config            # keep reference for _init_fsps
        self.model_type       = config.get('type', 'fsps')
        self.imf              = config.get('imf', 'kroupa')
        self.dust_model       = config.get('dust_model', 'calzetti')
        self.dust_type_int    = config.get('dust_type', None)   # integer override from config
        self.cf00_slope_ism   = float(config.get('cf00_slope_ism', -0.7))  # C&F ISM slope
        self.add_dust_emission = config.get('add_dust_emission', False)  # energy-balance IR
        self.config_sfh       = config.get('sfh', 0)
        self.add_neb_emission = config.get('add_neb_emission', False)
        self.redshift         = config.get('redshift', 0.0)
        # Distance: explicit config override wins; otherwise for z > 0.05
        # we compute the cosmological luminosity distance, else default to
        # IC 5332's ~9 Mpc for nearby PHANGS-style sources.
        explicit_distance = config.get('distance_mpc', None)
        if explicit_distance is not None:
            self.distance_mpc = float(explicit_distance)
        elif self.redshift > 0.05:
            self.distance_mpc = self._luminosity_distance_mpc(self.redshift)
            print(f"[SSP MODEL] Auto-set luminosity distance: {self.distance_mpc:.1f} Mpc "
                  f"for z={self.redshift:.3f}")
        else:
            self.distance_mpc = 9.01  # IC 5332 ~9 Mpc
        self.mock_mode        = True
        self.ssp              = None
        self.flux_calibration = None

        # BC03-specific state (populated by _init_bc03)
        self.bc03_wav_aa      = None   # 1-D wavelength array (Å)
        self.bc03_ages_gyr    = None   # 1-D age array (Gyr)
        self.bc03_logzsol     = None   # 1-D log10(Z/0.02) array
        self.bc03_grid        = None   # 3-D array (n_met, n_age, n_wav)
        self._bc03_filter_dir = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'filters')
        self._bc03_filter_cache = {}   # band_name → (wav_aa, transmission)

        if self.model_type == 'fsps':
            self._init_fsps()
        elif self.model_type == 'bc03':
            self._init_bc03(config)

    @staticmethod
    def _luminosity_distance_mpc(z, H0=70.0, Om=0.3, Ode=0.7):
        """Flat-ΛCDM luminosity distance in Mpc (no astropy dependency).

        Numerically integrates 1/E(z') from 0 to z with the trapezoidal rule.
        """
        if z <= 0:
            return 0.0
        c_km_s = 2.998e5
        D_H = c_km_s / H0  # Hubble distance ~4283 Mpc

        zp = np.linspace(0.0, z, 2048)
        Ez = np.sqrt(Om * (1.0 + zp) ** 3 + Ode)
        D_C = D_H * np.trapz(1.0 / Ez, zp)   # comoving distance (flat)
        return float(D_C * (1.0 + z))         # luminosity distance

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
                add_neb_emission=False,  # always off; BC03-calibrated nebular added manually
            )
            # For CF00 ISM-only (power-law) dust: slope = -0.7, no birth cloud
            if self.dust_model in ('charlot_fall', 'power_law') or dust_code == 0:
                self.ssp.params['dust_index'] = float(
                    self.config.get('cf00_slope_ism', -0.7)
                )
                self.ssp.params['dust1'] = 0.0   # no extra birth-cloud component
            self.mock_mode = False
            print("✓ FSPS initialized successfully")

        except RuntimeError as e:
            print(f"FSPS initialization failed: {e}")
            self.mock_mode = True
        except ImportError as e:
            print(f"FSPS import failed: {e}")
            print("Install with: pip install fsps")
            self.mock_mode = True

    def _init_bc03(self, config):
        """Load BC03 stellar population grids from ised_ASCII files.

        Config keys
        -----------
        bc03_data_dir : str
            Directory that contains the BC03 ``.ised_ASCII`` files.  The
            standard Bruzual & Charlot (2003) distribution produces files
            named like::

                bc2003_lr_m62_chab_ssp.ised_ASCII

            The ``lr`` / ``hr`` tag selects the spectral resolution, ``m**``
            the metallicity bin, and ``chab`` / ``krou`` / ``salp`` the IMF.
            All six metallicity files for the chosen IMF must be present.

        bc03_resolution : str, optional
            ``'lr'`` (low-res, default) or ``'hr'`` (high-res).
        """
        data_dir = config.get('bc03_data_dir', None) or os.environ.get('BC03_DATA_DIR')
        if not data_dir:
            warnings.warn(
                "BC03 requires 'bc03_data_dir' in ssp_model config (or BC03_DATA_DIR "
                "environment variable) pointing to the directory with *.ised_ASCII files. "
                "Falling back to mock mode.",
                UserWarning,
                stacklevel=3,
            )
            self.mock_mode = True
            return

        data_dir = os.path.expanduser(data_dir)
        if not os.path.isdir(data_dir):
            warnings.warn(
                f"BC03 data directory not found: {data_dir!r}. "
                "Falling back to mock mode.",
                UserWarning,
                stacklevel=3,
            )
            self.mock_mode = True
            return

        resolution = str(config.get('bc03_resolution', 'lr')).lower()
        imf_tag = {'salpeter': 'salp', 'chabrier': 'chab', 'kroupa': 'krou'}.get(
            self.imf.lower(), 'chab')

        # ── Fast path: load from preprocessed clean-grid cache ────────────
        # Users build this cache once by running:
        #   python -m src.utils.bc03_preprocess --data-dir <path> --imf <imf> --resolution <res>
        # The cache removes Wolf-Rayet spike artefacts that corrupt fits when
        # using the raw .ised_ASCII files directly (analogous to CIGALE's
        # database_builder preprocessing step).
        _data_dir_pkg = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'data'))
        _cache_name  = f'bc03_{resolution}_{imf_tag}_clean_grid.npz'
        _cache_path  = os.path.join(_data_dir_pkg, _cache_name)

        if os.path.isfile(_cache_path):
            try:
                d = np.load(_cache_path)
                self.bc03_wav_aa   = d['wav_aa'].astype(np.float64)
                self.bc03_ages_gyr = d['ages_gyr'].astype(np.float64)
                self.bc03_logzsol  = d['logzsol'].astype(np.float64)
                self.bc03_grid     = d['grid'].astype(np.float64)
                self.mock_mode     = False
                print(f"✓ BC03 loaded from preprocessed cache: {_cache_name}")
                print(f"  {len(self.bc03_logzsol)} metallicities, "
                      f"{len(self.bc03_ages_gyr)} ages, "
                      f"{len(self.bc03_wav_aa)} wavelengths "
                      f"(IMF={self.imf}, res={resolution})")
                return
            except Exception as _e:
                warnings.warn(
                    f"Failed to load BC03 preprocessed cache ({_e}). "
                    "Falling back to raw .ised_ASCII files.",
                    UserWarning,
                    stacklevel=3,
                )
        else:
            warnings.warn(
                f"\n"
                f"  No preprocessed BC03 cache found at:\n"
                f"    {_cache_path}\n"
                f"\n"
                f"  Loading raw .ised_ASCII files which contain Wolf-Rayet spike\n"
                f"  artefacts that can cause poor SED fits (chi²/DOF >> 1).\n"
                f"\n"
                f"  Run the preprocessor ONCE to build a clean cache:\n"
                f"    python -m src.utils.bc03_preprocess \\\n"
                f"        --data-dir \"{data_dir}\" \\\n"
                f"        --imf {self.imf} --resolution {resolution}\n"
                f"\n"
                f"  After that, BC03 fitting will be reliable.\n",
                UserWarning,
                stacklevel=3,
            )

        # ── Slow / raw-file path (falls through if no cache) ──────────────
        # BC03 metallicity grids used by different package variants.
        # Legacy bundles often use m22..m72, while official Padova bundles
        # use m122..m172 for the same metallicity values.
        legacy_tags = {
            'm22': np.log10(0.0001 / 0.02),
            'm32': np.log10(0.0004 / 0.02),
            'm42': np.log10(0.004  / 0.02),
            'm52': np.log10(0.008  / 0.02),
            'm62': np.log10(0.02   / 0.02),
            'm72': np.log10(0.05   / 0.02),
        }
        padova_tags = {
            'm122': np.log10(0.0001 / 0.02),
            'm132': np.log10(0.0004 / 0.02),
            'm142': np.log10(0.004  / 0.02),
            'm152': np.log10(0.008  / 0.02),
            'm162': np.log10(0.02   / 0.02),
            'm172': np.log10(0.05   / 0.02),
        }

        def _resolve_bc03_file(mtag):
            base = f"bc2003_{resolution}_{mtag}_{imf_tag}_ssp.ised_ASCII"
            p_ascii = os.path.join(data_dir, base)
            p_gz    = p_ascii + '.gz'
            if os.path.isfile(p_ascii):
                return p_ascii
            if os.path.isfile(p_gz):
                return p_gz
            return None

        # Try legacy naming first, then official Padova naming.
        selected_tags = None
        resolved_paths = None
        for tag_set in (legacy_tags, padova_tags):
            trial = {mtag: _resolve_bc03_file(mtag) for mtag in tag_set}
            if all(v is not None for v in trial.values()):
                selected_tags = tag_set
                resolved_paths = trial
                break

        if selected_tags is None:
            warnings.warn(
                "BC03 files not found for expected metallicity grids. "
                "Checked m22..m72 and m122..m172 with .ised_ASCII(.gz). "
                "Falling back to mock mode.",
                UserWarning,
                stacklevel=3,
            )
            self.mock_mode = True
            return

        grids   = []
        logzsol = []
        wav_aa  = None
        ages_gyr = None

        for mtag, lz in sorted(selected_tags.items(), key=lambda x: x[1]):
            fpath = resolved_paths[mtag]
            w, a, g = self._load_bc03_grid(fpath)
            if wav_aa is None:
                wav_aa   = w
                ages_gyr = a
            grids.append(g)
            logzsol.append(lz)

        self.bc03_wav_aa   = wav_aa
        self.bc03_ages_gyr = ages_gyr
        self.bc03_logzsol  = np.array(logzsol)
        self.bc03_grid     = np.array(grids)   # (n_met, n_age, n_wav)
        self.mock_mode     = False
        print(f"✓ BC03 initialized: {len(logzsol)} metallicities, "
              f"{len(ages_gyr)} ages, {len(wav_aa)} wavelengths "
              f"(IMF={self.imf}, res={resolution})")

    @staticmethod
    def _load_bc03_grid(filepath):
        """Parse a BC03 ``*.ised_ASCII`` file.

        Returns
        -------
        wav_aa : ndarray, shape (N_lambda,)
            Wavelengths in Angstroms.
        ages_gyr : ndarray, shape (N_age,)
            Ages in Gyr.
        grid : ndarray, shape (N_age, N_lambda)
            Specific luminosity in L_sun / Å per solar mass formed.
        """
        opener = gzip.open if filepath.endswith('.gz') else open
        with opener(filepath, 'rt', errors='replace') as fh:
            raw = fh.read()

        tokens = raw.split()
        idx = 0

        # ── 1. Number of age steps ────────────────────────────────────────
        n_ages = int(tokens[idx]); idx += 1

        # ── 2. Age array (years) ──────────────────────────────────────────
        ages_yr = np.array([float(tokens[idx + i]) for i in range(n_ages)])
        idx += n_ages
        ages_gyr = ages_yr / 1e9

        # ── 3. Locate wavelength block ─────────────────────────────────────
        # Real BC03 bundles include metadata between age and wavelength arrays.
        # We detect the wavelength block as an integer N followed by N strictly
        # increasing positive values (wavelengths in Å).
        n_tok = len(tokens)
        n_wav = None
        wav_start = None
        scan_start = idx
        scan_stop = min(n_tok - 32, idx + 5000)
        for j in range(scan_start, scan_stop):
            t = tokens[j]
            try:
                cand = int(float(t))
            except ValueError:
                continue
            if cand < 100 or cand > 20000:
                continue
            if j + 1 + cand >= n_tok:
                continue
            try:
                vals = np.array([float(x) for x in tokens[j + 1:j + 1 + cand]], dtype=float)
            except ValueError:
                continue
            if np.all(np.isfinite(vals)) and np.all(vals > 0) and np.all(np.diff(vals) > 0):
                n_wav = cand
                wav_start = j + 1
                break

        if n_wav is None or wav_start is None:
            raise ValueError(f"Could not locate wavelength grid in BC03 file: {filepath}")

        wav_aa = np.array([float(tokens[wav_start + i]) for i in range(n_wav)], dtype=float)
        idx = wav_start + n_wav

        # ── 4. Spectra: one block per age, each with N_wav points ─────────
        # BC03 files encode each spectrum as: [N_wav] [flux_1 ... flux_N_wav]
        grid = np.empty((n_ages, n_wav), dtype=np.float64)
        for i in range(n_ages):
            if idx >= n_tok:
                raise ValueError(f"Unexpected end-of-file while reading BC03 spectra: {filepath}")

            # Some files include a block-length marker equal to N_wav.
            try:
                marker = int(float(tokens[idx]))
            except ValueError:
                marker = None
            if marker == n_wav:
                idx += 1

            if idx + n_wav > n_tok:
                raise ValueError(f"Incomplete BC03 spectrum block in file: {filepath}")

            grid[i] = np.array([float(tokens[idx + j]) for j in range(n_wav)], dtype=float)
            idx += n_wav

        return wav_aa, ages_gyr, grid

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
        dust_map = {
            'nodust': 0,
            'charlot_fall': 0,   # power-law τ ∝ λ^dust_index; use dust_index=-0.7
            'power_law': 0,
            'calzetti': 2,
            'mw': 3,
        }
        return dust_map.get(dust_name.lower(), 2)

    def get_magnitudes(self, mass=4.5, age=0.5, metallicity=-0.5,
                       dust=0.0, lya_ew=0.0, wavelengths=None, **kwargs):
        """
        Return model fluxes in Jy.

        Parameters
        ----------
        mass        : log10(M/Msun)
        age         : Gyr
        metallicity : log10(Z/Zsun)
        dust        : E(B-V)
        lya_ew      : rest-frame Lyα equivalent width (Å), added as a
                      Gaussian emission line at rest 1215.67 Å
        wavelengths : array of wavelengths in Angstroms
        """
        if self.mock_mode:
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)
        elif self.model_type == 'bc03':
            return self._get_bc03_fluxes(mass, age, metallicity, dust,
                                         wavelengths=wavelengths)
        else:
            return self._get_fsps_fluxes(mass, age, metallicity, dust,
                                         wavelengths=wavelengths,
                                         lya_ew=lya_ew)

    def _add_lyalpha_line(self, flux_jy, wav_um_obs, lya_ew_rest_aa, z,
                          fwhm_rest_aa=10.0):
        """Add a Lyα emission line to an observed-frame Jy spectrum.

        Parameters
        ----------
        flux_jy : array
            Continuum flux density in Jy at observed wavelengths `wav_um_obs`.
        wav_um_obs : array
            Observed wavelengths (μm), assumed sorted ascending.
        lya_ew_rest_aa : float
            Rest-frame equivalent width of Lyα (Å). Positive = emission.
        z : float
            Source redshift.
        fwhm_rest_aa : float
            Rest-frame FWHM of the line (Å); broadened-LBG default 10 Å.

        Returns
        -------
        flux_jy_with_line : array
            Same shape as input, with Gaussian Lyα added (line flux conserved
            across rest ↔ observed frames).
        """
        lam_lya_rest_aa = 1215.67
        lam_lya_obs_aa  = lam_lya_rest_aa * (1.0 + z)
        sigma_obs_aa    = (fwhm_rest_aa / 2.355) * (1.0 + z)
        c_aa_s          = 2.998e18  # speed of light in Å/s

        wav_obs_aa = wav_um_obs * 1e4

        # Continuum f_λ at observed Lyα wavelength (erg/s/cm²/Å).
        cont_jy        = float(np.interp(lam_lya_obs_aa, wav_obs_aa, flux_jy))
        cont_fnu_cgs   = cont_jy * 1e-23
        cont_flam_obs  = cont_fnu_cgs * c_aa_s / (lam_lya_obs_aa ** 2)
        # De-redshift continuum to rest frame for EW interpretation.
        cont_flam_rest = cont_flam_obs * (1.0 + z)

        # Total integrated line flux (erg/s/cm²) — conserved across frames.
        line_flux_total = lya_ew_rest_aa * cont_flam_rest

        # Normalised Gaussian in observed wavelength → observed f_λ.
        gauss = (1.0 / (np.sqrt(2.0 * np.pi) * sigma_obs_aa)) * \
                np.exp(-0.5 * ((wav_obs_aa - lam_lya_obs_aa) / sigma_obs_aa) ** 2)
        flam_line_obs = line_flux_total * gauss   # erg/s/cm²/Å

        # Convert added f_λ contribution back to f_ν in Jy.
        fnu_line_jy = flam_line_obs * (wav_obs_aa ** 2) / c_aa_s * 1e23
        return flux_jy + fnu_line_jy

    def _get_fsps_fluxes(self, mass, age, metallicity, dust=0.0,
                         wavelengths=None, lya_ew=0.0):
        """Compute fluxes via FSPS."""
        try:
            mass_msun = 10 ** mass
            self.ssp.params['logzsol'] = metallicity
            self.ssp.params['dust2']   = dust
            # Ensure birth-cloud component stays zero for CF00 ISM-only mode
            if self.dust_model in ('charlot_fall', 'power_law'):
                self.ssp.params['dust1'] = 0.0

            # get_spectrum returns (wavelength_aa, L_sun_per_Hz)
            # L_sun_per_Hz is luminosity per Hz per solar mass of stars FORMED
            wav_aa_rest, spec_lsun_hz = self.ssp.get_spectrum(tage=age, peraa=False)
            wav_um_rest = wav_aa_rest / 1e4

            # ── Add BC03-calibrated nebular emission ──────────────────────
            # FSPS MILES stellar library gives 2-3× stronger Lyman continuum
            # than BC03 BaSeL-3.1 → too much Hα in F606W → optimizer finds
            # wrong (old) ages.  Instead we use the CIGALE-calibrated Q_H
            # lookup table (from Leitherer+1999 BC03 track) which gives the
            # correct (weaker) nebular scaling that CIGALE uses.
            if self.add_neb_emission:
                c_aa_s_local = 2.998e18   # speed of light in Å/s
                # L_sun/Hz → L_sun/Å per Msun (rest frame)
                _spec_lsun_aa = spec_lsun_hz * c_aa_s_local / np.maximum(wav_aa_rest, 1.0) ** 2
                _spec_lsun_aa = self._add_nebular_bc03(_spec_lsun_aa, wav_aa_rest, age)
                # L_sun/Å → L_sun/Hz per Msun (back)
                spec_lsun_hz = _spec_lsun_aa * np.maximum(wav_aa_rest, 1.0) ** 2 / c_aa_s_local

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

            # Add Lyα emission line if requested (operates on the dense
            # FSPS-native grid so np.interp captures the line correctly).
            if lya_ew and lya_ew > 0:
                flux_jy = self._add_lyalpha_line(flux_jy, wav_um_obs,
                                                 lya_ew_rest_aa=float(lya_ew),
                                                 z=z)

            if wavelengths is not None:
                # Use the same filter-convolution path as BC03 so emission lines
                # (Hα in F606W, Paα in F200W, etc.) are properly included.
                # wav_aa_obs is the observer-frame SED wavelength grid.
                wav_aa_obs_full = wav_um_obs * 1e4   # μm → Å
                out = np.empty(len(wavelengths), dtype=float)
                for i, pivot in enumerate(wavelengths):
                    out[i] = self._convolve_filter(wav_aa_obs_full, flux_jy, float(pivot))
                flux_jy = out
            else:
                pass  # return full SED unchanged

            return np.maximum(flux_jy, 1e-30)

        except Exception as e:
            print(f"Error in FSPS calculation: {e}")
            import traceback; traceback.print_exc()
            self.mock_mode = True
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)

    def _get_bc03_fluxes(self, mass, age, metallicity, dust=0.0, wavelengths=None):
        """Compute fluxes from the loaded BC03 grid.

        Parameters
        ----------
        mass        : log10(M/Msun)
        age         : Gyr
        metallicity : log10(Z/Zsun)  (same convention as FSPS logzsol)
        dust        : E(B-V) — Calzetti+00 attenuation applied
        wavelengths : observed-frame wavelengths in Angstroms to interpolate onto
        """
        try:
            from scipy.interpolate import RegularGridInterpolator

            mass_msun = 10.0 ** mass

            # ── 1. Bilinear interpolation over age and metallicity ────────
            log_age      = np.log10(max(age, 1e-4))
            log_ages_gyr = np.log10(np.clip(self.bc03_ages_gyr, 1e-4, None))
            met_arr      = self.bc03_logzsol   # already log10(Z/Zsun)

            # Clamp to grid bounds
            log_age_clamp = np.clip(log_age, log_ages_gyr[0], log_ages_gyr[-1])
            met_clamp     = np.clip(metallicity, met_arr[0], met_arr[-1])

            # Build (n_met, n_age) grid for each wavelength pixel using
            # RegularGridInterpolator — this handles the 2-D interpolation.
            # grid shape: (n_met, n_age, n_wav)
            interp = RegularGridInterpolator(
                (met_arr, log_ages_gyr),
                self.bc03_grid,           # (n_met, n_age, n_wav)
                method='linear',
                bounds_error=False,
                fill_value=None,
            )
            spec_lsun_aa = interp([[met_clamp, log_age_clamp]])[0]  # (n_wav,)

            wav_aa_rest = self.bc03_wav_aa   # Angstroms, rest frame

            # ── 1b. NIR taper: BC03 LR BaSeL-3.1 artifact correction ─────
            # BC03 LR BaSeL-3.1 stellar atmospheres produce 50–750× too much
            # NIR flux at certain age steps (e.g. 7 Myr, 50 Myr) where the
            # optical SED is near-zero while F277W/F356W is enormous.
            # CIGALE corrects this in its database_builder preprocessing.
            # We apply the same: clamp L_λ beyond 25000 Å (2.5 μm) to a R-J
            # tail anchored at the optical peak in 4000–9000 Å.
            # C_rj = 0.058 calibrated so clamped BC03 F356W at 5 Myr,
            # solar Z, 12100 Msun → ~62 nJy at D=94 Mpc (matches CIGALE).
            # Boundary at 25000 Å preserves BC03 F150W/F200W stellar emission.
            _nir_mask = wav_aa_rest > 25000.0
            if np.any(_nir_mask):
                _opt_L = np.where(
                    (wav_aa_rest >= 4000.0) & (wav_aa_rest <= 9000.0),
                    spec_lsun_aa, 0.0)
                _iw_pk  = int(np.argmax(_opt_L))
                _lam_pk = wav_aa_rest[_iw_pk]
                _L_pk   = spec_lsun_aa[_iw_pk]
                if _L_pk > 0:
                    _rj_lim = 0.057 * _L_pk * (_lam_pk / wav_aa_rest) ** 4
                    spec_lsun_aa = np.where(
                        _nir_mask,
                        np.minimum(spec_lsun_aa, np.maximum(_rj_lim, 1e-60)),
                        spec_lsun_aa,
                    )

            # ── 2a. Nebular emission (mirrors CIGALE [[nebular]] module) ──
            if self.add_neb_emission:
                spec_lsun_aa = self._add_nebular_bc03(spec_lsun_aa, wav_aa_rest, age)

            # ── 2b. Save pre-attenuation SED for energy balance ────────────
            # Used by Dale 2014 dust emission if add_dust_emission=True
            spec_lsun_aa_unatt = spec_lsun_aa.copy()

            # ── 2c. Scale to total stellar mass ───────────────────────────
            # BC03 spectra are in L_sun/Å per 1 M_sun formed
            Lsun_erg_s  = 3.828e33
            lum_erg_s_aa = spec_lsun_aa * mass_msun * Lsun_erg_s   # erg/s/Å

            # ── 3. Redshift and convert to Jy ─────────────────────────────
            z           = self.redshift
            wav_aa_obs  = wav_aa_rest * (1.0 + z)

            pc_cm        = 3.0857e18
            distance_cm  = self.distance_mpc * 1e6 * pc_cm
            c_aa_s       = 2.998e18   # speed of light in Å/s

            # f_ν [erg/s/cm²/Hz] = f_λ [erg/s/Å] * λ² / c   (per unit solid angle)
            # Observer-frame f_λ gains a (1+z) from bandwidth compression and
            # loses a (1+z) from photon energy → net (1+z)^0 for bolometric,
            # but for f_ν: f_ν_obs = f_λ_rest * λ_rest² / c / (1+z)
            flux_erg_s_cm2_aa = lum_erg_s_aa / (4.0 * np.pi * distance_cm ** 2)
            flux_erg_s_cm2_nu = flux_erg_s_cm2_aa * (wav_aa_obs ** 2) / (c_aa_s * (1.0 + z))
            flux_jy           = flux_erg_s_cm2_nu * 1e23

            # ── 4. Dust attenuation ────────────────────────────────────────
            if dust > 0:
                if self.dust_model == 'charlot_fall':
                    # Charlot & Fall (2000) ISM power law with mu=1 (ISM-only).
                    # dust = A_V in magnitudes — directly matches CIGALE Av_ISM.
                    # A_λ = A_V * (λ_rest / 5500 Å)^slope_ISM
                    # Applied in rest frame (λ_rest) as physically correct.
                    A_lambda  = dust * (wav_aa_rest / 5500.0) ** self.cf00_slope_ism
                    A_lambda  = np.maximum(A_lambda, 0.0)
                    flux_jy   = flux_jy * 10.0 ** (-0.4 * A_lambda)
                else:
                    # Calzetti+00 (default for backwards compatibility).
                    # dust = E(B-V); A_V = 4.05 * dust.
                    wav_um    = wav_aa_obs / 1e4
                    Rv        = 4.05
                    k_lam     = np.where(
                        wav_um < 0.63,
                        2.659 * (-2.156 + 1.509 / wav_um
                                 - 0.198 / wav_um ** 2
                                 + 0.011 / wav_um ** 3) + Rv,
                        2.659 * (-1.857 + 1.040 / wav_um) + Rv,
                    )
                    k_lam     = np.maximum(k_lam, 0.0)
                    flux_jy   = flux_jy * 10.0 ** (-0.4 * dust * k_lam)

            # ── 4c. Energy-balance dust emission (Dale 2014 alpha=2.0) ─────
            # Absorbed stellar light is re-emitted in the IR following the
            # Dale et al. (2014) SED template.  Key observable effects:
            #   • PAH 3.3 μm → JWST F356W at z=0.02
            #   • Hot stochastic VSG continuum (T~800 K) → F277W / F356W
            # Matches CIGALE's [[dustatt_modified_CF00]] + [[dale2014]] modules.
            if self.add_dust_emission and dust > 0:
                dale_jy = self._dale2014_emission(
                    spec_lsun_aa_unatt, wav_aa_rest, wav_aa_obs,
                    dust, mass_msun, distance_cm, c_aa_s, z)
                flux_jy = flux_jy + dale_jy

            # ── 4b. Global spike clip for BC03 WR emission artifacts ──────
            # BC03 `.ised_ASCII` SEDs contain Wolf-Rayet emission spikes
            # (Na D at 5890 Å, other WR features) that are 10^4× brighter
            # than the continuum.  CIGALE handles these by subtracting the
            # WR contribution before broadband integration.  Here we apply a
            # robust running-median replacement: any pixel >20× the local
            # 51-pixel median is replaced by that median.
            from scipy.ndimage import median_filter as _mf
            f_smooth = _mf(flux_jy, size=51, mode='reflect')
            spike_mask = flux_jy > 20.0 * np.maximum(f_smooth, 1e-60)
            if np.any(spike_mask):
                flux_jy = np.where(spike_mask, f_smooth, flux_jy)

            # ── 5. Interpolate / convolve onto requested wavelengths ──────
            if wavelengths is not None:
                # Use filter-convolution to avoid WR-line artifacts in BC03.
                # For each requested pivot wavelength, integrate the SED
                # through the filter transmission curve if the file is cached.
                out = np.empty(len(wavelengths), dtype=float)
                for i, pivot in enumerate(wavelengths):
                    out[i] = self._convolve_filter(wav_aa_obs, flux_jy, float(pivot))
                flux_jy = out
            else:
                flux_jy = flux_jy   # full SED (no change)

            return np.maximum(flux_jy, 1e-30)

        except Exception as e:
            print(f"Error in BC03 calculation: {e}")
            import traceback; traceback.print_exc()
            return self._get_mock_fluxes(mass, age, metallicity, dust, wavelengths)

    @staticmethod
    def _q_H_per_msun(age_gyr):
        """Return Q(H) [photons/s per Msun formed] for a BC03 Chabrier IMF SSP.

        BC03 `.ised_ASCII` files severely underestimate the Lyman-continuum
        flux (known stellar-atmosphere limitation).  CIGALE uses a separate
        Q_H lookup table instead of integrating the tabulated SED.  We
        reproduce that approach here using the published STARBURST99 /
        BC03-calibrated values for an instantaneous burst with Chabrier IMF
        and solar metallicity (Leitherer et al. 1999; Bruzual & Charlot 2003).

        Ages are in Gyr; Q_H drops to ≈ 0 beyond ~25 Myr.
        """
        # Table: (age_Myr, log10(Q_H/Msun) [s^-1])
        # Source: Leitherer et al. 1999 Table 7 instantaneous burst,
        #         Chabrier-equivalent IMF, Z=0.02
        _age_myr = np.array([  0.5,   1.0,   2.0,   3.0,   5.0,
                                7.0,  10.0,  12.0,  15.0,  20.0,  25.0])
        _log_qh  = np.array([ 47.0,  46.9,  46.9,  46.8,  46.7,
                               46.6,  46.2,  45.5,  44.5,  43.0,  41.5])

        age_myr = age_gyr * 1e3
        if age_myr > 25.0:
            return 0.0
        log_qh = float(np.interp(age_myr, _age_myr, _log_qh))
        return 10.0 ** log_qh

    @staticmethod
    def _add_nebular_bc03(spec_lsun_aa, wav_aa_rest, age_gyr):
        """Add Case-B recombination nebular emission to a BC03 stellar spectrum.

        Replicates CIGALE's [[nebular]] module:
          1. Get Q(H) from a calibrated STARBURST99 lookup table (NOT from
             integrating the BC03 Lyman continuum — those values are wrong).
          2. Scale Balmer/Paschen/Brackett lines + Balmer continuum to Q(H).
          3. Return stellar + nebular spectrum in the same L_sun/Å units.

        Line ratios are for Case B, T=10^4 K, Z=0.02 (solar), logU=-2.0
        matching Aromal et al. 2025 / pcigale.ini settings.
        Only significant for age < 25 Myr when O/B stars dominate.
        """
        # No ionizing photons for old populations
        if age_gyr > 0.025:
            return spec_lsun_aa.copy()

        Lsun    = 3.828e33    # solar luminosity  (erg/s)

        # ── 1. Q(H) from STARBURST99-calibrated lookup table ─────────────
        Q_H = SSPModel._q_H_per_msun(age_gyr)
        if Q_H <= 0.0:
            return spec_lsun_aa.copy()

        # ── 2. Hβ luminosity (Case B, αeff/αB = 0.119) ───────────────────
        L_Hb_erg = 4.76e-13 * Q_H          # erg/s
        L_Hb     = L_Hb_erg / Lsun         # L_sun

        # ── 3. Emission line ratios relative to Hβ ───────────────────────
        # Source: Hummer & Storey (1987) + Cloudy grid (logU=-2, Z=0.02)
        lines = {
            3727:  1.30,   # [O II] 3727 Å  (doublet)
            3869:  0.26,   # [Ne III] 3869 Å
            4102:  0.259,  # Hδ
            4340:  0.468,  # Hγ
            4861:  1.000,  # Hβ  (reference)
            4959:  0.350,  # [O III] 4959 Å
            5007:  1.000,  # [O III] 5007 Å
            6563:  2.860,  # Hα
            6584:  0.300,  # [N II] 6584 Å
            9069:  0.100,  # [S III] 9069 Å
            9532:  0.260,  # [S III] 9532 Å
            10830: 0.060,  # He I 10830 Å
            12818: 0.162,  # Paβ
            18751: 0.332,  # Paα  ← important for JWST F200W
            26252: 0.056,  # Brα
        }

        neb = np.zeros_like(spec_lsun_aa)

        # ── 4. Balmer continuum (λ = 3646–10000 Å) ────────────────────────
        # Simplified power-law approximation; amplitude ≈ 0.15 * L(Hβ) per Å
        bc_mask = (wav_aa_rest >= 3646.0) & (wav_aa_rest <= 10000.0)
        if np.any(bc_mask):
            dw = np.gradient(wav_aa_rest[bc_mask])
            dw = np.maximum(dw, 1.0)
            # Total Balmer continuum luminosity ≈ 0.15 * L(Hβ)
            # Distribute uniformly over the range as a rough approximation
            n_bc  = np.sum(bc_mask)
            width = wav_aa_rest[bc_mask].max() - wav_aa_rest[bc_mask].min()
            neb[bc_mask] += 0.15 * L_Hb / max(width, 1.0)

        # ── 5. Emission lines as narrow Gaussians ─────────────────────────
        # σ = 300 km/s (matching CIGALE lines_width=300.0)
        sigma_frac = 300.0 / 2.998e5   # Δλ/λ for 300 km/s
        for wl_rest, ratio in lines.items():
            L_line  = L_Hb * ratio                  # L_sun
            sigma_aa = wl_rest * sigma_frac          # Å
            gauss    = np.exp(-0.5 * ((wav_aa_rest - wl_rest) / sigma_aa) ** 2)
            norm     = np.sqrt(2.0 * np.pi) * sigma_aa
            neb     += L_line * gauss / norm         # L_sun/Å

        return spec_lsun_aa + neb

    # ── Dale 2014 energy-balance dust emission ────────────────────────────

    def _dale2014_emission(self, spec_lsun_aa_per_msun, wav_aa_rest, wav_aa_obs,
                           dust, mass_msun, distance_cm, c_aa_s, z):
        """Simplified Dale et al. (2014) energy-balance IR dust emission.

        Reproduces CIGALE's ``dale2014`` + ``dustatt_modified_CF00`` energy-
        balance principle: UV/optical light absorbed by dust is re-emitted
        in the IR following the Dale 2014 alpha=2.0 SED template.

        Two components are implemented (the ones observable in JWST NIR at
        z≈0.02 with the Aromal et al. 2025 filter set):

        1.  **PAH 3.3 μm** — Polycyclic aromatic hydrocarbon C-H stretch.
            Falls in JWST F356W at z=0.02.  Gaussian with λ₀=3.29 μm,
            FWHM=0.048 μm.  Luminosity ≈ 0.8 % of L_dust (Smith et al. 2007,
            ApJ 656, 770 — normal star-forming galaxies, α≈2).

        2.  **Hot stochastic VSG continuum** (T≈800 K) — Very small grains
            stochastically heated by single UV photons (Draine & Li 2001,
            ApJ 551, 807).  Modified blackbody peaking at ~3.6 μm.
            Contributes to F277W and F356W.  Fraction ≈ 3 % of L_dust in the
            1–10 μm window.

        The bulk of the absorbed energy is re-emitted in the FIR (50–200 μm)
        and does not affect the JWST NIR photometry; those components are
        therefore omitted for efficiency.

        Parameters
        ----------
        spec_lsun_aa_per_msun : ndarray
            Pre-attenuation SED (stellar + nebular) in L_sun/Å per 1 M_sun.
        wav_aa_rest : ndarray  Wavelengths in Å (rest frame).
        wav_aa_obs  : ndarray  Wavelengths in Å (observed frame).
        dust        : float    A_V (mag) for C&F law or E(B-V) for Calzetti.
        mass_msun   : float    Total stellar mass (M_sun).
        distance_cm : float    Luminosity distance (cm).
        c_aa_s      : float    Speed of light (Å/s).
        z           : float    Redshift.

        Returns
        -------
        flux_dust_jy : ndarray
            Dust emission SED in Jy at ``wav_aa_obs`` wavelengths.
        """
        Lsun_erg_s = 3.828e33

        # ── 1. Absorbed luminosity via energy balance ─────────────────────
        # A_λ in magnitudes using the appropriate dust law.
        if self.dust_model == 'charlot_fall':
            A_lam = dust * (wav_aa_rest / 5500.0) ** self.cf00_slope_ism
        else:
            # Calzetti: A_λ = k_λ × E(B-V)
            wav_um = wav_aa_obs / 1e4
            Rv = 4.05
            k_lam = np.where(
                wav_um < 0.63,
                2.659 * (-2.156 + 1.509/wav_um - 0.198/wav_um**2 + 0.011/wav_um**3) + Rv,
                2.659 * (-1.857 + 1.040/wav_um) + Rv,
            )
            A_lam = np.maximum(k_lam, 0.0) * dust

        A_lam    = np.maximum(A_lam, 0.0)
        abs_frac = 1.0 - 10.0 ** (-0.4 * A_lam)   # fraction absorbed per λ

        # L_dust [L_sun] = ∫ L_λ_unatt(per Msun) × abs_frac dλ × total Msun
        L_dust_lsun = (float(np.trapz(spec_lsun_aa_per_msun * abs_frac, wav_aa_rest))
                       * mass_msun)
        if L_dust_lsun <= 0:
            return np.zeros_like(wav_aa_rest)

        # ── 2. Dale 2014 IR SED (two components affecting JWST NIR) ──────
        dust_sed_lsun_aa = np.zeros_like(wav_aa_rest, dtype=float)

        # Component A: PAH 3.3 μm feature (Smith et al. 2007, Table 3 mean)
        # L(3.3 μm PAH) / L_TIR ≈ 0.8 % for normal SFGs (α ≈ 2)
        L_PAH33     = 0.008 * L_dust_lsun       # L_sun
        lam0_33     = 32900.0                    # Å  (3.29 μm)
        sigma_33    = 480.0 / 2.355              # Å  (FWHM 0.048 μm → σ≈204 Å)
        gauss_33    = np.exp(-0.5 * ((wav_aa_rest - lam0_33) / sigma_33) ** 2)
        dust_sed_lsun_aa += (L_PAH33 / (np.sqrt(2.0 * np.pi) * sigma_33)) * gauss_33

        # Component B: hot VSG continuum (T=800 K modified blackbody)
        # Peaks at ~3.6 μm in L_λ; dominates 2–5 μm in the Dale 2014 SED.
        # Fraction ≈ 3 % of L_dust re-emitted in the 1–10 μm window.
        h_si  = 6.626e-34    # J·s
        c_si  = 2.998e8      # m/s
        k_si  = 1.381e-23    # J/K
        T_vsg = 800.0        # K
        wav_m = wav_aa_rest * 1e-10
        x_vsg = np.clip(h_si * c_si / (wav_m * k_si * T_vsg), 0.0, 700.0)
        bb_vsg = (1.0 / wav_aa_rest ** 5) / (np.expm1(x_vsg) + 1e-300)  # B_λ shape

        # Normalise so that ∫ B_λ dλ (1–10 μm) = 1 L_sun/Å
        mask_nir = (wav_aa_rest >= 1e4) & (wav_aa_rest <= 1e5)
        if np.any(mask_nir):
            bb_norm = np.trapz(bb_vsg[mask_nir], wav_aa_rest[mask_nir])
            if bb_norm > 0:
                dust_sed_lsun_aa += (0.030 * L_dust_lsun) * bb_vsg / bb_norm

        # ── 3. Convert to observed-frame f_ν (Jy) ─────────────────────────
        flux_dust_erg_cm2_aa = (dust_sed_lsun_aa * Lsun_erg_s
                                / (4.0 * np.pi * distance_cm ** 2))
        flux_dust_erg_cm2_nu = (flux_dust_erg_cm2_aa * wav_aa_obs ** 2
                                / (c_aa_s * (1.0 + z)))
        flux_dust_jy = flux_dust_erg_cm2_nu * 1e23
        return np.maximum(flux_dust_jy, 0.0)

    # ── Filter-convolution helpers ────────────────────────────────────────

    # Map pivot wavelength (Å, rounded) → filter filename stem.
    # Populated from SVO filter files in src/data/filters/.
    _FILTER_MAP = {
        3350: 'HST_WFC3_F336W',
        4380: 'HST_WFC3_F438W',
        5470: 'HST_WFC3_F547M',
        6060: 'HST_WFC3_F606W',
        8140: 'HST_WFC3_F814W',
        9020: 'JWST_NIRCam_F090W',
        15010: 'JWST_NIRCam_F150W',
        19890: 'JWST_NIRCam_F200W',
        27620: 'JWST_NIRCam_F277W',
        35680: 'JWST_NIRCam_F356W',
    }

    def _load_filter(self, pivot_aa):
        """Return (wav_aa, transmission) for the filter nearest to pivot_aa.

        Looks up the filter filename from _FILTER_MAP, reads the SVO ASCII
        file, and caches the result. Returns None if no file is found.
        """
        # Find the closest registered pivot
        pivots = np.array(list(self._FILTER_MAP.keys()))
        best   = pivots[np.argmin(np.abs(pivots - pivot_aa))]
        if abs(best - pivot_aa) > 200:   # outside known filter pivots → skip
            return None
        name = self._FILTER_MAP[best]
        if name in self._bc03_filter_cache:
            return self._bc03_filter_cache[name]

        fpath = os.path.join(self._bc03_filter_dir, f'{name}.dat')
        if not os.path.exists(fpath):
            return None
        try:
            rows = []
            with open(fpath) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    rows.append((float(parts[0]), float(parts[1])))
            if not rows:
                return None
            data = np.array(rows)
            self._bc03_filter_cache[name] = (data[:, 0], data[:, 1])
            return self._bc03_filter_cache[name]
        except Exception:
            return None

    def _convolve_filter(self, wav_aa_obs, flux_jy, pivot_aa):
        """Return the filter-averaged flux in Jy at pivot_aa.

        Uses the energy-weighted (photon-counting) formula:
            <f_ν> = ∫ f_ν T(λ) dλ / ∫ T(λ) dλ

        Applies a local median clip to suppress Wolf-Rayet emission spikes
        in BC03 HR spectra before integrating.  Falls back to nearest-pixel
        interpolation if filter file is missing.
        """
        filt = self._load_filter(pivot_aa)
        if filt is None:
            # Fallback: linear interpolation (not nearest-pixel, which produces
            # a staircase on log-scale when the model SED grid is coarser than
            # the plotting wavelength grid).
            valid = (flux_jy > 0) & np.isfinite(flux_jy)
            if not np.any(valid):
                return 1e-30
            srt = np.argsort(wav_aa_obs[valid])
            return float(np.interp(
                pivot_aa,
                wav_aa_obs[valid][srt],
                flux_jy[valid][srt],
            ))

        filt_wav, filt_t = filt   # Å, dimensionless [0,1]

        # Interpolate flux onto filter wavelength grid
        valid = (flux_jy > 0) & np.isfinite(flux_jy)
        if not np.any(valid):
            return 1e-30
        srt = np.argsort(wav_aa_obs[valid])
        f_interp = np.interp(filt_wav,
                             wav_aa_obs[valid][srt],
                             flux_jy[valid][srt],
                             left=0.0, right=0.0)

        # ── Spike clip: suppress WR/emission line spikes in BC03 HR SEDs ──
        # Replace pixels >5× the 90th percentile of the filter-window flux
        # with the local running median (window = 21 pixels).
        if np.any(f_interp > 0):
            p90 = np.percentile(f_interp[f_interp > 0], 90)
            spike_thresh = 5.0 * p90
            spike_mask   = f_interp > spike_thresh
            if np.any(spike_mask):
                # Running median with a 21-pixel window for spike replacement
                from scipy.ndimage import median_filter
                f_smooth = median_filter(f_interp, size=21, mode='reflect')
                f_interp = np.where(spike_mask, f_smooth, f_interp)

        # Only integrate where both filter and flux are defined
        mask = (filt_t > 0) & (f_interp > 0)
        if not np.any(mask):
            return 1e-30

        num   = np.trapz(f_interp[mask] * filt_t[mask], filt_wav[mask])
        denom = np.trapz(filt_t[mask],                   filt_wav[mask])
        if denom <= 0:
            return 1e-30
        return float(num / denom)

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