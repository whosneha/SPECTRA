# Quick Start

## Primary Use Case: Rubin + External Sources

The recommended workflow combines **Rubin optical photometry with external UV/NIR/mid-IR sources**:

### Example: Rubin + GALEX multi-wavelength

```bash
# 1. Validate config
./bin/spectra --config example_configs/config_rubin_galex.yaml --validate

# 2. Run ML fit (fast, ~seconds)
./bin/spectra --config example_configs/config_rubin_galex.yaml --max-rows 10 --method ml

# 3. Inspect outputs
ls outputs/rubin_galex/
```

This query Rubin optical bands + GALEX UV → full SED from 0.15–0.97 μm.

---

## Alternative Examples

### PHANGS-HST star cluster fitting

```bash
./bin/spectra --config example_configs/config_phangs.yaml --max-rows 1 --method ml
```

### Fornax globular cluster CSV

```bash
./bin/spectra --config example_configs/config_phangs.yaml --validate
./bin/spectra --config config_fornax.yaml --method ml
```

### Using Python entry point

```bash
python run.py example_configs/config_rubin_galex.yaml
```

---

## Get Full Posteriors with MCMC

```bash
./bin/spectra --config example_configs/config_rubin_galex.yaml --max-rows 10 --method mcmc
```

(Takes ~2 min per object; see [MCMC Guide](../user-guide/mcmc.md) for details)

---

## Results

Outputs are written to your configured output directory:
- `outputs/rubin_galex/` – SED plots, parameter tables, diagnostics
- One subfolder per object with `sed.pdf`, `results.csv`, corner plots, etc.

See [Outputs](../outputs.md) for full details.
