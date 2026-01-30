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
        # Initialize walker positions with small random perturbations
        p0 = np.array([initial_params[p] for p in param_names])
        pos = p0 + 1e-4 * np.random.randn(self.n_walkers, len(param_names))
        
        # Ensure all walkers start within bounds
        for i, (pmin, pmax) in enumerate(bounds):
            pos[:, i] = np.clip(pos[:, i], pmin, pmax)
        
        print(f"Running MCMC with {self.n_walkers} walkers for {self.n_steps} steps...")
        print(f"Burn-in: {self.n_burnin} steps")
        
        # Create sampler
        if use_pool and self.n_threads > 1:
            with Pool(self.n_threads) as pool:
                self.sampler = emcee.EnsembleSampler(
                    self.n_walkers, len(param_names), 
                    self.log_probability, 
                    args=(param_names,),
                    pool=pool
                )
                # Run MCMC
                self.sampler.run_mcmc(pos, self.n_steps, progress=True)
        else:
            self.sampler = emcee.EnsembleSampler(
                self.n_walkers, len(param_names), 
                self.log_probability, 
                args=(param_names,)
            )
            # Run MCMC
            self.sampler.run_mcmc(pos, self.n_steps, progress=True)
        
        # Extract samples after burn-in
        self.samples = self.sampler.get_chain(discard=self.n_burnin, flat=True)
        
        # Compute statistics
        acceptance_fraction = np.mean(self.sampler.acceptance_fraction)
        print(f"Mean acceptance fraction: {acceptance_fraction:.3f}")
        
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