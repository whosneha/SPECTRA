import numpy as np
from scipy.stats import norm

class Likelihood:
    """Compute likelihood and posterior probabilities."""
    
    def __init__(self, obs_flux, obs_err, priors=None, error_floor=0.1):
        """
        Initialize likelihood.
        
        Args:
            obs_flux: Observed flux values
            obs_err: Observed flux errors
            priors: Dict of prior bounds {param: [min, max]}
            error_floor: Fractional error floor to add (accounts for model inadequacy)
        """
        self.obs_flux = obs_flux
        self.obs_err = obs_err
        self.priors = priors or {}
        self.error_floor = error_floor
        
        # Compute effective errors including floor
        # Use maximum of absolute and fractional error
        abs_floor = error_floor * np.median(obs_flux)  # Absolute floor based on median flux
        frac_floor = error_floor * obs_flux            # Fractional floor
        
        self.eff_err = np.sqrt(obs_err**2 + np.maximum(abs_floor, frac_floor)**2)
        
        print(f"[LIKELIHOOD] Using error floor of {error_floor*100:.0f}%")
        print(f"[LIKELIHOOD] Original errors: {obs_err.min():.2e} to {obs_err.max():.2e}")
        print(f"[LIKELIHOOD] Effective errors: {self.eff_err.min():.2e} to {self.eff_err.max():.2e}")
    
    def log_likelihood(self, mod_flux):
        """
        Compute log-likelihood (χ²) with error floor.
        
        Args:
            mod_flux: Model flux values (same shape as obs_flux)
            
        Returns:
            float: -0.5 * χ²
        """
        chi2 = np.sum(((self.obs_flux - mod_flux) / self.eff_err) ** 2)
        return -0.5 * chi2
    
    def log_prior(self, params):
        """
        Compute log-prior.
        
        Args:
            params: Dict {param_name: value}
            
        Returns:
            float: 0 if in bounds, -inf otherwise
        """
        for param, (pmin, pmax) in self.priors.items():
            if param in params:
                if not (pmin <= params[param] <= pmax):
                    return -np.inf
        return 0.0
    
    def log_posterior(self, mod_flux, params):
        """
        Compute log-posterior = log_likelihood + log_prior.
        
        Args:
            mod_flux: Model flux values
            params: Dict {param_name: value}
            
        Returns:
            float: log-posterior
        """
        lp = self.log_prior(params)
        if not np.isfinite(lp):
            return -np.inf
        return lp + self.log_likelihood(mod_flux)
