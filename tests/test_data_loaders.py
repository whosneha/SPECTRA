"""Tests for data loaders (src/data/)"""

import pytest
import numpy as np
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data.phangs_loader import load_phangs_fits


class TestPHANGSLoader:
    """Test PHANGS FITS loader."""
    
    def test_phangs_loader_basic(self):
        """Test PHANGS loader on real file (if available)."""
        test_file = Path(
            os.environ.get(
                "SPECTRA_PHANGS_TEST_FILE",
                "data/phangs/hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits",
            )
        )
        
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

    def test_external_combiner_preserves_spectra_schema(self):
        """External data should merge into the standard obs_flux/obs_err schema."""
        from src.data.external_sources import ExternalDataCombiner

        primary = {
            'wavelength': np.array([0.47, 0.62]),
            'obs_flux': np.array([1.0e-6, 2.0e-6]),
            'obs_err': np.array([1.0e-7, 2.0e-7]),
            'object_id': 'rubin_1',
            'ra': 10.0,
            'dec': -5.0,
        }
        external = {
            'wavelength': np.array([0.152, 3.4]),
            'flux': np.array([5.0e-7, 1.5e-6]),
            'flux_err': np.array([5.0e-8, 1.0e-7]),
            'source': np.array(['galex', 'allwise']),
        }

        combined = ExternalDataCombiner.combine_with_external(primary, external)

        assert 'obs_flux' in combined
        assert 'obs_err' in combined
        assert 'mod_flux' in combined
        assert len(combined['wavelength']) == 4
        assert combined['object_id'] == 'rubin_1'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
