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

    # ── CIGALE-style grid PDF analysis ───────────────────────────────────────

    def fit_pdf_analysis(self, priors, grid_config=None):
        """Evaluate every point on a discrete (age, mass, dust) grid, exactly
        like CIGALE's ``pdf_analysis`` module.

        CIGALE's method:
          1. Build a grid of all SSP parameter combinations.
          2. For each grid point compute χ² = Σ [(obs - mod) / σ_eff]²
          3. Convert to a likelihood weight:  w = exp(-0.5 * χ²)
          4. Marginalise each parameter:  E[p] = Σ w_i * p_i / Σ w_i
          5. Report the likelihood-weighted posterior mean (and std dev).

        This avoids all local-minimum problems because it never follows a
        gradient — it just sums over every model.

        Parameters
        ----------
        priors : dict  {param: [min, max]}
        grid_config : dict, optional
            Keys: age_steps, mass_steps, dust_steps (number of grid points)
            Defaults replicate CIGALE's density for a quick run.

        Returns
        -------
        dict  with keys:  parameters, log_likelihood, mod_flux,
                          pdf_mean, pdf_std, all_chi2 (for diagnostics)
        """
        gc = grid_config or {}
        age_steps  = int(gc.get('age_steps',  30))
        mass_steps = int(gc.get('mass_steps', 20))
        dust_steps = int(gc.get('dust_steps', 20))
        met_steps  = int(gc.get('met_steps',   1))

        age_min,  age_max  = float(priors['age'][0]),          float(priors['age'][1])
        mass_min, mass_max = float(priors['mass'][0]),         float(priors['mass'][1])
        dust_min, dust_max = float(priors['dust'][0]),         float(priors['dust'][1])
        met_min,  met_max  = float(priors['metallicity'][0]),  float(priors['metallicity'][1])

        # Log-spaced age grid (matches CIGALE's age grid spacing)
        age_grid  = np.logspace(np.log10(max(age_min, 1e-4)),
                                np.log10(age_max), age_steps)
        mass_grid = np.linspace(mass_min, mass_max, mass_steps)
        dust_grid = np.linspace(dust_min, dust_max, dust_steps)
        # Metallicity: if range is zero (locked), use single value
        if met_max == met_min:
            met_grid = np.array([met_min])
        else:
            met_grid = np.linspace(met_min, met_max, max(met_steps, 2))

        total = age_steps * mass_steps * dust_steps * len(met_grid)
        print(f"[PDF] Grid: {age_steps} ages × {mass_steps} masses × "
              f"{dust_steps} dusts × {len(met_grid)} mets = {total} models")

        # Storage
        chi2_arr  = np.full(total, np.inf)
        param_arr = np.zeros((total, 4))   # age, mass, dust, met

        idx = 0
        for age in age_grid:
            for mass in mass_grid:
                for dust in dust_grid:
                    for met in met_grid:
                        mod = self.ssp_model.get_magnitudes(
                            mass=mass, age=age, metallicity=met, dust=dust,
                            wavelengths=self.wavelengths,
                        )
                        chi2 = np.sum(
                            ((self.likelihood.obs_flux - mod)
                             / self.likelihood.eff_err) ** 2
                        )
                        chi2_arr[idx]    = chi2
                        param_arr[idx]   = [age, mass, dust, met]
                        idx += 1

        # Likelihood weights: w = exp(-0.5 * chi2)
        # Subtract minimum chi2 first for numerical stability (same as CIGALE)
        chi2_arr  = chi2_arr[:idx]
        param_arr = param_arr[:idx]
        dchi2 = chi2_arr - chi2_arr.min()
        weights = np.exp(-0.5 * dchi2)
        weights /= weights.sum()

        # Posterior means and standard deviations (CIGALE "bayes" estimates)
        names  = ['age', 'mass', 'dust', 'metallicity']
        pdf_mean = {}
        pdf_std  = {}
        for i, name in enumerate(names):
            mu  = np.sum(weights * param_arr[:, i])
            sig = np.sqrt(np.sum(weights * (param_arr[:, i] - mu) ** 2))
            pdf_mean[name] = float(mu)
            pdf_std[name]  = float(sig)

        # Best-fit = grid point with minimum chi2
        best_idx    = int(np.argmin(chi2_arr))
        best_age, best_mass, best_dust, best_met = param_arr[best_idx]
        best_params = {
            'age': float(best_age),
            'mass': float(best_mass),
            'dust': float(best_dust),
            'metallicity': float(best_met),
        }

        # Model fluxes at the PDF-mean parameters (what CIGALE reports)
        mod_flux_mean = self.ssp_model.get_magnitudes(
            wavelengths=self.wavelengths, **pdf_mean
        )
        log_like = float(self.likelihood.log_likelihood(mod_flux_mean))

        # Also keep best-grid-point fluxes for chi2 diagnostics
        mod_flux_best = self.ssp_model.get_magnitudes(
            wavelengths=self.wavelengths, **best_params
        )

        n_dof = max(len(self.likelihood.obs_flux) - 4, 1)
        chi2_best = float(chi2_arr[best_idx])
        print(f"[PDF] Best grid χ²/DOF = {chi2_best/n_dof:.2f}  "
              f"(age={best_age*1e3:.1f} Myr, logM={best_mass:.2f}, "
              f"Av={best_dust:.2f})")
        print(f"[PDF] Posterior mean:  "
              f"age={pdf_mean['age']*1e3:.1f} Myr  "
              f"logM={pdf_mean['mass']:.2f}  "
              f"Av={pdf_mean['dust']:.2f}")

        return {
            'parameters':    pdf_mean,      # report Bayesian mean, like CIGALE
            'parameters_map': best_params,  # MAP (grid minimum)
            'pdf_std':       pdf_std,
            'log_likelihood': log_like,
            'chi2':          chi2_best,
            'chi2_red':      chi2_best / n_dof,
            'success':       True,
            'message':       'pdf_analysis complete',
            'mod_flux':      mod_flux_mean,
            'mod_flux_map':  mod_flux_best,
            'all_chi2':      chi2_arr,
            'all_params':    param_arr,
            'weights':       weights,
        }


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
        
        result = minimize(
            objective, x0,
            bounds=bounds,
            method='L-BFGS-B',
            # FSPS evaluations are stochastic at the ~1e-5 level, so the
            # default finite-difference step (~1e-8) produces a zero gradient
            # and the optimizer never moves. Use a larger step.
            options={'eps': 1e-3, 'ftol': 1e-6},
        )

        # If L-BFGS-B made no progress (common with noisy FSPS objectives),
        # fall back to a derivative-free Nelder-Mead from the same start.
        if np.allclose(result.x, x0):
            print("[FIT] L-BFGS-B stalled; falling back to Nelder-Mead")
            result = minimize(
                objective, x0,
                method='Nelder-Mead',
                bounds=bounds,
                options={'xatol': 1e-3, 'fatol': 1e-3, 'maxiter': 2000},
            )
        
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
