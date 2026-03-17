# SSP Models

Simple Stellar Population (SSP) models are the foundation of SED fitting in SPECTRA.

## Overview

SSP models predict the spectral energy distribution of a stellar population with:
- **Uniform age**: All stars formed at the same time
- **Uniform metallicity**: Single chemical composition
- **Initial Mass Function (IMF)**: Distribution of stellar masses

SPECTRA uses these models to fit observed photometry and derive physical parameters.

## Available Models

### Bruzual & Charlot (2003)

The default SSP model in SPECTRA.

```yaml
ssp_model:
  model_type: 'bruzual_charlot'
  imf: 'chabrier'
  redshift: 0.0
```

**Features**:
- Age range: 0.1 Myr - 20 Gyr
- Metallicity range: Z = 0.0001 to 0.05 (−2.25 ≤ [Z/H] ≤ +0.4)
- IMF options: Chabrier, Salpeter, Kroupa
- Wavelength coverage: 91 Å - 160 μm

**Use cases**:
- General galaxy SED fitting
- High-redshift galaxies
- Quiescent and star-forming galaxies

### FSPS (Flexible Stellar Population Synthesis)

```yaml
ssp_model:
  model_type: 'fsps'
  imf: 'chabrier'
  dust_model: 'calzetti'
```

**Features**:
- More flexible dust attenuation
- AGN contribution modeling
- Emission line templates

*Note: FSPS integration is planned for future releases*

## Model Parameters

### Mass (log M☉)

Total stellar mass in solar masses (logarithmic).

```yaml
priors:
  mass: [8.0, 13.0]  # 10^8 to 10^13 M☉
```

**Typical values**:
- Dwarf galaxies: 8-10
- Milky Way-mass: 10-11
- Massive ellipticals: 11-12
- Galaxy clusters: 12-13

### Age (Gyr)

Time since star formation began.

```yaml
priors:
  age: [0.001, 13.0]  # 1 Myr to 13 Gyr
```

**Typical values**:
- Young starbursts: 0.001-0.1 Gyr
- Star-forming galaxies: 0.1-5 Gyr
- Quiescent galaxies: 5-13 Gyr
- Globular clusters: 10-13 Gyr

### Metallicity ([Z/H])

Metal abundance relative to solar.

```yaml
priors:
  metallicity: [-2.0, 0.5]  # [Z/H]
```

**Typical values**:
- Metal-poor: -2.0 to -1.0
- Sub-solar: -1.0 to -0.2
- Solar: ~0.0
- Super-solar: 0.0 to +0.5

**Conversions**:
```
[Z/H] = log₁₀(Z/Z☉)
Z☉ = 0.02 (solar metallicity)
```

### Dust Attenuation (E(B-V) or τ_V)

Amount of dust extinction.

```yaml
priors:
  dust: [0.0, 2.0]  # E(B-V) mag
```

**Dust laws**:
- Calzetti et al. (2000): Starburst galaxies
- Cardelli et al. (1989): Milky Way
- SMC: Small Magellanic Cloud

**Typical values**:
- No dust: 0.0
- Moderate: 0.1-0.5
- Dusty starbursts: 0.5-2.0
- ULIRGs: 1.0-3.0

## Redshift Effects

Models are automatically redshifted to match observations:

```yaml
ssp_model:
  redshift: 4.5  # Applied to all objects
```

**Or extract from filename**:
```
# object_z4p59.dat → z=4.59
# cluster_z6p01.fits → z=6.01
```

**Effects**:
- K-correction: Observed frame ≠ rest frame
- Wavelength shift: λ_obs = λ_rest × (1 + z)
- Flux dimming: Factor of (1 + z)⁴
- Lookback time: Age < age of universe at z

## Flux Calibration

Models are calibrated to observed flux levels:

```python
ssp_model.set_flux_calibration(observed_flux)
```

This accounts for:
- Distance/luminosity
- Instrumental throughput
- Absolute vs relative photometry

## Model Generation

### At Runtime

```python
from src.models.ssp_model import SSPModel

config = {
    'redshift': 0.5,
    'model_type': 'bruzual_charlot',
    'imf': 'chabrier'
}

model = SSPModel(config)

# Generate SED
wavelengths = np.array([0.4, 0.5, 0.6, 0.8, 1.0])  # μm
flux = model.get_magnitudes(
    mass=11.0,
    age=1.0,
    metallicity=-0.5,
    dust=0.3,
    wavelengths=wavelengths
)
```

### Interpolation

Models use interpolation for continuous parameter space:

- **Age**: Linear in log-space
- **Metallicity**: Linear in [Z/H]
- **Wavelength**: Linear or cubic spline

## Dust Attenuation

### Calzetti Law (Default)

```python
def calzetti_attenuation(wavelength, ebv, rv=4.05):
    """
    Calzetti et al. (2000) dust attenuation law.
    
    wavelength: μm
    ebv: E(B-V) magnitude
    rv: Total-to-selective extinction ratio
    """
    k_lambda = compute_k_lambda(wavelength)
    A_lambda = ebv * k_lambda * rv
    return 10**(-0.4 * A_lambda)
```

### Custom Dust Laws

Implement custom attenuation:

```python
class CustomSSPModel(SSPModel):
    def apply_dust_attenuation(self, flux, wavelength, dust):
        # Your custom dust law
        attenuation = my_dust_function(wavelength, dust)
        return flux * attenuation
```

## Model Limitations

### Assumptions

1. **Single stellar population**: All stars same age/metallicity
2. **Instantaneous burst**: Star formation at single epoch
3. **No AGN**: Pure stellar emission
4. **No nebular emission**: Only stellar continuum

### Extensions

For more complex scenarios:
- **Composite models**: Combine multiple SSPs
- **Star formation histories**: Delayed τ-models, constant SFR
- **Nebular emission**: Add emission line templates
- **AGN contribution**: Power-law or template components

## Model Comparison

```python
# Fit with different models
configs = [
    {'model_type': 'bc03', 'imf': 'chabrier'},
    {'model_type': 'bc03', 'imf': 'salpeter'},
]

for cfg in configs:
    model = SSPModel(cfg)
    # Fit and compare results
```

## Best Practices

1. **Choose appropriate priors**: Based on object type
2. **Match redshift**: Correct cosmology for high-z
3. **Dust treatment**: Consider dust law for object type
4. **Age-metallicity degeneracy**: Be aware of correlations
5. **Wavelength coverage**: More bands break degeneracies

## Diagnostic Plots

Visualize model SEDs:

```python
import matplotlib.pyplot as plt

ages = [0.1, 0.5, 1.0, 5.0, 10.0]  # Gyr
wavelengths = np.logspace(np.log10(0.1), np.log10(5.0), 100)

for age in ages:
    flux = model.get_magnitudes(
        mass=11.0, age=age, metallicity=0.0, dust=0.0,
        wavelengths=wavelengths
    )
    plt.plot(wavelengths, flux, label=f'{age} Gyr')

plt.xscale('log')
plt.yscale('log')
plt.xlabel('Wavelength (μm)')
plt.ylabel('Flux (Jy)')
plt.legend()
plt.show()
```

## Physical Interpretation

### Derived Properties

From best-fit parameters:

```python
# Star formation rate (for young ages)
if age < 0.1:  # Gyr
    sfr = mass / (age * 1e9)  # M☉/yr

# Specific star formation rate
ssfr = sfr / (10**mass)  # yr⁻¹

# Mass-to-light ratio
m_to_l = 10**mass / luminosity

# Colors
u_minus_r = flux_u / flux_r  # Flux ratio → mag difference
```

### Uncertainties

Parameter uncertainties from MCMC:

```python
# From corner plot or chain analysis
mass_median = np.median(chain[:, 0])
mass_std = np.std(chain[:, 0])

print(f"Mass: {mass_median:.2f} ± {mass_std:.2f} log M☉")
```

## Example Use Cases

### 1. High-z Galaxy

```yaml
ssp_model:
  redshift: 6.5
  model_type: 'bruzual_charlot'

fitting:
  priors:
    mass: [9.0, 11.5]
    age: [0.001, 1.0]  # Young universe!
    metallicity: [-2.0, -0.5]  # Lower metallicity
    dust: [0.0, 1.5]
```

### 2. Quiescent Galaxy

```yaml
fitting:
  priors:
    mass: [10.5, 12.0]
    age: [5.0, 13.0]  # Old
    metallicity: [-0.5, 0.3]  # Solar to super-solar
    dust: [0.0, 0.3]  # Little dust
```

### 3. Starburst

```yaml
fitting:
  priors:
    mass: [9.0, 11.0]
    age: [0.001, 0.5]  # Very young
    metallicity: [-1.0, 0.2]
    dust: [0.5, 2.0]  # Dusty!
```

## API Reference

See [Models API](../api/models.md) for complete documentation.

## Next Steps

- [Fitting Methods](fitting-methods.md)
- [Custom Models Tutorial](../tutorials/custom-models.md)
- [API Reference](../api/models.md)
