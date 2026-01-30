import numpy as np
from scipy.optimize import minimize

class SEDFitter:
    """SED fitting using maximum likelihood estimation."""
    
    def __init__(self, likelihood, ssp_model, wavelengths=None, mod_flux_input=None):
        """
        Initialize fitter.
        
        Args:
            likelihood: Likelihood object with log_posterior method
            ssp_model: SSP model object with get_magnitudes method
            wavelengths: Optional wavelength array (μm)
            mod_flux_input: Pre-calculated model fluxes from input file (for reference only)
        """
        self.likelihood = likelihood
        self.ssp_model = ssp_model
        self.wavelengths = wavelengths
        self.mod_flux_input = mod_flux_input  # Only for reference
    
    def fit_maximum_likelihood(self, initial_params, bounds=None):
        """
        Fit using maximum likelihood estimation.
        
        Args:
            initial_params: Dict {param: initial_value}
            bounds: List of (min, max) tuples for each parameter
            
        Returns:
            dict: Best-fit parameters and log-likelihood
        """
        param_names = list(initial_params.keys())
        x0 = np.array([initial_params[p] for p in param_names])
        
        def objective(x):
            params = dict(zip(param_names, x))
            # Generate model fluxes from parameters
            mod_flux = self.ssp_model.get_magnitudes(
                wavelengths=self.wavelengths,
                **params
            )
            return -self.likelihood.log_posterior(mod_flux, params)
        
        result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
        
        best_params = dict(zip(param_names, result.x))
        
        # Generate model fluxes at best-fit parameters
        mod_flux_best = self.ssp_model.get_magnitudes(
            wavelengths=self.wavelengths,
            **best_params
        )
        
        return {
            'parameters': best_params,
            'log_likelihood': self.likelihood.log_likelihood(mod_flux_best),
            'success': result.success,
            'message': result.message,
            'mod_flux': mod_flux_best,  # Use GENERATED model, not input file
        }
