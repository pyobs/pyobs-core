from .interface import *


class ISettings(Interface):
    def get_settings(self, *args, **kwargs) -> dict:
        """Returns a dict of name->type pairs for settings."""
        raise NotImplementedError

    def get_setting_value(self, setting: str, *args, **kwargs):
        """Returns the value of the given setting.

        Args:
            setting: Name of setting

        Returns:
            Current value

        Raises:
            KeyError if setting does not exist
        """
        raise NotImplementedError

    def set_setting_value(self, setting: str, value, *args, **kwargs):
        """Sets the value of the given setting.

        Args:
            setting: Name of setting
            value: New value

        Raises:
            KeyError if setting does not exist
        """
        raise NotImplementedError


__all__ = ['ISettings']
