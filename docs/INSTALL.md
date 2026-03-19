# SPECTRA Installation Guide

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/SPECTRA.git
cd SPECTRA

# 2. Add to PATH (for 'spectra' command)
export PATH="$PWD/bin:$PATH"

# 3. (Optional) Install FSPS for real SSP models
# Download FSPS first: https://github.com/cconroy20/fsps
export SPS_HOME=/path/to/fsps
pip install fsps

# 4. Run example
spectra --config config_phangs.yaml --max-rows 1
```

## Installation Options

### Option A: Simple Wrapper (No Installation)
This is the easiest method — no `pip` or package management needed.

```bash
cd SPECTRA
export PATH="$PWD/bin:$PATH"
spectra --version
```

To make it permanent, add to your shell config:
```bash
# For zsh (Mac default)
echo 'export PATH="/path/to/SPECTRA/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash (Linux)
echo 'export PATH="/path/to/SPECTRA/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Option B: Python Module (Always Works)
Run directly as a Python module:

```bash
cd SPECTRA
python run.py config_phangs.yaml
# or
python -m src.main config_phangs.yaml
```

### Option C: Pip Install (Advanced)
For developers who want the package installed:

```bash
cd SPECTRA
pip install -e .
# The 'spectra' command is now available system-wide
```

## Dependencies

### Required
Install via pip or conda:

```bash
pip install numpy scipy matplotlib astropy pyyaml pandas emcee corner h5py tqdm
```

Or from conda:
```bash
conda install numpy scipy matplotlib astropy pyyaml pandas
pip install emcee corner h5py tqdm
```

### Optional: FSPS (Real SSP Models)

**1. Download and build FSPS:**
```bash
git clone https://github.com/cconroy20/fsps.git
cd fsps/src
make
```

**2. Set environment variable:**
```bash
export SPS_HOME=/path/to/fsps
# Add to ~/.zshrc or ~/.bashrc to make permanent
echo 'export SPS_HOME=/path/to/fsps' >> ~/.zshrc
```

**3. Install Python wrapper:**
```bash
pip install fsps
```

**4. Test it works:**
```bash
python -c "import fsps; print('✓ FSPS loaded')"
```

If you skip FSPS, SPECTRA will use mock models (good for testing).

### Optional: Rubin/LSST TAP Queries

For querying Rubin Science Platform:

```bash
pip install requests astroquery
```

Set your RSP token:
```bash
export RSP_TOKEN="your_token_here"
# Add to ~/.zshrc to make permanent
echo 'export RSP_TOKEN="your_token"' >> ~/.zshrc
```

## Verify Installation

```bash
# Check CLI is available
spectra --version

# List example configs
spectra --list-configs

# Validate a config
spectra --config config_phangs.yaml --validate

# Run a quick test (1 cluster, ML fitting)
spectra --config config_phangs.yaml --max-rows 1 --method ml
```

## Troubleshooting

### "spectra: command not found"
Add the `bin/` directory to your PATH:
```bash
cd /path/to/SPECTRA
export PATH="$PWD/bin:$PATH"
```

Or use the alternative methods:
```bash
python run.py config.yaml
python -m src.main config.yaml
./bin/spectra --config config.yaml
```

### "SPS_HOME not set"
FSPS is optional. The pipeline will fall back to mock mode if FSPS isn't available.

To fix:
```bash
export SPS_HOME=/path/to/fsps
# Make permanent:
echo 'export SPS_HOME=/path/to/fsps' >> ~/.zshrc
```

### "RSP_TOKEN required"
For Rubin queries, set your token:
```bash
export RSP_TOKEN="your_token"
# Or pass directly:
spectra --rubin-id 123 --token YOUR_TOKEN
```

### Import errors
Make sure you're running from the SPECTRA directory or have added it to PATH:
```bash
cd /path/to/SPECTRA
python run.py config.yaml
```

### Permission denied on ~/.zshrc
If you can't write to shell config:
```bash
chmod u+w ~/.zshrc
# Then try again
```

Or just set PATH in each terminal session:
```bash
export PATH="/path/to/SPECTRA/bin:$PATH"
```

## Platform-Specific Notes

### macOS
- Default shell is `zsh` → use `~/.zshrc`
- FSPS builds require Xcode command line tools: `xcode-select --install`

### Linux
- Default shell is usually `bash` → use `~/.bashrc`
- FSPS requires `gfortran`: `sudo apt install gfortran` (Ubuntu/Debian)

### Windows (WSL)
- Use WSL2 (Windows Subsystem for Linux)
- Follow Linux instructions above

## Uninstalling

```bash
# Remove from PATH (delete the line from ~/.zshrc)
nano ~/.zshrc  # Remove the export PATH line

# If you used pip install:
pip uninstall spectra-sed

# Delete the repository
rm -rf /path/to/SPECTRA
```
