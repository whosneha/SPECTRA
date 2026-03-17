# Installation

## Requirements

- Python 3.8 or higher
- pip or conda package manager

## Dependencies

SPECTRA requires the following Python packages:

- `numpy` - Numerical computations
- `scipy` - Scientific computing and optimization
- `matplotlib` - Plotting and visualization
- `pandas` - Data manipulation
- `astropy` - Astronomical data handling
- `emcee` - MCMC sampling
- `corner` - Corner plots for MCMC results
- `PyYAML` - Configuration file parsing
- `h5py` - HDF5 file support

## Installation Steps

### Option 1: From Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA

# Install dependencies
pip install -r requirements.txt

# Or using conda
conda env create -f environment.yml
conda activate spectra
```

### Option 2: Development Installation

```bash
# Clone and install in development mode
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA
pip install -e .
```

## Verify Installation

```python
import sys
sys.path.insert(0, 'src')

from src.models.ssp_model import SSPModel
from src.likelihood import Likelihood
from src.fit import SEDFitter

print("SPECTRA installed successfully!")
```

## Optional: Rubin Observatory Access

For accessing Rubin Observatory data via TAP:

```bash
pip install lsst-rsp pyvo
```

Set your RSP token:

```bash
export RSP_TOKEN="your-token-here"
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration Guide](configuration.md)
