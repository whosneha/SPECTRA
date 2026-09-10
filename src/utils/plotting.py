import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import seaborn as sns

class Plotting:
    """Generate SED plots and comparison visualizations."""
    
    def __init__(self, config):
        """
        Initialize plotting.
        
        Args:
            config: Dict with output_dir and customization options
        """
        self.output_dir = config.get('output_dir', './results')
        legacy_plot_format = config.get('plot_format')
        if 'formats' in config:
            self.formats = config['formats']
        elif legacy_plot_format:
            self.formats = [legacy_plot_format]
        else:
            self.formats = ['png']
        os.makedirs(self.output_dir, exist_ok=True)
        
        # ── Plot Customization ──
        self.plot_style = config.get('plot_style', 'default')
        self.figure_size = tuple(config.get('figure_size', [12, 8]))
        self.dpi = config.get('dpi', 150)
        self.show_components = config.get('show_components', True)
        self.show_error_bars = config.get('show_error_bars', True)
        self.show_residuals = config.get('show_residuals', True)
        self.show_parameter_box = config.get('show_parameter_box', True)
        
        # Wavelength/flux units
        self.wavelength_units = config.get('wavelength_units', 'micron')
        self.flux_units = config.get('flux_units', 'jy')

        # Optional explicit x-axis range for SED plots, in microns: [min, max].
        # When set, overrides the data-driven auto x-limits so the model rise/fall
        # is visible even when photometry covers a narrow band.
        wr = config.get('wavelength_range', None)
        self.wavelength_range = tuple(wr) if wr is not None else None

        # Optional explicit y-axis range for SED plots, in Jy: [min, max].
        # When set, overrides the data-driven auto y-limits.
        fr = config.get('flux_range', None)
        self.flux_range = tuple(fr) if fr is not None else None
        
        # Color scheme
        color_scheme = config.get('color_scheme', {})
        self.colors = {
            'observed': color_scheme.get('observed', '#2980B9'),
            'model': color_scheme.get('model', '#E74C3C'),
            'unattenuated': color_scheme.get('unattenuated', '#F1C40F'),
            'residual_good': color_scheme.get('residual_good', '#2ECC71'),
            'residual_warn': color_scheme.get('residual_warn', '#F39C12'),
            'residual_bad': color_scheme.get('residual_bad', '#E74C3C'),
        }
        
        # Marker styles
        self.marker_size_obs = config.get('marker_size_obs', 12)
        self.marker_size_model = config.get('marker_size_model', 120)
        self.line_width = config.get('line_width', 1.5)
        
        # Legend settings
        self.legend_location = config.get('legend_location', 'upper right')
        self.legend_fontsize = config.get('legend_fontsize', 10)
        
        # Grid
        self.show_grid = config.get('show_grid', True)
        self.grid_alpha = config.get('grid_alpha', 0.3)
        
        # Set matplotlib style
        self._set_plot_style()
    
    def _set_plot_style(self):
        """Set matplotlib parameters based on plot_style."""
        if self.plot_style == 'publication':
            plt.rcParams['font.family'] = 'serif'
            plt.rcParams['font.size'] = 14
            plt.rcParams['axes.labelsize'] = 16
            plt.rcParams['legend.fontsize'] = 12
            plt.rcParams['xtick.labelsize'] = 14
            plt.rcParams['ytick.labelsize'] = 14
        elif self.plot_style == 'minimal':
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.labelsize'] = 11
            plt.rcParams['legend.fontsize'] = 9
        else:  # default
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.size'] = 11
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['legend.fontsize'] = 10
        
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['axes.linewidth'] = 1.0
    
    def plot_sed(self, phot_data, results, ssp_model=None, ax=None, **kwargs):
        """Plot SED with full customization support."""
        wavelength = phot_data['wavelength']
        obs_flux = phot_data['obs_flux']
        obs_err = phot_data['obs_err']
        mod_flux = results['mod_flux']
        object_id = phot_data.get('object_id', 'unknown')
        redshift = phot_data.get('redshift', ssp_model.redshift if ssp_model else 0.0)

        # CIGALE-style overrides: orange/blue/dark-red colors, mJy units,
        # "Best model" title, relative residual panel.
        is_cigale = (self.plot_style == 'cigale')
        flux_scale = 1000.0 if is_cigale else 1.0
        flux_units_label = r'$S_\nu$ [mJy]' if is_cigale else r'$F_\nu$ [Jy]'

        wavelength_um = wavelength / 1e4

        # Detect narrow-range spectroscopic data vs broadband photometry
        wav_ratio = wavelength_um.max() / wavelength_um.min()
        is_narrow = wav_ratio < 1.5  # less than 0.18 dex span
        # In CIGALE-style mode, dense narrow-range data is rendered as a
        # continuous "Observed spectrum" line (gray) AND binned into a few
        # synthetic photometry points (red circles + black X) — matching the
        # appearance of CIGALE's diagnostic plots. The x-axis stays log.
        treat_as_spectrum = bool(is_cigale and is_narrow and len(wavelength_um) >= 5)
        if is_cigale:
            is_narrow = False
        n_points = len(wavelength_um)
        
        if is_narrow:
            print(f"[PLOT] Narrow wavelength range detected (ratio={wav_ratio:.3f}), using linear x-axis")
        
        # Determine plot x-range
        if self.wavelength_range is not None:
            # Explicit user-specified range (in microns)
            x_min, x_max = float(self.wavelength_range[0]), float(self.wavelength_range[1])
        elif is_narrow:
            # Linear padding for narrow range
            wav_span = wavelength_um.max() - wavelength_um.min()
            pad = max(wav_span * 0.3, 0.005)  # at least 0.005 μm padding
            x_min = wavelength_um.min() - pad
            x_max = wavelength_um.max() + pad
        else:
            # Log-space padding for broadband
            log_wav_min = np.log10(wavelength_um.min())
            log_wav_max = np.log10(wavelength_um.max())
            log_wav_range = max(log_wav_max - log_wav_min, 0.3)
            pad = max(0.3, 0.4 * log_wav_range)
            x_min = 10 ** (log_wav_min - pad)
            x_max = 10 ** (log_wav_max + pad)
        
        # Generate smooth spectrum over the PLOT range for context
        smooth_spectrum = None
        stellar_unattenuated = None
        smooth_wavelengths_um = None
        
        if ssp_model is not None and self.show_components:
            try:
                if is_narrow:
                    wav_smooth_aa = np.linspace(x_min * 1e4, x_max * 1e4, 200)
                else:
                    # High resolution so narrow UV features (Lyman series,
                    # 2175 Å bump, etc.) are visible in the rendered curve.
                    wav_smooth_aa = np.logspace(
                        np.log10(x_min * 1e4),
                        np.log10(x_max * 1e4),
                        4000
                    )
                
                params = results['parameters']
                smooth_spectrum = ssp_model.get_magnitudes(
                    wavelengths=wav_smooth_aa, **params
                )
                smooth_wavelengths_um = wav_smooth_aa / 1e4
                
                # Build unattenuated params (only if dust is significant)
                dust_val = params.get('dust', 0.0)
                if dust_val > 0.01:
                    params_no_dust = {k: v for k, v in params.items()}
                    params_no_dust['dust'] = 0.0
                    stellar_unattenuated = ssp_model.get_magnitudes(
                        wavelengths=wav_smooth_aa, **params_no_dust
                    )
                else:
                    stellar_unattenuated = None
                    
            except Exception as e:
                print(f"Could not generate smooth spectrum: {e}")
        
        # Create figure
        if self.show_residuals:
            fig = plt.figure(figsize=self.figure_size)
            gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.0)
            ax_sed = fig.add_subplot(gs[0])
            ax_res = fig.add_subplot(gs[1], sharex=ax_sed)
        else:
            fig, ax_sed = plt.subplots(figsize=self.figure_size)

        # Reduced chi^2 (computed once, used in title and parameter box)
        if 'chi2_red' in results:
            reduced_chi2 = results['chi2_red']
        else:
            chi2 = -2 * results.get('log_likelihood', 0.0)
            n_data = len(obs_flux)
            n_params = len(results.get('parameters', {}))
            reduced_chi2 = chi2 / max(n_data - n_params, 1)

        # Title
        if is_cigale:
            ax_sed.set_title(
                f'Best model for {object_id}\n'
                f'(z={redshift:.2f}, reduced $\\chi^2$={reduced_chi2:.2f})',
                fontsize=14
            )
        else:
            ax_sed.set_title(f'SED Fit: {object_id} (z = {redshift:.4f})',
                            fontsize=14, fontweight='bold')

        # CIGALE-style colors
        if is_cigale:
            unatt_color = '#1F77FF'      # blue dashed
            model_color = '#8B0000'      # dark red
            obs_color   = '#D62728'      # red circles
            obs_edge    = '#1A1A1A'
            unatt_label = 'Stellar unattenuated'
            model_label = 'Modeled spectrum'
            obs_label   = 'Observed photometric fluxes'
            mod_phot_color = 'black'
        else:
            unatt_color = self.colors['unattenuated']
            model_color = self.colors['model']
            obs_color   = self.colors['observed']
            obs_edge    = '#1A5276'
            unatt_label = 'Stellar unattenuated'
            model_label = 'Model spectrum'
            obs_label   = 'Observed photometry'
            mod_phot_color = self.colors['model']

        # Plot components
        if self.show_components and stellar_unattenuated is not None:
            from scipy.ndimage import median_filter as _mf, gaussian_filter1d as _gf1d
            _unatt_cont = _gf1d(_mf(stellar_unattenuated.astype(float), size=51), sigma=3)
            ax_sed.plot(smooth_wavelengths_um, _unatt_cont * flux_scale, '--',
                       linewidth=self.line_width, color=unatt_color,
                       label=unatt_label, zorder=1, alpha=0.85)

        if smooth_spectrum is not None:
            # Show continuum envelope: median filter clips narrow emission-line
            # spikes (Hα, [O III], Paα …), then a light Gaussian smooths
            # pixelisation noise.  This matches the CIGALE SED display style.
            from scipy.ndimage import median_filter as _mf, gaussian_filter1d as _gf1d
            _cont = _gf1d(_mf(smooth_spectrum.astype(float), size=51), sigma=3)
            ax_sed.plot(smooth_wavelengths_um, _cont * flux_scale, '-',
                       linewidth=self.line_width, color=model_color,
                       label=model_label, zorder=2, alpha=0.95)

        # Adjust marker sizes for many-point data
        if n_points > 8:
            obs_ms = max(5, self.marker_size_obs - 4)
            mod_ms = max(40, self.marker_size_model // 3)
        else:
            obs_ms = self.marker_size_obs
            mod_ms = self.marker_size_model

        if treat_as_spectrum:
            # CIGALE-style rendering of a spectroscopic .dat file:
            #   1) Draw the per-pixel observations as a continuous gray
            #      "Observed spectrum" line (matches CIGALE's gray curve).
            #   2) Bin into a handful of synthetic photometry points (red
            #      open circles + black X model markers) so the legend keys
            #      ("Observed photometric fluxes", "Model photometric fluxes")
            #      still apply.
            sort_idx = np.argsort(wavelength_um)
            wav_sorted   = wavelength_um[sort_idx]
            obs_sorted   = obs_flux[sort_idx]
            err_sorted   = obs_err[sort_idx]
            mod_sorted   = mod_flux[sort_idx]

            ax_sed.plot(wav_sorted, obs_sorted * flux_scale, '-',
                       color='gray', linewidth=1.4, alpha=0.85,
                       label='Observed spectrum', zorder=3)

            # Bin into up to 5 equal-width windows
            n_bins = min(5, max(2, n_points // 3))
            bin_edges = np.linspace(wav_sorted.min(), wav_sorted.max(), n_bins + 1)
            bin_wav, bin_obs, bin_err, bin_mod = [], [], [], []
            for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
                mask = (wav_sorted >= lo) & (wav_sorted <= hi)
                if not np.any(mask):
                    continue
                bin_wav.append(np.mean(wav_sorted[mask]))
                bin_obs.append(np.mean(obs_sorted[mask]))
                # Errors combine in quadrature, divided by sqrt(N)
                bin_err.append(np.sqrt(np.mean(err_sorted[mask] ** 2)) /
                              np.sqrt(max(np.sum(mask), 1)))
                bin_mod.append(np.mean(mod_sorted[mask]))
            bin_wav = np.array(bin_wav)
            bin_obs = np.array(bin_obs)
            bin_err = np.array(bin_err)
            bin_mod = np.array(bin_mod)

            # Model photometric fluxes (black X) at binned wavelengths
            ax_sed.scatter(bin_wav, bin_mod * flux_scale, s=140,
                          marker='X', facecolor='black', edgecolors='black',
                          linewidth=1.0, label='Model photometric fluxes', zorder=5)
            # Observed photometric fluxes (red open circles + error bars)
            ax_sed.errorbar(bin_wav, bin_obs * flux_scale, yerr=bin_err * flux_scale,
                           fmt='o', markersize=10, capsize=3, capthick=1.5,
                           color=obs_color, ecolor=obs_color,
                           markerfacecolor='none', markeredgecolor=obs_color,
                           markeredgewidth=2.0, elinewidth=1.5,
                           label='Observed photometric fluxes', zorder=6)
        else:
            # Default rendering: per-point photometry markers
            ax_sed.scatter(wavelength_um, mod_flux * flux_scale, s=mod_ms,
                          marker=('X' if is_cigale else 's'),
                          facecolor=mod_phot_color,
                          edgecolors=('black' if is_cigale else 'darkred'),
                          linewidth=1.0,
                          label='Model photometric fluxes' if is_cigale else 'Model photometry',
                          zorder=5)
            if self.show_error_bars:
                ax_sed.errorbar(wavelength_um, obs_flux * flux_scale, yerr=obs_err * flux_scale,
                               fmt='o', markersize=obs_ms, capsize=3, capthick=1.5,
                               color=obs_color, ecolor=obs_color,
                               markerfacecolor=('none' if is_cigale else obs_color),
                               markeredgecolor=(obs_color if is_cigale else obs_edge),
                               markeredgewidth=(2.0 if is_cigale else 1.0),
                               elinewidth=1.5,
                               label=obs_label, zorder=6)
            else:
                ax_sed.scatter(wavelength_um, obs_flux * flux_scale, s=obs_ms**2,
                              marker='o', facecolor=('none' if is_cigale else obs_color),
                              edgecolors=(obs_color if is_cigale else obs_edge),
                              linewidth=(2.0 if is_cigale else 1.5),
                              label=obs_label, zorder=6)
        
        # Set axis scales based on data type
        if is_narrow:
            ax_sed.set_xscale('linear')
        else:
            ax_sed.set_xscale('log')
        ax_sed.set_yscale('log')
        ax_sed.set_ylabel(flux_units_label, fontsize=14)
        
        # Apply x-limits
        ax_sed.set_xlim(x_min, x_max)
        
        # Y limits: based on data AND visible smooth model
        all_flux = np.concatenate([obs_flux, mod_flux])
        if smooth_spectrum is not None and smooth_wavelengths_um is not None:
            in_range = (smooth_wavelengths_um >= x_min) & (smooth_wavelengths_um <= x_max)
            valid_smooth = smooth_spectrum[in_range]
            valid_smooth = valid_smooth[(valid_smooth > 0) & np.isfinite(valid_smooth)]
            if len(valid_smooth) > 0:
                all_flux = np.concatenate([all_flux, valid_smooth])
        if stellar_unattenuated is not None and smooth_wavelengths_um is not None:
            in_range = (smooth_wavelengths_um >= x_min) & (smooth_wavelengths_um <= x_max)
            valid_unatt = stellar_unattenuated[in_range]
            valid_unatt = valid_unatt[(valid_unatt > 0) & np.isfinite(valid_unatt)]
            if len(valid_unatt) > 0:
                all_flux = np.concatenate([all_flux, valid_unatt])
        
        all_flux = all_flux[all_flux > 0]
        if self.flux_range is not None:
            # flux_range is interpreted in the *displayed* units (mJy when
            # plot_style='cigale', Jy otherwise) — i.e. matches the y-axis tick
            # values the user sees.
            y_min_disp = float(self.flux_range[0])
            y_max_disp = float(self.flux_range[1])
            ax_sed.set_ylim(y_min_disp, y_max_disp)
        else:
            y_min = np.min(all_flux) * 0.3
            y_max = np.max(all_flux) * 5.0
            ax_sed.set_ylim(y_min * flux_scale, y_max * flux_scale)

        # Legend goes upper-left in CIGALE mode (parameter box is upper-right).
        legend_loc = 'upper left' if is_cigale else self.legend_location
        ax_sed.legend(loc=legend_loc, frameon=True, fancybox=False,
                     edgecolor='gray', fontsize=self.legend_fontsize, framealpha=0.95)
        
        if self.show_grid:
            ax_sed.grid(True, alpha=self.grid_alpha, linestyle='-', linewidth=0.3, which='both')
        
        if self.show_residuals:
            ax_sed.tick_params(axis='x', which='both', labelbottom=False)
        
        # Parameter box: shown in BOTH default and CIGALE modes; CIGALE mode
        # places it in the upper-right (legend goes upper-left).
        if self.show_parameter_box:
            textstr = f"z = {redshift:.4f}\n"
            textstr += f"$\\chi^2_{{\\nu}}$ = {reduced_chi2:.2f}\n"
            for param, value in results['parameters'].items():
                if param == 'mass':
                    textstr += f"log M = {value:.2f}\n"
                elif param == 'age':
                    textstr += f"Age = {value:.2f} Gyr\n"
                elif param == 'metallicity':
                    textstr += f"[Z/H] = {value:.2f}\n"
                elif param == 'dust':
                    textstr += f"E(B-V) = {value:.2f}\n"

            props = dict(boxstyle='round,pad=0.4', facecolor='white',
                        edgecolor='gray', alpha=0.95)
            if is_cigale:
                ax_sed.text(0.97, 0.97, textstr.strip(), transform=ax_sed.transAxes,
                           fontsize=11, verticalalignment='top', horizontalalignment='right',
                           bbox=props)
            else:
                ax_sed.text(0.03, 0.97, textstr.strip(), transform=ax_sed.transAxes,
                           fontsize=10, verticalalignment='top', horizontalalignment='left',
                           bbox=props)
        
        # Residuals panel
        if self.show_residuals:
            # Use the SAME effective errors as the likelihood/χ² calculation
            # (raw obs_err alone can be tiny for high-SNR data, producing
            # misleading 100-σ residuals that don't match the reported χ²).
            error_floor_frac = 0.05
            eff_err = np.sqrt(
                obs_err ** 2
                + np.maximum(
                    error_floor_frac * np.median(obs_flux),
                    error_floor_frac * obs_flux,
                ) ** 2
            )

            if is_cigale:
                # Relative residual: (Obs - Mod) / Obs (CIGALE convention)
                residuals = (obs_flux - mod_flux) / np.where(obs_flux > 0, obs_flux, 1.0)
            else:
                residuals = (obs_flux - mod_flux) / eff_err

            res_marker_color = obs_color if is_cigale else self.colors['observed']
            res_edge_color   = obs_color if is_cigale else '#1A5276'
            if is_narrow and n_points > 5:
                # Connected line for dense narrow-range data
                sort_idx = np.argsort(wavelength_um)
                ax_res.plot(wavelength_um[sort_idx], residuals[sort_idx], '-o',
                           markersize=4, color=res_marker_color, linewidth=0.8, zorder=3)
            elif is_cigale:
                ax_res.scatter(wavelength_um, residuals, s=120, marker='+',
                              color='black', linewidth=2.0, zorder=3)
            else:
                ax_res.scatter(wavelength_um, residuals, s=80, marker='o',
                              facecolor=res_marker_color,
                              edgecolors=res_edge_color,
                              linewidth=1.5, zorder=3)
            
            ax_res.axhline(y=0, color='black', linestyle='--', linewidth=1.0, zorder=2)
            if not is_cigale:
                ax_res.axhspan(-1, 1, alpha=0.3, color=self.colors['residual_good'], zorder=1)
                ax_res.axhspan(-2, -1, alpha=0.15, color=self.colors['residual_warn'], zorder=1)
                ax_res.axhspan(1, 2, alpha=0.15, color=self.colors['residual_warn'], zorder=1)
                ax_res.axhline(y=1, color=self.colors['residual_good'],
                              linestyle='--', linewidth=0.8, alpha=0.8)
                ax_res.axhline(y=-1, color=self.colors['residual_good'],
                              linestyle='--', linewidth=0.8, alpha=0.8)

            if is_cigale:
                ax_res.set_xlabel(r'Observed $\lambda$ ($\mu$m)', fontsize=14)
                ax_res.set_ylabel('Relative\nresidual', fontsize=12)
                ax_res.set_ylim(-1, 1)
            else:
                ax_res.set_xlabel(r'$\lambda_{\rm obs}$ [$\mu$m]', fontsize=14)
                ax_res.set_ylabel(r'$\chi$', fontsize=14)
                res_max = max(3, max(abs(residuals.min()), abs(residuals.max())) * 1.2)
                ax_res.set_ylim(-res_max, res_max)
            ax_res.set_xlim(x_min, x_max)
            
            if is_narrow:
                ax_res.set_xscale('linear')
            
            if self.show_grid:
                ax_res.grid(True, alpha=self.grid_alpha, linestyle='-', linewidth=0.3)
            
            plt.setp(ax_sed.get_xticklabels(), visible=False)
            fig.subplots_adjust(hspace=0)
        
        # Save
        for fmt in self.formats:
            filepath = os.path.join(self.output_dir, f'sed_fit_{object_id}.{fmt}')
            fig.savefig(filepath, dpi=self.dpi, bbox_inches='tight', facecolor='white')
            print(f"Saved: {filepath}")
        
        plt.close(fig)
    
    def plot_corner(self, samples, param_names):
        """Plot corner plot for MCMC samples with improved visualization."""
        try:
            import corner
            
            labels = []
            for p in param_names:
                if p == 'mass':
                    labels.append(r'$\log M/M_\odot$')
                elif p == 'age':
                    labels.append('Age [Gyr]')
                elif p == 'metallicity':
                    labels.append('[Z/H]')
                elif p == 'dust':
                    labels.append('E(B-V)')
                else:
                    labels.append(p)
            
            fig = corner.corner(
                samples, 
                labels=labels,
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True, 
                title_kwargs={"fontsize": 12},
                title_fmt='.2f',
                smooth=1.0,
                smooth1d=1.0,
                bins=30,
                plot_datapoints=True,
                plot_density=True,
                plot_contours=True,
                fill_contours=True,
                levels=(0.68, 0.95),
                color='#2980B9',
            )
            
            fig.set_size_inches(10, 10)
            
            for fmt in self.formats:
                filepath = os.path.join(self.output_dir, f'corner_plot.{fmt}')
                fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"Saved: {filepath}")
            
            plt.close(fig)
        except ImportError:
            print("corner package not installed. Skipping corner plot.")
    
    def plot_trace(self, samples, param_names, burn_in=0):
        """
        Plot MCMC trace (walker evolution) for burn-in diagnostics.
        
        Args:
            samples: MCMC chain array (nwalkers, nsteps, ndim)
            param_names: List of parameter names
            burn_in: Number of burn-in steps (for vertical line)
        """
        n_params = len(param_names)
        fig, axes = plt.subplots(n_params, 1, figsize=(10, 2*n_params), sharex=True)
        if n_params == 1:
            axes = [axes]
        
        for i, (ax, param) in enumerate(zip(axes, param_names)):
            # Plot all walker chains
            ax.plot(samples[:, :, i].T, 'k', alpha=0.1, linewidth=0.5)
            
            if burn_in > 0:
                ax.axvline(burn_in, color='red', linestyle='--', 
                          linewidth=1.5, label='Burn-in')
            
            # Labels
            if param == 'mass':
                label = r'$\log M/M_\odot$'
            elif param == 'age':
                label = 'Age [Gyr]'
            elif param == 'metallicity':
                label = '[Z/H]'
            elif param == 'dust':
                label = 'E(B-V)'
            else:
                label = param
            ax.set_ylabel(label, fontsize=10)
            
            if i == 0 and burn_in > 0:
                ax.legend(loc='upper right', fontsize=8)
        
        axes[-1].set_xlabel('Step', fontsize=12)
        fig.suptitle('MCMC Trace', fontsize=14, fontweight='bold')
        fig.tight_layout()
        
        for fmt in self.formats:
            filepath = os.path.join(self.output_dir, f'trace_plot.{fmt}')
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        plt.close(fig)
