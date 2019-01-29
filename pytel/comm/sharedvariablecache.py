import time

from pytel import PytelModule
from pytel.events import VariableChangedEvent, VariablesUpdateEvent


class SharedVariable:
    """A shared variable."""

    def __init__(self, name: str):
        """Creates a new shared variable.

        Args:
            name: Name of variable.
        """
        self.name = name
        self._value = None
        self.source = None
        self.updated = None
        self.on_change = []

    @property
    def value(self):
        """Value of the variable"""
        return self._value

    def set(self, v):
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


class SharedVariableCache(PytelModule):
    """A cache for variables shared among modules."""

    def __init__(self, *args, **kwargs):
        """Create a new variable cache."""
        PytelModule.__init__(self, thread_funcs=self._var_update, *args, **kwargs)

        # list of variables and values
        self._variables = {}

        # callback methods on value changes.
        self._on_change = {}

    def open(self) -> bool:
        """Open module"""

        # open parent class
        if not PytelModule.open(self):
            return False

        # register events
        self.comm.register_event(VariableChangedEvent, self._handle_variable_change)
        self.comm.register_event(VariablesUpdateEvent, self._handle_variables_update)

        # success
        return True

    def __getitem__(self, item: str):
        """Returns the value of a variable.

        Args:
            item: Name of variable.

        Returns:
            Value of variable.
        """
        return self._variables[item].value

    def __setitem__(self, key, value):
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
            self.comm.send_event(VariableChangedEvent(key, value))

    def __contains__(self, item: str) -> bool:
        """Whether this cache contains the given variable."""
        return item in self._variables

    def __len__(self):
        """Number of variables in cache."""
        return len(self._variables)

    def keys(self):
        """Names of variables in cache."""
        return self._variables.keys()

    def on_change(self, key, callback):
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

    def _set_external(self, key, value, sender):
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

    def _handle_variable_change(self, event: VariableChangedEvent, sender: str, *args, **kwargs) -> bool:
        """Changes variables on incoming change event.

        Args:
            event: Change event.
            sender: Source of event.

        Returns:
            Success or not.
        """

        self._set_external(event.name, event.value, sender)
        return True

    def _handle_variables_update(self, event: VariablesUpdateEvent, sender: str, *args, **kwargs) -> bool:
        """Changes variables on incoming update event.

        Args:
            event: Change event.
            sender: Source of event.

        Returns:
            Success or not.
        """

        # loop all variables
        for key, value in event.data.items():
            self._set_external(key, value, sender)
        return True

    def _var_update(self):
        """Periodically send variable values."""

        while not self.closing.is_set():
            # fetch all local variables
            vars = {k: v.value for k, v in self._variables.items() if v.source is None}

            # send event
            if vars:
                self.comm.send_event(VariablesUpdateEvent(vars))

            # wait a little
            self.closing.wait(10)


__all__ = ['SharedVariableCache']
