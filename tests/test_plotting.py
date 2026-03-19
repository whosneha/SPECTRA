"""Tests for plotting utilities (src/utils/plotting.py)"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.plotting import Plotting
from src.models.ssp_model import SSPModel


class TestPlottingInitialization:
    """Test plotting initialization."""
    
    def test_basic_initialization(self):
        """Test plotting initializes with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {'output_dir': tmpdir, 'formats': ['png']}
            plotting = Plotting(config)
            
            assert plotting.output_dir == tmpdir
            assert plotting.formats == ['png']


class TestSEDPlotting:
    """Test SED plot generation."""
    
    def test_plot_sed_creates_file(self):
        """Test SED plot creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {'output_dir': tmpdir, 'formats': ['png']}
            plotting = Plotting(config)
            
            # Create mock data
            phot_data = {
                'wavelength': np.array([2700, 4400, 5500, 8000]),
                'obs_flux': np.array([1e-6, 1.5e-6, 2e-6, 1.8e-6]),
                'obs_err': np.array([1e-7, 1.5e-7, 2e-7, 1.8e-7]),
                'bands': ['F275W', 'F438W', 'F555W', 'F814W'],
                'object_id': 'test_cluster',
                'redshift': 0.0
            }
            
            results = {
                'parameters': {'mass': 4.5, 'age': 0.5, 'metallicity': -0.5, 'dust': 0.1},
                'mod_flux': np.array([1.1e-6, 1.4e-6, 1.9e-6, 1.7e-6]),
                'log_likelihood': -5.0
            }
            
            model = SSPModel({'type': 'mock', 'redshift': 0.0})
            model.set_flux_calibration(phot_data['obs_flux'], wavelengths=phot_data['wavelength'])
            
            # Generate plot
            plotting.plot_sed(phot_data, results, ssp_model=model)
            
            # Check file was created
            expected_file = Path(tmpdir) / 'sed_fit_test_cluster.png'
            assert expected_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
