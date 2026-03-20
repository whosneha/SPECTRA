import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    # Default to example_configs/config_phangs.yaml if no argument given
    config_path = sys.argv[1] if len(sys.argv) > 1 else "example_configs/config_phangs.yaml"
    main(config_path)
