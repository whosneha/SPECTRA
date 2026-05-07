# Visualization & Plot Customization

All plot options are controlled through the `plotting` section of your config file. The same config drives every object in a run, so you set it once and it applies to all output plots.

## Output Plots

| Plot | When generated | Description |
|------|---------------|-------------|
| `sed.png` | Always | SED fit: observed photometry, model prediction, optional residuals panel |
| `residuals.png` | Always | Per-band residuals in units of sigma |
| `corner.png` | MCMC only | Joint posterior distributions for all fitted parameters |
| `trace.png` | MCMC only | Walker convergence diagnostics (burn-in visualization) |

## All Plotting Options

```yaml
plotting:
  output_dir: outputs/my_run   # Required: where to write plots

  # Output format(s)
  formats: [png, pdf]          # Any combination of: png, pdf, svg
  dpi: 150                     # 150 = screen quality; 300 = print quality
  figure_size: [12, 8]         # [width, height] in inches

  # Style preset (sets fonts and base text sizes)
  plot_style: default          # 'default', 'publication', 'minimal'

  # What to show on the SED plot
  show_components: true        # Unattenuated stellar model curve
  show_error_bars: true        # Error bars on observed photometry
  show_residuals: true         # Residuals panel below the SED
  show_parameter_box: true     # Best-fit parameter annotation on plot

  # Axis units
  wavelength_units: micron     # 'micron' or 'angstrom'
  flux_units: jy               # 'jy' or 'erg'

  # Sizes
  marker_size_obs: 12          # Observed data points
  marker_size_model: 120       # Model prediction markers
  line_width: 1.5

  # Legend
  legend_location: upper right
  legend_fontsize: 10

  # Grid
  show_grid: true
  grid_alpha: 0.3

  # Colors — any valid matplotlib hex or named color
  color_scheme:
    observed: '#2980B9'        # Observed photometry
    model: '#E74C3C'           # Best-fit model
    unattenuated: '#F1C40F'    # Unattenuated model component
    residual_good: '#2ECC71'   # < 1 sigma
    residual_warn: '#F39C12'   # 1–2 sigma
    residual_bad: '#E74C3C'    # > 2 sigma
```

## Style Presets

| Preset | Font | Base size | Best for |
|--------|------|-----------|----------|
| `default` | sans-serif | 11 pt | General use |
| `publication` | serif | 14 pt | Papers, proposals |
| `minimal` | sans-serif | 10 pt | Quick batch checks |

## Example Configs

Three ready-to-use examples are in `example_configs/`:

| Config | Description |
|--------|-------------|
| `config_custom_plotting.yaml` | All options set explicitly with comments |
| `config_minimal_plotting.yaml` | Fast, low-res PNGs, no residuals/annotation |
| `config_presentation_plotting.yaml` | 300 DPI PDF+PNG, publication style, deep colors |

