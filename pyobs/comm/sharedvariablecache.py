import threading
import time
import logging
from typing import TYPE_CHECKING, Dict, Any, Iterable, Callable, List, Optional

if TYPE_CHECKING:
    from pyobs.comm import Comm

from pyobs.events import VariableChangedEvent, VariablesUpdateEvent


log = logging.getLogger(__name__)


class SharedVariable:
    """A shared variable."""

    def __init__(self, name: str):
        """Creates a new shared variable.

        Args:
            name: Name of variable.
        """
        self.name = name
        self._value: Optional[Any] = None
        self.source: Optional[str] = None
        self.updated: Optional[float] = None
        self.on_change: List[Callable[[str, Any], bool]] = []

    @property
    def value(self) -> Any:
        """Value of the variable"""
        return self._value

    def set(self, v: Any) -> bool:
        """Set variable.

        Args:
            v: New value.
        """

        # update time
        self.updated = time.time()

        # did value change?
        if v == self._value:
            return False

        # update value and call callbacks
        self._value = v
        for callback in self.on_change:
            callback(self.name, v)
        return True


class SharedVariableCache:
    """A cache for variables shared among modules."""

    def __init__(self, comm: 'Comm'):
        """Create a new variable cache.

        Args:
            comm: The Comm object to use.
        """

        # store comm
        self._comm = comm

        # list of variables and values
        self._variables: Dict[str, Any] = {}

        # callback methods on value changes.
        self._on_change: Dict[str, Callable[[str, Any], None]] = {}

        # update thread
        self._closing = threading.Event()
        self._update_thread = threading.Thread(target=self._var_update)

    def open(self) -> None:
        """Open cache."""

        # register events
        self._comm.register_event(VariableChangedEvent, self._handle_variable_change)
        self._comm.register_event(VariablesUpdateEvent, self._handle_variables_update)

        # start update thread
        self._update_thread.start()

    def close(self) -> None:
        """Close cache."""

        # request quit and join thread
        self._closing.set()
        self._update_thread.join()

    def __getitem__(self, item: str) -> Any:
        """Returns the value of a variable.

        Args:
            item: Name of variable.

        Returns:
            Value of variable.
        """
        return self._variables[item].value

    def __setitem__(self, key: str, value: Any) -> None:
        """Sets the value of a variable.

        Args:
            key: Name of variable.
            value: New value for variable.
        """

        # create new variable, if needed
        if key not in self._variables:
            self._variables[key] = SharedVariable(key)

        # external?
        if self._variables[key].source is not None:
            log.warning('Overwriting external variable "%s"!', key)

        # set variable and broadcast it
        self._variables[key].source = None
        if self._variables[key].set(value):
            self._comm.send_event(VariableChangedEvent(key, value))

    def __contains__(self, item: str) -> bool:
        """Whether this cache contains the given variable."""
        return item in self._variables

    def __len__(self) -> int:
        """Number of variables in cache."""
        return len(self._variables)

    def keys(self) -> Iterable[str]:
        """Names of variables in cache."""
        return self._variables.keys()

    def on_change(self, key: str, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for a given variable.

        Args:
            key: Name of variable to create callback for.
            callback: Callback method.
        """

        # create new variable, if needed
        if key not in self._variables:
            self._variables[key] = SharedVariable(key)

        # add callback
        self._variables[key].on_change.append(callback)

    def _set_external(self, key: str, value: Any, sender: str) -> None:
        """Set value of variable without sending it again over the network.

        Args:
            key: Name of variable.
            value: Value of variable.
            sender: From where the value came.
        """

        # create new variable, if needed
        if key not in self._variables:
            self._variables[key] = SharedVariable(key)

        # set content
        self._variables[key].set(value)
        self._variables[key].source = sender

    def _handle_variable_change(self, event: VariableChangedEvent, sender: str) -> bool:
        """Changes variables on incoming change event.

        Args:
            event: Change event.
            sender: Source of event.

        Returns:
            Success or not.
        """

        self._set_external(event.name, event.value, sender)
        return True

    def _handle_variables_update(self, event: VariablesUpdateEvent, sender: str) -> bool:
        """Changes variables on incoming update event.

        Args:
            event: Change event.
            sender: Source of event.

        Returns:
            Success or not.
        """

        # loop all variables
        if event.data is not None:
            for key, value in event.data.items():
                self._set_external(key, value, sender)
        return True

    def _var_update(self) -> None:
        """Periodically send variable values."""

        while not self._closing.is_set():
            # fetch all local variables
            vars = {k: v.value for k, v in self._variables.items() if v.source is None}

            # send event
            if vars:
                self._comm.send_event(VariablesUpdateEvent(vars))

            # wait a little
            self._closing.wait(10)


__all__ = ['SharedVariableCache']
