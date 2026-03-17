# Visualization

Comprehensive guide to visualizing SED fitting results in SPECTRA.

## Overview

SPECTRA automatically generates several types of plots:

1. **SED Plots**: Observed vs. model photometry
2. **Corner Plots**: Parameter posteriors and correlations (MCMC)
3. **Trace Plots**: MCMC convergence diagnostics
4. **Residual Plots**: Fit quality assessment

## SED Plots

### Default SED Plot

Automatically generated for every fit:

```yaml
plotting:
  output_dir: './output'
  save_format: 'png'
  dpi: 150
  
  sed_plot:
    figsize: [10, 6]
    show_errors: true
    wavelength_unit: 'microns'
    flux_unit: 'Jy'
```

### SED Plot Components

- **Data points**: Observed photometry with error bars
- **Model curve**: Best-fit SSP model SED
- **Residuals**: (Obs - Model) / Error subplot
- **Annotations**: Object ID, redshift, χ²/dof

### Customization

```python
from src.utils.plotting import Plotting

config = {
    'output_dir': './plots',
    'save_format': 'pdf',
    'dpi': 300,
    'sed_plot': {
        'figsize': [12, 8],
        'show_errors': True,
        'show_residuals': True,
        'wavelength_unit': 'angstroms',  # or 'microns'
        'flux_unit': 'mJy',  # or 'Jy', 'erg/s/cm2/Hz'
        'xscale': 'log',
        'yscale': 'log',
        'color_obs': 'steelblue',
        'color_model': 'darkred',
        'marker_size': 8,
        'line_width': 2
    }
}

plotting = Plotting(config)
plotting.plot_sed(phot_data, results, ssp_model=model)
```

### Advanced SED Plotting

```python
import matplotlib.pyplot as plt
import numpy as np

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), 
                                gridspec_kw={'height_ratios': [3, 1]},
                                sharex=True)

# Main SED plot
ax1.errorbar(wavelength, obs_flux, yerr=obs_err,
             fmt='o', color='steelblue', label='Observed',
             markersize=8, capsize=3, capthick=1.5)

ax1.plot(wavelength, mod_flux, '-', color='darkred', 
         linewidth=2, label='Best-fit model')

# Add filter transmission curves
for band_name, band_wave in filter_curves.items():
    ax1.fill_between(band_wave, 0, transmission,
                     alpha=0.1, color='gray')

ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_ylabel('Flux Density (Jy)', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Residuals
residuals = (obs_flux - mod_flux) / obs_err
ax2.errorbar(wavelength, residuals, yerr=np.ones_like(residuals),
             fmt='o', color='steelblue', markersize=6)
ax2.axhline(0, color='k', linestyle='--', alpha=0.5)
ax2.axhline(2, color='r', linestyle=':', alpha=0.3)
ax2.axhline(-2, color='r', linestyle=':', alpha=0.3)

ax2.set_xscale('log')
ax2.set_xlabel('Wavelength (μm)', fontsize=12)
ax2.set_ylabel('Residuals (σ)', fontsize=12)
ax2.grid(True, alpha=0.3)

# Add text annotations
textstr = '\n'.join([
    f'z = {redshift:.2f}',
    f'log(M/M$_\\odot$) = {mass:.2f}',
    f'Age = {age:.2f} Gyr',
    f'[Z/H] = {metallicity:.2f}',
    f'E(B-V) = {dust:.2f}',
    f'χ²/dof = {chi2_dof:.2f}'
])
props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes,
         fontsize=10, verticalalignment='top', bbox=props)

plt.tight_layout()
plt.savefig(f'{object_id}_sed.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Corner Plots

### Default Corner Plot

Generated automatically for MCMC fits:

```yaml
plotting:
  corner_plot:
    figsize: [12, 12]
    show_titles: true
    title_fmt: '.3f'
    quantiles: [0.16, 0.5, 0.84]
    levels: [0.68, 0.95]
    smooth: 1.0
```

### Using Corner

```python
import corner

# Flatten MCMC chain
flat_samples = chain[n_burn:].reshape(-1, n_params)

# Create corner plot
fig = corner.corner(
    flat_samples,
    labels=['log(M/M$_\\odot$)', 'Age (Gyr)', '[Z/H]', 'E(B-V)'],
    quantiles=[0.16, 0.5, 0.84],
    show_titles=True,
    title_kwargs={"fontsize": 12},
    label_kwargs={"fontsize": 14},
    levels=(0.68, 0.95),
    plot_datapoints=False,
    fill_contours=True,
    smooth=1.0,
    color='steelblue',
    truth_color='red',
    truths=ml_values  # Compare to ML solution
)

plt.savefig('corner_plot.png', dpi=150, bbox_inches='tight')
```

### Customized Corner Plot

```python
import corner
import matplotlib.pyplot as plt

# Setup
ndim = 4
fig = plt.figure(figsize=(14, 14))

# Create corner plot
corner.corner(
    flat_samples,
    fig=fig,
    labels=param_labels,
    quantiles=[0.16, 0.5, 0.84],
    show_titles=True,
    title_fmt='.3f',
    levels=(1 - np.exp(-0.5), 1 - np.exp(-2)),  # 1σ, 2σ
    plot_contours=True,
    plot_datapoints=True,
    plot_density=False,
    data_kwargs={'alpha': 0.1},
    hist_kwargs={'density': True, 'color': 'steelblue'},
    contour_kwargs={'colors': ['steelblue', 'darkblue']},
    truths=true_values,
    truth_color='darkred'
)

# Add custom annotations
axes = np.array(fig.axes).reshape((ndim, ndim))

for i in range(ndim):
    # Add prior ranges as vertical lines
    axes[i, i].axvline(prior_mins[i], color='gray', linestyle=':', alpha=0.5)
    axes[i, i].axvline(prior_maxs[i], color='gray', linestyle=':', alpha=0.5)

plt.savefig('custom_corner.png', dpi=300, bbox_inches='tight')
```

## Trace Plots

### Basic Trace Plot

Monitor MCMC convergence:

```python
import matplotlib.pyplot as plt

# Get full chain (not flattened)
chain = sampler.get_chain()  # shape: (n_steps, n_walkers, n_params)

fig, axes = plt.subplots(n_params, figsize=(10, 8), sharex=True)

for i in range(n_params):
    ax = axes[i]
    ax.plot(chain[:, :, i], "k", alpha=0.3)
    ax.set_xlim(0, len(chain))
    ax.set_ylabel(param_names[i])
    ax.yaxis.set_label_coords(-0.1, 0.5)
    
    # Mark burn-in
    ax.axvline(n_burn, color='r', linestyle='--', alpha=0.5)

axes[-1].set_xlabel("Step Number")
plt.tight_layout()
plt.savefig('trace_plots.png', dpi=150)
```

### Enhanced Trace Plot

```python
fig, axes = plt.subplots(n_params, 2, figsize=(14, 8),
                        gridspec_kw={'width_ratios': [3, 1]})

for i in range(n_params):
    # Trace plot
    axes[i, 0].plot(chain[:, :, i], alpha=0.1, color='k')
    axes[i, 0].axvline(n_burn, color='r', linestyle='--', 
                       label='Burn-in' if i == 0 else '')
    axes[i, 0].set_ylabel(param_names[i], fontsize=12)
    axes[i, 0].grid(True, alpha=0.3)
    
    # 1D posterior
    flat = chain[n_burn:, :, i].flatten()
    axes[i, 1].hist(flat, bins=30, orientation='horizontal',
                    color='steelblue', alpha=0.7, density=True)
    axes[i, 1].set_yticks([])
    axes[i, 1].grid(True, alpha=0.3, axis='x')

axes[-1, 0].set_xlabel('Step Number', fontsize=12)
axes[0, 0].legend()
plt.tight_layout()
plt.savefig('enhanced_trace.png', dpi=150)
```

## Diagnostic Plots

### Autocorrelation Plot

```python
import emcee

# Compute autocorrelation
tau = emcee.autocorr.integrated_time(chain, quiet=True)

fig, axes = plt.subplots(n_params, figsize=(10, 8), sharex=True)

for i in range(n_params):
    ax = axes[i]
    
    # Compute autocorrelation function
    n = emcee.autocorr.function_1d(chain[:, 0, i])
    ax.plot(n, label=param_names[i])
    ax.axhline(0, color='k', linestyle='--', alpha=0.3)
    ax.set_ylabel('ACF')
    ax.legend()
    
    # Mark autocorrelation time
    ax.axvline(tau[i], color='r', linestyle=':', alpha=0.5)
    ax.text(tau[i], 0.5, f'τ={tau[i]:.0f}', color='r')

axes[-1].set_xlabel('Lag')
plt.tight_layout()
plt.savefig('autocorrelation.png', dpi=150)
```

### Acceptance Fraction Plot

```python
acceptance = sampler.acceptance_fraction

plt.figure(figsize=(10, 5))
plt.plot(acceptance, 'o-', color='steelblue')
plt.axhline(np.mean(acceptance), color='r', linestyle='--',
            label=f'Mean: {np.mean(acceptance):.3f}')
plt.axhspan(0.2, 0.5, alpha=0.2, color='green', label='Ideal range')
plt.xlabel('Walker Index')
plt.ylabel('Acceptance Fraction')
plt.title('MCMC Acceptance Fractions')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('acceptance.png', dpi=150)
```

### Parameter Evolution Plot

```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for i, (ax, param) in enumerate(zip(axes, param_names)):
    # Mean and std over walkers at each step
    mean = np.mean(chain[:, :, i], axis=1)
    std = np.std(chain[:, :, i], axis=1)
    
    ax.plot(mean, 'steelblue', label='Mean')
    ax.fill_between(range(len(mean)), mean-std, mean+std,
                    alpha=0.3, color='steelblue', label='±1σ')
    ax.axvline(n_burn, color='r', linestyle='--', alpha=0.5)
    ax.set_ylabel(param)
    ax.set_xlabel('Step')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('parameter_evolution.png', dpi=150)
```

## Comparison Plots

### ML vs MCMC Comparison

```python
fig, axes = plt.subplots(1, n_params, figsize=(16, 4))

for i, (ax, param) in enumerate(zip(axes, param_names)):
    # MCMC posterior
    ax.hist(flat_samples[:, i], bins=50, density=True,
            alpha=0.7, color='steelblue', label='MCMC')
    
    # ML value
    ax.axvline(ml_values[i], color='darkred', linewidth=2,
              label='ML', linestyle='--')
    
    # MCMC median
    median = np.median(flat_samples[:, i])
    ax.axvline(median, color='darkblue', linewidth=2,
              label='MCMC median')
    
    ax.set_xlabel(param)
    ax.set_ylabel('Density')
    ax.legend()

plt.tight_layout()
plt.savefig('ml_vs_mcmc.png', dpi=150)
```

### Multi-Object Comparison

```python
import pandas as pd

# Load summary
df = pd.read_csv('fit_summary.csv')

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

params = ['mass', 'age', 'metallicity', 'dust']

for ax, param in zip(axes, params):
    ax.scatter(df['redshift'], df[param], 
              c=df['log_likelihood'], cmap='viridis',
              s=50, alpha=0.7)
    
    # Add error bars if MCMC
    if f'{param}_err_lower' in df.columns:
        ax.errorbar(df['redshift'], df[param],
                   yerr=[df[f'{param}_err_lower'], 
                         df[f'{param}_err_upper']],
                   fmt='none', color='gray', alpha=0.3)
    
    ax.set_xlabel('Redshift')
    ax.set_ylabel(param.capitalize())
    ax.grid(True, alpha=0.3)

plt.colorbar(ax.collections[0], ax=axes, label='log(Likelihood)')
plt.tight_layout()
plt.savefig('multi_object_comparison.png', dpi=150)
```

## Interactive Visualization

### Using Plotly

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Create subplots
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=('SED', 'Residuals'),
    vertical_spacing=0.1,
    row_heights=[0.7, 0.3]
)

# Observed data
fig.add_trace(
    go.Scatter(
        x=wavelength,
        y=obs_flux,
        error_y=dict(type='data', array=obs_err),
        mode='markers',
        name='Observed',
        marker=dict(size=8, color='steelblue')
    ),
    row=1, col=1
)

# Model
fig.add_trace(
    go.Scatter(
        x=wavelength,
        y=mod_flux,
        mode='lines',
        name='Model',
        line=dict(color='darkred', width=2)
    ),
    row=1, col=1
)

# Residuals
residuals = (obs_flux - mod_flux) / obs_err
fig.add_trace(
    go.Scatter(
        x=wavelength,
        y=residuals,
        mode='markers',
        name='Residuals',
        marker=dict(size=6, color='steelblue'),
        showlegend=False
    ),
    row=2, col=1
)

# Layout
fig.update_xaxes(type='log', title_text='Wavelength (μm)', row=2, col=1)
fig.update_yaxes(type='log', title_text='Flux (Jy)', row=1, col=1)
fig.update_yaxes(title_text='Residuals (σ)', row=2, col=1)

fig.update_layout(height=800, title_text=f"SED Fit: {object_id}")
fig.write_html(f'{object_id}_interactive.html')
```

## Output Organization

### Directory Structure

```
output/
├── object1/
│   ├── object1_sed.png
│   ├── object1_corner.png
│   ├── object1_trace.png
│   ├── object1_diagnostics.png
│   └── mcmc_samples.h5
├── object2/
│   └── ...
└── fit_summary.csv
```

### Batch Plot Generation

```python
for object_id, results in all_results.items():
    output_dir = os.path.join(base_dir, object_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # SED plot
    plot_sed(results, output=f'{output_dir}/{object_id}_sed.png')
    
    # Corner plot (if MCMC)
    if 'samples' in results:
        plot_corner(results['samples'], 
                   output=f'{output_dir}/{object_id}_corner.png')
        
        # Diagnostics
        plot_diagnostics(results,
                        output=f'{output_dir}/{object_id}_diagnostics.png')
```

## Publication-Quality Figures

### LaTeX-style Plots

```python
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'text.usetex': True,
    'axes.labelsize': 12,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300
})

# Your plotting code here
```

### Multi-Panel Figure

```python
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Main SED
ax_sed = fig.add_subplot(gs[0:2, :])
plot_sed_on_axis(ax_sed, data, results)

# Parameter posteriors
ax_mass = fig.add_subplot(gs[2, 0])
ax_age = fig.add_subplot(gs[2, 1])
ax_met = fig.add_subplot(gs[2, 2])

for ax, param, samples in zip([ax_mass, ax_age, ax_met],
                               ['Mass', 'Age', 'Metallicity'],
                               [mass_samples, age_samples, met_samples]):
    ax.hist(samples, bins=30, color='steelblue', alpha=0.7)
    ax.set_xlabel(param)
    ax.set_ylabel('Density')

plt.savefig('publication_figure.pdf', dpi=300, bbox_inches='tight')
```

## Best Practices

1. **Always include error bars**: Essential for understanding fit quality
2. **Use log scales**: For wavelength and flux when spanning orders of magnitude
3. **Show residuals**: Highlight systematic deviations
4. **Label clearly**: Units, parameters, chi-squared values
5. **Save high-resolution**: DPI ≥ 300 for publications
6. **Include metadata**: Redshift, object ID, fit parameters
7. **Use consistent coloring**: Same colors across related plots
8. **Check corner plots**: Verify parameter correlations make sense

## Next Steps

- [MCMC Sampling](mcmc.md)
- [Fitting Methods](fitting-methods.md)
- [Examples Gallery](../examples/gallery.md)
