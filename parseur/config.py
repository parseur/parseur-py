import configparser
import logging


class Config:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.api_key = None
        self.api_base = None

    def load(self):
        cfg = configparser.ConfigParser()
        if self.config_path:
            cfg.read(self.config_path)
        api_key = cfg.get("parseur", "api_key", fallback=None)
        api_base = cfg.get("parseur", "api_base", fallback=None)
        self.api_key = api_key
        self.api_base = api_base
        return cfg

    def save(self):
        if not self.config_path:
            raise ValueError("Config path must be set before saving.")
        cfg = configparser.ConfigParser()
        cfg.read(self.config_path)
        if not cfg.has_section("parseur"):
            cfg.add_section("parseur")
        cfg.set("parseur", "api_key", self.api_key)
        cfg.set("parseur", "api_base", self.api_base)
        with open(self.config_path, "w") as f:
            cfg.write(f)
        logging.info(f"Config saved to {self.config_path}")
