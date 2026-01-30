import numpy as np
import emcee
from multiprocessing import Pool

class MCMCRunner:
    """Run MCMC fitting using emcee."""
    
    def __init__(self, likelihood, ssp_model, config=None):
        """
        Initialize MCMC runner.
        
        Args:
            likelihood: Likelihood object with log_posterior method
            ssp_model: SSP model object with get_magnitudes method
            config: Dict with mcmc configuration (n_walkers, n_steps, etc.)
        """
        self.likelihood = likelihood
        self.ssp_model = ssp_model
        self.config = config or {}
        
        self.n_walkers = self.config.get('n_walkers', 32)
        self.n_steps = self.config.get('n_steps', 1000)
        self.n_burnin = self.config.get('n_burnin', 300)
        self.n_threads = self.config.get('n_threads', 1)
        self.thin = self.config.get('thin', 1)  # Thinning factor
        
        self.sampler = None
        self.samples = None
        self.wavelengths = None
    
    def set_wavelengths(self, wavelengths):
        """Set wavelength array for model."""
        self.wavelengths = wavelengths
    
    def log_probability(self, params_array, param_names):
        """
        Compute log probability for emcee.
        
        Args:
            params_array: Array of parameter values
            param_names: List of parameter names
            
        Returns:
            float: log probability
        """
        params = dict(zip(param_names, params_array))
        
        # Compute prior
        lp = self.likelihood.log_prior(params)
        if not np.isfinite(lp):
            return -np.inf
        
        # Compute likelihood
        try:
            mod_flux = self.ssp_model.get_magnitudes(
                wavelengths=self.wavelengths,
                **params
            )
            ll = self.likelihood.log_likelihood(mod_flux)
            return lp + ll
        except Exception as e:
            print(f"Error computing likelihood: {e}")
            return -np.inf
    
    def run(self, initial_params, bounds, param_names, use_pool=False):
        """
        Run MCMC fitting.
        
        Args:
            initial_params: Dict {param: initial_value}
            bounds: List of (min, max) tuples for each parameter
            param_names: List of parameter names
            use_pool: Whether to use multiprocessing
            
        Returns:
            dict: MCMC results with samples, acceptance fraction, etc.
        """
        # Initialize walker positions spread across the prior volume
        # Use Latin hypercube-like initialization for better coverage
        p0_base = np.array([initial_params[p] for p in param_names])
        n_dim = len(param_names)
        
        # Spread walkers more broadly across prior space
        pos = np.zeros((self.n_walkers, n_dim))
        for i, (pmin, pmax) in enumerate(bounds):
            # Use uniform distribution across 20%-80% of prior range
            prior_range = pmax - pmin
            pos[:, i] = pmin + 0.2 * prior_range + 0.6 * prior_range * np.random.rand(self.n_walkers)
        
        print(f"Running MCMC with {self.n_walkers} walkers for {self.n_steps} steps...")
        print(f"Burn-in: {self.n_burnin} steps, Thinning: {self.thin}")
        print(f"Initial positions span:")
        for i, p in enumerate(param_names):
            print(f"  {p}: {pos[:, i].min():.3f} to {pos[:, i].max():.3f}")
        
        # DEBUG: Check what fluxes we get at the center of the prior
        test_params = {p: (bounds[i][0] + bounds[i][1]) / 2 for i, p in enumerate(param_names)}
        test_flux = self.ssp_model.get_magnitudes(wavelengths=self.wavelengths, **test_params)
        print(f"\n[MCMC DEBUG] Test flux at prior center:")
        print(f"  Parameters: {test_params}")
        print(f"  Flux range: {test_flux.min():.2e} to {test_flux.max():.2e} Jy")
        print(f"  Observed flux range: {self.likelihood.obs_flux.min():.2e} to {self.likelihood.obs_flux.max():.2e} Jy")
        print(f"  Ratio (model/obs): {np.median(test_flux)/np.median(self.likelihood.obs_flux):.2f}")
        
        # Create sampler
        if use_pool and self.n_threads > 1:
            with Pool(self.n_threads) as pool:
                self.sampler = emcee.EnsembleSampler(
                    self.n_walkers, n_dim, 
                    self.log_probability, 
                    args=(param_names,),
                    pool=pool
                )
                self.sampler.run_mcmc(pos, self.n_steps, progress=True)
        else:
            self.sampler = emcee.EnsembleSampler(
                self.n_walkers, n_dim, 
                self.log_probability, 
                args=(param_names,)
            )
            self.sampler.run_mcmc(pos, self.n_steps, progress=True)
        
        # Extract samples after burn-in with thinning
        self.samples = self.sampler.get_chain(discard=self.n_burnin, thin=self.thin, flat=True)
        
        # Compute statistics
        acceptance_fraction = np.mean(self.sampler.acceptance_fraction)
        print(f"Mean acceptance fraction: {acceptance_fraction:.3f}")
        
        # Check for convergence issues
        if acceptance_fraction < 0.1:
            print("WARNING: Low acceptance fraction. Chain may not have converged.")
        elif acceptance_fraction > 0.5:
            print("WARNING: High acceptance fraction. Consider using larger step sizes.")
        
        # Get best-fit parameters (median of posterior)
        medians = np.median(self.samples, axis=0)
        best_params = dict(zip(param_names, medians))
        
        # Compute credible intervals
        percentiles = {}
        for i, param in enumerate(param_names):
            p16, p50, p84 = np.percentile(self.samples[:, i], [16, 50, 84])
            percentiles[param] = {
                'median': p50,
                'lower': p50 - p16,
                'upper': p84 - p50,
                'samples': self.samples[:, i]
            }
            # Check if hitting boundaries
            pmin, pmax = bounds[i]
            if p50 - p16 < 0.1 * (pmax - pmin) and p50 < pmin + 0.15 * (pmax - pmin):
                print(f"WARNING: {param} is hitting lower prior bound")
            if p84 - p50 < 0.1 * (pmax - pmin) and p50 > pmax - 0.15 * (pmax - pmin):
                print(f"WARNING: {param} is hitting upper prior bound")
        
        # Compute log likelihood at best-fit
        mod_flux_best = self.ssp_model.get_magnitudes(
            wavelengths=self.wavelengths,
            **best_params
        )
        log_likelihood_best = self.likelihood.log_likelihood(mod_flux_best)
        
        return {
            'samples': self.samples,
            'parameters': best_params,
            'percentiles': percentiles,
            'log_likelihood': log_likelihood_best,
            'acceptance_fraction': acceptance_fraction,
            'mod_flux': mod_flux_best,
            'sampler': self.sampler
        }
    
    def get_samples(self):
        """Return flattened MCMC samples."""
        if self.samples is None:
            raise RuntimeError("No samples available. Run MCMC first.")
        return self.samples
    
    def save_results(self, filepath):
        """Save MCMC results to HDF5."""
        if self.samples is None:
            raise RuntimeError("No samples to save.")
        
        try:
            import h5py
            with h5py.File(filepath, 'w') as f:
                f.create_dataset('samples', data=self.samples)
                f.create_dataset('chain', data=self.sampler.get_chain())
                f.create_dataset('log_prob', data=self.sampler.get_log_prob())
                f.attrs['n_walkers'] = self.n_walkers
                f.attrs['n_steps'] = self.n_steps
                f.attrs['n_burnin'] = self.n_burnin
            print(f"Saved MCMC results to {filepath}")
        except ImportError:
            print("h5py not installed. Cannot save results.")