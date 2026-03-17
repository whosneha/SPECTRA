"""
SPECTRA: Stellar Population Extractor for Clusters via
Template-fitted Resolved Aperture photometry.

Public API
----------
run_pipeline(config_path)   Run the full SED fitting pipeline from a config file.
"""

from spectra.main import main as run_pipeline

__all__ = ["run_pipeline"]
__version__ = "0.1.0"
