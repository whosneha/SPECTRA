from setuptools import setup

setup(
    name="spectra-sed",
    version="1.0.0",
    description="SPECTRA: Stellar Population Estimation via Comprehensive Template Response Analysis",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/SPECTRA",
    py_modules=["spectra_cli"],
    install_requires=[
        "numpy>=1.20",
        "scipy>=1.7",
        "matplotlib>=3.5",
        "astropy>=5.0",
        "pyyaml>=6.0",
        "pandas>=1.3",
        "emcee>=3.1",
        "corner>=2.2",
        "h5py>=3.7",
        "tqdm>=4.62",
    ],
    extras_require={
        "fsps": ["fsps>=0.4"],
        "rubin": ["requests>=2.28", "astroquery>=0.4"],
        "test": ["pytest>=7.0", "pytest-cov>=3.0"],  # Test dependencies
    },
    entry_points={
        "console_scripts": [
            "spectra=spectra_cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
