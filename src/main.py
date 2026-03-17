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
from src.data.data_loader import DataLoader
from src.data.rubin_query import RubinDataQuery
from src.data.fornax_loader import load_fornax_csv


def get_input_data(config):
    """
    Get input photometry data based on configuration.
    
    Returns:
        List of (object_id, phot_data) tuples
    """
    input_config = config['input']
    input_type = input_config.get('type', 'file_list')
    
    data_loader = DataLoader(config)
    datasets = []
    
    print(f"\n[INPUT] Loading data with type: {input_type}")
    
    # ---------------------------------------------------------------------
    # Fornax GC CSV (new)
    # ---------------------------------------------------------------------
    if input_type == 'fornax_csv':
        filepath = input_config.get('filepath')
        if not filepath:
            raise ValueError("filepath must be specified for fornax_csv input type")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fornax CSV not found: {filepath}")

        print(f"[INPUT] Loading Fornax GC photometry from: {filepath}")
        datasets = load_fornax_csv(filepath)
        print(f"[INPUT] Loaded {len(datasets)} clusters")

    # ---------------------------------------------------------------------
    # Batch FITS Processing (NEW)
    # ---------------------------------------------------------------------
    elif input_type == 'fits_batch':
        fits_dir = input_config.get('fits_dir')
        file_pattern = input_config.get('file_pattern', '*.fits')
        max_rows = input_config.get('max_rows_per_file', None)
        row_indices = input_config.get('row_indices', None)
        
        if not fits_dir:
            raise ValueError("fits_dir must be specified for fits_batch")
        
        # Find all matching FITS files
        import glob
        fits_files = sorted(glob.glob(os.path.join(fits_dir, file_pattern)))
        
        if not fits_files:
            raise ValueError(f"No FITS files found matching {os.path.join(fits_dir, file_pattern)}")
        
        print(f"[INPUT] Found {len(fits_files)} FITS files to process")
        
        for fits_file in fits_files:
            print(f"\n[INPUT] Loading: {os.path.basename(fits_file)}")
            
            # Get number of rows in this file
            from astropy.io import fits as pyfits
            with pyfits.open(fits_file) as hdul:
                n_rows = len(hdul[1].data)
            
            # Determine which rows to process
            if row_indices is not None:
                rows_to_process = [r for r in row_indices if r < n_rows]
            elif max_rows is not None:
                rows_to_process = list(range(min(max_rows, n_rows)))
            else:
                rows_to_process = list(range(n_rows))
            
            print(f"[INPUT] Processing {len(rows_to_process)} rows from {n_rows} total")
            
            # Load each row
            for row_idx in rows_to_process:
                try:
                    phot_data = data_loader.load('fits', filepath=fits_file, row_index=row_idx)
                    
                    # Create unique object ID
                    file_base = os.path.basename(fits_file).replace('.fits', '')
                    cluster_id = phot_data.get('object_id', row_idx)
                    object_id = f"{file_base}_cluster{cluster_id}"
                    phot_data['object_id'] = object_id
                    phot_data['source_file'] = fits_file
                    phot_data['row_index'] = row_idx
                    
                    datasets.append((object_id, phot_data))
                    
                except Exception as e:
                    print(f"  [WARNING] Failed to load row {row_idx}: {e}")
                    continue
        
        print(f"\n[INPUT] Successfully loaded {len(datasets)} objects from {len(fits_files)} files")
    
    # ---------------------------------------------------------------------
    # Rubin TAP Query by Object ID
    # ---------------------------------------------------------------------
    elif input_type == 'rubin_id':
        rubin_config = config.get('rubin', {})
        token = rubin_config.get('rsp_token') or os.environ.get('RSP_TOKEN')
        
        object_id = input_config.get('rubin_id')
        if object_id is None:
            raise ValueError("rubin_id must be specified in config")
        
        phot_data = data_loader.load(
            'rubin_id',
            object_id=object_id,
            token=token,
            flux_type=rubin_config.get('flux_type', 'psfFlux'),
            bands=rubin_config.get('bands')
        )
        phot_data['object_id'] = f"rubin_{object_id}"
        datasets.append((f"rubin_{object_id}", phot_data))
    
    # ---------------------------------------------------------------------
    # Rubin TAP Query by Coordinates
    # ---------------------------------------------------------------------
    elif input_type == 'rubin_tap':
        rubin_config = config.get('rubin', {})
        token = rubin_config.get('rsp_token') or os.environ.get('RSP_TOKEN')
        
        ra = input_config.get('ra')
        dec = input_config.get('dec')
        if ra is None or dec is None:
            raise ValueError("ra and dec must be specified for rubin_tap")
        
        phot_data = data_loader.load(
            'rubin_tap',
            ra=ra,
            dec=dec,
            radius_arcsec=input_config.get('radius_arcsec', 10.0),
            token=token,
            flux_type=rubin_config.get('flux_type', 'psfFlux'),
            bands=rubin_config.get('bands')
        )
        object_id = f"ra{ra:.4f}_dec{dec:.4f}"
        phot_data['object_id'] = object_id
        datasets.append((object_id, phot_data))
    
    # ---------------------------------------------------------------------
    # Single File (FITS, DAT, CSV)
    # ---------------------------------------------------------------------
    elif input_type in ['fits', 'dat', 'csv']:
        filepath = input_config.get('filepath')
        if filepath is None:
            raise ValueError(f"filepath must be specified for {input_type}")
        
        phot_data = data_loader.load(input_type, filepath=filepath)
        object_id = extract_object_id(filepath)
        phot_data['object_id'] = object_id
        datasets.append((object_id, phot_data))
    
    # ---------------------------------------------------------------------
    # File List (existing behavior)
    # ---------------------------------------------------------------------
    elif input_type == 'file_list':
        files = get_input_files(config)
        file_format = input_config.get('format', 'dat')
        
        for filepath in files:
            phot_data = data_loader.load(file_format, filepath=filepath)
            object_id = extract_object_id(filepath)
            phot_data['object_id'] = object_id
            datasets.append((object_id, phot_data))
    
    else:
        raise ValueError(f"Unknown input type: {input_type}")
    
    # ---------------------------------------------------------------------
    # Combine with additional data sources if enabled
    # ---------------------------------------------------------------------
    additional_config = config.get('additional_data', {})
    if additional_config.get('enabled', False):
        additional_files = additional_config.get('files', [])
        
        for i, (object_id, phot_data) in enumerate(datasets):
            additional_datasets = [phot_data]
            
            for add_file in additional_files:
                add_path = add_file.get('path')
                add_format = add_file.get('format', 'csv')
                
                if add_path and os.path.exists(add_path):
                    print(f"[INPUT] Adding additional data from: {add_path}")
                    add_data = data_loader.load(add_format, filepath=add_path)
                    additional_datasets.append(add_data)
            
            if len(additional_datasets) > 1:
                combined = data_loader.combine_datasets(additional_datasets)
                combined['object_id'] = object_id
                datasets[i] = (object_id, combined)
                print(f"[INPUT] Combined {len(additional_datasets)} datasets for {object_id}")
    
    return datasets


def get_input_files(config):
    """Get list of input photometry files from config (legacy support)."""
    input_config = config['input']
    files = []
    
    if 'photometry_file' in input_config:
        files.append(input_config['photometry_file'])
    
    if 'photometry_files' in input_config:
        files.extend(input_config['photometry_files'])
    
    if 'photometry_dir' in input_config:
        directory = input_config['photometry_dir']
        pattern = input_config.get('file_pattern', '*.dat')
        matched_files = glob.glob(os.path.join(directory, pattern))
        files.extend(sorted(matched_files))
    
    # Remove duplicates
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
    name = basename.replace('.dat', '').replace('.csv', '').replace('.fits', '')
    name = name.replace('_ObsSpec_model', '')
    return name


def extract_redshift_from_filename(filepath):
    """Extract redshift from filename pattern like 'id_z4p59' or 'id_z6p01'."""
    import re
    basename = os.path.basename(filepath)
    
    match = re.search(r'z(\d+)p(\d+)', basename)
    if match:
        integer_part = match.group(1)
        decimal_part = match.group(2)
        return float(f"{integer_part}.{decimal_part}")
    
    match = re.search(r'z(\d+\.?\d*)', basename)
    if match:
        return float(match.group(1))
    
    return None


def process_single_object(object_id, phot_data, config, ssp_model_base_config):
    """Process a single object's photometry data."""
    print(f"\n{'='*70}")
    print(f"PROCESSING: {object_id}")
    print(f"{'='*70}")

    # Priority: 1) redshift already in phot_data (from CSV), 2) filename, 3) config default
    if phot_data.get('redshift') and phot_data['redshift'] != 0.0:
        redshift = float(phot_data['redshift'])
        print(f"Using redshift from data: z = {redshift}")
    else:
        redshift = extract_redshift_from_filename(object_id)
        if redshift is None:
            redshift = ssp_model_base_config.get('redshift', 0.0)
            print(f"Using config redshift: z = {redshift}")
        else:
            print(f"Extracted redshift from filename: z = {redshift}")

    phot_data['redshift'] = redshift

    # Create SSP model with correct redshift
    ssp_config = ssp_model_base_config.copy()
    ssp_config['redshift'] = redshift
    ssp_model = SSPModel(ssp_config)
    
    # Calibrate mock model to observed flux levels
    ssp_model.set_flux_calibration(phot_data['obs_flux'])
    
    # Debug calibration
    test_flux = ssp_model.get_magnitudes(
        mass=12.0, age=0.1, metallicity=-0.5, dust=0.0,
        wavelengths=phot_data['wavelength']
    )
    print(f"[CALIBRATION] At mass=12, age=0.1:")
    print(f"  Model: {test_flux.min():.2e} to {test_flux.max():.2e} Jy")
    print(f"  Observed: {phot_data['obs_flux'].min():.2e} to {phot_data['obs_flux'].max():.2e} Jy")
    
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
    
    # Create output directory
    base_output_dir = config['plotting']['output_dir']
    object_output_dir = os.path.join(base_output_dir, object_id)
    os.makedirs(object_output_dir, exist_ok=True)
    
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
            initial_params, bounds, 
            config['fitting']['parameters'],
            use_pool=False
        )
        
        mcmc_runner.save_results(os.path.join(object_output_dir, 'mcmc_samples.h5'))
        
        plotting = Plotting(plot_config)
        plotting.plot_corner(results['samples'], config['fitting']['parameters'])
    else:
        raise ValueError(f"Unknown fitting method: {fitting_method}")

    # --- Compute and print chi-squared diagnostics ---
    mod_flux = results['mod_flux']
    obs_flux = phot_data['obs_flux']
    obs_err  = phot_data['obs_err']
    error_floor = config['fitting'].get('error_floor', 0.05)
    eff_err  = np.sqrt(obs_err**2 + (error_floor * obs_flux)**2)
    residuals = (obs_flux - mod_flux) / eff_err
    chi2      = np.sum(residuals**2)
    n_bands   = len(obs_flux)
    n_params  = len(config['fitting']['parameters'])
    dof       = max(n_bands - n_params, 1)
    chi2_red  = chi2 / dof

    print(f"\n[CHI2] Chi-squared diagnostics for {object_id}:")
    print(f"  Bands: {phot_data.get('bands', n_bands)}")
    print(f"  Chi2 = {chi2:.3f}  |  DOF = {dof}  |  Chi2/DOF = {chi2_red:.3f}")
    for i, band in enumerate(phot_data.get('bands', range(n_bands))):
        print(f"  {band}: obs={obs_flux[i]:.3e} Jy  mod={mod_flux[i]:.3e} Jy  "
              f"residual={residuals[i]:+.2f} sigma")

    results['chi2']     = chi2
    results['chi2_red'] = chi2_red
    results['residuals'] = residuals

    # Generate SED plot (always)
    plotting = Plotting(plot_config)
    plotting.plot_sed(phot_data, results, ssp_model=ssp_model)

    # Generate residuals plot (always, so ML runs also get a diagnostic)
    _plot_residuals(phot_data, results, plot_config, object_id)
    
    # Save photometry if requested
    if config.get('output', {}).get('save_photometry', False):
        import pandas as pd
        phot_df = pd.DataFrame({
            'wavelength': phot_data['wavelength'],
            'obs_flux': phot_data['obs_flux'],
            'obs_err': phot_data['obs_err'],
            'mod_flux': results['mod_flux']
        })
        phot_path = os.path.join(object_output_dir, f'{object_id}_photometry.csv')
        phot_df.to_csv(phot_path, index=False)
        print(f"Saved photometry to: {phot_path}")
    
    # Print results
    print(f"\nResults for {object_id} (z={redshift:.5f}):")
    for param, value in results['parameters'].items():
        if fitting_method == 'mcmc' and 'percentiles' in results:
            stats = results['percentiles'][param]
            print(f"  {param}: {stats['median']:.4f} +{stats['upper']:.4f} -{stats['lower']:.4f}")
        else:
            print(f"  {param}: {value:.4f}")
    print(f"  Log-likelihood : {results['log_likelihood']:.2f}")
    print(f"  Chi2/DOF       : {chi2_red:.3f}  ({'good' if chi2_red < 2 else 'poor — check model/data'})")
    
    # Add metadata
    results['object_id'] = object_id
    results['output_dir'] = object_output_dir
    results['redshift'] = redshift
    
    return results


def _plot_residuals(phot_data, results, plot_config, object_id):
    """Save a simple residuals bar chart so ML fits have a diagnostic plot."""
    import matplotlib.pyplot as plt

    bands     = phot_data.get('bands', [str(i) for i in range(len(phot_data['obs_flux']))])
    residuals = results['residuals']
    chi2_red  = results['chi2_red']

    fig, ax = plt.subplots(figsize=(6, 3))
    colors = ['#d62728' if abs(r) > 2 else '#1f77b4' for r in residuals]
    ax.bar(bands, residuals, color=colors)
    ax.axhline(0,  color='k', linewidth=0.8)
    ax.axhline( 1, color='k', linewidth=0.4, linestyle='--')
    ax.axhline(-1, color='k', linewidth=0.4, linestyle='--')
    ax.axhline( 2, color='r', linewidth=0.4, linestyle=':')
    ax.axhline(-2, color='r', linewidth=0.4, linestyle=':')
    ax.set_ylabel('Residual (σ)')
    ax.set_title(f'{object_id}  —  χ²/DOF = {chi2_red:.2f}')
    fig.tight_layout()

    out_path = os.path.join(plot_config['output_dir'], 'residuals.png')
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved residuals plot: {out_path}")


def save_summary(all_results, output_dir, config):
    """Save summary of all fits to a CSV file."""
    import pandas as pd
    
    rows = []
    for result in all_results:
        if result is None:
            continue
        
        row = {
            'object_id':    result['object_id'],
            'redshift':     result.get('redshift', np.nan),
            'log_likelihood': result['log_likelihood'],
            'chi2':         result.get('chi2', np.nan),
            'chi2_red':     result.get('chi2_red', np.nan),
        }
        
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
        print("\n" + "="*70)
        print("SUMMARY OF ALL FITS")
        print("="*70)
        print(df.to_string(index=False))
        print("="*70)


def main(config_path: str | None = None) -> None:
    # Load configuration
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    if not os.path.exists(config_path):
        print(f"Configuration file not found at {config_path}")
        return

    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)

    # Get input data
    try:
        datasets = get_input_data(config)
    except Exception as e:
        print(f"ERROR loading input data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not datasets:
        print("ERROR: No input data found. Check your config.yaml")
        return
    
    print(f"\nFound {len(datasets)} object(s) to process")
    
    # Get base SSP model config
    ssp_model_base_config = config['ssp_model']
    
    # Create output directory
    base_output_dir = config['plotting']['output_dir']
    os.makedirs(base_output_dir, exist_ok=True)
    
    # Process each object
    all_results = []
    for i, (object_id, phot_data) in enumerate(datasets):
        print(f"\n[{i+1}/{len(datasets)}] Processing {object_id}...")
        
        try:
            result = process_single_object(object_id, phot_data, config, ssp_model_base_config)
            all_results.append(result)
        except Exception as e:
            print(f"ERROR processing {object_id}: {e}")
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