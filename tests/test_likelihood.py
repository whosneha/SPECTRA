"""Tests for likelihood computation (src/likelihood.py)"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.likelihood import Likelihood


class TestLikelihoodInitialization:
    """Test likelihood initialization."""
    
    def test_basic_initialization(self):
        """Test likelihood initializes correctly."""
        obs_flux = np.array([1e-6, 2e-6, 3e-6])
        obs_err = np.array([1e-7, 2e-7, 3e-7])
        priors = {'mass': [3.0, 6.0], 'age': [0.001, 1.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors, error_floor=0.05)
        
        assert len(likelihood.obs_flux) == 3
        assert len(likelihood.eff_err) == 3
        assert np.all(likelihood.eff_err >= obs_err)
    
    def test_error_floor_applied(self):
        """Test error floor is added in quadrature."""
        obs_flux = np.array([1.0])
        obs_err = np.array([0.01])  # 1% error
        
        likelihood = Likelihood(obs_flux, obs_err, error_floor=0.05)  # 5% floor
        
        # Effective error should be sqrt(0.01^2 + 0.05^2) ≈ 0.051
        expected = np.sqrt(0.01**2 + 0.05**2)
        assert np.isclose(likelihood.eff_err[0], expected, rtol=0.01)


class TestLogPrior:
    """Test prior computation."""
    
    def test_within_bounds(self):
        """Test parameters within bounds return 0."""
        obs_flux = np.array([1e-6])
        obs_err = np.array([1e-7])
        priors = {'mass': [3.0, 6.0], 'age': [0.001, 1.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        assert likelihood.log_prior({'mass': 4.5, 'age': 0.5}) == 0.0
    
    def test_out_of_bounds_mass(self):
        """Test mass out of bounds returns -inf."""
        obs_flux = np.array([1e-6])
        obs_err = np.array([1e-7])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        assert likelihood.log_prior({'mass': 7.0}) == -np.inf
        assert likelihood.log_prior({'mass': 2.0}) == -np.inf
    
    def test_boundary_values(self):
        """Test boundary values are valid."""
        obs_flux = np.array([1e-6])
        obs_err = np.array([1e-7])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        assert likelihood.log_prior({'mass': 3.0}) == 0.0
        assert likelihood.log_prior({'mass': 6.0}) == 0.0


class TestLogLikelihood:
    """Test likelihood computation."""
    
    def test_perfect_match(self):
        """Test perfect match gives log-likelihood = 0."""
        obs_flux = np.array([1.0, 2.0, 3.0])
        obs_err = np.array([0.1, 0.2, 0.3])
        
        likelihood = Likelihood(obs_flux, obs_err, error_floor=0.0)
        
        mod_flux = np.array([1.0, 2.0, 3.0])
        ll = likelihood.log_likelihood(mod_flux)
        
        assert np.isclose(ll, 0.0, atol=1e-10)
    
    def test_poor_match_negative(self):
        """Test poor match gives large negative log-likelihood."""
        obs_flux = np.array([1.0, 2.0, 3.0])
        obs_err = np.array([0.1, 0.2, 0.3])
        
        likelihood = Likelihood(obs_flux, obs_err, error_floor=0.0)
        
        # Model is 2× too high
        mod_flux = np.array([2.0, 4.0, 6.0])
        ll = likelihood.log_likelihood(mod_flux)
        
        assert ll < -10
    
    def test_chi_squared_computation(self):
        """Test chi-squared is computed correctly."""
        obs_flux = np.array([1.0])
        obs_err = np.array([0.1])
        
        likelihood = Likelihood(obs_flux, obs_err, error_floor=0.0)
        
        mod_flux = np.array([1.2])  # 2σ away
        ll = likelihood.log_likelihood(mod_flux)
        
        # log-likelihood = -0.5 * chi2 = -0.5 * 4 = -2
        assert np.isclose(ll, -2.0, atol=0.01)


class TestLogPosterior:
    """Test posterior computation."""
    
    def test_posterior_in_bounds(self):
        """Test posterior = prior + likelihood when in bounds."""
        obs_flux = np.array([1.0])
        obs_err = np.array([0.1])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors, error_floor=0.0)
        
        mod_flux = np.array([1.0])
        params = {'mass': 4.5}
        
        lp = likelihood.log_posterior(mod_flux, params)
        assert np.isfinite(lp)
        assert lp == 0.0  # Perfect match + flat prior
    
    def test_posterior_out_of_bounds(self):
        """Test posterior = -inf when out of bounds."""
        obs_flux = np.array([1.0])
        obs_err = np.array([0.1])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        mod_flux = np.array([1.0])
        params = {'mass': 7.0}  # Out of bounds
        
        lp = likelihood.log_posterior(mod_flux, params)
        assert lp == -np.inf


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
