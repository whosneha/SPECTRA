import sys
import os
import yaml
import numpy as np
import glob
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.io import PhotometryLoader
from src.likelihood import Likelihood
from src.fit import SEDFitter
from src.mcmc.mcmc_runner import MCMCRunner
from src.models.ssp_model import SSPModel
from src.utils.plotting import Plotting


def get_input_files(config):
    """
    Get list of input photometry files from config.
    
    Supports:
    - Single file: input.photometry_file
    - List of files: input.photometry_files
    - Directory pattern: input.photometry_dir + input.file_pattern
    """
    input_config = config['input']
    files = []
    
    # Option 1: Single file (backwards compatibility)
    if 'photometry_file' in input_config:
        files.append(input_config['photometry_file'])
    
    # Option 2: List of files
    if 'photometry_files' in input_config:
        files.extend(input_config['photometry_files'])
    
    # Option 3: Directory with pattern
    if 'photometry_dir' in input_config:
        directory = input_config['photometry_dir']
        pattern = input_config.get('file_pattern', '*.dat')
        matched_files = glob.glob(os.path.join(directory, pattern))
        files.extend(sorted(matched_files))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    return unique_files


def extract_object_id(filepath):
    """Extract object ID from filename."""
    basename = os.path.basename(filepath)
    # Remove extension and common suffixes
    name = basename.replace('.dat', '').replace('_ObsSpec_model', '')
    return name


def extract_redshift_from_filename(filepath):
    """
    Extract redshift from filename pattern like 'id_z4p59' or 'id_z6p01'.
    Returns None if redshift cannot be extracted.
    """
    import re
    basename = os.path.basename(filepath)
    
    # Pattern: z followed by digits, 'p' for decimal point, more digits
    # e.g., z4p59 -> 4.59, z6p01 -> 6.01
    match = re.search(r'z(\d+)p(\d+)', basename)
    if match:
        integer_part = match.group(1)
        decimal_part = match.group(2)
        redshift = float(f"{integer_part}.{decimal_part}")
        return redshift
    
    # Also try pattern like z4.59 (with actual decimal)
    match = re.search(r'z(\d+\.?\d*)', basename)
    if match:
        return float(match.group(1))
    
    return None


def process_single_file(filepath, config, ssp_model_base_config):
    """
    Process a single photometry file.
    
    Returns:
        dict: Results dictionary or None if failed
    """
    object_id = extract_object_id(filepath)
    print(f"\n{'='*70}")
    print(f"PROCESSING: {object_id}")
    print(f"File: {filepath}")
    print(f"{'='*70}")
    
    # Check file exists
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return None
    
    # Extract redshift from filename
    extracted_redshift = extract_redshift_from_filename(filepath)
    if extracted_redshift is not None:
        print(f"Extracted redshift from filename: z = {extracted_redshift}")
        redshift = extracted_redshift
    else:
        redshift = ssp_model_base_config.get('redshift', 0.0)
        print(f"Using default redshift from config: z = {redshift}")
    
    # Create SSP model with correct redshift for this object
    ssp_config = ssp_model_base_config.copy()
    ssp_config['redshift'] = redshift
    ssp_model = SSPModel(ssp_config)
    
    # Load photometry data
    loader = PhotometryLoader()
    try:
        phot_data = loader.load_photometry(filepath, format=config['input']['format'])
    except Exception as e:
        print(f"ERROR loading {filepath}: {e}")
        return None
    
    phot_data['object_id'] = object_id
    phot_data['redshift'] = redshift
    
    # IMPORTANT: Calibrate mock model to observed flux levels
    ssp_model.set_flux_calibration(phot_data['obs_flux'])
    
    # DEBUG: Verify calibration works
    test_flux = ssp_model.get_magnitudes(
        mass=12.0, age=0.1, metallicity=-0.5, dust=0.0,
        wavelengths=phot_data['wavelength']
    )
    print(f"[CALIBRATION DEBUG] At mass=12, age=0.1:")
    print(f"  Model flux range: {test_flux.min():.2e} to {test_flux.max():.2e} Jy")
    print(f"  Observed flux range: {phot_data['obs_flux'].min():.2e} to {phot_data['obs_flux'].max():.2e} Jy")
    
    # Convert priors to numeric
    priors_numeric = {}
    for param, bounds in config['fitting']['priors'].items():
        priors_numeric[param] = [float(b) for b in bounds]
    
    # Initialize likelihood
    error_floor = config['fitting'].get('error_floor', 0.1)
    likelihood = Likelihood(
        obs_flux=phot_data['obs_flux'],
        obs_err=phot_data['obs_err'],
        priors=priors_numeric,
        error_floor=error_floor
    )
    
    # Initialize parameters
    initial_params = {}
    bounds = []
    for p in config['fitting']['parameters']:
        pmin, pmax = priors_numeric[p]
        initial_params[p] = (pmin + pmax) / 2.0
        bounds.append((pmin, pmax))
    
    # Create output directory for this object
    base_output_dir = config['plotting']['output_dir']
    object_output_dir = os.path.join(base_output_dir, object_id)
    os.makedirs(object_output_dir, exist_ok=True)
    
    # Update plotting config for this object
    plot_config = config['plotting'].copy()
    plot_config['output_dir'] = object_output_dir
    
    # Run fitting
    fitting_method = config['fitting'].get('method', 'ml')
    
    if fitting_method == 'ml':
        print("Running Maximum Likelihood fitting...")
        fitter = SEDFitter(likelihood, ssp_model, wavelengths=phot_data['wavelength'])
        results = fitter.fit_maximum_likelihood(initial_params, bounds=bounds)
        
    elif fitting_method == 'mcmc':
        print("Running MCMC fitting...")
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
        mcmc_runner.save_results(os.path.join(object_output_dir, 'mcmc_samples.h5'))
        
        # Plot corner plot
        plotting = Plotting(plot_config)
        plotting.plot_corner(results['samples'], config['fitting']['parameters'])
    else:
        print(f"Unknown fitting method: {fitting_method}")
        return None
    
    # Generate SED plot
    plotting = Plotting(plot_config)
    plotting.plot_sed(phot_data, results, ssp_model=ssp_model)
    
    # Print results summary
    print(f"\nResults for {object_id} (z={redshift}):")
    for param, value in results['parameters'].items():
        if fitting_method == 'mcmc' and 'percentiles' in results:
            stats = results['percentiles'][param]
            print(f"  {param}: {stats['median']:.4f} +{stats['upper']:.4f} -{stats['lower']:.4f}")
        else:
            print(f"  {param}: {value:.4f}")
    print(f"Log-likelihood: {results['log_likelihood']:.2f}")
    
    # Add metadata to results
    results['object_id'] = object_id
    results['filepath'] = filepath
    results['output_dir'] = object_output_dir
    results['redshift'] = redshift
    
    return results


def save_summary(all_results, output_dir, config):
    """Save summary of all fits to a CSV file."""
    import pandas as pd
    
    rows = []
    for result in all_results:
        if result is None:
            continue
        
        row = {
            'object_id': result['object_id'],
            'filepath': result['filepath'],
            'log_likelihood': result['log_likelihood'],
        }
        
        # Add parameters
        for param, value in result['parameters'].items():
            row[param] = value
            if 'percentiles' in result:
                row[f'{param}_err_lower'] = result['percentiles'][param]['lower']
                row[f'{param}_err_upper'] = result['percentiles'][param]['upper']
        
        rows.append(row)
    
    if rows:
        df = pd.DataFrame(rows)
        summary_path = os.path.join(output_dir, 'fit_summary.csv')
        df.to_csv(summary_path, index=False)
        print(f"\nSaved summary to: {summary_path}")
        
        # Also print summary table
        print("\n" + "="*70)
        print("SUMMARY OF ALL FITS")
        print("="*70)
        print(df.to_string(index=False))
        print("="*70)


def main():
    # Load configuration
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    if not os.path.exists(config_path):
        print(f"Configuration file not found at {config_path}")
        return

    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # Get list of input files
    input_files = get_input_files(config)
    
    if not input_files:
        print("ERROR: No input files found. Check your config.yaml")
        return
    
    print(f"\nFound {len(input_files)} file(s) to process:")
    for f in input_files:
        print(f"  - {f}")
    
    # Get base SSP model config (redshift will be overridden per object)
    ssp_model_base_config = config['ssp_model']
    print(f"\nBase SSP model config (redshift will be extracted from filenames):")
    print(f"  IMF: {ssp_model_base_config.get('imf', 'kroupa')}")
    print(f"  Dust model: {ssp_model_base_config.get('dust_model', 'calzetti')}")
    
    # Create base output directory
    base_output_dir = config['plotting']['output_dir']
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Process each file (SSP model created per-object with correct redshift)
    all_results = []
    for i, filepath in enumerate(input_files):
        print(f"\n[{i+1}/{len(input_files)}] Processing {os.path.basename(filepath)}...")
        
        try:
            result = process_single_file(filepath, config, ssp_model_base_config)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR processing {filepath}: {e}")
            import traceback
            traceback.print_exc()
            all_results.append(None)
    
    # Save summary
    save_summary(all_results, base_output_dir, config)
    
    # Print final summary
    n_success = sum(1 for r in all_results if r is not None)
    n_failed = len(all_results) - n_success
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"  Successful: {n_success}")
    print(f"  Failed: {n_failed}")
    print(f"  Output directory: {base_output_dir}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()