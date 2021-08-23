# std
from pathlib import Path

# 3rd
import yaml


class Config:
    def __init__(self, config_file=Path("~/.ppserver").expanduser()):
        # All settings MUST be listed here
        # None stands for "no default value available"
        self.settings_default = {
            "character_sheet_link": None,
            "character_sheet_name": None,
            "relations_sheet_link": None,
            "relations_sheet_name": None,
            "certificate_path": None,
        }
        self.config_file = config_file

    def __getitem__(self, key):
        if key not in self.settings_default:
            raise ValueError(f"Key {key} not listed in default settings")
        with self.config_file.open("r") as inf:
            try:
                return yaml.load(inf)[key]
            except KeyError:
                default = self.settings_default[key]
                if default is not None:
                    return default
                else:
                    raise ValueError(
                        f"Key {key} not listed in settings file "
                        f"{self.config_file} and also doesn't have a "
                        f"default value."
                    )


config = Config()
