import json

def read_config(app, config_file='config.json'):
    config = app.config
    with open(config_file, 'r') as config_fp:
        new_configs = json.load(config_fp)
    for (key, value) in new_configs.items():
        config[key] = value