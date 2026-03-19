"""Integration tests for full pipeline (src/main.py)"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.main import process_single_object
from src.cli import validate_config


@pytest.mark.integration
class TestFullPipeline:
    """Test end-to-end pipeline."""
    
    def test_pipeline_mock_data(self):
        """Test full pipeline on synthetic data."""
        phot_data = {
            'wavelength': np.array([2700, 4400, 5500, 8000]),
            'obs_flux': np.array([8e-7, 1.2e-6, 1.5e-6, 1.3e-6]),
            'obs_err': np.array([8e-8, 1.2e-7, 1.5e-7, 1.3e-7]),
            'bands': ['F275W', 'F438W', 'F555W', 'F814W'],
            'redshift': 0.0,
            'object_id': 'test_cluster'
        }
        
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
        
        result = process_single_object('test_cluster', phot_data, config, ssp_config)
        
        assert 'parameters' in result
        assert 'log_likelihood' in result
        assert 'chi2_red' in result
        assert result['chi2_red'] < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
