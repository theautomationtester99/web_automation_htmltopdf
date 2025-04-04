import configparser
import os

class ConfigReader:
    """
    A class to read and manage configuration files using the `configparser` module.

    Attributes:
        config_file (str): Path to the configuration file.
        config (ConfigParser): ConfigParser instance containing the loaded configuration.
    """
    def __init__(self, config_file):
        """
        Initializes the ConfigReader instance with the specified configuration file.

        Args:
            config_file (str): Path to the configuration file.
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        """
        Loads the configuration file and creates a ConfigParser instance.

        Returns:
            ConfigParser: A ConfigParser object containing the parsed configuration data.
        """
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        return config

    def get_property(self, section, property_name, fallback=None):
        """
        Retrieves the value of a property from the specified section of the configuration file.

        Args:
            section (str): Name of the section in the configuration file.
            property_name (str): Name of the property to retrieve.
            fallback (str, optional): Value to return if the property does not exist. Defaults to None.

        Returns:
            str: The value of the property, or the fallback value if the property does not exist.
        """
        return self.config.get(section, property_name, fallback=fallback)
