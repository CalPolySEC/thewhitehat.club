import json
from flask import Flask


def read_config(app: Flask, config_file: str='config.json'):
    config = app.config
    with open(config_file, 'r') as config_fp:
        new_configs = json.load(config_fp)
    for (key, value) in new_configs.items():
        config[key] = value