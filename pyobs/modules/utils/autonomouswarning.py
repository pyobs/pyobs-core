import logging
import os
import subprocess

from pyobs.events import Event
from pyobs.modules import Module
from pyobs.interfaces import IAutonomous
from pyobs.object import get_class_from_string

log = logging.getLogger(__name__)


class AutonomousWarning(Module):
    """A module that can plays a warning sound while an IAutonomous module is running."""

    def __init__(self, warn_sound: str, warn_interval: float = 1,
                 start_sound: str = None, started_sound: str = None, stop_sound: str = None, stopped_sound: str = None,
                 player: str = 'mpg123', trigger_file: str = None, *args, **kwargs):
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
        Module.__init__(self, *args, **kwargs)

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
        self.add_thread_func(self._heartbeat)
        self.add_thread_func(self._check_autonomous)
        self.add_thread_func(self._check_trigger)

    def _play_sound(self, sound: str):
        """Play a sound.

        Args:
            sound: Sound file to play.
        """

        # no sound given?
        if sound is None:
            return

        # play sound and set stderr to devnull to avoid warning
        subprocess.Popen([self._player, '-q', sound], stderr=subprocess.DEVNULL,).wait()

    def _heartbeat(self):
        """Play sound in given interval, if an autonomous module is running."""

        while not self.closing.is_set():
            # play sound
            if self._autonomous:
                self._play_sound(self._warn_sound)

            # sleep
            self.closing.wait(self._warn_interval)

    def _check_autonomous(self):
        """Checks for autonomous modules."""

        while not self.closing.is_set():
            # check for autonomous modules
            autonomous = list(self.comm.clients_with_interface(IAutonomous))
            is_auto = any([self.comm[a].is_running().wait() for a in autonomous])

            # did it change?
            if is_auto != self._autonomous:
                log.info('Robotic systems %s.', 'started' if is_auto else 'stopped')
                self._play_sound(self._started_sound if is_auto else self._stopped_sound)

            # store it
            self._autonomous = is_auto

            # sleep a little
            self.closing.wait(1)

    def _check_trigger(self):
        """Checks for trigger to start/stop autonomous modules."""

        while not self.closing.is_set():
            # does file exist?
            if self._trigger_file is not None and os.path.exists(self._trigger_file):
                # check for autonomous modules
                autonomous = list(self.comm.clients_with_interface(IAutonomous))
                is_auto = any([self.comm[a].is_running().wait() for a in autonomous])

                # play sound
                self._play_sound(self._stop_sound if is_auto else self._start_sound)

                # loop all modules
                log.info('%s robotic systems:', 'Stopping' if is_auto else 'Starting')
                for auto in autonomous:
                    # get proxy
                    log.info('  - %s', auto)
                    proxy: IAutonomous = self.comm[auto]

                    # start/stop
                    if is_auto:
                        proxy.stop()
                    else:
                        proxy.start()
                log.info('Finished.')

                # remove file
                os.remove(self._trigger_file)

            # sleep a little
            self.closing.wait(1)


__all__ = ['AutonomousWarning']
