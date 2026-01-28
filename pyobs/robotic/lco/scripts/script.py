import logging
from typing import Any

from pyobs.robotic.scripts import Script
from pyobs.robotic import ObservationArchive, TaskArchive, TaskRunner

log = logging.getLogger(__name__)


class LcoScript(Script):
    """Auto SCRIPT script for LCO configs."""

    def __init__(self, scripts: dict[str, Script], **kwargs: Any):
        """Initialize a new LCO auto focus script.

        Args:
            scripts: External scripts to run
        """
        Script.__init__(self, **kwargs)

        # store
        self.scripts = scripts

    def _get_config_script(self, config: dict[str, Any]) -> Script:
        """Get config script for given configuration.

        Args:
            config: Config to create runner for.

        Returns:
            Script for running config

        Raises:
            ValueError: If could not create runner.
        """

        # what do we run?
        config_type = config["extra_params"]["script_name"]
        if config_type not in self.scripts:
            raise ValueError('No script found for script type "%s".' % config_type)

        # create script handler
        return self.get_object(self.scripts[config_type], Script, configuration=config)

    async def can_run(self) -> bool:
        """Checks, whether this task could run now.

        Returns:
            True, if task can run now.
        """

        # get config runner
        runner = self._get_config_script(self.configuration)

        # if any runner can run, we proceed
        return await runner.can_run()

    async def run(
        self,
        task_runner: TaskRunner | None = None,
        observation_archive: ObservationArchive | None = None,
        task_archive: TaskArchive | None = None,
    ) -> None:
        """Run script.

        Raises:
            InterruptedError: If interrupted
        """

        # get config runner
        runner = self._get_config_script(self.configuration)

        # run it
        await runner.run(task_runner=task_runner, observation_archive=observation_archive, task_archive=task_archive)


__all__ = ["LcoScript"]
