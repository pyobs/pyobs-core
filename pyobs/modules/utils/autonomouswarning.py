import asyncio
import logging
import os
import subprocess
from typing import Optional, Any

from pyobs.modules import Module
from pyobs.interfaces import IAutonomous

log = logging.getLogger(__name__)


class AutonomousWarning(Module):
    """A module that can plays a warning sound while an IAutonomous module is running."""
    __module__ = 'pyobs.modules.utils'

    def __init__(self, warn_sound: str, warn_interval: float = 1, start_sound: Optional[str] = None,
                 started_sound: Optional[str] = None, stop_sound: Optional[str] = None,
                 stopped_sound: Optional[str] = None, player: str = 'mpg123', trigger_file: Optional[str] = None,
                 **kwargs: Any):
        """Initialize a new warning.

        Args:
            warn_sound: Name of file to play.
            warn_interval: Interval in seconds between sounds.
            start_sound: Sound to play when starting systems.
            started_sound: Sound to play when systems started.
            stop_sound: Sound to play when stopping systems.
            stopped_sound: Sound to play when systems stopped.
            trigger_file: File, which triggers to switch on-off and vice versa, when created.
                Will be deleted afterwards.
        """
        Module.__init__(self, **kwargs)

        # store
        self._warn_sound = warn_sound
        self._warn_interval = warn_interval
        self._start_sound = start_sound
        self._started_sound = started_sound
        self._stop_sound = stop_sound
        self._stopped_sound = stopped_sound
        self._trigger_file = trigger_file
        self._player = player
        self._autonomous = False

        # threads
        self.add_background_task(self._heartbeat)
        self.add_background_task(self._check_autonomous)
        self.add_background_task(self._check_trigger)

    def _play_sound(self, sound: str) -> None:
        """Play a sound.

        Args:
            sound: Sound file to play.
        """

        # no sound given?
        if sound is None:
            return

        # play sound and set stderr to devnull to avoid warning
        subprocess.Popen([self._player, '-q', sound], stderr=subprocess.DEVNULL,).wait()

    async def _heartbeat(self) -> None:
        """Play sound in given interval, if an autonomous module is running."""

        while not self.closing.is_set():
            # play sound
            if self._autonomous:
                self._play_sound(self._warn_sound)

            # sleep
            await asyncio.sleep(self._warn_interval)

    async def _check_autonomous(self) -> None:
        """Checks for autonomous modules."""

        while not self.closing.is_set():
            # check for autonomous modules
            autonomous = list(await self.comm.clients_with_interface(IAutonomous))
            is_auto = any([await(await self.comm.proxy(a, IAutonomous)).is_running().wait() for a in autonomous])

            # did it change?
            if is_auto != self._autonomous:
                log.info('Robotic systems %s.', 'started' if is_auto else 'stopped')
                if self._stop_sound is not None and is_auto:
                    self._play_sound(self._stop_sound)
                elif self._start_sound is not None and not is_auto:
                    self._play_sound(self._start_sound)

            # store it
            self._autonomous = is_auto

            # sleep a little
            await asyncio.sleep(1)

    async def _check_trigger(self) -> None:
        """Checks for trigger to start/stop autonomous modules."""

        while not self.closing.is_set():
            # does file exist?
            if self._trigger_file is not None and os.path.exists(self._trigger_file):
                # check for autonomous modules
                autonomous = list(await self.comm.clients_with_interface(IAutonomous))
                is_auto = any([await (await self.proxy(a, IAutonomous)).is_running() for a in autonomous])

                # play sound
                if self._stop_sound is not None and is_auto:
                    self._play_sound(self._stop_sound)
                elif self._start_sound is not None and not is_auto:
                    self._play_sound(self._start_sound)

                # loop all modules
                log.info('%s robotic systems:', 'Stopping' if is_auto else 'Starting')
                for auto in autonomous:
                    # get proxy
                    log.info('  - %s', auto)
                    proxy = await self.comm.proxy(auto)

                    # start/stop
                    if is_auto:
                        await proxy.stop()
                    else:
                        await proxy.start()
                log.info('Finished.')

                # remove file
                os.remove(self._trigger_file)

            # sleep a little
            await asyncio.sleep(1)


__all__ = ['AutonomousWarning']
