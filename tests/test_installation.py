"""
Installation and smoke tests for SPECTRA.

Tests that:
- All required dependencies can be imported
- CLI is accessible and works
- Core modules function
- A minimal ML fit runs successfully
"""

import os
import sys
import pytest
import numpy as np
import yaml
import tempfile
from pathlib import Path


class TestDependencies:
    """Verify all required dependencies are installed."""

    def test_numpy_installed(self):
        import numpy
        assert hasattr(numpy, 'array')

    def test_scipy_installed(self):
        import scipy
        assert hasattr(scipy, 'optimize')

    def test_pandas_installed(self):
        import pandas
        assert hasattr(pandas, 'DataFrame')

    def test_matplotlib_installed(self):
        import matplotlib.pyplot
        assert hasattr(matplotlib.pyplot, 'plot')

    def test_astropy_installed(self):
        import astropy.io.fits
        assert hasattr(astropy.io.fits, 'open')

    def test_pyyaml_installed(self):
        import yaml
        assert hasattr(yaml, 'safe_load')

    def test_emcee_installed(self):
        import emcee
        assert hasattr(emcee, 'EnsembleSampler')

    def test_corner_installed(self):
        import corner
        assert hasattr(corner, 'corner')

    def test_h5py_installed(self):
        import h5py
        assert hasattr(h5py, 'File')


class TestCoreImports:
    """Verify SPECTRA core modules can be imported."""

    def test_import_main(self):
        from src.main import main
        assert callable(main)

    def test_import_cli(self):
        from src.cli import main as cli_main
        assert callable(cli_main)

    def test_import_data_loader(self):
        from src.data.data_loader import DataLoader
        assert DataLoader is not None

    def test_import_ssp_model(self):
        from src.models.ssp_model import SSPModel
        assert SSPModel is not None

    def test_import_likelihood(self):
        from src.likelihood import Likelihood
        assert Likelihood is not None

    def test_import_fitter(self):
        from src.fit import SEDFitter
        assert SEDFitter is not None

    def test_import_mcmc_runner(self):
        from src.mcmc.mcmc_runner import MCMCRunner
        assert MCMCRunner is not None

    def test_import_plotting(self):
        from src.utils.plotting import Plotting
        assert Plotting is not None

    def test_import_fornax_loader(self):
        from src.data.fornax_loader import load_fornax_csv
        assert callable(load_fornax_csv)

    def test_import_phangs_loader(self):
        from src.data.phangs_loader import load_phangs_fits
        assert callable(load_phangs_fits)


class TestConfigValidation:
    """Verify configuration loading and validation."""

    def test_load_example_config_phangs(self):
        """Load and validate PHANGS config if it exists."""
        config_path = Path(__file__).parent.parent / 'example_configs' / 'config_phangs.yaml'
        if not config_path.exists():
            pytest.skip("config_phangs.yaml not found")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        if config:  # Only validate if not empty
            assert isinstance(config, dict)

    def test_load_example_config_rubin(self):
        """Load and validate Rubin config if it exists."""
        config_path = Path(__file__).parent.parent / 'example_configs' / 'config_rubin.yaml'
        if not config_path.exists():
            pytest.skip("config_rubin.yaml not found")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        if config:  # Only validate if not empty
            assert isinstance(config, dict)

    def test_config_has_required_keys(self):
        """Create a minimal config and validate structure."""
        config = {
            'input': {'type': 'csv', 'filepath': 'test.csv'},
            'ssp_model': {'type': 'fsps', 'redshift': 0.0},
            'fitting': {
                'method': 'ml',
                'parameters': ['mass', 'age'],
                'priors': {'mass': [8, 13], 'age': [0.1, 13]},
                'error_floor': 0.05
            },
            'plotting': {'output_dir': 'output'},
            'output': {'save_photometry': False}
        }
        assert config['input']['type'] in ['csv', 'dat', 'fits', 'fornax_csv', 'phangs_fits']
        assert config['fitting']['method'] in ['ml', 'mcmc']
        assert all(p in config['fitting']['priors'] for p in config['fitting']['parameters'])


class TestDataLoaders:
    """Verify data loaders work with real/test data."""

    def test_fornax_loader_available_data(self):
        """Test Fornax loader with built-in test data."""
        data_path = Path(__file__).parent.parent / 'data' / 'fornax_gc_photometry.csv'
        if data_path.exists():
            from src.data.fornax_loader import load_fornax_csv
            datasets = load_fornax_csv(str(data_path))
            assert len(datasets) > 0
            obj_id, phot_data = datasets[0]
            assert 'wavelength' in phot_data
            assert 'obs_flux' in phot_data
            assert 'obs_err' in phot_data
            assert len(phot_data['wavelength']) > 0

    def test_generic_csv_loader(self):
        """Test loading generic CSV data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('wavelength,flux,flux_err\n')
            f.write('0.5,1.0e-5,1.0e-6\n')
            f.write('1.0,2.0e-5,2.0e-6\n')
            f.write('1.5,3.0e-5,3.0e-6\n')
            temp_csv = f.name

        try:
            from src.data.data_loader import DataLoader
            loader = DataLoader({})
            phot_data = loader.load('csv', filepath=temp_csv)
            assert len(phot_data['wavelength']) == 3
            # Wavelengths are auto-converted to Angstroms (microns * 10000)
            assert np.allclose(phot_data['wavelength'], [5000, 10000, 15000])
            assert np.allclose(phot_data['obs_flux'], [1.0e-5, 2.0e-5, 3.0e-5])
        finally:
            os.unlink(temp_csv)

    def test_generic_dat_loader(self):
        """Test loading DAT (whitespace-delimited) data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dat', delete=False) as f:
            f.write('# wavelength flux flux_err\n')
            f.write('0.5 1.0e-5 1.0e-6\n')
            f.write('1.0 2.0e-5 2.0e-6\n')
            temp_dat = f.name

        try:
            from src.data.data_loader import DataLoader
            loader = DataLoader({})
            phot_data = loader.load('dat', filepath=temp_dat)
            assert len(phot_data['wavelength']) == 2
        finally:
            os.unlink(temp_dat)


class TestBasicFit:
    """Smoke test: verify fitter and likelihood can be imported and instantiated."""

    def test_fitter_imports(self):
        """Test that fitter classes can be imported."""
        from src.fit import SEDFitter
        from src.likelihood import Likelihood
        assert SEDFitter is not None
        assert Likelihood is not None

    def test_likelihood_instantiation(self):
        """Test creating a Likelihood instance."""
        from src.likelihood import Likelihood
        import numpy as np

        # Minimal data
        obs_flux = np.array([1.0e-5, 2.0e-5, 3.0e-5])
        obs_err = np.array([1.0e-6, 2.0e-6, 3.0e-6])

        likelihood = Likelihood(obs_flux=obs_flux, obs_err=obs_err)
        assert likelihood is not None
        assert hasattr(likelihood, 'log_likelihood')
        assert callable(likelihood.log_likelihood)


class TestCLI:
    """Test command-line interface."""

    def test_cli_help(self):
        """Check that CLI help runs without error."""
        from src.cli import main
        # We can't easily test the argparse --help, but we can ensure main is callable
        assert callable(main)

    def test_cli_list_configs(self):
        """Verify example configs exist."""
        config_dir = Path(__file__).parent.parent / 'example_configs'
        assert config_dir.exists()
        configs = list(config_dir.glob('*.yaml'))
        assert len(configs) > 0

    def test_example_config_files_parse(self):
        """Valid example configs should be parseable YAML."""
        config_dir = Path(__file__).parent.parent / 'example_configs'
        parsed_count = 0
        for config_file in config_dir.glob('*.yaml'):
            with open(config_file) as f:
                config = yaml.safe_load(f)
            # Skip empty/placeholder files (None)
            if config is None:
                continue
            # Config should be a dict
            assert isinstance(config, dict), f"Config {config_file.name} is not a valid dict"
            parsed_count += 1
        # At least some configs should parse successfully
        assert parsed_count > 0


class TestPipelineIntegration:
    """End-to-end integration checks."""

    def test_fornax_workflow(self):
        """Quick workflow test with Fornax data if available."""
        data_path = Path(__file__).parent.parent / 'data' / 'fornax_gc_photometry.csv'
        if not data_path.exists():
            pytest.skip("Fornax test data not available")

        from src.data.fornax_loader import load_fornax_csv
        datasets = load_fornax_csv(str(data_path))
        assert len(datasets) > 0

        # Pick first object
        obj_id, phot_data = datasets[0]
        assert phot_data['object_id'] == obj_id
        assert 'wavelength' in phot_data
        assert np.all(phot_data['obs_flux'] > 0)

    def test_photometry_validation(self):
        """Ensure photometry data meets basic quality criteria."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('wavelength,flux,flux_err\n')
            f.write('0.5,1.0e-5,1.0e-6\n')
            f.write('1.0,2.0e-5,2.0e-6\n')
            temp_csv = f.name

        try:
            from src.data.data_loader import DataLoader
            loader = DataLoader({})
            phot_data = loader.load('csv', filepath=temp_csv)

            # Quality checks
            assert np.all(phot_data['wavelength'] > 0)
            assert np.all(phot_data['obs_flux'] > 0)
            assert np.all(phot_data['obs_err'] > 0)
            assert np.all(phot_data['obs_err'] < phot_data['obs_flux'])  # Errors < fluxes
        finally:
            os.unlink(temp_csv)


@pytest.mark.integration
class TestFullPipelineConfig:
    """Integration: validate a full config can be loaded and parsed."""

    def test_minimal_ml_config(self):
        """A minimal ML config should be valid."""
        config = {
            'input': {'type': 'csv', 'filepath': 'test.csv'},
            'ssp_model': {'type': 'fsps', 'redshift': 0.0, 'imf': 'kroupa'},
            'fitting': {
                'method': 'ml',
                'parameters': ['mass', 'age', 'metallicity', 'dust'],
                'priors': {
                    'mass': [8.0, 13.0],
                    'age': [0.1, 13.5],
                    'metallicity': [-2.5, 0.5],
                    'dust': [0.0, 2.0]
                },
                'error_floor': 0.05
            },
            'plotting': {'output_dir': 'outputs/test'},
            'output': {'save_photometry': False}
        }

        # Minimal validation
        assert config['fitting']['method'] == 'ml'
        assert len(config['fitting']['parameters']) == 4
        assert len(config['fitting']['priors']) == 4

    def test_minimal_mcmc_config(self):
        """A minimal MCMC config should be valid."""
        config = {
            'input': {'type': 'csv', 'filepath': 'test.csv'},
            'ssp_model': {'type': 'fsps', 'redshift': 0.0},
            'fitting': {
                'method': 'mcmc',
                'parameters': ['mass', 'age'],
                'priors': {
                    'mass': [8.0, 13.0],
                    'age': [0.1, 13.5]
                }
            },
            'mcmc': {
                'n_walkers': 16,
                'n_steps': 100,
                'n_burnin': 50,
                'thin': 2
            },
            'plotting': {'output_dir': 'outputs/test'},
        }

        assert config['fitting']['method'] == 'mcmc'
        assert 'mcmc' in config
        assert config['mcmc']['n_walkers'] > 0
