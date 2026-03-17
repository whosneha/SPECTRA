"""Basic sanity checks for the Likelihood class."""

import numpy as np
import pytest


@pytest.fixture
def simple_likelihood():
    from src.likelihood import Likelihood
    obs_flux = np.array([1.0e-3, 2.0e-3, 3.0e-3])
    obs_err  = np.array([1.0e-4, 1.0e-4, 1.0e-4])
    priors   = {
        'mass':        [8.0, 14.0],
        'age':         [0.01, 13.5],
        'metallicity': [-2.5, 0.5],
        'dust':        [0.0, 2.0],
    }
    return Likelihood(obs_flux=obs_flux, obs_err=obs_err, priors=priors, error_floor=0.05)


def test_likelihood_instantiates(simple_likelihood):
    assert simple_likelihood is not None


def test_log_likelihood_is_finite(simple_likelihood):
    mod_flux = np.array([1.0e-3, 2.0e-3, 3.0e-3])
    params   = {'mass': 11.0, 'age': 1.0, 'metallicity': -0.5, 'dust': 0.1}
    ll = simple_likelihood(params, mod_flux)
    assert np.isfinite(ll)


def test_perfect_fit_beats_bad_fit(simple_likelihood):
    perfect = np.array([1.0e-3, 2.0e-3, 3.0e-3])
    bad     = np.array([9.0e-3, 9.0e-3, 9.0e-3])
    params  = {'mass': 11.0, 'age': 1.0, 'metallicity': -0.5, 'dust': 0.1}
    assert simple_likelihood(params, perfect) > simple_likelihood(params, bad)
