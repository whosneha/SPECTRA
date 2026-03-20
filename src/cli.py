"""
SPECTRA Command-Line Interface

Usage:
    spectra --config config.yaml              # Run with config file
    spectra --rubin-id 12345 --config cfg     # Quick Rubin query
    spectra --help                             # Show help
"""

import argparse
import sys
import os
from pathlib import Path

# Import from src.main directly (no package structure needed)
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.main import main as run_pipeline


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="spectra",
        description="SPECTRA: Stellar Population SED Fitter for Rubin/LSST and multi-wavelength data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with existing config file
  spectra --config config_rubin.yaml
  
  # Run batch processing on PHANGS catalog
  spectra --config config_phangs.yaml
  
  # Process single Rubin object (creates temporary config)
  spectra --rubin-id 1234567890 --token YOUR_TOKEN
  
  # Process FITS catalog with custom priors
  spectra --config my_clusters.yaml --output results/run01
  
Configuration File Structure:
  See example configs in the repository:
    - config_rubin.yaml    (Rubin/LSST TAP queries)
    - config_phangs.yaml   (PHANGS-HST cluster catalogs)
    - config_fornax.yaml   (Fornax GC photometry)
  
For detailed documentation: https://github.com/yourusername/SPECTRA
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to YAML configuration file (required unless using --rubin-id shortcut)"
    )
    
    # Quick Rubin query mode
    parser.add_argument(
        "--rubin-id",
        type=str,
        help="Rubin object ID for quick query (creates temporary config)"
    )
    
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Rubin RSP authentication token (or set RSP_TOKEN env variable)"
    )
    
    # Optional overrides
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Override output directory from config"
    )
    
    parser.add_argument(
        "--method",
        type=str,
        choices=["ml", "mcmc"],
        default=None,
        help="Override fitting method (ml=fast, mcmc=full posteriors)"
    )
    
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Override max_rows for batch processing (useful for testing)"
    )
    
    # Info flags
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="SPECTRA 1.0.0"
    )
    
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="List available example config files"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate config file without running"
    )
    
    args = parser.parse_args()
    
    # Handle --list-configs
    if args.list_configs:
        list_example_configs()
        return 0
    
    # Determine config file path
    if args.rubin_id:
        # Quick Rubin mode: create temporary config
        config_path = create_temp_rubin_config(args.rubin_id, args.token, args.output)
        print(f"[SPECTRA] Created temporary config for Rubin ID {args.rubin_id}")
        print(f"[SPECTRA] Config: {config_path}")
    elif args.config:
        config_path = args.config
        if not os.path.exists(config_path):
            print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
            print(f"\nUse --list-configs to see available examples", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        print("\nERROR: Either --config or --rubin-id must be specified", file=sys.stderr)
        return 1
    
    # Validate config
    if args.validate:
        return validate_config(config_path)
    
    # Apply CLI overrides
    if args.output or args.method or args.max_rows:
        config_path = apply_config_overrides(
            config_path, args.output, args.method, args.max_rows
        )
    
    # Run pipeline
    print(f"\n{'='*70}")
    print(f"SPECTRA: Stellar Population SED Fitter")
    print(f"Config: {config_path}")
    print(f"{'='*70}\n")
    
    try:
        run_pipeline(config_path)
        return 0
    except Exception as e:
        print(f"\nERROR: Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def list_example_configs():
    """List available example configuration files."""
    repo_root = Path(__file__).parent.parent
    config_dir = repo_root / "example_configs"
    
    print("\n" + "="*70)
    print("AVAILABLE EXAMPLE CONFIGS")
    print("="*70)
    print(f"\nConfig directory: {config_dir}\n")
    
    examples = [
        ("config_phangs.yaml", "PHANGS-HST star cluster catalogs (FITS tables)"),
        ("config_rubin.yaml", "Rubin/LSST TAP queries (single object)"),
        ("config_rubin_batch.yaml", "Batch Rubin object IDs"),
        ("config_rubin_cone_search.yaml", "Rubin spatial cone search"),
        ("config_rubin_galex.yaml", "Rubin + GALEX multi-wavelength"),
        ("config_rubin_from_csv.yaml", "Rubin IDs from CSV file"),
        ("config_single_fits.yaml", "Single FITS binary table"),
        ("config_custom_plotting.yaml", "Plot customization demo"),
        ("config_minimal_plotting.yaml", "Minimal plot style"),
        ("config_presentation_plotting.yaml", "Presentation plot style"),
    ]
    
    for filename, description in examples:
        filepath = config_dir / filename
        status = "[found]" if filepath.exists() else "[missing]"
        print(f"  {status} {filename}")
        print(f"          {description}")
    
    print("\n" + "="*70)
    print("Copy and modify an example config for your use case:")
    print("  cp example_configs/config_rubin.yaml my_project.yaml")
    print("  spectra --config my_project.yaml")
    print("="*70 + "\n")


def create_temp_rubin_config(rubin_id, token, output_dir):
    """Create temporary config for quick Rubin query."""
    import yaml
    import tempfile
    
    token = token or os.environ.get("RSP_TOKEN")
    if not token:
        print("ERROR: --token required or set RSP_TOKEN environment variable", file=sys.stderr)
        sys.exit(1)
    
    config = {
        "input": {
            "type": "rubin_id",
            "rubin_id": int(rubin_id),
        },
        "rubin": {
            "rsp_token": token,
            "flux_type": "psfFlux",
            "bands": ["u", "g", "r", "i", "z", "y"],
        },
        "ssp_model": {
            "type": "fsps",
            "redshift": 0.0,
            "imf": "chabrier",
            "sfh": 0,
            "dust_type": 2,
            "add_neb_emission": False,
        },
        "fitting": {
            "method": "ml",
            "error_floor": 0.05,
            "parameters": ["mass", "age", "metallicity", "dust"],
            "priors": {
                "mass": [8.0, 13.0],
                "age": [0.001, 13.5],
                "metallicity": [-2.5, 0.5],
                "dust": [0.0, 3.0],
            },
        },
        "plotting": {
            "output_dir": output_dir or f"outputs/rubin_{rubin_id}",
            "show_plots": False,
            "save_plots": True,
            "plot_format": "png",
            "dpi": 150,
        },
        "output": {
            "save_photometry": True,
        },
    }
    
    # Save to temp file
    temp_dir = Path(tempfile.gettempdir()) / "spectra"
    temp_dir.mkdir(exist_ok=True)
    config_path = temp_dir / f"rubin_{rubin_id}.yaml"
    
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return str(config_path)


def validate_config(config_path):
    """Validate configuration file without running."""
    import yaml
    
    print(f"\n{'='*70}")
    print(f"VALIDATING CONFIG: {config_path}")
    print(f"{'='*70}\n")
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required = ["input", "ssp_model", "fitting", "plotting"]
        missing = [sec for sec in required if sec not in config]
        if missing:
            print(f"✗ Missing required sections: {', '.join(missing)}")
            return 1
        
        # Validate input section
        input_type = config["input"].get("type")
        if not input_type:
            print("✗ input.type is required")
            return 1
        
        valid_types = ["rubin_id", "rubin_tap", "phangs_fits", "fornax_csv", 
                       "fits", "dat", "csv", "file_list", "fits_batch"]
        if input_type not in valid_types:
            print(f"✗ Unknown input.type: {input_type}")
            print(f"   Valid types: {', '.join(valid_types)}")
            return 1
        
        print(f"✓ Input type: {input_type}")
        
        # Type-specific validation
        if input_type == "rubin_id":
            if "rubin_id" not in config["input"]:
                print("✗ input.rubin_id is required for rubin_id type")
                return 1
            if "rubin" not in config or "rsp_token" not in config["rubin"]:
                if "RSP_TOKEN" not in os.environ:
                    print("✗ rubin.rsp_token required or set RSP_TOKEN env variable")
                    return 1
        
        elif input_type in ["phangs_fits", "fornax_csv", "fits", "dat", "csv"]:
            if "filepath" not in config["input"]:
                print(f"✗ input.filepath is required for {input_type} type")
                return 1
            filepath = config["input"]["filepath"]
            if not os.path.exists(filepath):
                print(f"✗ File not found: {filepath}")
                return 1
            print(f"✓ Input file: {filepath}")
        
        # Validate fitting parameters
        params = config["fitting"].get("parameters", [])
        priors = config["fitting"].get("priors", {})
        for p in params:
            if p not in priors:
                print(f"✗ Missing prior for parameter: {p}")
                return 1
        print(f"✓ Fitting parameters: {', '.join(params)}")
        
        # Validate output directory
        output_dir = config["plotting"]["output_dir"]
        print(f"✓ Output directory: {output_dir}")
        
        print(f"\n{'='*70}")
        print("✓ CONFIG VALIDATION PASSED")
        print(f"{'='*70}\n")
        return 0
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def apply_config_overrides(config_path, output_dir, method, max_rows):
    """Apply CLI overrides to config."""
    import yaml
    import tempfile
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if output_dir:
        config["plotting"]["output_dir"] = output_dir
        print(f"[OVERRIDE] Output directory: {output_dir}")
    
    if method:
        config["fitting"]["method"] = method
        print(f"[OVERRIDE] Fitting method: {method}")
    
    if max_rows:
        config["input"]["max_rows"] = max_rows
        print(f"[OVERRIDE] Max rows: {max_rows}")
    
    # Save modified config to temp file
    temp_dir = Path(tempfile.gettempdir()) / "spectra"
    temp_dir.mkdir(exist_ok=True)
    temp_config = temp_dir / f"config_override_{os.getpid()}.yaml"
    
    with open(temp_config, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    return str(temp_config)


if __name__ == "__main__":
    sys.exit(main())
