# Main Pipeline API

The main orchestration code lives in `src/main.py`.

## Core functions

- `main(config_path)`
- `get_input_data(config)`
- `process_single_object(object_id, phot_data, config, ssp_model_base_config)`
- `save_summary(all_results, output_dir, config)`

## Typical flow

1. Load YAML config
2. Build object datasets from configured input type
3. Fit each object
4. Save plots and summary outputs
