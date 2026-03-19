"""Tests for MCMC runner (src/mcmc/mcmc_runner.py)"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.ssp_model import SSPModel
from src.likelihood import Likelihood
from src.mcmc.mcmc_runner import MCMCRunner


class TestMCMCInitialization:
    """Test MCMC runner initialization."""
    
    def test_basic_initialization(self):
        """Test MCMC initializes with config."""
        obs_flux = np.array([1e-6])
        obs_err = np.array([1e-7])
        priors = {'mass': [3.0, 6.0]}
        
        likelihood = Likelihood(obs_flux, obs_err, priors)
        model = SSPModel({'type': 'mock', 'redshift': 0.0})
        
        config = {'n_walkers': 32, 'n_steps': 100, 'n_burnin': 20}
        mcmc = MCMCRunner(likelihood, model, config=config)
        
        assert mcmc.n_walkers == 32
        assert mcmc.n_steps == 100
        assert mcmc.n_burnin == 20


@pytest.mark.slow
class TestMCMCFitting:
    """Test MCMC fitting (slow tests)."""
    
    def test_mcmc_runs(self):
        """Test MCMC completes without errors."""
        # Simple 1-parameter fit for speed
        wavelengths = np.array([5500])
        
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        model.set_flux_calibration(np.array([1e-6]), wavelengths=wavelengths)
        
        obs_flux = model.get_magnitudes(mass=4.5, age=0.5, metallicity=0.0, dust=0.0,
                                         wavelengths=wavelengths)
        obs_err = 0.1 * obs_flux
        
        priors = {'mass': [3.0, 6.0]}
        likelihood = Likelihood(obs_flux, obs_err, priors)
        
        mcmc_config = {'n_walkers': 16, 'n_steps': 50, 'n_burnin': 10, 'thin': 2}
        mcmc = MCMCRunner(likelihood, model, config=mcmc_config)
        mcmc.set_wavelengths(wavelengths)
        
        initial = {'mass': 4.0}
        bounds = [(3.0, 6.0)]
        param_names = ['mass']
        
        result = mcmc.run(initial, bounds, param_names, use_pool=False)
        
        assert 'samples' in result
        assert 'parameters' in result
        assert 'percentiles' in result
        assert len(result['samples']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
