import configparser
from pathlib import Path

# Definitions of types
ConfigOption = dict[str, str]
ConfigSection = list[ConfigOption]
ConfigDict = dict[str, ConfigSection]


class ConfigManager:
    """Helper class to manage an INI file with options to customize the app
    """

    def __init__(self, config_file: Path):
        self._file = config_file
        self.config = configparser.ConfigParser()

    def load_config(self):
        self.config.read(self._file)

    def save_config(self):
        f = open(self._file, "w")
        self.config.write(f)
        f.close()

    # SETTERS

    def add_section(self, section: str):
        """Add section if it doesn't exist.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)

    def set_str(self, section: str, name: str, value: str):
        self.config.set(section, name, value)

    def set_int(self, section: str, name: str, value: int):
        self.config.set(section, name, str(value))

    def set_float(self, section: str, name: str, value: float):
        self.config.set(section, name, str(value))

    def set_bool(self, section: str, name: str, value: bool):
        self.config.set(section, name, str(int(value)))

    # GETTERS

    def get_config(self) -> ConfigDict:
        """Get all sections with their options.
        """
        options: ConfigDict = {}

        for section in self.config.sections():
            options[section] = []
            for option in self.config.options(section):
                value = self.config.get(section, option)
                options[section].append({option: value})

        return options

    def get_section(self, section: str) -> ConfigSection:
        """Get all options in a section.
        """
        if not self.config.has_section(section):
            return []

        options: ConfigSection = []
        for option in self.config.options(section):
            value = self.config.get(section, option)
            options.append({option: value})

        return options

    def get_str(self, section: str, name: str, default: str = "") -> str:
        try:
            return self.config.get(section, name)
        except Exception:
            return default

    def get_int(self, section: str, name: str, default: int = 0) -> int:
        try:
            return self.config.getint(section, name)
        except Exception:
            return default

    def get_float(self, section: str, name: str, default: float = 0.0) -> float:
        try:
            return self.config.getfloat(section, name)
        except Exception:
            return default

    def get_bool(self, section: str, name: str, default: bool = False) -> bool:
        try:
            return self.config.getboolean(section, name)
        except Exception:
            return default
