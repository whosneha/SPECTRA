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
        self.formats = config.get('formats', ['png'])
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
        
        wavelength_um = wavelength / 1e4
        
        # Detect narrow-range spectroscopic data vs broadband photometry
        wav_ratio = wavelength_um.max() / wavelength_um.min()
        is_narrow = wav_ratio < 1.5  # less than 0.18 dex span
        n_points = len(wavelength_um)
        
        if is_narrow:
            print(f"[PLOT] Narrow wavelength range detected (ratio={wav_ratio:.3f}), using linear x-axis")
        
        # Determine plot x-range
        if is_narrow:
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
                    wav_smooth_aa = np.logspace(
                        np.log10(x_min * 1e4),
                        np.log10(x_max * 1e4),
                        500
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
        
        # Title
        ax_sed.set_title(f'SED Fit: {object_id} (z = {redshift:.4f})', 
                        fontsize=14, fontweight='bold')
        
        # Plot components
        if self.show_components and stellar_unattenuated is not None:
            ax_sed.plot(smooth_wavelengths_um, stellar_unattenuated, '--', 
                       linewidth=self.line_width, color=self.colors['unattenuated'],
                       label='Stellar unattenuated', zorder=1, alpha=0.8)
        
        if smooth_spectrum is not None:
            ax_sed.plot(smooth_wavelengths_um, smooth_spectrum, '-', 
                       linewidth=self.line_width, color=self.colors['model'],
                       label='Model spectrum', zorder=2, alpha=0.9)
        
        # Adjust marker sizes for many-point data
        if n_points > 8:
            obs_ms = max(5, self.marker_size_obs - 4)
            mod_ms = max(40, self.marker_size_model // 3)
        else:
            obs_ms = self.marker_size_obs
            mod_ms = self.marker_size_model
        
        # Model photometry
        ax_sed.scatter(wavelength_um, mod_flux, s=mod_ms, marker='s',
                      facecolor=self.colors['model'], edgecolors='darkred', 
                      linewidth=1.0, label='Model photometry', zorder=5)
        
        # Observed photometry
        if self.show_error_bars:
            ax_sed.errorbar(wavelength_um, obs_flux, yerr=obs_err,
                           fmt='o', markersize=obs_ms, capsize=3, capthick=1.5,
                           color=self.colors['observed'], ecolor=self.colors['observed'],
                           elinewidth=1.5, markeredgecolor='#1A5276', markeredgewidth=1.0,
                           label='Observed photometry', zorder=6)
        else:
            ax_sed.scatter(wavelength_um, obs_flux, s=obs_ms**2,
                          marker='o', facecolor=self.colors['observed'],
                          edgecolors='#1A5276', linewidth=1.5,
                          label='Observed photometry', zorder=6)
        
        # Set axis scales based on data type
        if is_narrow:
            ax_sed.set_xscale('linear')
        else:
            ax_sed.set_xscale('log')
        ax_sed.set_yscale('log')
        ax_sed.set_ylabel(r'$F_\nu$ [Jy]', fontsize=14)
        
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
        y_min = np.min(all_flux) * 0.3
        y_max = np.max(all_flux) * 5.0
        ax_sed.set_ylim(y_min, y_max)
        
        ax_sed.legend(loc=self.legend_location, frameon=True, fancybox=False,
                     edgecolor='gray', fontsize=self.legend_fontsize, framealpha=0.95)
        
        if self.show_grid:
            ax_sed.grid(True, alpha=self.grid_alpha, linestyle='-', linewidth=0.3, which='both')
        
        if self.show_residuals:
            ax_sed.tick_params(axis='x', which='both', labelbottom=False)
        
        # Parameter box
        if self.show_parameter_box:
            if 'chi2_red' in results:
                reduced_chi2 = results['chi2_red']
            else:
                chi2 = -2 * results['log_likelihood']
                n_data = len(obs_flux)
                n_params = len(results['parameters'])
                reduced_chi2 = chi2 / max(n_data - n_params, 1)
            
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
            
            props = dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor='gray', alpha=0.95)
            ax_sed.text(0.03, 0.97, textstr.strip(), transform=ax_sed.transAxes,
                       fontsize=10, verticalalignment='top', horizontalalignment='left',
                       bbox=props)
        
        # Residuals panel
        if self.show_residuals:
            residuals = (obs_flux - mod_flux) / obs_err
            
            if is_narrow and n_points > 5:
                # Connected line for dense narrow-range data
                sort_idx = np.argsort(wavelength_um)
                ax_res.plot(wavelength_um[sort_idx], residuals[sort_idx], '-o', 
                           markersize=4, color=self.colors['observed'], linewidth=0.8, zorder=3)
            else:
                ax_res.scatter(wavelength_um, residuals, s=80, marker='o',
                              facecolor=self.colors['observed'], 
                              edgecolors='#1A5276', linewidth=1.5, zorder=3)
            
            ax_res.axhline(y=0, color='black', linestyle='-', linewidth=1.0, zorder=2)
            ax_res.axhspan(-1, 1, alpha=0.3, color=self.colors['residual_good'], zorder=1)
            ax_res.axhspan(-2, -1, alpha=0.15, color=self.colors['residual_warn'], zorder=1)
            ax_res.axhspan(1, 2, alpha=0.15, color=self.colors['residual_warn'], zorder=1)
            ax_res.axhline(y=1, color=self.colors['residual_good'], 
                          linestyle='--', linewidth=0.8, alpha=0.8)
            ax_res.axhline(y=-1, color=self.colors['residual_good'],
                          linestyle='--', linewidth=0.8, alpha=0.8)
            
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