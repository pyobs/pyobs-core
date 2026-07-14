from __future__ import annotations

import asyncio
import inspect
import logging
import typing
from collections.abc import Callable
from typing import Any, TypeVar, cast

import packaging.version
from py_expression_eval import Parser

from pyobs.events import Event, ModuleOpenedEvent
from pyobs.interfaces import (
    ConfigCapabilities,
    ConfigValue,
    IConfig,
    IModule,
    Interface,
    ModuleCapabilities,
    ModuleLocation,
)
from pyobs.object import Object
from pyobs.utils import exceptions as exc
from pyobs.utils.enums import ModuleState
from pyobs.version import version

log = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Any])


def timeout(func_timeout: str | int | Callable[..., Any] | None = None) -> Callable[[F], F]:
    """Decorates a method with information about timeout for an async HTTP call.

    :param func_timeout:  Integer or string that specifies the timeout.
                          If string, it is parsed using the variables in kwargs.
    """

    def timeout_decorator(func: F) -> F:
        async def _timeout(obj: Any, *args: Any, **kwargs: Any) -> float:
            # init to 0 second
            to = 0.0

            # do we have a timeout?
            if func_timeout is not None:
                # what is it?
                if callable(func_timeout):
                    # this is a method, does it have a timeout on it's own? then use it
                    try:
                        if hasattr(func_timeout, "timeout"):
                            # call timeout method, only works if this has the same parameters
                            to = await getattr(func_timeout, "timeout")(obj, *args, **kwargs)
                        else:
                            # call method directly
                            to = await func_timeout(obj, *args, **kwargs)
                    except Exception:
                        log.exception("Could not call timeout method.")

                elif isinstance(func_timeout, str):
                    # this is a string with a function, so evaluate it
                    try:
                        parser = Parser()
                        to = parser.parse(func_timeout).evaluate(kwargs)
                    except Exception:
                        log.error('Could not find timeout "%s" in list of parameters.', func_timeout)

                else:
                    # it's a number, add timeout directly
                    try:
                        to = float(func_timeout)
                    except ValueError:
                        log.exception("Could not convert timeout to float.")
                        to = 0.0

            # return it
            return to

        # decorate method
        setattr(func, "timeout", _timeout)
        return func

    return timeout_decorator


def raises(*exceptions: type[exc.PyObsError]) -> Callable[[F], F]:
    """
    Decorates a method with information about which pyobs exceptions it raises. These exceptions are
    logged in this module, but as INFO without stacktrace.

    :param exceptions:  One or more exceptions.
    """

    def raises_decorator(func: F) -> F:
        # decorate method
        setattr(func, "raises", exceptions)
        return func

    return raises_decorator


class Module(Object, IModule, IConfig):
    """Base class for all pyobs modules."""

    __module__ = "pyobs.modules"

    def __init__(
        self,
        label: str | None = None,
        own_comm: bool = True,
        additional_config_variables: list[str] | None = None,
        acl: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """
        Args:
            label: Label for module. If None, name is used.
            own_comm: If True, module owns comm and opens/closes it.
            additional_config_variables: List of additional variable names available to remote config getter/setter.
            acl: Access control config, with either an "allow" or a "deny" key (mutually exclusive), and an
                optional "mode" key ("enforce", the default, or "log"). No acl block means fully open access.
        """
        Object.__init__(self, **kwargs)

        # get list of client interfaces
        self._interfaces: list[type[Interface]] = []
        self._methods: dict[str, tuple[Callable[..., Any], inspect.Signature, dict[Any, Any]]] = {}
        self._interface_methods: dict[str, list[str]] = {}
        self._get_interfaces_and_methods()

        # access control -- parsed after interfaces/methods, since "allow" entries may
        # name an interface as shorthand for all of that interface's methods
        self._acl_allow: dict[str, list[str] | str] | None = None
        self._acl_deny: list[str] | None = None
        self._acl_mode: str = "enforce"
        self._parse_acl(acl)

        # get configuration caps, i.e. all parameters from c'tor
        self._additional_config_variables = additional_config_variables
        self._config_caps = self._get_config_caps()

        # name and label -- name always tracks the comm's own identity (e.g. XMPP JID),
        # since other modules address us by that, not by any locally configured string
        self._device_name = self.comm.name
        self._label = label if label is not None else self._device_name

        # state
        self._state = ModuleState.READY
        self._error_string = ""

        # own?
        self._own_comm = own_comm

        # close
        self._closing = asyncio.Event()
        self._quit_parent: Callable[[], None] | None = None  # set by MultiModule

    async def open(self) -> None:
        # open comm
        if self._comm is not None and self._own_comm:
            # open it and connect module
            self.comm.module = self
            await self.comm.open()

            # react to connecting modules
            await self.comm.register_event(ModuleOpenedEvent, self._on_module_opened)

        """Open module."""
        await Object.open(self)

        # publish base capabilities
        if self._comm is not None:
            location = (
                ModuleLocation(
                    longitude=self._observer.location.lon.degree,
                    latitude=self._observer.location.lat.degree,
                    elevation=self._observer.location.height.value,
                    timezone=str(self._timezone),
                )
                if self._observer is not None
                else None
            )
            await self._comm.set_capabilities(
                IModule,
                ModuleCapabilities(
                    version=await self.get_version(),
                    label=await self.get_label(),
                    location=location,
                ),
            )
            await self._comm.set_capabilities(
                IConfig,
                ConfigCapabilities(caps=self._config_caps),
            )

    async def close(self) -> None:
        """Close module."""
        await Object.close(self)

        # close comm
        if self._comm is not None and self._own_comm:
            log.info("Closing connection to server...")
            await self.comm.close()

    @staticmethod
    def new_event_loop() -> asyncio.AbstractEventLoop:
        return asyncio.new_event_loop()

    async def main(self) -> None:
        """Main loop for application."""
        await self._closing.wait()

    @property
    def name(self) -> str:
        """Returns name of module."""
        return "" if self._device_name is None else self._device_name

    async def get_label(self, **kwargs: Any) -> str:
        """Returns label of module."""
        return "" if self._label is None else self._label

    async def get_version(self, **kwargs: Any) -> str:
        """Returns pyobs version of module."""
        return version()

    async def _on_module_opened(self, event: Event, sender: str) -> bool:
        """React to other modules connecting."""
        if sender == self.comm.name or not isinstance(event, ModuleOpenedEvent):
            return False

        # get proxy and version
        try:
            async with self.proxy(sender, IModule) as proxy:
                caps = proxy.get_capabilities(IModule)
                module_version = caps.version if caps is not None else ""
                remote_location = caps.location if caps is not None else None
        except exc.RemoteError:
            return True

        # log it
        log.debug("Other module %s found, running on pyobs %s.", sender, module_version)

        # compare location, if both sides have one configured -- surfaces config drift between
        # modules that are supposed to share a site, since pyobs has no shared "site" concept
        if remote_location is not None and self._observer is not None:
            from astropy.coordinates import EarthLocation

            local = self._observer.location
            remote = EarthLocation.from_geodetic(
                remote_location.longitude, remote_location.latitude, remote_location.elevation
            )
            distance = ((remote.x - local.x) ** 2 + (remote.y - local.y) ** 2 + (remote.z - local.z) ** 2) ** 0.5
            if distance.to_value("m") > 100:  # tolerance, tune as needed
                log.warning(
                    "Module %s reports a location %.0fm from ours (lon=%.4f, lat=%.4f, elevation=%.1fm).",
                    sender,
                    distance.to_value("m"),
                    remote_location.longitude,
                    remote_location.latitude,
                    remote_location.elevation,
                )

        # no version reported, cannot compare
        if not module_version:
            return True

        # check version, only compare major and minor, ignore patch level
        v1, v2 = packaging.version.parse(version()), packaging.version.parse(module_version)
        msg = (
            f'Found module "{sender}" with different pyobs version {module_version} (≠{version()}), '
            f"please update pyobs."
        )
        if v1.major != v2.major:
            log.critical(msg)
        elif v1.minor != v2.minor:
            log.info(msg)

        # okay
        return True

    @property
    def interfaces(self) -> list[type[Interface]]:
        """List of implemented interfaces."""
        return self._interfaces

    @property
    def methods(self) -> dict[str, tuple[Callable[..., Any], inspect.Signature, dict[Any, Any]]]:
        """List of methods."""
        return self._methods

    def _parse_acl(self, acl: dict[str, Any] | None) -> None:
        """Parse the optional "acl" config block into _acl_allow/_acl_deny/_acl_mode.

        Args:
            acl: Raw "acl" config dict, or None if no ACL block was given (fully open access).

        Raises:
            ValueError: If both "allow" and "deny" are set, or "mode" is neither "enforce" nor "log".
        """
        if acl is None:
            return

        allow = acl.get("allow")
        deny = acl.get("deny")
        mode = acl.get("mode", "enforce")

        if allow is not None and deny is not None:
            raise ValueError('acl config must set either "allow" or "deny", not both.')
        if mode not in ("enforce", "log"):
            raise ValueError(f'Invalid acl mode "{mode}", must be "enforce" or "log".')

        if allow is not None:
            allow = {sender: self._expand_acl_entries(entries) for sender, entries in allow.items()}

        self._acl_allow = allow
        self._acl_deny = deny
        self._acl_mode = mode

    def _expand_acl_entries(self, entries: list[str] | str) -> list[str] | str:
        """Expand any interface names (e.g. "ICamera") in an "allow" entry list into that
        interface's own method names, so listing an interface is shorthand for listing all
        of its methods individually. Unrecognized entries are kept as-is (plain method names).

        Args:
            entries: Either "*" (kept as-is) or a list of method and/or interface names.
        """
        if entries == "*":
            return entries

        expanded = []
        for entry in entries:
            expanded.extend(self._interface_methods.get(entry, [entry]))

        # de-duplicate while preserving order
        return list(dict.fromkeys(expanded))

    def _get_interfaces_and_methods(self) -> None:
        """List interfaces and methods of this module."""
        from pyobs.interfaces.interface import registered_interfaces

        # get interfaces
        self._interfaces = []
        self._methods = {}
        self._interface_methods = {}
        for interface in registered_interfaces().values():
            # is module a sub-class of that class that inherits from Interface?
            if isinstance(self, interface):
                # add interface
                self._interfaces += [interface]

                # loop methods of that interface
                method_names = []
                for method_name, method in inspect.getmembers(interface, predicate=inspect.isfunction):
                    # get method and signature
                    func = getattr(self, method_name)
                    signature = inspect.signature(func)
                    type_hints = typing.get_type_hints(func)

                    # fill dict of name->(method, signature)
                    self._methods[method_name] = (func, signature, type_hints)
                    method_names.append(method_name)

                # remember method names per interface, for acl "allow" interface-name sugar
                self._interface_methods[interface.__name__] = method_names

    def _acl_denied(self, sender: str, method: str) -> bool:
        """Whether the acl policy denies `sender` calling `method`, ignoring `mode` (enforce vs. log).

        Args:
            sender: Name of the calling module.
            method: Name of the method being called.

        Returns:
            True if the configured "allow"/"deny" policy denies this call.
        """
        if self._acl_allow is not None:
            allowed = self._acl_allow.get(sender)
            if allowed is None:
                return True
            if allowed == "*":
                return False
            return method not in allowed
        if self._acl_deny is not None:
            return sender in self._acl_deny
        return False

    def quit(self) -> None:
        """Quit module."""
        self._closing.set()
        if self._quit_parent is not None:
            self._quit_parent()
        else:
            asyncio.get_running_loop().stop()

    async def execute(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a local method safely with type conversion

        All incoming variables in args and kwargs must be of simple type (i.e. int, float, str, bool, tuple) and will
        be converted to the requested type automatically. All outgoing variables are converted to simple types
        automatically as well.

        Args:
            method: Name of method to execute.
            *args: Parameters for method.
            **kwargs: Parameters for method.

        Returns:
            Response from method call.

        Raises:
            KeyError: If method does not exist.
        """

        # is module in error state?
        if self._state == ModuleState.ERROR:
            # if called method is not from IModule, raise error
            if not hasattr(IModule, method):
                raise exc.ModuleError("Module is in error state, please reset it.")

        # get method and signature (may raise KeyError)
        func, signature, type_hints = self._methods[method]

        # check acl, exempting get_permitted_methods itself so a denied caller can still ask what it's denied from
        sender = kwargs.get("sender", "")
        if method != "get_permitted_methods" and self._acl_denied(sender, method):
            if self._acl_mode == "enforce":
                raise exc.ForbiddenError(sender, method)
            else:
                log.warning('Caller "%s" would be denied calling "%s" (acl mode=log, allowing).', sender, method)

        # bind parameters
        ba = signature.bind(*args, **kwargs)
        ba.apply_defaults()

        # get additional args and kwargs and delete from ba
        func_args = []
        func_kwargs = {}
        if "args" in ba.arguments:
            func_args = ba.arguments["args"]
            del ba.arguments["args"]
        if "kwargs" in ba.arguments:
            func_kwargs = ba.arguments["kwargs"]
            del ba.arguments["kwargs"]

        # call method — set module name context var so log messages from RPC calls
        # carry the correct module name rather than the caller's context
        from pyobs.utils.logging.context import module_name as _module_name_var

        _module_name_var.set(self._device_name or "")

        try:
            response = await func(*func_args, **ba.arguments, **func_kwargs)
        except Exception as e:
            # something else went wrong, but only log if not a ModuleError
            if isinstance(e, exc.PyObsError) and not isinstance(e, exc.ModuleError):
                # in list of named exceptions?
                level = (
                    "INFO"
                    if hasattr(func, "raises")
                    and isinstance(getattr(func, "raises"), tuple)
                    and type(e) in getattr(func, "raises")
                    else "ERROR"
                )
                exc_info = level == "ERROR"
                e.log(log, level, f"Exception was raised in call to {method}: {e}", exc_info=exc_info)
            raise e

        return response

    def _get_config_caps(self) -> dict[str, tuple[bool, bool, bool]]:
        """Returns a dictionary with config caps."""

        # init dict of caps and types
        caps: dict[str, tuple[bool, bool, bool]] = {}

        # loop super classes
        for cls in inspect.getmro(self.__class__):
            # ignore Object and Module
            if cls in [Object, Module]:
                continue

            # get signature
            sig = inspect.signature(getattr(cls, "__init__"))
            for name in sig.parameters:
                # ignore self, args, kwargs
                if name in ["self", "args", "kwargs"]:
                    continue

                # only add if at least one capability flag is set
                cap = self._add_config_cap(name)
                if any(cap):
                    caps[name] = cap

            # also add all additional config vars
            if self._additional_config_variables:
                for name in self._additional_config_variables:
                    cap = self._add_config_cap(name)
                    if any(cap):
                        caps[name] = cap

        # finished
        return caps

    def _add_config_cap(self, name: str) -> tuple[bool, bool, bool]:
        """Check for getter and setter

        Params:
            name: Name of variable.

        Returns:
            Tuple of booleans indication whether getter, setter and get_options exist.
        """
        return (
            hasattr(self, "_get_config_" + name),
            hasattr(self, "_set_config_" + name),
            hasattr(self, "_get_config_options_" + name),
        )

    async def get_config_caps(self, **kwargs: Any) -> dict[str, tuple[bool, bool, bool]]:
        """Returns dict of all config capabilities. First value is whether it has a getter, second is for the setter,
        third is for a list of possible options..

        Returns:
            Dict with config caps
        """
        return self._config_caps

    async def get_config_value(self, name: str, **kwargs: Any) -> ConfigValue:
        """Returns current value of config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Current value.

        Raises:
            ValueError: If config item of given name does not exist.
        """

        # valid parameter?
        if not name:
            raise ValueError("No parameter name given.")
        if name not in self._config_caps:
            raise ValueError(f"Invalid parameter {name}")
        if not self._config_caps[name][0]:
            raise ValueError("Parameter %s is not remotely accessible.")

        # get getter method and call it
        getter = getattr(self, "_get_config_" + name)
        return await getter()

    async def get_config_value_options(self, name: str, **kwargs: Any) -> list[str]:
        """Returns possible values for config item with given name.

        Args:
            name: Name of config item.

        Returns:
            Possible values.

        Raises:
            ValueError: If config item of given name does not exist.
        """

        # valid parameter?
        if not name:
            raise ValueError("No parameter name given.")
        if name not in self._config_caps:
            raise ValueError(f"Invalid parameter {name}")
        if not self._config_caps[name][2]:
            raise ValueError("Parameter %s has no list of possible values.")

        # get getter method and call it
        options = getattr(self, "_get_config_options_" + name)
        return cast(list[str], await options())

    async def set_config_value(self, name: str, value: ConfigValue, **kwargs: Any) -> None:
        """Sets value of config item with given name.

        Args:
            name: Name of config item.
            value: New value.

        Raises:
            ValueError: If config item of given name does not exist or value is invalid.
        """

        # valid parameter?
        if not name:
            raise ValueError("No parameter name given.")
        if name not in self._config_caps:
            raise ValueError(f"Invalid parameter {name}")
        if not self._config_caps[name][1]:
            raise ValueError("Parameter %s is not remotely settable.")

        # get setter and call it
        setter = getattr(self, "_set_config_" + name)
        await setter(value)

    async def set_state(self, state: ModuleState, error_string: str | None = None) -> None:
        """Set state of module.

        Args:
            state: New state to set.
            error_string: If given, set error string.
        """

        # log?
        if state != self._state:
            log.info("Set module state to %s.", state)

        # set it
        self._state = state
        if error_string is not None:
            self.set_error_string(error_string)

        # publish presence
        if self._comm is not None:
            await self._comm.set_presence(state, error_string if error_string is not None else self._error_string)

    async def get_state(self, **kwargs: Any) -> ModuleState:  # type: ignore[override]
        """Returns current state of module."""
        return self._state

    async def reset_error(self, **kwargs: Any) -> bool:
        """Reset error of module, if any. Should be overwritten by derived class to handle error resolution."""
        self._state = ModuleState.READY
        self.set_error_string()
        return True

    async def get_permitted_methods(self, **kwargs: Any) -> list[str]:
        """Returns names of all methods the calling module is allowed to invoke on this module."""
        # a rule that isn't actually enforced yet (mode=log) shouldn't be reflected here
        if self._acl_mode == "log":
            return list(self._methods.keys())

        sender = kwargs.get("sender", "")
        return [name for name in self._methods if not self._acl_denied(sender, name)]

    async def _default_remote_error_callback(self, exception: exc.PyObsError) -> None:
        """Called on severe errors.

        Args:
            exception: Exception that caused severe error.
        """

        # set error string
        if isinstance(exception, exc.RemoteError):
            error = f"Servere error in {exception.module} module: {exception}"
        else:
            error = f"Severe error: {exception}"
        self.set_error_string(error)

        # log it and set state
        log.critical(error)
        await self.set_state(ModuleState.ERROR)

    def set_error_string(self, error: str = "") -> None:
        """Set error string."""
        self._error_string = error

    async def get_error_string(self, **kwargs: Any) -> str:
        """Returns description of error, if any."""
        return self._error_string


class MultiModule(Module):
    """Wrapper for running multiple modules in a single process."""

    __module__ = "pyobs.modules"

    def __init__(
        self,
        modules: dict[str, Module | dict[str, Any]],
        shared: dict[str, Any | dict[str, Any]] | None = None,
        **kwargs: Any,
    ):
        """
        Args:
            modules: Dictionary with modules.
            shared: Shared objects between modules.
        """
        Module.__init__(self, **kwargs)
        # MultiModule itself has no real comm identity (its children each have their own),
        # so give it a fixed, recognizable tag for its own log lines
        self._device_name = "multi"

        # create shared objects
        self._shared: dict[str, Module] = {}
        if shared:
            for name, obj in shared.items():
                # if obj is an object definition, create it, otherwise just set it
                self._shared[name] = self.add_child_object(obj, None)

        # create modules
        self._modules = {}
        for name, mod in modules.items():
            # what is it?
            if isinstance(mod, Module):
                # it's a module already, store it
                self._modules[name] = mod
            elif isinstance(mod, dict):
                # dictionary, create it
                self._modules[name] = self.add_child_object(mod, None, **self._shared, copy_comm=False)

        # register ourselves as quit parent on each child so any child quitting
        # propagates to the MultiModule
        for mod in self._modules.values():
            mod._quit_parent = self.quit

    @property
    def modules(self) -> dict[str, Module]:
        return self._modules

    def __contains__(self, name: str) -> bool:
        """Checks, whether this multi-module contains a module of given name."""
        return name in self._modules

    def __getitem__(self, name: str) -> Module:
        """Returns module of given name."""
        return self._modules[name]

    async def open(self) -> None:
        """Open MultiModule.

        Shared/non-module child objects are opened normally. Each sub-module is
        spawned as its own asyncio task so that the module name context var — set
        at the top of each task — is inherited by all background tasks that module
        creates, giving correct PYOBS_MODULE attribution in log output.
        """
        # open shared objects (anything in _child_objects that is not a sub-module)
        for obj in self._child_objects:
            if obj not in self._modules.values() and hasattr(obj, "open"):
                if inspect.iscoroutinefunction(obj.open):
                    await obj.open()
                else:
                    obj.open()

        # spawn each sub-module as its own task, each with a fresh context
        # so that module_name ContextVar is isolated per module from the start
        from contextvars import copy_context

        from pyobs.utils.logging.context import module_name as _module_name_var

        self._module_tasks: list[asyncio.Task[None]] = []
        for name, mod in self._modules.items():
            # create a fresh context for each module with module_name pre-set
            ctx = copy_context()
            ctx.run(_module_name_var.set, name)
            task = asyncio.create_task(self._run_module(name, mod), name=f"pyobs.module.{name}", context=ctx)
            self._module_tasks.append(task)

        self._opened = True

    async def _run_module(self, name: str, mod: Module) -> None:
        """Run a single sub-module: open, main, close — all within one task.

        Setting the context var here means every background task spawned by
        mod.open() inherits it via asyncio's copy-on-create_task semantics.
        """
        from pyobs.utils.logging.context import module_name as _module_name_var

        _module_name_var.set(name)
        try:
            await mod.open()
            await mod.main()
        except asyncio.CancelledError:
            pass
        except Exception:
            log.exception("Exception in sub-module %s.", name)
        finally:
            try:
                await mod.close()
            except Exception:
                log.exception("Error closing sub-module %s.", name)

    async def main(self) -> None:
        """Wait until all sub-module tasks have finished."""
        if self._module_tasks:
            await asyncio.gather(*self._module_tasks, return_exceptions=True)

    async def close(self) -> None:
        """Cancel sub-module tasks and close shared objects."""
        for task in getattr(self, "_module_tasks", []):
            task.cancel()

        for obj in self._child_objects:
            if obj not in self._modules.values() and hasattr(obj, "close"):
                await obj.close()

        await Module.close(self)

    def quit(self) -> None:
        """Quit all sub-modules."""
        # temporarily clear _quit_parent on children to avoid recursion
        # (children would otherwise call back into this method)
        for mod in self._modules.values():
            mod._quit_parent = None
            mod.quit()
        super().quit()


__all__ = ["Module", "MultiModule", "timeout", "raises"]
