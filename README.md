# SED Fitting Pipeline

This repository contains a Stellar Energy Distribution (SED) fitting pipeline designed for analyzing astronomical data. The pipeline utilizes various models and techniques to fit SEDs and extract meaningful parameters from the data.

## Project Structure

```
sed-fitting-pipeline
├── src
│   ├── main.py               # Entry point for the SED fitting pipeline
│   ├── data
│   │   └── data_loader.py    # Functions for loading and preprocessing data
│   ├── models
│   │   └── ssp_model.py      # Stellar Population Synthesis model implementation
│   ├── mcmc
│   │   └── mcmc_runner.py    # Markov Chain Monte Carlo fitting process
│   ├── utils
│   │   └── plotting.py       # Utility functions for generating plots
│   └── config
│       └── config_parser.py  # Functions for parsing configuration settings
├── config.yaml               # Configuration settings for the pipeline
├── requirements.txt          # Project dependencies
└── README.md                 # Documentation for the project
```

## Installation

To set up the SED fitting pipeline, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd sed-fitting-pipeline
pip install -r requirements.txt
```

## Configuration

The pipeline configuration is managed through the `config.yaml` file. This file allows you to specify input types, SSP model parameters, MCMC settings, output paths, and plotting options.

## Usage

To run the SED fitting pipeline, execute the main script:

```bash
python src/main.py
```

This will initialize the application, load the configuration, and orchestrate the data loading, model fitting, and plotting processes.

## Components

- **Data Loading**: The `data_loader.py` module handles the loading and preprocessing of data from various sources.
- **SSP Model**: The `ssp_model.py` module implements the Stellar Population Synthesis model.
- **MCMC Fitting**: The `mcmc_runner.py` module manages the MCMC fitting process.
- **Plotting**: The `plotting.py` module provides utility functions for generating various plots.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.