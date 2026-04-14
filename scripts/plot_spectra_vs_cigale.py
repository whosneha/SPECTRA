"""
Compare SPECTRA and CIGALE best-fit parameters side by side.

Usage:
    python scripts/plot_spectra_vs_cigale.py

Reads:
    outputs/phangs_ic5332_no_dust/fit_summary.csv   (SPECTRA results)
    cigale_runs/phangs/output/results.fits           (CIGALE results)
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SPECTRA_SUMMARY  = 'outputs/phangs_ic5332_no_dust/fit_summary.csv'
CIGALE_RESULTS   = 'cigale_runs/phangs/output/results.fits'
OUTPUT_DIR       = 'outputs/comparison_spectra_vs_cigale'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_spectra_results(path):
    if not os.path.exists(path):
        print(f"SPECTRA summary not found: {path}")
        print("Run:  python run.py example_configs/config_phangs_no_dust.yaml  first")
        return None
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} SPECTRA results from {path}")
    return df


def load_cigale_results(path):
    if not os.path.exists(path):
        print(f"CIGALE results not found: {path}")
        print("Run CIGALE first:  python scripts/run_cigale_phangs.py")
        return None
    try:
        from astropy.table import Table
        t = Table.read(path)
        df = t.to_pandas()
        print(f"Loaded {len(df)} CIGALE results from {path}")
        return df
    except Exception as e:
        print(f"Could not load CIGALE results: {e}")
        return None


def plot_parameter_comparison(spectra_df, cigale_df):
    """Side-by-side scatter plots: SPECTRA vs CIGALE per parameter."""

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('SPECTRA vs CIGALE Parameter Comparison\n(PHANGS IC 5332 Clusters)',
                 fontsize=14, fontweight='bold')

    # ── Mass comparison ────────────────────────────────────────────────
    ax = axes[0]
    if cigale_df is not None and 'stellar.mass' in cigale_df.columns:
        cigale_logmass = np.log10(cigale_df['stellar.mass'].values)
        spectra_mass = spectra_df['mass'].values[:len(cigale_logmass)]

        ax.scatter(spectra_mass, cigale_logmass, s=80, alpha=0.8,
                   color='#2980B9', edgecolors='k', linewidth=0.5)
        lim = [min(spectra_mass.min(), cigale_logmass.min()) - 0.3,
               max(spectra_mass.max(), cigale_logmass.max()) + 0.3]
        ax.plot(lim, lim, 'k--', linewidth=1, alpha=0.5, label='1:1')
        ax.set_xlim(lim); ax.set_ylim(lim)

        # Residuals
        diff = cigale_logmass - spectra_mass
        ax.set_xlabel(r'SPECTRA  $\log(M/M_\odot)$', fontsize=11)
        ax.set_ylabel(r'CIGALE  $\log(M/M_\odot)$', fontsize=11)
        ax.set_title(f'Stellar Mass\n'
                     f'Δ = {np.mean(diff):.2f} ± {np.std(diff):.2f} dex', fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No CIGALE\nmass data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_title('Stellar Mass', fontsize=11)

    # ── Age comparison ─────────────────────────────────────────────────
    ax = axes[1]
    cigale_age_col = next((c for c in (cigale_df.columns if cigale_df is not None else [])
                           if 'age' in c.lower()), None)
    if cigale_df is not None and cigale_age_col:
        cigale_age = cigale_df[cigale_age_col].values / 1e3  # Myr -> Gyr
        spectra_age = spectra_df['age'].values[:len(cigale_age)]

        ax.scatter(spectra_age, cigale_age, s=80, alpha=0.8,
                   color='#E74C3C', edgecolors='k', linewidth=0.5)
        lim = [0, max(spectra_age.max(), cigale_age.max()) * 1.1]
        ax.plot(lim, lim, 'k--', linewidth=1, alpha=0.5, label='1:1')
        ax.set_xlim(lim); ax.set_ylim(lim)

        diff = cigale_age - spectra_age
        ax.set_xlabel('SPECTRA  Age [Gyr]', fontsize=11)
        ax.set_ylabel('CIGALE  Age [Gyr]', fontsize=11)
        ax.set_title(f'Age\n'
                     f'Δ = {np.mean(diff):.3f} ± {np.std(diff):.3f} Gyr', fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No CIGALE\nage data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        ax.set_title('Age', fontsize=11)

    # ── Chi-squared comparison ─────────────────────────────────────────
    ax = axes[2]
    cigale_chi2_col = next((c for c in (cigale_df.columns if cigale_df is not None else [])
                            if 'chi2' in c.lower() or 'reduced' in c.lower()), None)
    if cigale_df is not None and cigale_chi2_col and 'chi2_red' in spectra_df.columns:
        cigale_chi2 = cigale_df[cigale_chi2_col].values
        spectra_chi2 = spectra_df['chi2_red'].values[:len(cigale_chi2)]

        objects = spectra_df['object_id'].values[:len(cigale_chi2)]
        x = np.arange(len(objects))
        width = 0.35

        ax.bar(x - width/2, spectra_chi2, width, label='SPECTRA',
               color='#2980B9', alpha=0.8, edgecolor='k', linewidth=0.5)
        ax.bar(x + width/2, cigale_chi2, width, label='CIGALE',
               color='#E74C3C', alpha=0.8, edgecolor='k', linewidth=0.5)

        ax.axhline(1.0, color='green', linestyle='--', linewidth=1, alpha=0.7, label='χ²/DOF=1')
        ax.axhline(2.0, color='orange', linestyle=':', linewidth=1, alpha=0.7, label='χ²/DOF=2')

        ax.set_xticks(x)
        ax.set_xticklabels([o.split('_')[-1] for o in objects], rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('χ²/DOF', fontsize=11)
        ax.set_title('Goodness of Fit\nχ²/DOF per cluster', fontsize=11)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
    else:
        # Show SPECTRA chi2 only
        if 'chi2_red' in spectra_df.columns:
            objects = spectra_df['object_id'].values
            x = np.arange(len(objects))
            ax.bar(x, spectra_df['chi2_red'].values, color='#2980B9', alpha=0.8,
                   edgecolor='k', linewidth=0.5, label='SPECTRA')
            ax.axhline(1.0, color='green', linestyle='--', linewidth=1, alpha=0.7)
            ax.axhline(2.0, color='orange', linestyle=':', linewidth=1, alpha=0.7)
            ax.set_xticks(x)
            ax.set_xticklabels([o.split('_')[-1] for o in objects],
                               rotation=45, ha='right', fontsize=8)
            ax.set_ylabel('χ²/DOF', fontsize=11)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
        ax.set_title('Goodness of Fit\n(CIGALE not available)', fontsize=11)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, 'parameter_comparison.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_sed_overlay(spectra_df, cigale_df):
    """Overlay SPECTRA and CIGALE best-fit SEDs for the first cluster."""
    from src.data.phangs_loader import load_phangs_fits
    from src.models.ssp_model import SSPModel

    phangs_fits = ("/Users/snehanair/Downloads/catalogs 2/"
                   "hlsp_phangs-cat_hst_uvis_ic5332_multi_v1_obs-human-cluster-class12.fits")

    if not os.path.exists(phangs_fits):
        print("PHANGS FITS not found — skipping SED overlay")
        return

    datasets = load_phangs_fits(phangs_fits, max_rows=1)
    if not datasets:
        return

    obj_id, phot = datasets[0]
    wav_um = phot['wavelength'] / 1e4

    # SPECTRA best-fit model
    spectra_row = spectra_df.iloc[0]
    ssp = SSPModel({'type': 'fsps', 'redshift': 0.00184, 'imf': 'chabrier', 'dust_type': 2})
    ssp.set_flux_calibration(phot['obs_flux'], wavelengths=phot['wavelength'])

    wav_smooth = np.logspace(np.log10(2000), np.log10(10000), 300)
    spectra_flux = ssp.get_magnitudes(
        mass=spectra_row['mass'],
        age=spectra_row['age'],
        metallicity=spectra_row['metallicity'],
        dust=0.0,
        wavelengths=wav_smooth
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f'SED Comparison: {obj_id}\nSPECTRA vs CIGALE Best-Fit',
                 fontsize=13, fontweight='bold')

    # Observed data
    ax.errorbar(wav_um, phot['obs_flux'], yerr=phot['obs_err'],
                fmt='o', markersize=10, capsize=4, color='k', label='Observed', zorder=6)

    # SPECTRA model
    ax.plot(wav_smooth/1e4, spectra_flux, '-', color='#2980B9',
            linewidth=2, label='SPECTRA best-fit', zorder=3)

    # CIGALE model (load best-fit SED if available)
    cigale_sed_file = os.path.join('cigale_runs/phangs/output',
                                   f'{obj_id}_best_model.fits')
    if os.path.exists(cigale_sed_file):
        try:
            from astropy.table import Table
            cigale_sed = Table.read(cigale_sed_file)
            cigale_wav = cigale_sed['wavelength'].data / 1e4  # Å -> μm
            cigale_fnu = cigale_sed['Fnu'].data               # Jy
            ax.plot(cigale_wav, cigale_fnu, '--', color='#E74C3C',
                    linewidth=2, label='CIGALE best-fit', zorder=4)
        except Exception as e:
            print(f"Could not load CIGALE SED: {e}")
    else:
        print(f"CIGALE best-fit SED not found: {cigale_sed_file}")
        ax.text(0.98, 0.95, 'CIGALE SED\nnot available',
                transform=ax.transAxes, ha='right', va='top',
                fontsize=9, color='#E74C3C',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor='#E74C3C', alpha=0.8))

    # Parameter labels
    textstr  = f"SPECTRA:  logM={spectra_row['mass']:.2f}, Age={spectra_row['age']:.3f} Gyr\n"
    textstr += f"χ²/DOF = {spectra_row['chi2_red']:.2f}"
    ax.text(0.03, 0.97, textstr, transform=ax.transAxes,
            fontsize=9, va='top',
            bbox=dict(boxstyle='round', facecolor='#EBF5FB', edgecolor='#2980B9', alpha=0.9))

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r'$\lambda_{\rm obs}$ [$\mu$m]', fontsize=12)
    ax.set_ylabel(r'$F_\nu$ [Jy]', fontsize=12)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)

    out_path = os.path.join(OUTPUT_DIR, f'sed_overlay_{obj_id}.png')
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path}")


def print_comparison_table(spectra_df, cigale_df):
    """Print side-by-side parameter table."""
    print("\n" + "="*80)
    print("SPECTRA vs CIGALE PARAMETER COMPARISON")
    print("="*80)
    print(f"{'Object':<35} {'SPECTRA logM':>12} {'SPECTRA Age':>12} {'χ²/DOF':>8}")
    print("-"*80)
    for _, row in spectra_df.iterrows():
        print(f"{str(row['object_id']):<35} "
              f"{row['mass']:>12.3f} "
              f"{row['age']:>12.4f} "
              f"{row['chi2_red']:>8.2f}")
    print("="*80)

    if cigale_df is not None:
        print("\nCIGALE results loaded — run plot_parameter_comparison() to see scatter plots")
    else:
        print("\nCIGALE results not available yet.")
        print("Steps to get CIGALE results:")
        print("  1. pip install cigale")
        print("  2. python scripts/prepare_cigale_input.py --source phangs")
        print("  3. python scripts/run_cigale_phangs.py")
        print("  4. Re-run this script")


if __name__ == '__main__':
    spectra_df = load_spectra_results(SPECTRA_SUMMARY)
    if spectra_df is None:
        sys.exit(1)

    cigale_df = load_cigale_results(CIGALE_RESULTS)

    print_comparison_table(spectra_df, cigale_df)
    plot_parameter_comparison(spectra_df, cigale_df)
    plot_sed_overlay(spectra_df, cigale_df)

    print(f"\nComparison plots saved to: {OUTPUT_DIR}/")
