# Science Use Cases

This guide explains where SPECTRA is most effective and when alternative approaches may be needed.

## Ideal Use Cases

### Star Clusters (Nearby, z < 0.01)

**Best for**: Young to intermediate-age clusters (ages 5 Myr–1 Gyr) with resolved or integrated photometry.

**Why it works**:
- Age-metallicity degeneracy reduced by young ages and high metallicity precision
- 5–10 HST/UVIS bands provide strong age discrimination
- Dust attenuation simple and well-modeled
- Example: PHANGS-HST (IC 5332, z = 0.00184)

**Recommended setup**:
```yaml
input:
  type: phangs_fits
  filepath: "cluster_catalog.fits"
ssp_model:
  type: fsps
  imf: kroupa
  dust_model: calzetti
fitting:
  method: ml  # or mcmc for uncertainties
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [3, 7]        # log10(M/Msun)
    age: [-3, 0]        # log10(age/Gyr), i.e., 1 Myr to 1 Gyr
    metallicity: [-0.5, 0.3]  # log10(Z/Zsun)
    dust: [0, 1]        # E(B-V)
```

### Nearby Galaxies (z < 0.1)

**Best for**: Integrated light from nearby galaxies with secure photometry in 8+ bands spanning UV–NIR.

**Why it works**:
- Kiloparsec-scale resolution reduces dust clumping effects
- UV coverage (GALEX) constrains stellar mass
- NIR coverage (WISE, Spitzer) constrains dust
- Metallicity variations are averaged
- Example: SDSS, Rubin/LSST (z ~ 0.01–0.1)

**Recommended setup**:
```yaml
input:
  type: csv
  filepath: "nearby_galaxies.csv"  # Must have columns: wavelength, flux, flux_err
ssp_model:
  type: fsps
  redshift: 0.05
  distance_mpc: 50
fitting:
  method: mcmc  # Use MCMC for Bayesian posteriors
  parameters: [mass, age, metallicity, dust, sfr_fraction]
  priors:
    mass: [8, 12]       # log10(M/Msun)
    age: [-1, 1]        # log10(age/Gyr), i.e., 100 Myr to 10 Gyr
    metallicity: [-1, 0.3]
    dust: [0, 1]
```

### Multi-Wavelength Surveys (z < 1)

**Best for**: Large samples with good photometry coverage (≥8 bands) and reliable redshifts.

**Why it works**:
- Sufficient wavelength baseline to break age-metallicity-dust degeneracies
- Photometric redshift validation becomes possible
- High sample size enables statistical analysis
- Example: CANDELS, COSMOS, Rubin DP0.2

**Recommended setup**:
```yaml
input:
  type: rubin_tap
  ra: 150.1
  dec: 2.2
  radius_arcsec: 1.0
  bands: [u, g, r, i, z, y]
fitting:
  method: ml  # Fast; use MCMC for subset
  parameters: [mass, age, metallicity]
  priors:
    mass: [6, 12]
    age: [0, 1]         # log10(age/Gyr)
    metallicity: [-1.5, 0.3]
```

---

## Known Limitations

### High-Redshift Objects (z > 2–3)

High-redshift SED fitting is challenging due to fundamental physical and observational limitations:

#### 1. Age-Metallicity-Redshift Degeneracies

At high-z, three different models can produce nearly identical photometry:
- **Young, metal-rich** at z=4 may look like **old, metal-poor** at z=4
- Adding redshift as a free parameter (when uncertain) compounds degeneracies
- SSP models assume single-burst star formation, but most high-z galaxies have complex SFH

**Impact**: Fitted stellar mass can vary by ±0.5 dex; age by ±1 order of magnitude.

#### 2. Limited Wavelength Coverage

Observer-frame optical (0.4–1.0 μm) at high-z probes rest-frame UV (0.08–0.2 μm at z=4):

| Redshift | Rest Frame UV Probed | Observer Frame Bands | Best For |
|----------|---------------------|---------------------|----------|
| z = 0–0.1 | 0.16–1.6 μm | UV (GALEX) → NIR (WISE) | All parameters |
| z = 1–2 | 0.08–0.4 μm | Optical (HST) + NIR (Spitzer) | Mass + dust |
| z = 3–4 | 0.08–0.25 μm | Optical (HST) + FIR (JWST) | Mass only; age unconstrained |
| z > 4 | < 0.1 μm | FUV gap; need JWST NIR | Dust; stellar mass uncertain |

**Impact**: Only stellar mass is well-constrained; age and metallicity are highly uncertain.

#### 3. Dust Attenuation Degeneracies

High-z galaxies are systematically dustier (A_V ~ 0.5–2 mag) than nearby galaxies:
- Dust reddening mimics old age or high metallicity
- Calzetti dust law varies with galaxy properties; simple models break down
- Observational uncertainties in UV slope are ~2× larger at high-z

**Impact**: Fitted age can shift by ±0.3 dex if dust model is incorrect.

#### 4. Model Extrapolation Issues

FSPS/BC03 models are calibrated on nearby stars and Galactic globular clusters:
- Stellar libraries extend to ~4000 K (M dwarfs), but coverage is sparse
- High-z observations probe mainly massive stars (hot, blue)
- Isochrone extrapolation to z > 0.3 carries ~5–10% systematic error

**Impact**: Fits to high-z data have irreducible systematic uncertainty ~ 0.1–0.3 dex in derived properties.

#### 5. Observational Challenges

- **Sky subtraction**: High-z faint galaxies require extremely precise sky background (10× harder than z~0)
- **Photometric scatter**: Flux errors are typically 10–20% at z > 3 (vs. 2–5% locally)
- **Redshift uncertainty**: Photo-z scatter of ±0.05(1+z) creates huge age-z covariance

**Impact**: Formal uncertainties underestimate true systematic error; confidence intervals too small by 2–3×.

---

## When to Use SPECTRA vs. Alternatives

### Use SPECTRA if:
- Target is nearby (z < 1) with secure spectroscopic redshift
- Photometry SNR > 5 per band
- You have 5+ photometric bands
- Age/metallicity estimates are scientifically important
- You have time for manual validation (~10 min per fit)

### Use alternatives if:
- **Photo-z dominated error**: Use template codes (EazyPy, Le Phare, EAZY) optimized for photo-z accuracy
- **Complex SFH required**: Use Prospector, Bagpipes, or other codes with flexible SFH grids
- **Very high-z (z > 4)**: Use ASTRODEEP, CANDELS-specialized codes with z-optimized templates
- **AGN contribution uncertain**: Include AGN templates; SPECTRA doesn't model AGN emission
- **Bayesian model comparison needed**: Use Prospector (supports model selection via evidence)

---

## Configuration Recommendations by Science Goal

### Goal: Stellar Mass (all-z)

**Best case (z < 1 with IR)**: Mass accurate to ±0.1 dex
```yaml
fitting:
  parameters: [mass, dust]  # Fix age/metallicity
  priors:
    mass: [7, 12]
    dust: [0, 1]
  error_floor: 0.1
```

**Worst case (z > 3, optical only)**: Mass uncertain by ±0.3–0.5 dex
```yaml
fitting:
  parameters: [mass, metallicity]  # Age unconstrained
  priors:
    mass: [8, 12]
    metallicity: [-2, 0.5]
  error_floor: 0.15
```

### Goal: Age + Metallicity (z < 0.5)

**Setup**:
```yaml
fitting:
  method: mcmc  # Use MCMC for posteriors; ML alone is insufficient
  parameters: [mass, age, metallicity, dust]
  priors:
    mass: [6, 12]
    age: [-2, 1.5]
    metallicity: [-1.5, 0.5]
    dust: [0, 1]
```

**Validation**: Run on known SSP templates first (globular clusters, star clusters) to test accuracy.

### Goal: Dust Attenuation (UV-rich data)

**Setup**:
```yaml
fitting:
  parameters: [dust, metallicity]  # Decouple dust from age
  priors:
    dust: [0, 2]
    metallicity: [-1, 0.3]
  error_floor: 0.05
  dust_law: calzetti  # or cardelli for MW dust
```

---

## Troubleshooting High-z Fits

If your high-z fit has χ²_red > 3 or looks pathological:

1. **Check photometry**: Plot SED; look for outlier bands or flux sign errors
2. **Add error floor**: Increase `error_floor` from 0.1 to 0.2–0.3 to account for systematic errors
3. **Fix age or metallicity**: If highly degenerate, hold one parameter fixed (e.g., solar metallicity)
4. **Use ML only**: MCMC can waste compute exploring degenerate parameter space; use ML for initial fit
5. **Validate redshift**: Verify spectroscopic redshift is secure; photo-z scatter breaks fitting badly
6. **Add NIR data**: If available (Spitzer, JWST), include in photometry; dramatically improves age constraints

---

## References

- **FSPS models**: Conroy, Gunn & White (2009); Conroy & Gunn (2010)
- **Dust laws**: Calzetti et al. (2000); Cardelli, Clayton & Mathis (1989)
- **High-z SED fitting**: Dickinson et al. (2003, GOODS); Skelton et al. (2014, CANDELS)
- **Bayesian methods**: Gallazzi et al. (2005); Conroy (2013, SFH review)
