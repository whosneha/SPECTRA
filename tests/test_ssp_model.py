"""Tests for SSP model (src/models/ssp_model.py)"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.ssp_model import SSPModel


class TestSSPModelInitialization:
    """Test SSP model initialization."""
    
    def test_mock_mode_initialization(self):
        """Test mock mode initializes correctly."""
        config = {'type': 'mock', 'redshift': 0.0, 'distance_mpc': 10.0}
        model = SSPModel(config)
        assert model.mock_mode is True
        assert model.redshift == 0.0
        assert model.distance_mpc == 10.0
    
    def test_fsps_fallback_to_mock(self):
        """Test FSPS falls back to mock if SPS_HOME not set."""
        import os
        if 'SPS_HOME' in os.environ:
            pytest.skip("FSPS is installed")
        
        config = {'type': 'fsps'}
        model = SSPModel(config)
        assert model.mock_mode is True


class TestFluxCalibration:
    """Test flux calibration functionality."""
    
    def test_calibration_with_wavelengths(self):
        """Test V-band calibration."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([2700, 4400, 5500, 8000])  # Å
        obs_flux = np.array([1e-6, 1.5e-6, 2e-6, 1.8e-6])
        
        model.set_flux_calibration(obs_flux, wavelengths=wavelengths)
        
        # Should calibrate to V-band (5500 Å)
        assert model.flux_calibration == 2e-6
    
    def test_calibration_without_wavelengths(self):
        """Test median calibration."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        obs_flux = np.array([1e-6, 2e-6, 3e-6])
        model.set_flux_calibration(obs_flux)
        
        assert model.flux_calibration == 2e-6  # median


class TestMockFluxGeneration:
    """Test mock SSP flux generation."""
    
    def test_flux_generation_basic(self):
        """Test mock model generates valid fluxes."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([2700, 4400, 5500, 8000])
        model.set_flux_calibration(np.array([1e-6]*4), wavelengths=wavelengths)
        
        fluxes = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=-0.5, dust=0.1,
            wavelengths=wavelengths
        )
        
        assert len(fluxes) == 4
        assert np.all(fluxes > 0)
        assert np.all(np.isfinite(fluxes))
    
    def test_mass_scaling(self):
        """Test flux scales with mass."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([5500])
        model.set_flux_calibration(np.array([1e-6]), wavelengths=wavelengths)
        
        flux_low = model.get_magnitudes(mass=3.0, age=0.5, metallicity=0.0, dust=0.0,
                                         wavelengths=wavelengths)[0]
        flux_high = model.get_magnitudes(mass=5.0, age=0.5, metallicity=0.0, dust=0.0,
                                          wavelengths=wavelengths)[0]
        
        # Higher mass → higher flux
        assert flux_high > flux_low
        # Should scale as 10^2 = 100
        assert 50 < flux_high / flux_low < 200
    
    def test_age_dependency(self):
        """Test younger clusters are brighter."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([5500])
        model.set_flux_calibration(np.array([1e-6]), wavelengths=wavelengths)
        
        flux_young = model.get_magnitudes(mass=4.5, age=0.01, metallicity=0.0, dust=0.0,
                                           wavelengths=wavelengths)[0]
        flux_old = model.get_magnitudes(mass=4.5, age=1.0, metallicity=0.0, dust=0.0,
                                         wavelengths=wavelengths)[0]
        
        # Young clusters brighter (lower M/L)
        assert flux_young > flux_old


class TestDustAttenuation:
    """Test Calzetti dust attenuation."""
    
    def test_dust_reduces_flux(self):
        """Test dust reduces flux."""
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
        
        assert np.all(flux_with_dust < flux_no_dust)
    
    def test_uv_more_attenuated_than_optical(self):
        """Test UV is more attenuated than optical."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([2700, 5500])  # UV, optical
        model.set_flux_calibration(np.array([1e-6, 1e-6]), wavelengths=wavelengths)
        
        flux_no_dust = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=0.0, dust=0.0,
            wavelengths=wavelengths
        )
        
        flux_with_dust = model.get_magnitudes(
            mass=4.5, age=0.5, metallicity=0.0, dust=0.5,
            wavelengths=wavelengths
        )
        
        # UV attenuation fraction > optical attenuation fraction
        uv_atten = flux_with_dust[0] / flux_no_dust[0]
        opt_atten = flux_with_dust[1] / flux_no_dust[1]
        assert uv_atten < opt_atten


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_dust(self):
        """Test E(B-V) = 0 works correctly."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([5500])
        model.set_flux_calibration(np.array([1e-6]), wavelengths=wavelengths)
        
        flux = model.get_magnitudes(mass=4.5, age=0.5, metallicity=0.0, dust=0.0,
                                     wavelengths=wavelengths)
        assert flux[0] > 0
    
    def test_very_young_age(self):
        """Test very young ages (1 Myr) work."""
        config = {'type': 'mock', 'redshift': 0.0}
        model = SSPModel(config)
        
        wavelengths = np.array([5500])
        model.set_flux_calibration(np.array([1e-6]), wavelengths=wavelengths)
        
        flux = model.get_magnitudes(mass=4.5, age=0.001, metallicity=0.0, dust=0.0,
                                     wavelengths=wavelengths)
        assert flux[0] > 0
        assert np.isfinite(flux[0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
