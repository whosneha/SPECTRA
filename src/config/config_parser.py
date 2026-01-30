import yaml

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_input_config(config):
    return config.get('input', {})

def get_ssp_model_config(config):
    return config.get('ssp_model', {})

def get_mcmc_config(config):
    return config.get('mcmc', {})

def get_output_config(config):
    return config.get('output', {})

def get_plotting_config(config):
    return config.get('plotting', {})