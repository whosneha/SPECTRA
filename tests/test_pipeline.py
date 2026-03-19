"""
Test suite for SPECTRA pipeline components.
Run with: pytest tests/
"""

import pytest
import numpy as np
import os
import tempfile
import yaml
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.ssp_model import SSPModel
from src.likelihood import Likelihood
from src.fit import SEDFitter


class TestSSPModel:
    """Test SSP model functionality."""
    
    def test_mock_model_initialization(self):
        """Test mock mode initializes correctly."""
        config = {'type': 'mock', 'redshift': 0.0, 'distance_mpc': 10.0}
        model = SSPModel(config)
        assert model.mock_mode is True
        
    def test_mock_model_flux_generation(self):
        """Test mock model generates reasonable fluxes."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([2700, 4400, 5500, 8000])  # Å
        model.set_flux_calibration(np.array([1e-6]*4), wavelengths=wavelengths)
        
        fluxes = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=-0.5, dust=0.1,
            wavelengths=wavelengths
        )
        
        assert len(fluxes) == 4
        assert np.all(fluxes > 0)
        assert np.all(np.isfinite(fluxes))
        
    def test_dust_attenuation(self):
        """Test dust reduces flux correctly."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([2700, 5500])
        model.set_flux_calibration(np.array([1e-6, 1e-6]), wavelengths=wavelengths)
        
        flux_no_dust = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=0.0, dust=0.0,
            wavelengths=wavelengths
        )
        
        flux_with_dust = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=0.0, dust=0.5,
            wavelengths=wavelengths
        )
        
        # UV should be more attenuated than optical
        assert flux_with_dust[0] < flux_no_dust[0]
        assert flux_with_dust[1] < flux_no_dust[1]
        assert (flux_with_dust[0] / flux_no_dust[0]) < (flux_with_dust[1] / flux_no_dust[1])


class TestLikelihood:
    """Test likelihood computation."""
    
    def test_likelihood_initialization(self):
        """Test likelihood initializes with error floor."""
        obs_flux = np.array([1e-6, 2e-6, 3e-6])
        obs_err = np.array([1e-7, 2e-7, 3e-7])
        priors = {'mass': [3.0, 6.0], 'age': [0.001, 1.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors, error_floor=0.05)
        
        assert len(likelihood.eff_err) == 3
        assert np.all(likelihood.eff_err >= obs_err)
        
    def test_log_prior(self):
        """Test prior bounds are enforced."""
        obs_flux = np.array([1e-6, 2e-6])
        obs_err = np.array([1e-7, 2e-7])
        priors = {'mass': [3.0, 6.0], 'age': [0.001, 1.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        # Valid parameters
        assert likelihood.log_prior({'mass': 4.5, 'age': 0.5}) == 0.0
        
        # Out of bounds
        assert likelihood.log_prior({'mass': 7.0, 'age': 0.5}) == -np.inf
        assert likelihood.log_prior({'mass': 4.5, 'age': 2.0}) == -np.inf
        
    def test_log_likelihood(self):
        """Test chi-squared computation."""
        obs_flux = np.array([1.0, 2.0, 3.0])
        obs_err = np.array([0.1, 0.2, 0.3])
        
        likelihood = Likelihood(obs_flux, obs_err, error_floor=0.0)
        
        # Perfect match
        mod_flux = np.array([1.0, 2.0, 3.0])
        ll = likelihood.log_likelihood(mod_flux)
        assert ll == 0.0
        
        # Poor match
        mod_flux = np.array([2.0, 4.0, 6.0])
        ll = likelihood.log_likelihood(mod_flux)
        assert ll < -10  # Large negative log-likelihood


class TestFitter:
    """Test SED fitting."""
    
    def test_ml_fitting_converges(self):
        """Test ML fitting finds reasonable parameters."""
        # Create synthetic data
        true_params = {'mass': 4.5, 'age': 0.5, 'metallicity': -0.5, 'dust': 0.1}
        wavelengths = np.array([2700, 4400, 5500, 8000])
        
        # Generate "observed" data
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        model.set_flux_calibration(np.array([1e-6]*4), wavelengths=wavelengths)
        
        obs_flux = model.get_magnitudes(wavelengths=wavelengths, **true_params)
        obs_err = 0.05 * obs_flux  # 5% errors
        
        # Add noise
        np.random.seed(42)
        obs_flux += np.random.normal(0, obs_err)
        
        # Fit
        priors = {
            'mass': [3.0, 6.0],
            'age': [0.001, 1.0],
            'metallicity': [-1.5, 0.3],
            'dust': [0.0, 1.0]
        }
        likelihood = Likelihood(obs_flux, obs_err, priors, error_floor=0.05)
        fitter = SEDFitter(likelihood, model, wavelengths=wavelengths)
        
        initial = {'mass': 4.0, 'age': 0.3, 'metallicity': -0.8, 'dust': 0.2}
        bounds = [(3.0, 6.0), (0.001, 1.0), (-1.5, 0.3), (0.0, 1.0)]
        
        result = fitter.fit_maximum_likelihood(initial, bounds)
        
        assert result['success']
        # Check parameters are close to truth (within ~20%)
        assert abs(result['parameters']['mass'] - true_params['mass']) < 0.5
        assert abs(result['parameters']['age'] - true_params['age']) < 0.3


class TestDataLoaders:
    """Test data loading functions."""
    
    def test_phangs_loader_handles_missing_data(self):
        """Test PHANGS loader skips rows with insufficient data."""
        from src.data.phangs_loader import load_phangs_fits
        
        # This requires a real PHANGS file - skip if not available
        test_file = Path("/Users/snehanair/Downloads/catalogs 2/hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits")
        
        if not test_file.exists():
            pytest.skip("PHANGS test file not available")
        
        datasets = load_phangs_fits(str(test_file), max_rows=5, min_valid_bands=3)
        
        assert len(datasets) > 0
        for obj_id, phot_data in datasets:
            assert 'wavelength' in phot_data
            assert 'obs_flux' in phot_data
            assert len(phot_data['wavelength']) >= 3
            assert np.all(phot_data['obs_flux'] > 0)


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_config_validation(self):
        """Test config file validation."""
        from src.cli import validate_config
        
        # Create temporary valid config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                'input': {'type': 'mock'},
                'ssp_model': {'type': 'mock'},
                'fitting': {
                    'method': 'ml',
                    'parameters': ['mass', 'age'],
                    'priors': {'mass': [3.0, 6.0], 'age': [0.001, 1.0]}
                },
                'plotting': {'output_dir': 'test_output'}
            }, f)
            config_path = f.name
        
        try:
            result = validate_config(config_path)
            assert result == 0  # Success
        finally:
            os.unlink(config_path)
    
    def test_full_pipeline_mock_data(self):
        """Test full pipeline on synthetic data."""
        from src.main import process_single_object
        
        # Create synthetic photometry
        phot_data = {
            'wavelength': np.array([2700, 4400, 5500, 8000]),
            'obs_flux': np.array([8e-7, 1.2e-6, 1.5e-6, 1.3e-6]),
            'obs_err': np.array([8e-8, 1.2e-7, 1.5e-7, 1.3e-7]),
            'bands': ['F275W', 'F438W', 'F555W', 'F814W'],
            'redshift': 0.0,
            'object_id': 'test_cluster'
        }
        
        # Create minimal config
        config = {
            'ssp_model': {'type': 'mock', 'redshift': 0.0},
            'fitting': {
                'method': 'ml',
                'error_floor': 0.05,
                'parameters': ['mass', 'age', 'metallicity', 'dust'],
                'priors': {
                    'mass': [3.0, 6.0],
                    'age': [0.001, 1.0],
                    'metallicity': [-1.5, 0.3],
                    'dust': [0.0, 1.0]
                }
            },
            'plotting': {'output_dir': tempfile.mkdtemp()},
            'output': {'save_photometry': False}
        }
        
        ssp_config = config['ssp_model']
        
        try:
            result = process_single_object('test_cluster', phot_data, config, ssp_config)
            
            assert 'parameters' in result
            assert 'log_likelihood' in result
            assert 'chi2_red' in result
            assert result['chi2_red'] < 100  # Reasonable fit
            
        except Exception as e:
            pytest.fail(f"Pipeline failed: {e}")


def test_imports():
    """Test all critical imports work."""
    try:
        from src.models.ssp_model import SSPModel
        from src.likelihood import Likelihood
        from src.fit import SEDFitter
        from src.mcmc.mcmc_runner import MCMCRunner
        from src.utils.plotting import Plotting
        from src.data.data_loader import DataLoader
        from src.cli import main
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
