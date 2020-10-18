import logging
import threading
import typing

from pyobs import get_object
from pyobs.robotic.scripts import Script


log = logging.getLogger(__name__)


class LcoScript(Script):
    """Auto SCRIPT script for LCO configs."""

    def __init__(self, scripts: typing.Dict[str, Script], *args, ** kwargs):
        """Initialize a new LCO auto focus script.

        Args:
            scripts: External scripts to run
        """
        Script.__init__(self, *args, **kwargs)

        # store
        self.scripts = scripts

    def _get_config_script(self, config: dict) -> Script:
        """Get config script for given configuration.

        Args:
            config: Config to create runner for.

        Returns:
            Script for running config

        Raises:
            ValueError: If could not create runner.
        """

        # what do we run?
        config_type = config['extra_params']['script_name']
        if config_type not in self.scripts:
            raise ValueError('No script found for script type "%s".' % config_type)

        # create script handler
        return get_object(self.scripts[config_type],
                          configuration=config, task_archive=self.task_archive, comm=self.comm, observer=self.observer)

    def can_run(self) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """

        # get config runner
        runner = self._get_config_script(self.configuration)

        # if any runner can run, we proceed
        if runner.can_run():
            return True

    def run(self, abort_event: threading.Event):
        """Run script.

        Args:
            abort_event: Event to abort run.

        Raises:
            InterruptedError: If interrupted
        """

        # get config runner
        runner = self._get_config_script(self.configuration)

        # run it
        runner.run(abort_event=abort_event)


__all__ = ['LcoScript']
