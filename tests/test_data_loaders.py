"""Tests for data loaders (src/data/)"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data.phangs_loader import load_phangs_fits


class TestPHANGSLoader:
    """Test PHANGS FITS loader."""
    
    def test_phangs_loader_basic(self):
        """Test PHANGS loader on real file (if available)."""
        test_file = Path("/Users/snehanair/Downloads/catalogs 2/hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits")
        
        if not test_file.exists():
            pytest.skip("PHANGS test file not available")
        
        datasets = load_phangs_fits(str(test_file), max_rows=5, min_valid_bands=3)
        
        assert len(datasets) > 0
        
        for obj_id, phot_data in datasets:
            assert 'wavelength' in phot_data
            assert 'obs_flux' in phot_data
            assert 'obs_err' in phot_data
            assert 'bands' in phot_data
            assert len(phot_data['wavelength']) >= 3
            assert np.all(phot_data['obs_flux'] > 0)
            assert np.all(np.isfinite(phot_data['obs_flux']))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
