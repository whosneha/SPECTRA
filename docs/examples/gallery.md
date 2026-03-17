# Example Gallery

Visual examples of SPECTRA outputs for different types of objects and fitting scenarios.

## Example 1: Young Star Cluster

### Object Properties
- **Type**: Young star cluster (100 Myr)
- **Redshift**: z = 0.005
- **Mass**: 10^5.2 M☉
- **Metallicity**: Solar ([Z/H] = 0.0)
- **Dust**: E(B-V) = 0.3

### SED Plot

```
Wavelength range: UV (0.15 μm) to mid-IR (22 μm)
Photometry: GALEX (FUV, NUV) + HST (F275W-F814W) + AllWISE (W1-W4)

                    ┌─────────────────────────────────┐
     10^-4 Jy  ─────┤                                 │
                    │      ●                          │
                    │    ●   ●                        │
     10^-5 Jy  ─────┤  ●       ●───●                  │
                    │              ───●               │
                    │                  ───●           │
     10^-6 Jy  ─────┤                      ───●───●   │
                    └─────────────────────────────────┘
                    0.1     1.0      10.0      μm

Legend:
  ● = Observed photometry with error bars
  ─ = Best-fit SSP model
```

**Key Features**:
- Strong UV emission from young stars
- Balmer break at ~0.36 μm
- Flat/rising mid-IR (dust heating)

### Corner Plot

Shows parameter correlations from MCMC fitting:

```
              mass           age          [Z/H]         E(B-V)
        ┌──────────┬──────────┬──────────┬──────────┐
  mass  │    ●●    │          │          │          │
        │   ●●●●   │    ●     │          │          │
        │    ●●    │   ●●●    │     ●    │          │
        ├──────────┼──────────┼──────────┼──────────┤
  age   │          │   ●●●    │   ●●     │          │
        │    ●     │  ●●●●●   │  ●●●●    │    ●     │
        │   ●●●    │   ●●●    │   ●●     │   ●●●    │
        ├──────────┼──────────┼──────────┼──────────┤
 [Z/H]  │          │          │   ●●●    │   ●●     │
        │     ●    │   ●●     │  ●●●●●   │  ●●●●    │
        │    ●●●   │  ●●●●    │   ●●●    │   ●●     │
        ├──────────┼──────────┼──────────┼──────────┤
E(B-V)  │          │          │          │   ●●●    │
        │          │    ●     │   ●●     │  ●●●●●   │
        │          │   ●●●    │  ●●●●    │   ●●●    │
        └──────────┴──────────┴──────────┴──────────┘

Best-fit values:
  log(M/M☉) = 5.20 ± 0.08
  Age = 0.10 ± 0.02 Gyr
  [Z/H] = 0.0 ± 0.2
  E(B-V) = 0.30 ± 0.05
```

**Notable Correlations**:
- Age-metallicity degeneracy (ρ = -0.4)
- Dust-metallicity anti-correlation (ρ = -0.3)
- Mass well-constrained (narrow distribution)

### Parameter Space

1D marginalized posteriors:

```
Mass (log M☉)
     │     ╱╲
 PDF │    ╱  ╲
     │   ╱    ╲___
     └──────────────
        5.0  5.2  5.4

Age (Gyr)
     │   ╱╲
 PDF │  ╱  ╲
     │ ╱    ╲____
     └──────────────
       0.05 0.1 0.15

[Z/H]
     │     ╱╲
 PDF │    ╱  ╲
     │  _╱    ╲_
     └──────────────
       -0.4  0.0  0.4

E(B-V)
     │    ╱╲
 PDF │   ╱  ╲
     │  ╱    ╲___
     └──────────────
       0.2  0.3  0.4
```

---

## Example 2: Old Globular Cluster

### Object Properties
- **Type**: Ancient globular cluster (12 Gyr)
- **Redshift**: z = 0.0
- **Mass**: 10^5.8 M☉
- **Metallicity**: Metal-poor ([Z/H] = -1.5)
- **Dust**: Minimal (E(B-V) = 0.05)

### SED Plot

```
Wavelength range: Optical (0.4 μm) to NIR (2.2 μm)
Photometry: HST (F555W, F814W) + VISTA (Z, Y, J, H, Ks)

                    ┌─────────────────────────────────┐
     10^-5 Jy  ─────┤                                 │
                    │        ●───●───●───●───●        │
                    │      ●                   ●      │
     10^-6 Jy  ─────┤    ●                       ●    │
                    │                                 │
                    └─────────────────────────────────┘
                    0.4     0.8      1.5      2.0  μm

Legend:
  ● = Observed photometry
  ─ = Best-fit old SSP model
```

**Key Features**:
- Red optical colors (old stellar population)
- No UV emission
- Smooth red continuum to NIR

### Corner Plot

```
              mass           age          [Z/H]         E(B-V)
        ┌──────────┬──────────┬──────────┬──────────┐
  mass  │   ●●●    │          │          │          │
        │  ●●●●●   │    ●     │          │          │
        │   ●●●    │   ●●     │     ●    │          │
        ├──────────┼──────────┼──────────┼──────────┤
  age   │          │    ●     │  ●●●●●   │          │
        │    ●     │   ●●●    │ ●●●●●●●  │    ●     │
        │   ●●     │  ●●●●●   │  ●●●●●   │    ●     │
        ├──────────┼──────────┼──────────┼──────────┤
 [Z/H]  │          │          │  ●●●●●   │          │
        │     ●    │  ●●●●●   │ ●●●●●●●  │    ●     │
        │    ●●    │ ●●●●●●●  │  ●●●●●   │   ●●     │
        ├──────────┼──────────┼──────────┼──────────┤
E(B-V)  │          │          │          │   ●●●    │
        │          │    ●     │    ●     │  ●●●●●   │
        │          │    ●     │   ●●     │   ●●●    │
        └──────────┴──────────┴──────────┴──────────┘

Best-fit values:
  log(M/M☉) = 5.80 ± 0.05
  Age = 12.0 ± 1.0 Gyr
  [Z/H] = -1.5 ± 0.2
  E(B-V) = 0.05 ± 0.03
```

**Notable Features**:
- Strong age-metallicity degeneracy for old populations
- Age posterior peaks at old limit
- Very low dust (consistent with old population)

---

## Example 3: High-Redshift Galaxy (z=6)

### Object Properties
- **Type**: Young galaxy in early universe
- **Redshift**: z = 6.5
- **Mass**: 10^9.5 M☉
- **Metallicity**: Low ([Z/H] = -1.0)
- **Dust**: Moderate (E(B-V) = 0.4)

### SED Plot with K-correction

```
Rest-frame UV shifted to observed NIR:
Photometry: HST (F105W-F160W) + JWST (F200W-F444W)

                    ┌─────────────────────────────────┐
     10^-8 Jy  ─────┤                                 │
                    │     ●                           │
                    │   ●   ●──●                      │
     10^-9 Jy  ─────┤           ──●──●                │
                    │                ───●             │
                    │                    ───●         │
                    └─────────────────────────────────┘
                    1.0      2.0      4.0      μm
                   (observed frame, z=6.5)

Rest frame: 0.13-0.60 μm → Observed: 1.0-4.5 μm
```

**Key Features**:
- Lyman break shifted to ~1.2 μm
- Young stellar population signature
- Effects of IGM absorption

### MCMC Trace Plots

Convergence diagnostics showing walker evolution:

```
Mass (log M☉)
10.0 ────────────────────────────────────
     ││││││││││││││││││││││││││││││││││││
 9.5 ─────────────────────────●──────────  ← Converged
     ││││││││││││││││││││││││││││││││││││
 9.0 ────────────────────────────────────
     0    500   1000  1500  2000  steps

Age (Gyr)
0.8 ────────────────────────────────────
     ││││││││││││││││││││││││││││││││││││
0.4 ─────────────────────────●──────────  ← Converged
     ││││││││││││││││││││││││││││││││││││
0.1 ────────────────────────────────────
     0    500   1000  1500  2000  steps

Burn-in │← Sampling →
```

**Convergence Metrics**:
- Autocorrelation time: τ ≈ 50 steps
- Effective sample size: N_eff > 1000
- Gelman-Rubin: R̂ < 1.05 (converged)

---

## Example 4: Dusty Starburst

### Object Properties
- **Type**: Obscured starburst galaxy
- **Redshift**: z = 0.1
- **Mass**: 10^10.5 M☉
- **Metallicity**: Super-solar ([Z/H] = +0.3)
- **Dust**: Heavy (E(B-V) = 1.5)

### Multi-Wavelength SED

```
UV to far-IR coverage showing dust re-emission:
GALEX + optical + WISE + Herschel

     ┌───────────────────────────────────────┐
10^-4│                             ╱╲        │
  Jy │                           ╱    ╲      │
     │    ●                    ╱        ╲    │
10^-5│      ───●──●──●──●───●             ●  │
     │                      ──────────────    │
10^-6│  ●                                     │
     └───────────────────────────────────────┘
      0.2    1      10       100       μm

Dust emission peak at ~60 μm
```

**Key Features**:
- Suppressed UV (dust extinction)
- Strong far-IR emission (dust heating)
- Two-component model needed

### Parameter Correlations

Dust vs other parameters:

```
E(B-V) vs Age
   2.0│     ●●●●
      │   ●●●●●●●●
   1.5│  ●●●●●●●●●   ← Strong correlation
      │   ●●●●●●●
   1.0│     ●●●
      └────────────
       0.1  0.5  1.0  Gyr

E(B-V) vs [Z/H]
   2.0│         ●●●
      │       ●●●●●●
   1.5│      ●●●●●●●  ← Metallicity affects dust
      │       ●●●●●
   1.0│         ●●
      └────────────
      -0.5  0.0  0.5  [Z/H]
```

---

## Example 5: Batch Processing Results

### Multi-Object Summary

Processing 50 clusters from PHANGS survey:

```
Distribution of fitted parameters:

Mass Distribution
     15│    ╱╲
objects │   ╱  ╲╲
     10│  ╱      ╲
      5│ ╱        ╲___
        └──────────────
         4   5   6   7  log(M/M☉)

Age Distribution  
     20│       ╱╲
objects │      ╱  ╲
     10│   __╱    ╲
      5│__╱        ╲___
        └──────────────
        0.01 0.1  1  10  Gyr

Color-coded by galaxy:
  NGC 628  : ● (10 clusters)
  NGC 1365 : ■ (15 clusters)
  IC 5332  : ▲ (25 clusters)
```

### Mass-Age Relation

```
Age (Gyr)
  10 ┤                    ●
     │                  ● ● ●
   1 ┤            ● ● ●
     │        ● ●
 0.1 ┤    ● ●
     │  ●
0.01 ┤●
     └────────────────────
      4    5    6    7    8
           log(M/M☉)

Young clusters: Lower mass
Old clusters: Higher mass (survivorship)
```

### Fitting Quality

```
χ²/dof distribution:
     25│   ╱╲
objects │  ╱  ╲
     15│ ╱    ╲
      5│╱      ╲___
        └──────────────
        0.5  1.0  2.0  3.0

Good fits: χ²/dof < 2 (90%)
Outliers: 5 objects require follow-up
```

---

## Example 6: Convergence Diagnostics

### MCMC Chain Analysis

```
Autocorrelation Function:
ACF
1.0 ┤●
    │ ●
0.5 │  ●
    │   ●●
0.0 │     ●●●●●●●─────────
    └────────────────────
     0   50  100  150  lag

τ_autocorr = 42 steps
N_effective = 2380 samples
```

### Walker Spread

```
Parameter evolution (32 walkers):

Step 1-200 (burn-in):
mass ││││░░░░░░░░░░░░░░░░░░  Spreading out
     ░░░░░░░░░░░░░░░░░░░░││││

Step 200-2000 (sampling):
mass ││││││││││││││││││││││││  Well-mixed
     ││││││││││││││││││││││││
```

### Acceptance Rate

```
Acceptance fraction per walker:
     │  ●                    ●
0.4  ├──●──●──●──●──●──●──●──●
     │         ●    ●
0.2  ├─────────────────────────
     │
     └────────────────────────
      0   8   16  24  32  walker

Mean: 0.35 (ideal: 0.2-0.5)
```

---

## Creating Your Own Plots

### Reproduce These Examples

```python
import matplotlib.pyplot as plt
import corner
from src.main import main

# Run SPECTRA
main()

# Load results
import pandas as pd
results = pd.read_csv('output/fit_summary.csv')

# Plot mass-age relation
plt.figure(figsize=(8, 6))
plt.scatter(results['mass'], results['age'], 
           c=results['metallicity'], cmap='viridis')
plt.xlabel('log(M/M☉)')
plt.ylabel('Age (Gyr)')
plt.yscale('log')
plt.colorbar(label='[Z/H]')
plt.savefig('mass_age_relation.png', dpi=300)
```

### Custom Corner Plots

```python
import corner
import numpy as np

# Load MCMC samples
samples = np.load('output/object1/mcmc_samples.npy')

# Create custom corner plot
fig = corner.corner(
    samples,
    labels=['log(M/M☉)', 'Age (Gyr)', '[Z/H]', 'E(B-V)'],
    quantiles=[0.16, 0.5, 0.84],
    show_titles=True,
    title_kwargs={"fontsize": 12},
    color='steelblue',
    smooth=1.0,
    bins=30
)
plt.savefig('custom_corner.png', dpi=300)
```

### Publication-Ready SEDs

```python
import matplotlib.pyplot as plt
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
})

fig, (ax1, ax2) = plt.subplots(2, 1, 
                                figsize=(8, 6),
                                height_ratios=[3, 1],
                                sharex=True)

# SED
ax1.errorbar(wavelength, obs_flux, yerr=obs_err,
            fmt='o', color='black', label='Observed')
ax1.plot(wavelength, model_flux, 'r-', lw=2, label='Best-fit')
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_ylabel('Flux (Jy)')
ax1.legend()

# Residuals
residuals = (obs_flux - model_flux) / obs_err
ax2.scatter(wavelength, residuals, color='black')
ax2.axhline(0, ls='--', color='gray')
ax2.set_xscale('log')
ax2.set_xlabel('Wavelength (μm)')
ax2.set_ylabel('Residuals (σ)')

plt.tight_layout()
plt.savefig('publication_sed.pdf', dpi=300, bbox_inches='tight')
```

---

## Parameter Space Interpretation

### Understanding Degeneracies

**Age-Metallicity Degeneracy**:
```
Both increase redness:
- Older age → Redder SED
- Higher metallicity → Redder SED

Solution: Multi-band coverage breaks degeneracy
```

**Mass-Dust Degeneracy**:
```
Both affect flux normalization:
- Lower mass → Fainter SED
- More dust → Dimmer SED

Solution: UV+optical+IR constrains dust separately
```

### Prior Choice Impact

```
Wide priors:          Narrow priors:
age: [0.001, 13] →    age: [0.1, 5.0]

    ╱────╲               ╱╲
   ╱      ╲             ╱  ╲
  ╱        ╲           ╱    ╲
 ╱          ╲         ╱      ╲

Explores full space   Focused on range
May find bimodal      Faster convergence
```

---

## Interactive Examples

View interactive HTML versions with Plotly:

```bash
# Generate interactive plots
python scripts/make_interactive_plots.py

# Open in browser
open output/interactive/sed_plot.html
```

Features:
- Zoom and pan
- Hover for data values
- Toggle individual bands
- Export as PNG/SVG

---

## Next Steps

- [Visualization Guide](../user-guide/visualization.md)
- [MCMC Sampling](../user-guide/mcmc.md)
- [Batch Processing](../user-guide/batch-processing.md)
- [Example Configs](configs.md)
