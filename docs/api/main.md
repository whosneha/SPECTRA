# Main Module API

::: src.main
    options:
      show_source: true
      heading_level: 2
      members:
        - main
        - get_input_data
        - process_single_object
        - save_summary
        - get_input_files
        - extract_object_id
        - extract_redshift_from_filename

## Overview

The main module orchestrates the entire fitting pipeline, from data loading to result visualization.

## Key Functions

### `main()`

Main entry point for SPECTRA. Loads configuration, processes all objects, and generates summary.

**Returns**: None

**Side effects**: 
- Creates output directories
- Generates plots
- Saves fit results and summary CSV

### `get_input_data(config)`

Load input data based on configuration type.

**Parameters**:
- `config` (dict): Configuration dictionary

**Returns**: List of (object_id, phot_data) tuples

**Supported input types**:
- `fits_batch`: Multiple rows from FITS files
- `fits`: Single FITS file
- `rubin_id`: Rubin Observatory by object ID
- `rubin_tap`: Rubin Observatory by coordinates
- `dat`, `csv`: Single data files
- `file_list`: List of files

### `process_single_object(object_id, phot_data, config, ssp_model_base_config)`

Process a single object's photometry.

**Parameters**:
- `object_id` (str): Unique identifier
- `phot_data` (dict): Photometry data
- `config` (dict): Configuration
- `ssp_model_base_config` (dict): SSP model configuration

**Returns**: Dictionary containing:
- `parameters`: Best-fit parameters
- `log_likelihood`: Final likelihood value
- `mod_flux`: Model flux values
- `percentiles`: Error estimates (MCMC only)

### `save_summary(all_results, output_dir, config)`

Save summary CSV of all fits.

**Parameters**:
- `all_results` (list): List of result dictionaries
- `output_dir` (str): Output directory path
- `config` (dict): Configuration

**Returns**: None

## Example Usage

```python
import yaml
from src.main import main, get_input_data, process_single_object

# Run full pipeline
main()

# Or process individually
with open('config.yaml') as f:
    config = yaml.safe_load(f)

datasets = get_input_data(config)
for obj_id, phot_data in datasets:
    result = process_single_object(obj_id, phot_data, config, config['ssp_model'])
    print(f"Processed {obj_id}: log_L = {result['log_likelihood']:.2f}")
```
