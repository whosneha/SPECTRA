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
            config: Dict with output_dir and formats keys
        """
        self.output_dir = config.get('output_dir', './results')
        self.formats = config.get('formats', ['png'])
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set style - clean white background matching reference
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 8
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['axes.linewidth'] = 1.0
    
    def plot_sed(self, phot_data, results, ssp_model=None):
        """
        Plot observed vs model SED matching reference style with log-log axes.
        """
        wavelength = phot_data['wavelength']  # in microns
        obs_flux = phot_data['obs_flux']
        obs_err = phot_data['obs_err']
        mod_flux = results['mod_flux']
        
        # Convert wavelength to Angstroms
        wavelength_aa = wavelength * 1e4
        
        # Debug
        print("\n[PLOTTING DEBUG]")
        print(f"Model flux range: {mod_flux.min():.6e} to {mod_flux.max():.6e} Jy")
        print(f"Observed flux range: {obs_flux.min():.6e} to {obs_flux.max():.6e} Jy")
        
        # Generate extended smooth spectrum from FSPS (wider wavelength range)
        smooth_spectrum = None
        smooth_wavelengths_aa = None
        
        if ssp_model and not ssp_model.mock_mode:
            try:
                # Extended wavelength range: 1000 Å to 100,000 Å (0.1 to 10 μm)
                smooth_wavelengths_um = np.logspace(np.log10(0.1), np.log10(10), 1000)
                smooth_wavelengths_aa = smooth_wavelengths_um * 1e4
                smooth_spectrum = ssp_model.get_magnitudes(
                    wavelengths=smooth_wavelengths_um,
                    **results['parameters']
                )
                print(f"[PLOTTING] Generated smooth spectrum from {smooth_wavelengths_aa.min():.0f} to {smooth_wavelengths_aa.max():.0f} Å")
            except Exception as e:
                print(f"Could not generate smooth spectrum: {e}")
        
        # Create figure with 2 subplots (SED + residuals) - matching reference proportions
        fig = plt.figure(figsize=(8, 6))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.0)
        
        ax_sed = fig.add_subplot(gs[0])
        ax_res = fig.add_subplot(gs[1], sharex=ax_sed)
        
        # ===== TOP PANEL: SED with LOG-LOG scales =====
        
        # Plot smooth modeled spectrum (orange line) - extended range
        if smooth_spectrum is not None:
            ax_sed.plot(smooth_wavelengths_aa, smooth_spectrum, '-', linewidth=1.2, 
                       color='#E67E22', label='Best-fit model', zorder=2)
        
        # Plot model photometric fluxes (orange squares)
        ax_sed.scatter(wavelength_aa, mod_flux, s=60, marker='s', 
                      facecolor='#E67E22', edgecolors='#D35400', linewidth=0.8,
                      label='Model photometry', zorder=4)
        
        # Plot observed photometric fluxes (blue circles with error bars)
        ax_sed.errorbar(wavelength_aa, obs_flux, yerr=obs_err, 
                       fmt='o', markersize=6, capsize=2, capthick=1,
                       color='#3498DB', ecolor='#3498DB', elinewidth=1,
                       markeredgecolor='#2980B9', markeredgewidth=0.8,
                       label='Observed photometry', zorder=5)
        
        # Set LOG-LOG scales (matching reference)
        ax_sed.set_xscale('log')
        ax_sed.set_yscale('log')
        
        # Formatting
        ax_sed.set_ylabel(r'$F_\nu$ [Jy]', fontsize=12)
        
        # Extended x-axis range to show full model spectrum
        if smooth_wavelengths_aa is not None:
            ax_sed.set_xlim(1e3, 1e5)  # 1000 Å to 100,000 Å
        else:
            xlim_pad = 0.2
            ax_sed.set_xlim(wavelength_aa.min() * (1 - xlim_pad), 
                           wavelength_aa.max() * (1 + xlim_pad))
        
        # Y-axis limits - show full dynamic range
        if smooth_spectrum is not None:
            all_flux = np.concatenate([obs_flux, mod_flux, smooth_spectrum[smooth_spectrum > 0]])
        else:
            all_flux = np.concatenate([obs_flux, mod_flux])
        ylim_min = np.min(all_flux[all_flux > 0]) * 0.1
        ylim_max = np.max(all_flux) * 5.0
        ax_sed.set_ylim(ylim_min, ylim_max)
        
        # Legend - upper right
        ax_sed.legend(loc='upper right', frameon=True, fancybox=False, 
                     edgecolor='gray', fontsize=8, framealpha=0.9)
        
        # Grid
        ax_sed.grid(True, alpha=0.3, linestyle='-', linewidth=0.3, which='both')
        ax_sed.tick_params(axis='x', which='both', labelbottom=False)
        
        # Add text box with fit parameters - upper left
        chi2 = -2 * results['log_likelihood']
        n_data = len(obs_flux)
        n_params = len(results['parameters'])
        reduced_chi2 = chi2 / (n_data - n_params) if n_data > n_params else chi2
        
        textstr = f"$\\chi^2_{{\\nu}}$ = {reduced_chi2:.2f}\n"
        for param, value in results['parameters'].items():
            if param == 'mass':
                textstr += f"log M = {value:.2f}\n"
            elif param == 'age':
                textstr += f"Age = {value:.2f} Gyr\n"
            elif param == 'metallicity':
                textstr += f"Z = {value:.2f}\n"
        
        props = dict(boxstyle='round,pad=0.3', facecolor='white', 
                    edgecolor='gray', alpha=0.9)
        ax_sed.text(0.03, 0.97, textstr.strip(), transform=ax_sed.transAxes, 
                   fontsize=9, verticalalignment='top', horizontalalignment='left',
                   bbox=props)
        
        # ===== BOTTOM PANEL: RESIDUALS (χ) =====
        residuals = (obs_flux - mod_flux) / obs_err
        
        ax_res.scatter(wavelength_aa, residuals, s=40, marker='o',
                      facecolor='#3498DB', edgecolors='#2980B9', linewidth=0.8,
                      zorder=3)
        
        # Add zero line
        ax_res.axhline(y=0, color='black', linestyle='-', linewidth=1.0, zorder=2)
        
        # Add ±1σ and ±2σ shaded regions
        ax_res.axhspan(-1, 1, alpha=0.3, color='#2ECC71', zorder=1, label='±1σ')
        ax_res.axhspan(-2, -1, alpha=0.15, color='#F39C12', zorder=1)
        ax_res.axhspan(1, 2, alpha=0.15, color='#F39C12', zorder=1)
        ax_res.axhline(y=1, color='#2ECC71', linestyle='--', linewidth=0.6, alpha=0.8)
        ax_res.axhline(y=-1, color='#2ECC71', linestyle='--', linewidth=0.6, alpha=0.8)
        
        # Formatting
        ax_res.set_xlabel(r'$\lambda_{\rm obs}$ [$\AA$]', fontsize=12)
        ax_res.set_ylabel(r'$\chi$', fontsize=12)
        
        # Auto-scale residuals y-axis
        res_max = max(3, max(abs(residuals.min()), abs(residuals.max())) * 1.2)
        ax_res.set_ylim(-res_max, res_max)
        
        ax_res.grid(True, alpha=0.3, linestyle='-', linewidth=0.3)
        
        # Hide top x-labels
        plt.setp(ax_sed.get_xticklabels(), visible=False)
        
        # Remove space between plots
        fig.subplots_adjust(hspace=0)
        
        # Save
        for fmt in self.formats:
            filepath = os.path.join(self.output_dir, f'sed_fit.{fmt}')
            fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"Saved: {filepath}")
        
        plt.close(fig)
    
    def plot_corner(self, samples, param_names):
        """Plot corner plot for MCMC samples."""
        try:
            import corner
            
            # Clean labels for corner plot
            labels = []
            for p in param_names:
                if p == 'mass':
                    labels.append(r'$\log M/M_\odot$')
                elif p == 'age':
                    labels.append('Age [Gyr]')
                elif p == 'metallicity':
                    labels.append('[Z/H]')
                else:
                    labels.append(p)
            
            fig = corner.corner(samples, labels=labels, 
                              quantiles=[0.16, 0.5, 0.84],
                              show_titles=True, title_kwargs={"fontsize": 10},
                              title_fmt='.2f')
            
            for fmt in self.formats:
                filepath = os.path.join(self.output_dir, f'corner_plot.{fmt}')
                fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"Saved: {filepath}")
            
            plt.close(fig)
        except ImportError:
            print("corner package not installed. Skipping corner plot.")