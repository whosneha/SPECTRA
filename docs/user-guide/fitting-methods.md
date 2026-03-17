# Fitting Methods

SPECTRA provides two primary methods for SED fitting: Maximum Likelihood and MCMC.

## Overview

| Method | Speed | Uncertainties | Use Case |
|--------|-------|---------------|----------|
| Maximum Likelihood (ML) | Fast | None | Quick fits, testing |
| MCMC | Slow | Full posteriors | Publication-quality |

## Maximum Likelihood Fitting

### Overview

Finds parameter values that maximize the likelihood function:

```
L(θ) = ∏ₐexp(-0.5 * ((f_obs - f_mod(θ))/σ)²)
```

**Advantages**:
- Fast (~seconds per object)
- Good for large samples
- Provides point estimates

**Disadvantages**:
- No uncertainty estimates
- May find local minima
- No parameter covariances

### Configuration

```yaml
fitting:
  method: 'ml'
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.0]
    metallicity: [-2.0, 0.5]
    dust: [0.0, 2.0]
  error_floor: 0.1
```

### Algorithm

Uses `scipy.optimize.minimize` with:
- Method: L-BFGS-B (bounded optimization)
- Bounds: From prior ranges
- Initial guess: Midpoint of priors

```python
from scipy.optimize import minimize

def neg_log_likelihood(params):
    model_flux = ssp_model.get_magnitudes(*params, wavelengths=wave)
    chi2 = np.sum(((obs_flux - model_flux) / obs_err)**2)
    return 0.5 * chi2

result = minimize(neg_log_likelihood, initial_params, 
                 method='L-BFGS-B', bounds=bounds)
```

### Output

```python
{
    'parameters': {
        'mass': 11.23,
        'age': 1.45,
        'metallicity': -0.32,
        'dust': 0.58
    },
    'log_likelihood': -45.67,
    'mod_flux': array([...]),
    'success': True
}
```

### When to Use ML

- **Initial exploration**: Quick survey of parameter space
- **Large samples**: Processing hundreds/thousands of objects
- **Testing configuration**: Validate priors before MCMC
- **Real-time analysis**: Interactive fitting sessions

## MCMC Sampling

### Overview

Markov Chain Monte Carlo explores the full posterior distribution:

```
P(θ|data) ∝ P(data|θ) × P(θ)
```

Uses the `emcee` affine-invariant ensemble sampler.

**Advantages**:
- Full posterior distributions
- Robust uncertainty estimates
- Parameter correlations
- Multiple modes if present

**Disadvantages**:
- Slow (~minutes per object)
- Requires convergence checks
- More complex interpretation

### Configuration

```yaml
fitting:
  method: 'mcmc'
  parameters: ["mass", "age", "metallicity", "dust"]
  priors:
    mass: [8.0, 13.0]
    age: [0.001, 13.0]
    metallicity: [-2.0, 0.5]
    dust: [0.0, 2.0]

mcmc:
  n_walkers: 32
  n_steps: 5000
  n_burn: 1000
  thin: 1
  backend: 'mcmc_samples.h5'
  progress: true
```

### Parameters

**n_walkers**: Number of ensemble walkers
- Rule of thumb: ≥ 2 × n_parameters
- More walkers = better exploration
- Typical: 32-64 walkers

**n_steps**: Total MCMC steps
- Depends on convergence
- Typical: 2000-10000 steps
- Check autocorrelation time

**n_burn**: Burn-in steps to discard
- Allows convergence to posterior
- Typical: 20-50% of total steps
- Visualize traces to verify

**thin**: Thin chain by factor
- Reduces correlation
- Typical: 1-10
- Thin = 1 keeps all samples

### Initialization

Walkers initialized around ML solution:

```python
# Start from ML fit
p0 = ml_result + 0.01 * np.random.randn(n_walkers, n_params)

# Or random in prior range
p0 = np.random.uniform(low=prior_mins, high=prior_maxs, 
                       size=(n_walkers, n_params))
```

### Running MCMC

```python
from src.mcmc.mcmc_runner import MCMCRunner

mcmc_runner = MCMCRunner(likelihood, ssp_model, config=mcmc_config)
mcmc_runner.set_wavelengths(wavelengths)

results = mcmc_runner.run(
    initial_params, bounds, parameter_names,
    use_pool=False  # Set True for multiprocessing
)
```

### Output

```python
{
    'parameters': {  # Median values
        'mass': 11.23,
        'age': 1.45,
        'metallicity': -0.32,
        'dust': 0.58
    },
    'percentiles': {
        'mass': {'median': 11.23, 'lower': 0.15, 'upper': 0.18},
        'age': {'median': 1.45, 'lower': 0.23, 'upper': 0.31},
        # ...
    },
    'samples': array([[...]]),  # Full chain
    'log_likelihood': -45.67,
    'acceptance_fraction': 0.42,
    'autocorr_time': array([234, 189, 156, 145])
}
```

### Convergence Diagnostics

#### 1. Trace Plots

Visualize walker trajectories:

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(4, 1, figsize=(10, 8))
for i, param in enumerate(parameter_names):
    axes[i].plot(samples[:, :, i], alpha=0.3, color='k')
    axes[i].set_ylabel(param)
axes[-1].set_xlabel('Step')
plt.show()
```

Should show:
- Stable wandering after burn-in
- All walkers in same region
- Trending or drift
- Walkers in separate modes

#### 2. Autocorrelation Time

```python
import emcee

tau = emcee.autocorr.integrated_time(samples, quiet=True)
print(f"Autocorrelation time: {tau}")
```

Rule: Run for ≥ 50 × τ steps

#### 3. Gelman-Rubin Statistic

```python
def gelman_rubin(chains):
    """R-hat statistic. Should be < 1.1 for convergence."""
    # chains: (n_chains, n_steps, n_params)
    pass
```

#### 4. Acceptance Fraction

```python
acceptance = np.mean(sampler.acceptance_fraction)
print(f"Acceptance fraction: {acceptance:.2f}")
```

Ideal range: 0.2 - 0.5

### When to Use MCMC

- **Publication-quality fits**: Need robust uncertainties
- **Parameter correlations**: Understand degeneracies
- **Complex posteriors**: Multiple modes or non-Gaussian
- **Small samples**: Can afford computation time
- **Model comparison**: Bayesian evidence calculation

## Comparison: ML vs MCMC

### Example: Same Object

**ML Fit** (5 seconds):
```
mass:        11.23
age:         1.45
metallicity: -0.32
dust:        0.58
log_L:       -45.67
```

**MCMC Fit** (10 minutes):
```
mass:        11.23 ± 0.17
age:         1.45 +0.31 -0.23
metallicity: -0.32 ± 0.09
dust:        0.58 +0.12 -0.09
log_L:       -45.67
```

### Corner Plot Reveals

- Age-metallicity degeneracy
- Mass well-constrained
- Dust skewed toward lower values

## Priors

### Flat Priors

Default: uniform probability in range

```yaml
priors:
  mass: [8.0, 13.0]  # Flat from 8 to 13
```

### Gaussian Priors

*Future feature*:

```yaml
priors:
  mass:
    type: 'gaussian'
    mean: 11.0
    sigma: 0.5
```

### Custom Priors

Implement custom prior functions:

```python
def custom_log_prior(params):
    mass, age, metallicity, dust = params
    
    # Flat priors on ranges
    if not (8.0 < mass < 13.0):
        return -np.inf
    
    # Gaussian prior on age
    age_prior = -0.5 * ((age - 5.0) / 2.0)**2
    
    return age_prior
```

## Error Modeling

### Error Floor

Minimum fractional uncertainty:

```yaml
fitting:
  error_floor: 0.1  # 10% minimum
```

Applied as:
```python
obs_err = np.maximum(obs_err, error_floor * obs_flux)
```

### Systematic Errors

Add in quadrature:

```python
sys_err = 0.05  # 5% systematic
total_err = np.sqrt(obs_err**2 + (sys_err * obs_flux)**2)
```

### Outlier Rejection

*Future feature*: Mixture models for outliers

## Multi-Modal Posteriors

### Identification

Look for:
- Bimodal corner plots
- Separated walker groups
- Multiple χ² minima

### Handling

1. **Run longer**: Allow full exploration
2. **Tempered MCMC**: Parallel tempering
3. **Multiple runs**: Different initializations
4. **Physical interpretation**: Which mode is physical?

## Optimization Tips

### For ML

1. **Good initial guess**: Start near expected values
2. **Tight bounds**: Constrain unphysical regions
3. **Try multiple initializations**: Avoid local minima

### For MCMC

1. **More walkers**: Better exploration
2. **Longer chains**: Ensure convergence
3. **Parallel processing**: Use `use_pool=True`
4. **HDF5 backend**: Save progress, resume if crashed

```yaml
mcmc:
  backend: 'chains/object_samples.h5'
  use_pool: true
  n_workers: 4
```

## Troubleshooting

### ML Issues

**Problem**: Optimization fails
- Solution: Adjust bounds, try different initial guess

**Problem**: χ² too high
- Solution: Check priors, increase error floor

**Problem**: Unphysical results
- Solution: Tighten bounds, check data quality

### MCMC Issues

**Problem**: Walkers stuck
- Solution: Better initialization, more walkers

**Problem**: Not converged
- Solution: Run longer, check τ_autocorr

**Problem**: Low acceptance
- Solution: Adjust proposal scale (automatic in emcee)

**Problem**: Slow performance
- Solution: Enable multiprocessing, reduce n_walkers

## Example Workflows

### Workflow 1: Quick ML Survey

```yaml
fitting:
  method: 'ml'
  error_floor: 0.15
```

```bash
python src/main.py  # Process 100 objects in minutes
```

### Workflow 2: MCMC Follow-up

```yaml
fitting:
  method: 'mcmc'

mcmc:
  n_walkers: 64
  n_steps: 10000
  n_burn: 2000
```

```bash
python src/main.py  # Deep dive on interesting objects
```

### Workflow 3: Hybrid

1. ML fit for all objects
2. MCMC for high S/N objects
3. MCMC for unusual/important objects

## API Reference

See [Fitting API](../api/fitting.md) for complete documentation.

## Next Steps

- [MCMC Sampling](mcmc.md) - Detailed MCMC guide
- [Visualization](visualization.md) - Interpreting results
- [Single Object Tutorial](../tutorials/single-object.md)
