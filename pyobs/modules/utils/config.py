import logging
import os
from io import StringIO

import yaml

from pyobs.interfaces import IConfigProvider
from pyobs import PyObsModule
from pyobs.utils.config import pre_process_yaml

log = logging.getLogger(__name__)


class Config(PyObsModule, IConfigProvider):
    """Config provider."""

    def __init__(self, path: str, *args, **kwargs):
        """Initialize a new config provider.

        Args:
            path: Path to config YAML files.
        """
        PyObsModule.__init__(self, *args, **kwargs)
        self._path = path

    def get_config(self, module: str, *args, **kwargs) -> dict:
        """Returns the config for the given module.

        Args:
            module: Name of module.

        Returns:
            Dictionary containing module config.

        Raises:
            FileNotFoundError: If config could not be found.
        """

        # get full filename
        filename = os.path.join(self._path, module + '.yaml')

        # load config
        log.info('Loading configuration from {0:s}...'.format(filename))
        with StringIO(pre_process_yaml(filename)) as f:
            cfg = yaml.load(f)

        # if there is a comm config in here, remove it
        if 'comm' in cfg:
            del cfg['comm']

        # return config
        return cfg


__all__ = ['Config']
