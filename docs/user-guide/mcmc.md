# MCMC Sampling

Deep dive into MCMC sampling for robust parameter estimation and uncertainty quantification.

## What is MCMC?

Markov Chain Monte Carlo (MCMC) is a class of algorithms for sampling from probability distributions. In SED fitting, MCMC explores the posterior distribution of model parameters given the observed data.

### Why Use MCMC?

1. **Full posterior distributions**: Not just point estimates
2. **Uncertainty quantification**: Proper error bars on all parameters
3. **Parameter correlations**: Understand degeneracies
4. **Non-Gaussian posteriors**: Handles complex likelihood surfaces
5. **Marginalization**: Integrate over nuisance parameters

## The Affine-Invariant Ensemble Sampler

SPECTRA uses `emcee`, which implements the Goodman & Weare (2010) ensemble sampler.

### Key Features

- **Affine-invariant**: Performance independent of parameter scaling
- **Ensemble**: Multiple walkers explore parameter space simultaneously
- **Parallel-friendly**: Easy to run on multiple cores
- **No tuning required**: Automatic proposal adaptation

### How It Works

1. Initialize ensemble of walkers in parameter space
2. Each walker proposes new position based on other walkers
3. Accept/reject based on likelihood ratio
4. Repeat for many steps
5. Walkers converge to posterior distribution

## Configuration

### Basic Setup

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
  backend: null
  progress: true
```

### Advanced Configuration

```yaml
mcmc:
  n_walkers: 64           # More walkers for better exploration
  n_steps: 10000          # Longer chains for convergence
  n_burn: 2000            # Longer burn-in
  thin: 5                 # Thin to reduce autocorrelation
  backend: 'chains/mcmc_samples.h5'  # Save to HDF5
  progress: true          # Show progress bar
  moves: null             # Use default moves
  vectorize: false        # Vectorize likelihood calls
```

## Choosing MCMC Parameters

### Number of Walkers

**Rule of thumb**: `n_walkers ≥ 2 × n_parameters`

```python
n_params = 4  # mass, age, metallicity, dust
n_walkers = 32  # 8 × n_params (conservative)
```

**More walkers**:
- Better exploration
- More robust convergence
- Slower per step

**Fewer walkers**:
- Faster per step
- Risk of poor exploration
- May not converge

### Number of Steps

Depends on convergence time (autocorrelation time τ):

**Rule**: Run for at least 50-100 × τ steps

```python
# After initial run
tau = sampler.get_autocorr_time()
n_steps_needed = 100 * np.max(tau)
```

**Typical values**:
- Simple posteriors: 1000-2000 steps
- Complex posteriors: 5000-10000 steps
- Multi-modal: 10000+ steps

### Burn-in Period

Discard initial steps while walkers converge to posterior.

**Rule**: 20-50% of total steps, or 10 × τ

```yaml
mcmc:
  n_steps: 5000
  n_burn: 1000  # 20% burn-in
```

**Check convergence**:
```python
# Trace plots should show stable wandering after burn-in
import matplotlib.pyplot as plt

for i, param in enumerate(param_names):
    plt.subplot(4, 1, i+1)
    plt.plot(chain[:, :, i], alpha=0.3)
    plt.axvline(n_burn, color='r', linestyle='--')
    plt.ylabel(param)
plt.xlabel('Step')
plt.show()
```

### Thinning

Reduce autocorrelation by keeping every N-th sample.

```yaml
mcmc:
  thin: 5  # Keep every 5th sample
```

**When to thin**:
- High autocorrelation (τ > 50)
- Memory constraints
- Speeding up corner plots

**When not to thin**:
- Well-converged chains (τ < 10)
- Need maximum information
- Doing further analysis

## Initialization Strategies

### Strategy 1: Tight Ball Around ML

```python
# Start from maximum likelihood solution
ml_result = ml_fit(data)
p0 = ml_result + 0.01 * np.random.randn(n_walkers, n_params)
```

**Best for**: Well-behaved posteriors, good ML solution

### Strategy 2: Random in Prior Range

```python
# Sample uniformly from prior
p0 = np.random.uniform(
    low=[8.0, 0.001, -2.0, 0.0],
    high=[13.0, 13.0, 0.5, 2.0],
    size=(n_walkers, n_params)
)
```

**Best for**: Exploring full parameter space, no good initial guess

### Strategy 3: Latin Hypercube Sampling

```python
from scipy.stats.qmc import LatinHypercube

lhs = LatinHypercube(d=n_params)
p0_unit = lhs.random(n=n_walkers)
# Scale to prior ranges
p0 = prior_mins + p0_unit * (prior_maxs - prior_mins)
```

**Best for**: Efficient coverage of parameter space

### Strategy 4: Multiple Modes

```python
# Initialize walkers around multiple peaks
mode1 = [11.0, 1.0, -0.5, 0.3]
mode2 = [10.0, 5.0, 0.0, 0.1]

p0_mode1 = mode1 + 0.01 * np.random.randn(n_walkers//2, n_params)
p0_mode2 = mode2 + 0.01 * np.random.randn(n_walkers//2, n_params)
p0 = np.vstack([p0_mode1, p0_mode2])
```

**Best for**: Known multi-modal posteriors

## Running MCMC

### Basic Execution

```python
from src.mcmc.mcmc_runner import MCMCRunner

# Setup
mcmc_runner = MCMCRunner(likelihood, ssp_model, config=mcmc_config)
mcmc_runner.set_wavelengths(wavelengths)

# Run
results = mcmc_runner.run(
    initial_params, 
    bounds, 
    parameter_names,
    use_pool=False
)
```

### With Multiprocessing

```python
results = mcmc_runner.run(
    initial_params, 
    bounds, 
    parameter_names,
    use_pool=True  # Enable parallel execution
)
```

**Note**: Requires picklable likelihood function

### With HDF5 Backend

Save progress and resume if interrupted:

```python
mcmc_config['backend'] = 'chains/object_mcmc.h5'

# First run
results = mcmc_runner.run(...)

# Resume later
results = mcmc_runner.resume(additional_steps=5000)
```

### Interactive Monitoring

```python
import emcee
from IPython.display import display, clear_output

for i in range(100):  # 100 batches
    sampler.run_mcmc(pos, nsteps=50)
    
    # Check convergence every 50 steps
    if i % 10 == 0:
        tau = sampler.get_autocorr_time(tol=0)
        clear_output(wait=True)
        print(f"Step {i*50}, τ = {tau}")
```

## Convergence Diagnostics

### 1. Visual Inspection: Trace Plots

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(n_params, 1, figsize=(10, 8), sharex=True)

for i, (ax, param) in enumerate(zip(axes, param_names)):
    # Plot all walkers
    ax.plot(samples[:, :, i], 'k', alpha=0.1)
    ax.set_ylabel(param)
    ax.axvline(n_burn, color='r', linestyle='--', label='Burn-in')

axes[-1].set_xlabel('Step Number')
axes[0].legend()
plt.tight_layout()
plt.savefig('trace_plots.png', dpi=150)
```

**Look for**:
- Stable fluctuations after burn-in
- All walkers mixed together
- No trends or drifts
- Walkers stuck in separate regions
- Continuing trends

### 2. Autocorrelation Time

Measures how many steps needed for independent samples:

```python
tau = sampler.get_autocorr_time(quiet=False)
print(f"Autocorrelation times: {tau}")
print(f"Mean τ: {np.mean(tau):.1f}")
print(f"Max τ: {np.max(tau):.1f}")

# Check convergence criterion
n_effective = n_steps / np.mean(tau)
print(f"Effective sample size: {n_effective:.0f}")
```

**Rules**:
- Run for > 50 × τ steps
- Effective sample size > 1000 for robust uncertainties
- τ should stabilize (not still increasing)

### 3. Gelman-Rubin Statistic (R̂)

Compare multiple chains to assess convergence:

```python
def gelman_rubin(chains):
    """
    chains: (n_chains, n_steps, n_params)
    Returns: R̂ for each parameter
    """
    n_chains, n_steps, n_params = chains.shape
    
    # Chain means
    chain_means = np.mean(chains, axis=1)
    # Overall mean
    overall_mean = np.mean(chain_means, axis=0)
    
    # Between-chain variance
    B = n_steps * np.var(chain_means, axis=0, ddof=1)
    
    # Within-chain variance
    W = np.mean(np.var(chains, axis=1, ddof=1), axis=0)
    
    # Pooled variance
    var_plus = ((n_steps - 1) * W + B) / n_steps
    
    # R-hat
    R_hat = np.sqrt(var_plus / W)
    
    return R_hat

# Split chain into multiple segments
n_segments = 4
segment_length = n_steps // n_segments
chains = [samples[i*segment_length:(i+1)*segment_length] 
          for i in range(n_segments)]
chains = np.array(chains)

R_hat = gelman_rubin(chains)
print(f"Gelman-Rubin statistic: {R_hat}")
```

**Interpretation**:
- R̂ < 1.01: Excellent convergence
- R̂ < 1.1: Good convergence
- R̂ > 1.1: Poor convergence, run longer

### 4. Acceptance Fraction

Fraction of proposals accepted:

```python
acceptance = sampler.acceptance_fraction
print(f"Acceptance fractions: {acceptance}")
print(f"Mean acceptance: {np.mean(acceptance):.3f}")
```

**Ideal range**: 0.2 - 0.5
- < 0.2: Proposals too large, slow exploration
- > 0.7: Proposals too small, high autocorrelation

**Note**: `emcee` automatically adapts proposals, so this is usually fine

### 5. Effective Sample Size

```python
def effective_sample_size(chain):
    """Estimate effective number of independent samples."""
    n_steps = len(chain)
    tau = compute_autocorr_time(chain)
    return n_steps / tau

for i, param in enumerate(param_names):
    ess = effective_sample_size(samples[:, :, i].flatten())
    print(f"{param}: ESS = {ess:.0f}")
```

**Rule**: ESS > 1000 for reliable uncertainties

## Analyzing Results

### Extract Parameter Estimates

```python
# Flatten chain (all walkers, post burn-in)
flat_samples = samples[n_burn:].reshape(-1, n_params)

# Median and percentiles
for i, param in enumerate(param_names):
    mcmc = np.percentile(flat_samples[:, i], [16, 50, 84])
    q = np.diff(mcmc)
    print(f"{param} = {mcmc[1]:.3f} +{q[1]:.3f} -{q[0]:.3f}")
```

### Corner Plots

Visualize full posterior:

```python
import corner

fig = corner.corner(
    flat_samples,
    labels=param_names,
    quantiles=[0.16, 0.5, 0.84],
    show_titles=True,
    title_kwargs={"fontsize": 12},
    truths=true_values  # If known
)
plt.savefig('corner_plot.png', dpi=150)
```

### Parameter Correlations

```python
import numpy as np

# Correlation matrix
corr_matrix = np.corrcoef(flat_samples.T)

import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='RdBu_r', center=0,
            xticklabels=param_names, yticklabels=param_names,
            vmin=-1, vmax=1)
plt.title('Parameter Correlations')
plt.tight_layout()
plt.savefig('correlations.png', dpi=150)
```

### 1D Marginalized Posteriors

```python
fig, axes = plt.subplots(1, n_params, figsize=(16, 4))

for i, (ax, param) in enumerate(zip(axes, param_names)):
    ax.hist(flat_samples[:, i], bins=50, density=True, 
            alpha=0.7, color='steelblue')
    
    # Add percentiles
    q16, q50, q84 = np.percentile(flat_samples[:, i], [16, 50, 84])
    ax.axvline(q50, color='k', linewidth=2, label='Median')
    ax.axvline(q16, color='k', linestyle='--', linewidth=1)
    ax.axvline(q84, color='k', linestyle='--', linewidth=1)
    
    ax.set_xlabel(param)
    ax.set_ylabel('Probability Density')
    ax.legend()

plt.tight_layout()
plt.savefig('1d_posteriors.png', dpi=150)
```

## Advanced Topics

### Parallel Tempering

For multi-modal posteriors:

```python
# Future feature
from emcee import PTSampler

# Multiple temperatures
betas = np.logspace(0, -3, 10)  # T = 1/beta

sampler = PTSampler(n_walkers, n_params, log_likelihood, log_prior,
                    ntemps=len(betas), betas=betas)
```

### Custom Moves

Modify proposal distribution:

```python
from emcee.moves import DEMove, DESnookerMove

moves = [(DEMove(), 0.8), (DESnookerMove(), 0.2)]

sampler = emcee.EnsembleSampler(
    n_walkers, n_params, log_prob,
    moves=moves
)
```

### Saving and Loading Chains

```python
# Save
np.save('chain.npy', sampler.get_chain())
np.save('log_prob.npy', sampler.get_log_prob())

# Load
chain = np.load('chain.npy')
log_prob = np.load('log_prob.npy')

# Or use HDF5 backend (automatic)
backend = emcee.backends.HDFBackend('chain.h5')
sampler = emcee.EnsembleSampler(..., backend=backend)
```

## Troubleshooting

### Walkers Stuck

**Symptoms**: Some walkers have much lower log-prob
**Solutions**:
1. Better initialization
2. More walkers
3. Check for bugs in likelihood

### Not Converging

**Symptoms**: τ still increasing, R̂ > 1.1
**Solutions**:
1. Run longer
2. Check initialization
3. Simplify model/priors

### Low Acceptance Rate

**Symptoms**: Acceptance < 0.1
**Solutions**:
1. Check for parameter scaling issues
2. Verify likelihood is smooth
3. emcee usually handles this automatically

### High Autocorrelation

**Symptoms**: τ > 100
**Solutions**:
1. Thin the chain
2. Run much longer
3. Check for parameter correlations
4. Consider reparameterization

### Memory Issues

**Symptoms**: Out of memory errors
**Solutions**:
1. Save to HDF5 backend
2. Process in batches
3. Thin more aggressively
4. Reduce n_walkers

## Best Practices

1. **Always check convergence**: Don't trust results without diagnostics
2. **Burn-in is crucial**: Discard unconverged samples
3. **Multiple chains**: Run 2-3 independent chains to verify
4. **Save everything**: Use HDF5 backend for large runs
5. **Plot frequently**: Visual inspection catches problems
6. **Report ESS**: Not just raw sample count
7. **Check priors**: Make sure they're sensible
8. **Compare to ML**: Should be consistent

## Example Workflow

```python
# 1. Run quick ML fit first
ml_result = run_ml_fit(data)

# 2. Initialize MCMC around ML solution
p0 = ml_result['parameters'] + 0.01 * np.random.randn(32, 4)

# 3. Short test run
test_sampler = run_mcmc(p0, n_steps=500)
test_tau = test_sampler.get_autocorr_time(quiet=True)
print(f"Initial τ ≈ {np.mean(test_tau):.0f}")

# 4. Full run with enough steps
n_steps = int(100 * np.max(test_tau))
sampler = run_mcmc(p0, n_steps=n_steps)

# 5. Check convergence
final_tau = sampler.get_autocorr_time()
print(f"Final τ = {final_tau}")
print(f"Ran for {n_steps / np.max(final_tau):.1f} × τ steps")

# 6. Analyze results
chain = sampler.get_chain(discard=n_steps//5, flat=True)
results = analyze_chain(chain)

# 7. Make plots
make_corner_plot(chain)
make_trace_plots(sampler.get_chain())
```

## Further Reading

- [emcee documentation](https://emcee.readthedocs.io/)
- Foreman-Mackey et al. (2013): emcee paper
- Goodman & Weare (2010): Affine-invariant ensemble sampler
- Gelman & Rubin (1992): Convergence diagnostics
- Betancourt (2017): Conceptual introduction to HMC

## Next Steps

- [Visualization Guide](visualization.md)
- [Fitting Methods](fitting-methods.md)
- [Single Object Tutorial](../tutorials/single-object.md)
