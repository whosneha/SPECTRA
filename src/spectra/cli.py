"""
Command-line interface for SPECTRA.

Usage
-----
    spectra run [--config CONFIG]
    spectra --help
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="spectra",
        description="SPECTRA: SED fitting for resolved star clusters.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- spectra run ---
    run_parser = subparsers.add_parser("run", help="Run the SED fitting pipeline.")
    run_parser.add_argument(
        "--config",
        default="config.yaml",
        metavar="CONFIG",
        help="Path to config.yaml (default: config.yaml in current directory).",
    )

    args = parser.parse_args()

    if args.command == "run":
        from spectra.main import main as run_pipeline
        run_pipeline(config_path=args.config)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
