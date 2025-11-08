"""Gerenciador de configurações do aplicativo"""

import json
from pathlib import Path


class ConfigManager:
    """Gerencia as configurações do aplicativo"""

    DEFAULT_CONFIG = {
        'timeout': 5,
        'max_workers': 10,
        'theme': 'dark',
        'auto_refresh_interval': 300,  # 5 minutos
        'api_keys': {
            'semrush': '',
            'estibot': '',
            'moz': ''
        }
    }

    def __init__(self, config_file='data/config.json'):
        """Inicializa o gerenciador de configurações"""
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load()

    def load(self):
        """Carrega as configurações do arquivo"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge com configurações padrão
                    return {**self.DEFAULT_CONFIG, **config}
            except:
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def save(self):
        """Salva as configurações no arquivo"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key, default=None):
        """Obtém um valor de configuração"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def set(self, key, value):
        """Define um valor de configuração"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save()

    def reset(self):
        """Restaura configurações padrão"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
