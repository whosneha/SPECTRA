"""Tests for ML fitter (src/fit.py)"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.ssp_model import SSPModel
from src.likelihood import Likelihood
from src.fit import SEDFitter


class TestFitterInitialization:
    """Test fitter initialization."""
    
    def test_basic_initialization(self):
        """Test fitter initializes correctly."""
        obs_flux = np.array([1e-6, 2e-6])
        obs_err = np.array([1e-7, 2e-7])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        model = SSPModel({'type': 'mock', 'redshift': 0.0})
        wavelengths = np.array([4400, 5500])
        
        fitter = SEDFitter(likelihood, model, wavelengths=wavelengths)
        
        assert fitter.likelihood is not None
        assert fitter.ssp_model is not None
        assert len(fitter.wavelengths) == 2


class TestMaximumLikelihood:
    """Test ML fitting."""
    
    def test_fit_converges(self):
        """Test ML fitting converges."""
        # Create synthetic data
        true_params = {'mass': 4.5, 'age': 0.5, 'metallicity': -0.5, 'dust': 0.1}
        wavelengths = np.array([2700, 4400, 5500, 8000])
        
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        model.set_flux_calibration(np.array([1e-6]*4), wavelengths=wavelengths)
        
        obs_flux = model.get_magnitudes(wavelengths=wavelengths, **true_params)
        obs_err = 0.05 * obs_flux
        
        # Add noise
        np.random.seed(42)
        obs_flux += np.random.normal(0, obs_err)
        
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
        assert 'parameters' in result
        assert 'log_likelihood' in result
        assert 'mod_flux' in result
    
    def test_fit_recovers_parameters(self):
        """Test fit recovers true parameters (within uncertainty)."""
        true_params = {'mass': 4.5, 'age': 0.5, 'metallicity': -0.5, 'dust': 0.1}
        wavelengths = np.array([2700, 4400, 5500, 8000])
        
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        model.set_flux_calibration(np.array([1e-6]*4), wavelengths=wavelengths)
        
        obs_flux = model.get_magnitudes(wavelengths=wavelengths, **true_params)
        obs_err = 0.05 * obs_flux
        
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
        
        # Check parameters close to truth (within ~30%)
        assert abs(result['parameters']['mass'] - true_params['mass']) < 0.5
        assert abs(result['parameters']['age'] - true_params['age']) < 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
