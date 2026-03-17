"""Tests for the Fornax GC CSV loader."""

import os
import pytest
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fornax_gc_photometry.csv')


def test_loader_returns_four_clusters():
    from src.data.fornax_loader import load_fornax_csv
    datasets = load_fornax_csv(DATA_PATH)
    assert len(datasets) == 4


def test_phot_data_keys():
    from src.data.fornax_loader import load_fornax_csv
    _, phot_data = load_fornax_csv(DATA_PATH)[0]
    for key in ('wavelength', 'obs_flux', 'obs_err', 'bands', 'redshift', 'object_id'):
        assert key in phot_data


def test_flux_units_are_jy():
    """Fluxes should be in Jy (converted from nJy), i.e. < 1 Jy for typical GCs."""
    from src.data.fornax_loader import load_fornax_csv
    for _, phot_data in load_fornax_csv(DATA_PATH):
        assert np.all(phot_data['obs_flux'] < 1.0), "Fluxes look too large — nJy->Jy conversion may be broken"


def test_redshift_is_nonzero():
    from src.data.fornax_loader import load_fornax_csv
    for _, phot_data in load_fornax_csv(DATA_PATH):
        assert phot_data['redshift'] == pytest.approx(0.00032)


def test_missing_band_clusters_have_two_bands():
    """ESO356-SC005 and FornaxGC6 are missing g-band — should have 2 bands."""
    from src.data.fornax_loader import load_fornax_csv
    datasets = dict(load_fornax_csv(DATA_PATH))
    assert len(datasets['ESO356-SC005']['bands']) == 2
    assert len(datasets['FornaxGC6']['bands']) == 2
