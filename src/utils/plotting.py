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
    
    def plot_sed(self, phot_data, results, ssp_model=None, ax=None, **kwargs):
        """
        Plot observed vs model SED matching CIGALE reference style with multiple components.
        """
        wavelength = phot_data['wavelength']
        obs_flux = phot_data['obs_flux']
        obs_err = phot_data['obs_err']
        mod_flux = results['mod_flux']
        object_id = phot_data.get('object_id', 'unknown')
        redshift = phot_data.get('redshift', ssp_model.redshift if ssp_model else 0.0)
        
        wavelength_um = wavelength
        
        print("\n[PLOTTING DEBUG]")
        print(f"Model flux range: {mod_flux.min():.6e} to {mod_flux.max():.6e} Jy")
        print(f"Observed flux range: {obs_flux.min():.6e} to {obs_flux.max():.6e} Jy")
        
        # Set wavelength range - WIDER for full SED view
        wave_min = 0.1   # 0.1 µm (100 nm) - far UV
        wave_max = 3.0   # 3.0 µm - extend into NIR
        
        # Generate smooth spectrum components
        smooth_spectrum = None
        stellar_attenuated = None
        stellar_unattenuated = None
        smooth_wavelengths_um = None
        
        if ssp_model is not None:
            try:
                smooth_wavelengths_um = np.logspace(np.log10(wave_min), np.log10(wave_max), 500)
                
                # Generate model spectrum at best-fit parameters
                smooth_spectrum = ssp_model.get_magnitudes(
                    wavelengths=smooth_wavelengths_um,
                    **results['parameters']
                )
                
                # Create attenuated/unattenuated versions for visualization
                dust_av = results['parameters'].get('dust', 0.0)
                if dust_av > 0:
                    # Calzetti law approximation for visualization
                    k_lambda = 2.659 * (-2.156 + 1.509/smooth_wavelengths_um - 
                                        0.198/smooth_wavelengths_um**2 + 
                                        0.011/smooth_wavelengths_um**3) + 4.05
                    k_lambda = np.clip(k_lambda, 0, 20)
                    attenuation = 10**(-0.4 * dust_av * k_lambda / 4.05)
                    stellar_unattenuated = smooth_spectrum / np.clip(attenuation, 0.01, 1.0)
                    stellar_attenuated = smooth_spectrum
                else:
                    stellar_unattenuated = smooth_spectrum * 1.0
                    stellar_attenuated = smooth_spectrum * 1.0
                
                print(f"[PLOTTING] Generated smooth spectrum from {smooth_wavelengths_um.min():.3f} to {smooth_wavelengths_um.max():.3f} μm")
                print(f"[PLOTTING] Spectrum flux range: {smooth_spectrum.min():.2e} to {smooth_spectrum.max():.2e} Jy")
            except Exception as e:
                print(f"Could not generate smooth spectrum: {e}")
                import traceback
                traceback.print_exc()
        
        # Create figure
        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.0)
        
        ax_sed = fig.add_subplot(gs[0])
        ax_res = fig.add_subplot(gs[1], sharex=ax_sed)
        
        # Add title with object ID and redshift
        ax_sed.set_title(f'SED Fit: {object_id} (z = {redshift:.4f})', fontsize=14, fontweight='bold')
        
        # Plot components - smooth spectra first (background)
        if stellar_unattenuated is not None and smooth_wavelengths_um is not None:
            ax_sed.plot(smooth_wavelengths_um, stellar_unattenuated, '--', linewidth=1.0, 
                       color='#F1C40F', label='Stellar unattenuated', zorder=1, alpha=0.8)
        
        if stellar_attenuated is not None and smooth_wavelengths_um is not None:
            ax_sed.plot(smooth_wavelengths_um, stellar_attenuated, '-', linewidth=1.5, 
                       color='#E74C3C', label='Model spectrum', zorder=2, alpha=0.9)
        
        # Plot model photometry points
        ax_sed.scatter(wavelength_um, mod_flux, s=120, marker='s', 
                      facecolor='#E74C3C', edgecolors='#C0392B', linewidth=1.5,
                      label='Model photometry', zorder=5)
        
        # Plot observed photometry with error bars
        ax_sed.errorbar(wavelength_um, obs_flux, yerr=obs_err, 
                       fmt='o', markersize=12, capsize=4, capthick=2,
                       color='#2980B9', ecolor='#2980B9', elinewidth=2,
                       markeredgecolor='#1A5276', markeredgewidth=1.5,
                       label='Observed photometry', zorder=6)
        
        ax_sed.set_xscale('log')
        ax_sed.set_yscale('log')
        ax_sed.set_ylabel(r'$F_\nu$ [Jy]', fontsize=14)
        
        # Set axis limits
        ax_sed.set_xlim(wave_min, wave_max)
        
        # Y-axis: use all fluxes to set range
        all_flux = np.concatenate([obs_flux, mod_flux])
        if smooth_spectrum is not None:
            valid_spectrum = smooth_spectrum[smooth_spectrum > 0]
            if len(valid_spectrum) > 0:
                all_flux = np.concatenate([all_flux, valid_spectrum])
        
        y_min = np.min(all_flux[all_flux > 0]) * 0.1
        y_max = np.max(all_flux) * 10
        ax_sed.set_ylim(y_min, y_max)
        
        ax_sed.legend(loc='upper right', frameon=True, fancybox=False, 
                     edgecolor='gray', fontsize=10, framealpha=0.95)
        ax_sed.grid(True, alpha=0.3, linestyle='-', linewidth=0.3, which='both')
        ax_sed.tick_params(axis='x', which='both', labelbottom=False)
        
        # Text box with fit parameters
        chi2 = -2 * results['log_likelihood']
        n_data = len(obs_flux)
        n_params = len(results['parameters'])
        reduced_chi2 = chi2 / (n_data - n_params) if n_data > n_params else chi2
        
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
        
        props = dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.95)
        ax_sed.text(0.03, 0.97, textstr.strip(), transform=ax_sed.transAxes, 
                   fontsize=10, verticalalignment='top', horizontalalignment='left', bbox=props)
        
        # Residuals panel
        residuals = (obs_flux - mod_flux) / obs_err
        ax_res.scatter(wavelength_um, residuals, s=80, marker='o',
                      facecolor='#2980B9', edgecolors='#1A5276', linewidth=1.5, zorder=3)
        ax_res.axhline(y=0, color='black', linestyle='-', linewidth=1.0, zorder=2)
        ax_res.axhspan(-1, 1, alpha=0.3, color='#2ECC71', zorder=1)
        ax_res.axhspan(-2, -1, alpha=0.15, color='#F39C12', zorder=1)
        ax_res.axhspan(1, 2, alpha=0.15, color='#F39C12', zorder=1)
        ax_res.axhline(y=1, color='#2ECC71', linestyle='--', linewidth=0.8, alpha=0.8)
        ax_res.axhline(y=-1, color='#2ECC71', linestyle='--', linewidth=0.8, alpha=0.8)
        
        ax_res.set_xlabel(r'$\lambda_{\rm obs}$ [$\mu$m]', fontsize=14)
        ax_res.set_ylabel(r'$\chi$', fontsize=14)
        res_max = max(3, max(abs(residuals.min()), abs(residuals.max())) * 1.2)
        ax_res.set_ylim(-res_max, res_max)
        ax_res.set_xlim(wave_min, wave_max)
        ax_res.grid(True, alpha=0.3, linestyle='-', linewidth=0.3)
        plt.setp(ax_sed.get_xticklabels(), visible=False)
        fig.subplots_adjust(hspace=0)
        
        # Save with object ID in filename
        for fmt in self.formats:
            filepath = os.path.join(self.output_dir, f'sed_fit_{object_id}.{fmt}')
            fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
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