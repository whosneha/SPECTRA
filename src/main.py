import sys
import os
import yaml
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io import PhotometryLoader
from src.likelihood import Likelihood
from src.fit import SEDFitter
from src.mcmc.mcmc_runner import MCMCRunner
from src.models.ssp_model import SSPModel
from src.utils.plotting import Plotting

def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    if not os.path.exists(config_path):
        print(f"Configuration file not found at {config_path}. Please ensure it exists.")
        return

    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # Load photometry data
    loader = PhotometryLoader()
    photometry_file = config['input']['photometry_file']
    if not os.path.exists(photometry_file):
        print(f"Photometry file not found at {photometry_file}. Please ensure it exists.")
        return

    phot_data = loader.load_photometry(
        photometry_file,
        format=config['input']['format']
    )
    
    print(f"\n[MAIN DEBUG] Raw loaded mod_flux from file:")
    print(f"  Values: {phot_data['mod_flux']}")
    print(f"  Range: {phot_data['mod_flux'].min():.2e} to {phot_data['mod_flux'].max():.2e}")
    print(f"  dtype: {phot_data['mod_flux'].dtype}")
    
    # Add object ID to photometry data
    phot_data['object_id'] = config['rubin']['object_id']
    
    # Initialize SSP model
    ssp_model = SSPModel(config['ssp_model'])
    
    # Convert priors to numeric and initialize likelihood
    priors_numeric = {}
    for param, bounds in config['fitting']['priors'].items():
        priors_numeric[param] = [float(b) for b in bounds]
    
    likelihood = Likelihood(
        obs_flux=phot_data['obs_flux'],
        obs_err=phot_data['obs_err'],
        priors=priors_numeric
    )
    
    # Initialize parameters at midpoint of prior ranges
    initial_params = {}
    bounds = []
    for p in config['fitting']['parameters']:
        pmin, pmax = priors_numeric[p]
        initial_params[p] = (pmin + pmax) / 2.0
        bounds.append((pmin, pmax))
    
    print(f"Initial parameters: {initial_params}")
    print(f"Bounds: {bounds}\n")
    
    # Run fitting based on method
    fitting_method = config['fitting'].get('method', 'ml')
    
    if fitting_method == 'ml':
        print("Running Maximum Likelihood fitting...\n")
        fitter = SEDFitter(likelihood, ssp_model, wavelengths=phot_data['wavelength'],
                          mod_flux_input=phot_data['mod_flux'])
        results = fitter.fit_maximum_likelihood(initial_params, bounds=bounds)
        
    elif fitting_method == 'mcmc':
        print("Running MCMC fitting...\n")
        mcmc_config = config.get('mcmc', {})
        mcmc_runner = MCMCRunner(likelihood, ssp_model, config=mcmc_config)
        mcmc_runner.set_wavelengths(phot_data['wavelength'])
        
        results = mcmc_runner.run(
            initial_params, 
            bounds, 
            config['fitting']['parameters'],
            use_pool=False
        )
        
        # Save MCMC samples
        output_dir = config['plotting']['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        mcmc_runner.save_results(os.path.join(output_dir, 'mcmc_samples.h5'))
        
        # Plot corner plot
        plotting = Plotting(config['plotting'])
        plotting.plot_corner(results['samples'], config['fitting']['parameters'])
    else:
        print(f"Unknown fitting method: {fitting_method}")
        return
    
    # ===== DEBUG: Print flux values =====
    print("\n" + "="*70)
    print("OBSERVED vs MODEL PHOTOMETRIC FLUXES")
    print("="*70)
    print(f"{'Wavelength (μm)':<18} {'Obs Flux (Jy)':<18} {'Mod Flux (Jy)':<18} {'Obs Err (Jy)':<18}")
    print("-"*70)
    for i, (wav, obs, mod, err) in enumerate(zip(phot_data['wavelength'], 
                                                   phot_data['obs_flux'], 
                                                   results['mod_flux'],
                                                   phot_data['obs_err'])):
        print(f"{wav:<18.6f} {obs:<18.6e} {mod:<18.6e} {err:<18.6e}")
    print("="*70 + "\n")
    
    # Convert to mJy for display
    print("\nIN mJy UNITS:")
    print("="*70)
    print(f"{'Wavelength (μm)':<18} {'Obs Flux (mJy)':<18} {'Mod Flux (mJy)':<18} {'Obs Err (mJy)':<18}")
    print("-"*70)
    for i, (wav, obs, mod, err) in enumerate(zip(phot_data['wavelength'], 
                                                   phot_data['obs_flux']*1e3, 
                                                   results['mod_flux']*1e3,
                                                   phot_data['obs_err']*1e3)):
        print(f"{wav:<18.6f} {obs:<18.6e} {mod:<18.6e} {err:<18.6e}")
    print("="*70 + "\n")
    
    # Generate SED plot
    plotting = Plotting(config['plotting'])
    plotting.plot_sed(phot_data, results, ssp_model=ssp_model)
    
    print(f"\nBest-fit parameters:")
    for param, value in results['parameters'].items():
        if fitting_method == 'mcmc' and 'percentiles' in results:
            stats = results['percentiles'][param]
            print(f"  {param}: {stats['median']:.4f} +{stats['upper']:.4f} -{stats['lower']:.4f}")
        else:
            print(f"  {param}: {value:.4f}")
    
    print(f"Log-likelihood: {results['log_likelihood']:.2f}")
    if fitting_method == 'ml':
        print(f"Fit success: {results['success']}")
    else:
        print(f"Acceptance fraction: {results['acceptance_fraction']:.3f}")

if __name__ == "__main__":
    main()