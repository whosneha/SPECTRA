#!/usr/bin/env python3
"""BC03 SSP spectra preprocessor for SPECTRA.

Reads raw Bruzual & Charlot (2003) ``.ised_ASCII`` files, applies spectral
cleaning (Wolf-Rayet spike removal), and writes a clean ``.npz`` cache that
SPECTRA loads at runtime in preference to the raw ASCII files — exactly
analogous to CIGALE's ``database_builder`` preprocessing step.

Usage
-----
Run once after downloading the BC03 stellar population models::

    python -m src.utils.bc03_preprocess \\
        --data-dir /path/to/bc03/Padova2000/chabrier \\
        --imf chabrier \\
        --resolution lr

    # Or, using the BC03_DATA_DIR environment variable:
    python -m src.utils.bc03_preprocess --imf chabrier --resolution lr

The output cache is written to::

    <spectra_repo>/src/data/bc03_<resolution>_<imf>_clean_grid.npz

The cache is excluded from version control (see ``.gitignore``) because it
can be 50–200 MB.  Every user who wants to use BC03 inside SPECTRA needs to
run this script once.

What this script fixes
----------------------
**WR emission spikes (age < 20 Myr)**
    BC03 raw files contain Wolf-Rayet optical emission features — HeII at
    4686 Å, the CIII/NIV blend at 4640–4650 Å, broad WR bumps at
    4600–4720 Å and 5650–5820 Å, and the notorious sodium-D line at 5890 Å
    — that are 10³–10⁴× brighter than the surrounding continuum in the
    raw ASCII tables.  CIGALE removes these inside its ``database_builder``.
    This script replaces them with a robust running-median baseline.

**What this script cannot fix (by design)**
    *TP-AGB NIR excess (age 200 Myr – 2 Gyr)*: The BC03 Padova2000 tracks
    over-predict NIR luminosity at intermediate ages due to the treatment of
    thermally pulsating AGB stars (Maraston 2005; Conroy & van Dokkum 2012).
    This is a stellar-model physics issue, not an ASCII artifact — the same
    numbers appear in CIGALE's database.  A warning is printed if the excess
    is detected.  For accurate NIR photometry at these ages, switch to FSPS
    with MIST or PADOVA isochrones.
"""

import argparse
import gzip
import os
import sys
import warnings

import numpy as np
from scipy.ndimage import median_filter

# ---------------------------------------------------------------------------
# Spectral cleaning parameters
# ---------------------------------------------------------------------------

# Known WR emission-feature windows to replace with running-median baseline.
# Wavelengths are in Å (rest frame).
# Sources: Conti 1991; Smith 1991; van der Hucht 2001; Crowther 2007
WR_SPIKE_WINDOWS = [
    (4580, 4720),   # WR blue bump: HeII 4686 Å, CIII/NIV 4640–4650 Å
    (5650, 5950),   # WR red bump + Na D: WR 5696/5812 Å, Na D 5876–5896 Å
]

# Running-median kernel half-width (in array pixels, not Å).
# LR BC03 has ~20 Å/pixel → 51 pixels ≈ 1000 Å window.
MEDIAN_KERNEL = 51

# After replacing WR windows, any pixel still above this multiple of the
# running-median baseline is also replaced (catches residual artefacts).
SPIKE_THRESHOLD = 10.0

# TP-AGB warning: if NIR/optical flux ratio at ~500 Myr exceeds this value,
# the TP-AGB over-prediction is considered significant enough to warn.
TPAGB_RATIO_WARN = 30.0   # physical SSPs have NIR/V ~ 5–15 at 500 Myr

# ---------------------------------------------------------------------------
# BC03 file parsing  (mirrors SSPModel._load_bc03_grid)
# ---------------------------------------------------------------------------

def _load_bc03_file(filepath):
    """Parse one BC03 ``.ised_ASCII`` (or ``.ised_ASCII.gz``) file.

    Parameters
    ----------
    filepath : str

    Returns
    -------
    wav_aa : ndarray, shape (N_lambda,)
        Wavelengths in Angstroms.
    ages_gyr : ndarray, shape (N_age,)
        Ages in Gyr.
    grid : ndarray, shape (N_age, N_lambda)
        Specific luminosity in L_sun / Å per solar mass formed (raw, uncleaned).
    """
    opener = gzip.open if filepath.endswith('.gz') else open
    with opener(filepath, 'rt', errors='replace') as fh:
        raw = fh.read()

    tokens = raw.split()
    idx = 0

    n_ages = int(tokens[idx]); idx += 1
    ages_yr = np.array([float(tokens[idx + i]) for i in range(n_ages)])
    idx += n_ages
    ages_gyr = ages_yr / 1e9

    # Detect wavelength block: first integer N in the plausible range
    # followed by N strictly increasing positive values.
    n_tok = len(tokens)
    n_wav, wav_start = None, None
    for j in range(idx, min(n_tok - 32, idx + 5000)):
        try:
            cand = int(float(tokens[j]))
        except ValueError:
            continue
        if not (100 <= cand <= 20000):
            continue
        if j + 1 + cand >= n_tok:
            continue
        try:
            vals = np.array([float(x) for x in tokens[j + 1: j + 1 + cand]], dtype=float)
        except ValueError:
            continue
        if (np.all(np.isfinite(vals)) and np.all(vals > 0)
                and np.all(np.diff(vals) > 0)):
            n_wav, wav_start = cand, j + 1
            break

    if n_wav is None:
        raise ValueError(f"Could not locate wavelength grid in: {filepath}")

    wav_aa = np.array([float(tokens[wav_start + i]) for i in range(n_wav)], dtype=float)
    idx = wav_start + n_wav

    grid = np.empty((n_ages, n_wav), dtype=np.float64)
    for i in range(n_ages):
        if idx >= n_tok:
            raise ValueError(f"Unexpected end-of-file while reading spectra: {filepath}")
        try:
            marker = int(float(tokens[idx]))
        except ValueError:
            marker = None
        if marker == n_wav:
            idx += 1
        if idx + n_wav > n_tok:
            raise ValueError(f"Incomplete spectrum block in: {filepath}")
        grid[i] = np.array([float(tokens[idx + j]) for j in range(n_wav)], dtype=float)
        idx += n_wav

    return wav_aa, ages_gyr, grid


# ---------------------------------------------------------------------------
# Spectral cleaning
# ---------------------------------------------------------------------------

def clean_spectrum(spec, wav_aa,
                   wr_windows=WR_SPIKE_WINDOWS,
                   kernel=MEDIAN_KERNEL,
                   threshold=SPIKE_THRESHOLD):
    """Remove Wolf-Rayet emission spikes from one BC03 spectrum.

    Parameters
    ----------
    spec : ndarray, shape (N_lambda,)
        Raw L_sun / Å values from the .ised_ASCII file.
    wav_aa : ndarray, shape (N_lambda,)
        Corresponding wavelengths in Å.
    wr_windows : list of (lo, hi) tuples
        Wavelength ranges (Å) of known WR emission features.
    kernel : int
        Pixel width of the running-median filter used to build a smooth
        baseline.
    threshold : float
        Pixels that exceed ``threshold`` × the smooth baseline are replaced.

    Returns
    -------
    cleaned : ndarray, shape (N_lambda,)
        Spectrum with WR artefacts replaced by the running-median baseline.
    """
    spec = spec.copy()

    # Build a smooth, spike-free baseline once.
    baseline = median_filter(spec, size=kernel, mode='reflect')

    # Step 1 — zero-out the known WR windows and replace with baseline.
    for lo, hi in wr_windows:
        mask = (wav_aa >= lo) & (wav_aa <= hi)
        spec[mask] = baseline[mask]

    # Step 2 — global clip: catch any spikes outside the defined windows.
    # Recompute the baseline after step 1 so it isn't pulled up by the
    # windows themselves.
    baseline2 = median_filter(spec, size=kernel, mode='reflect')
    spike_mask = spec > threshold * np.maximum(baseline2, 1e-60)
    spec[spike_mask] = baseline2[spike_mask]

    return spec


def _check_tpagb(ages_gyr, wav_aa, grid):
    """Warn if the TP-AGB NIR excess is detected in the cleaned grid.

    Parameters
    ----------
    ages_gyr : ndarray
    wav_aa : ndarray
    grid : ndarray, shape (n_age, n_wav)
        *Cleaned* spectra for a single metallicity.
    """
    idx_v   = np.argmin(np.abs(wav_aa - 5500.0))
    idx_nir = np.argmin(np.abs(wav_aa - 15000.0))
    idx_500 = np.argmin(np.abs(ages_gyr - 0.5))

    v_flux   = grid[idx_500, idx_v]
    nir_flux = grid[idx_500, idx_nir]

    if v_flux > 0 and (nir_flux / v_flux) > TPAGB_RATIO_WARN:
        warnings.warn(
            f"\n  TP-AGB NIR excess detected: NIR/V = {nir_flux / v_flux:.0f}× at ~500 Myr "
            f"(expected 5–15 for a normal SSP).\n"
            "  This is a known BC03 Padova2000 stellar-model limitation and CANNOT be fixed "
            "by preprocessing.\n"
            "  It affects NIR (F150W, F200W, F277W, F356W) fits at ages 0.2–2 Gyr.\n"
            "  For accurate NIR photometry at these ages, use FSPS with MIST isochrones.",
            UserWarning,
            stacklevel=2,
        )


# ---------------------------------------------------------------------------
# Locate the six BC03 metallicity files
# ---------------------------------------------------------------------------

def _find_bc03_files(data_dir, resolution, imf):
    """Return an ordered list of (logzsol, filepath) for the six metallicities.

    Tries both the legacy ``m22..m72`` and the official Padova ``m122..m172``
    naming conventions.

    Parameters
    ----------
    data_dir : str
    resolution : {'lr', 'hr'}
    imf : {'chabrier', 'kroupa', 'salpeter'}

    Returns
    -------
    list of (logzsol, filepath) sorted by logzsol
    """
    imf_tag = {'salpeter': 'salp', 'chabrier': 'chab', 'kroupa': 'krou'}.get(
        imf.lower(), 'chab')
    resolution = resolution.lower()

    tag_sets = [
        {  # legacy
            'm22': np.log10(0.0001 / 0.02),
            'm32': np.log10(0.0004 / 0.02),
            'm42': np.log10(0.004  / 0.02),
            'm52': np.log10(0.008  / 0.02),
            'm62': np.log10(0.02   / 0.02),
            'm72': np.log10(0.05   / 0.02),
        },
        {  # official Padova bundle
            'm122': np.log10(0.0001 / 0.02),
            'm132': np.log10(0.0004 / 0.02),
            'm142': np.log10(0.004  / 0.02),
            'm152': np.log10(0.008  / 0.02),
            'm162': np.log10(0.02   / 0.02),
            'm172': np.log10(0.05   / 0.02),
        },
    ]

    for tag_set in tag_sets:
        found = {}
        for mtag, lz in tag_set.items():
            base  = f"bc2003_{resolution}_{mtag}_{imf_tag}_ssp.ised_ASCII"
            plain = os.path.join(data_dir, base)
            gz    = plain + '.gz'
            if os.path.isfile(plain):
                found[mtag] = (lz, plain)
            elif os.path.isfile(gz):
                found[mtag] = (lz, gz)
        if len(found) == len(tag_set):
            return sorted(found.values(), key=lambda x: x[0])

    raise FileNotFoundError(
        f"Could not find all six BC03 metallicity files in {data_dir!r}.\n"
        f"Expected names like: bc2003_{resolution}_m62_{imf_tag}_ssp.ised_ASCII\n"
        "Check the --data-dir path and that --imf / --resolution match your files."
    )


# ---------------------------------------------------------------------------
# Main preprocessing routine
# ---------------------------------------------------------------------------

def preprocess(data_dir, imf='chabrier', resolution='lr', output_path=None,
               verbose=True):
    """Run the full BC03 preprocessing pipeline.

    Parameters
    ----------
    data_dir : str
        Directory containing the raw ``.ised_ASCII`` files.
    imf : str
        IMF tag: ``'chabrier'``, ``'kroupa'``, or ``'salpeter'``.
    resolution : str
        ``'lr'`` (low-res, 1221 wavelengths) or ``'hr'`` (high-res, 6900 wavelengths).
    output_path : str, optional
        Where to write the ``.npz`` cache.  Defaults to
        ``src/data/bc03_{resolution}_{imf}_clean_grid.npz`` relative to the
        SPECTRA repository root.
    verbose : bool
        Print progress messages.

    Returns
    -------
    output_path : str
        Path to the written ``.npz`` file.
    """
    imf_tag    = {'salpeter': 'salp', 'chabrier': 'chab', 'kroupa': 'krou'}.get(
        imf.lower(), 'chab')
    resolution = resolution.lower()

    # Default output path: src/data/ inside the SPECTRA repo
    if output_path is None:
        _here = os.path.dirname(os.path.abspath(__file__))    # src/utils/
        output_path = os.path.normpath(
            os.path.join(_here, '..', 'data',
                         f'bc03_{resolution}_{imf_tag}_clean_grid.npz'))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if verbose:
        print(f"[BC03 preprocessor] data_dir  : {data_dir}")
        print(f"[BC03 preprocessor] IMF       : {imf} ({imf_tag})")
        print(f"[BC03 preprocessor] resolution: {resolution}")
        print(f"[BC03 preprocessor] output    : {output_path}")
        print()

    # ── 1. Locate files ──────────────────────────────────────────────────────
    file_list = _find_bc03_files(data_dir, resolution, imf)
    if verbose:
        print(f"Found {len(file_list)} metallicity files:")
        for lz, fp in file_list:
            print(f"  logZ/Zsun = {lz:+.3f}  →  {os.path.basename(fp)}")
        print()

    # ── 2. Load, clean, stack ────────────────────────────────────────────────
    grids   = []
    logzsol = []
    wav_aa  = None
    ages_gyr = None

    for i, (lz, fpath) in enumerate(file_list, 1):
        if verbose:
            tag = os.path.basename(fpath)
            print(f"  [{i}/{len(file_list)}] Loading {tag} ...", end='', flush=True)

        w, a, raw_grid = _load_bc03_file(fpath)

        if verbose:
            print(f"  {len(a)} ages, {len(w)} wavelengths", end='', flush=True)

        if wav_aa is None:
            wav_aa   = w
            ages_gyr = a
        else:
            # Sanity-check that grids are on the same wavelength axis
            if len(w) != len(wav_aa) or not np.allclose(w, wav_aa, rtol=1e-4):
                raise ValueError(
                    f"Wavelength grid mismatch between metallicity files.\n"
                    f"Expected {len(wav_aa)} wavelengths, got {len(w)} in {fpath!r}."
                )

        # Clean each age step independently
        cleaned = np.empty_like(raw_grid)
        n_fixed = 0
        for j in range(len(ages_gyr)):
            orig = raw_grid[j]
            cl   = clean_spectrum(orig, wav_aa)
            cleaned[j] = cl
            n_fixed += int(np.sum(cl != orig))

        if verbose:
            print(f"  →  {n_fixed} pixels cleaned")

        grids.append(cleaned)
        logzsol.append(lz)

    grids_arr   = np.array(grids, dtype=np.float32)   # (n_met, n_age, n_wav); float32 saves ~half the disk space
    logzsol_arr = np.array(logzsol)

    # ── 3. TP-AGB check ──────────────────────────────────────────────────────
    # Check on the solar-metallicity grid (closest to m62 / m162)
    solar_idx = np.argmin(np.abs(logzsol_arr))
    _check_tpagb(ages_gyr, wav_aa, grids_arr[solar_idx])

    # ── 4. Save cache ────────────────────────────────────────────────────────
    np.savez_compressed(
        output_path,
        wav_aa   = wav_aa.astype(np.float32),
        ages_gyr = ages_gyr.astype(np.float32),
        logzsol  = logzsol_arr.astype(np.float32),
        grid     = grids_arr,         # (n_met, n_age, n_wav)
    )

    fsize_mb = os.path.getsize(output_path) / 1e6
    if verbose:
        print()
        print(f"✓ Preprocessed cache saved: {output_path}")
        print(f"  Shape: {grids_arr.shape[0]} metallicities × "
              f"{grids_arr.shape[1]} ages × {grids_arr.shape[2]} wavelengths")
        print(f"  File size: {fsize_mb:.1f} MB")

    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    p = argparse.ArgumentParser(
        prog='python -m src.utils.bc03_preprocess',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        '--data-dir', '-d',
        default=None,
        help="Directory containing raw BC03 .ised_ASCII files.  "
             "Falls back to the BC03_DATA_DIR environment variable.",
    )
    p.add_argument(
        '--imf', '-i',
        default='chabrier',
        choices=['chabrier', 'kroupa', 'salpeter'],
        help="IMF to preprocess (default: chabrier).",
    )
    p.add_argument(
        '--resolution', '-r',
        default='lr',
        choices=['lr', 'hr'],
        help="Spectral resolution: 'lr' (default) or 'hr'.",
    )
    p.add_argument(
        '--output', '-o',
        default=None,
        help="Output .npz path.  Defaults to "
             "src/data/bc03_<resolution>_<imf>_clean_grid.npz.",
    )
    p.add_argument(
        '--quiet', '-q',
        action='store_true',
        help="Suppress progress output.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)

    data_dir = args.data_dir or os.environ.get('BC03_DATA_DIR')
    if not data_dir:
        print(
            "ERROR: BC03 data directory not specified.\n"
            "  Pass --data-dir /path/to/bc03/files  or set BC03_DATA_DIR.",
            file=sys.stderr,
        )
        sys.exit(1)

    data_dir = os.path.expanduser(data_dir)
    if not os.path.isdir(data_dir):
        print(f"ERROR: Directory not found: {data_dir!r}", file=sys.stderr)
        sys.exit(1)

    try:
        preprocess(
            data_dir=data_dir,
            imf=args.imf,
            resolution=args.resolution,
            output_path=args.output,
            verbose=not args.quiet,
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Preprocessing failed: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
