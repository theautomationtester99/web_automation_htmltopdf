import configparser
import os

class ConfigReader:
    """
    A utility class to read and manage configuration files using the `configparser` module.

    This class provides methods to load configuration files and retrieve properties from specific sections.
    It ensures that configuration files are parsed correctly and allows for fallback values if properties are missing.

    Attributes:
        config_file (str): The path to the configuration file.
        config (ConfigParser): An instance of `ConfigParser` containing the loaded configuration data.
    """
    def __init__(self, config_file):
        """
        Initializes the ConfigReader instance with the specified configuration file.

        Args:
            config_file (str): The path to the configuration file.

        Raises:
            FileNotFoundError: If the specified configuration file does not exist.
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        """
        Loads the configuration file and creates a ConfigParser instance.

        This method reads the configuration file and parses its contents into a `ConfigParser` object.

        Returns:
            ConfigParser: A `ConfigParser` object containing the parsed configuration data.
        """
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
        return config

    def get_property(self, section, property_name, fallback=None):
        """
        Retrieves the value of a property from the specified section of the configuration file.

        This method allows you to fetch a property value from a specific section. If the property or section
        does not exist, the method returns the specified fallback value.

        Args:
            section (str): The name of the section in the configuration file.
            property_name (str): The name of the property to retrieve.
            fallback (str, optional): The value to return if the property does not exist. Defaults to None.

        Returns:
            str: The value of the property, or the fallback value if the property does not exist.
        """
        return self.config.get(section, property_name, fallback=fallback)
