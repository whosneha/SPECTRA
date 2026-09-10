# Installation

## Requirements

- Python 3.9+
- `pip`
- a Rubin Science Platform token only if you plan to use Rubin TAP queries

## Recommended setup

```bash
git clone https://github.com/whosneha/SPECTRA.git
cd SPECTRA

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export PATH="$PWD/bin:$PATH"
spectra --help
```

## Verify the install

```bash
python tests/run_installation_tests.py
pytest
```

If `pytest` is too slow for a fresh environment, the installation test script is the faster smoke test.

## Rubin setup

For Rubin workflows, export your token before running a config that uses `rubin_id`, `rubin_tap`, `rubin_cone_search`, or `rubin_from_csv`:

```bash
export RSP_TOKEN="your_rsp_token"
spectra --validate --config example_configs/config_dp02_test.yaml
```

## Optional FSPS setup

SPECTRA can run in a fallback/mock mode without FSPS. If you want FSPS-backed models:

```bash
export SPS_HOME=/path/to/fsps
pip install fsps
```

If you plan to use BC03 grids instead, see `spectra setup bc03 --help`.
