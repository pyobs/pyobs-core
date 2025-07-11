"""
:class:`~pyobs.object.Object` is the base for almost all classes in *pyobs*. It adds some convenience methods
and helper methods for creating other Objects.

There are a few convenience functions:

    - :func:`~pyobs.object.create_object` creates objects from dictionaries.
    - :func:`~pyobs.object.get_object` is a wrapper around :func:`pyobs.object.create_object` that can do further checks.
    - :func:`~pyobs.object.get_safe_object` is a wrapper around :func:`~pyobs.object.get_object` that never raises
      exceptions.
"""

from __future__ import annotations

import asyncio
import copy
import datetime
import inspect
from abc import ABCMeta
from collections.abc import Coroutine
from typing import Union, Callable, TypeVar, Optional, Type, List, Tuple, Any, overload, TYPE_CHECKING
import logging
import pytz
from astroplan import Observer
from astropy.coordinates import EarthLocation

from pyobs.background_task import BackgroundTask
from pyobs.comm import Comm
from pyobs.comm.dummy import DummyComm

if TYPE_CHECKING:
    from pyobs.vfs import VirtualFileSystem

log = logging.getLogger(__name__)


"""Class of an Object."""
ObjectClass = TypeVar("ObjectClass")


"""Class of a proxy."""
ProxyType = TypeVar("ProxyType")


@overload
def get_object(
    config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
    object_class: type[ObjectClass] | ABCMeta,
    **kwargs: Any,
) -> ObjectClass: ...


@overload
def get_object(
    config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass], object_class: None = None, **kwargs: Any
) -> ObjectClass | Any | None: ...


def get_object(
    config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
    object_class: type[ObjectClass] | ABCMeta | None = None,
    **kwargs: Any,
) -> ObjectClass | Any | None:
    """Creates object from config or returns object directly, both optionally after check of type.

    Args:
        config_or_object: A configuration dict or an object itself to create/check. If a dict with a class key
            is given, a new object is created.
        object_class: Class to check object against.

    Returns:
        (New) object (created from config) that optionally passed class check.

    Raises:
        TypeError: If the object does not match the given class.
    """

    if config_or_object is None:
        raise TypeError("No config or object given.")

    elif isinstance(config_or_object, dict):
        # copy kwargs to config_or_object, so that we don't have any duplicates
        for k, v in kwargs.items():
            config_or_object[k] = v

        # a dict is given, so create object
        obj = create_object(config_or_object)

    elif inspect.isclass(config_or_object):
        # config_or_object is a type, so create it using its constructor
        obj = config_or_object(**kwargs)

    else:
        # just use given object
        obj = config_or_object

    # do we need a type check and does the given object pass?
    if object_class is not None and not isinstance(obj, object_class):
        raise TypeError("Provided object is not of requested type %s." % object_class.__name__)
    return obj


@overload
def get_safe_object(
    config_or_object: ObjectClass | dict[str, Any], object_class: type[ObjectClass] | ABCMeta, **kwargs: Any
) -> ObjectClass: ...


@overload
def get_safe_object(config_or_object: ObjectClass | Any, object_class: None, **kwargs: Any) -> Any | None: ...


def get_safe_object(
    config_or_object: dict[str, Any] | Any, object_class: type[ObjectClass] | ABCMeta | None = None, **kwargs: Any
) -> ObjectClass | Any | None:
    """Calls get_object in a safe way and returns None, if an exceptions thrown.

    Args:
        config_or_object: A configuration dict or an object itself to create/check. If a dict with a class key
            is given, a new object is created.
        object_class: Class to check object against.

    Returns:
        (New) object (created from config) that optionally passed class check or None.
    """
    try:
        return get_object(config_or_object, object_class, **kwargs)
    except Exception:
        return None


def get_class_from_string(class_name: str) -> Any:
    """Get class from a given string.

    Args:
        class_name: Name of class as string.

    Returns:
        Actual class.
    """

    parts = class_name.split(".")
    module_name = ".".join(parts[:-1])
    cls = __import__(module_name)
    for comp in parts[1:]:
        cls = getattr(cls, comp)
    return cls


def create_object(config: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
    """Create object from dict config.

    Args:
        config: Config to create object from
        *args: Parameters to be passed to object.
        **kwargs: Parameters to be passed to object.

    Returns:
        Created object.
    """

    # get class name
    class_name = config["class"]

    # create class
    klass = get_class_from_string(class_name)

    # remove class from kwargs
    cfg = copy.copy(config)
    del cfg["class"]

    # create object
    return klass(*args, **cfg, **kwargs)


class Object:
    """Base class for all objects in *pyobs*."""

    def __init__(
        self,
        vfs: "VirtualFileSystem" | dict[str, Any] | None = None,
        comm: Comm | dict[str, Any] | None = None,
        timezone: str | datetime.tzinfo = "utc",
        location: str | dict[str, Any] | EarthLocation | None = None,
        observer: Observer | None = None,
        **kwargs: Any,
    ):
        """
        .. note::

            Objects must always be opened and closed using :meth:`~pyobs.object.Object.open` and
            :meth:`~pyobs.object.Object.close`, respectively.

        This class provides a :class:`~pyobs.vfs.VirtualFileSystem`, a timezone and a location. From the latter two, an
        observer object is automatically created.

        Object also adds support for easily adding threads using the :meth:`~pyobs.object.Object.add_background_task`
        method as well as a watchdog thread that automatically restarts threads, if requested.

        Using :meth:`~pyobs.object.Object.add_child_object`, other objects can be (created an) attached to this object,
        which then automatically handles calls to :meth:`~pyobs.object.Object.open` and :meth:`~pyobs.object.Object.close`
        on those objects.

        Args:
            vfs: VFS to use (either object or config)
            comm: Comm object to use
            timezone: Timezone at observatory.
            location: Location of observatory, either a name or a dict containing latitude, longitude, and elevation.

        """
        from pyobs.vfs import VirtualFileSystem

        # child objects
        self._child_objects: list[Any] = []

        # create vfs
        if vfs:
            self.vfs = get_object(vfs, VirtualFileSystem)
        else:
            self.vfs = VirtualFileSystem()

        # timezone
        if isinstance(timezone, datetime.tzinfo):
            self.timezone = timezone
        elif isinstance(timezone, str):
            self.timezone = pytz.timezone(timezone)
        else:
            raise ValueError("Unknown format for timezone.")

        # location
        if location is None:
            self.location = None
        elif isinstance(location, EarthLocation):
            self.location = location
        elif isinstance(location, str):
            self.location = EarthLocation.of_site(location)
        elif isinstance(location, dict):
            self.location = EarthLocation.from_geodetic(
                location["longitude"], location["latitude"], location["elevation"]
            )
        else:
            raise ValueError("Unknown format for location.")

        # create observer
        self.observer = observer
        if self.observer is None and self.location is not None and self.timezone is not None:
            log.info(
                "Setting location to longitude=%s, latitude=%s, and elevation=%s.",
                self.location.lon,
                self.location.lat,
                self.location.height,
            )
            self.observer = Observer(location=self.location, timezone=timezone)

        # comm object
        self.comm: Comm
        if comm is None:
            self.comm = DummyComm()
        elif isinstance(comm, Comm):
            self.comm = comm
        elif isinstance(comm, dict):
            log.info("Creating comm object...")
            self.comm = get_object(comm, Comm)
        else:
            raise ValueError("Invalid Comm object")

        # opened?
        self._opened = False

        # background tasks
        self._background_tasks: List[Tuple[BackgroundTask, bool]] = []

    def add_background_task(
        self, func: Callable[..., Coroutine[Any, Any, None]], restart: bool = True, autostart: bool = True
    ) -> BackgroundTask:
        """Add a new function that should be run in the background.

        MUST be called in constructor of derived class or at least before calling open() on the object.

        Args:
            func: Func to add.
            restart: Whether to restart this function.
            autostart: Whether to start this function when the module is opened
        Returns:
            Background task
        """

        background_task = BackgroundTask(func, restart)
        self._background_tasks.append((background_task, autostart))

        return background_task

    async def open(self) -> None:
        """Open module."""

        self._perform_background_task_autostart()

        # open child objects
        for obj in self._child_objects:
            if hasattr(obj, "open"):
                if asyncio.iscoroutinefunction(obj.open):
                    await obj.open()
                else:
                    obj.open()

        # success
        self._opened = True

    def _perform_background_task_autostart(self) -> None:
        todo = filter(lambda b: b[1] is True, self._background_tasks)
        for task, _ in todo:
            task.start()

    @property
    def opened(self) -> bool:
        """Whether object has been opened."""
        return self._opened

    async def close(self) -> None:
        """Close module."""

        # close child objects
        for obj in self._child_objects:
            if hasattr(obj, "close"):
                await obj.close()

        self._stop_background_tasks()

    def _stop_background_tasks(self) -> None:
        for task, _ in self._background_tasks:
            task.stop()

    def quit(self) -> None:
        """Can be overloaded to quit program."""
        pass

    @overload
    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: type[ObjectClass] | ABCMeta,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass: ...

    @overload
    def get_object(
        self, config_or_object: type[ObjectClass], object_class: None = None, copy_comm: bool = True, **kwargs: Any
    ) -> ObjectClass: ...

    @overload
    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass: ...

    def get_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass],
        object_class: type[ObjectClass] | ABCMeta | None = None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass | Any | None:
        """Creates object from config or returns object directly, both optionally after check of type.

        Args:
            config_or_object: A configuration dict or an object itself to create/check. If a dict with a class key
                is given, a new object is created.
            object_class: Class to check object against.
            copy_comm: Copy comm from this object to the new one.

        Returns:
            (New) object (created from config) that optionally passed class check.

        Raises:
            TypeError: If the object does not match the given class.
        """

        # set parameters
        params = copy.copy(kwargs)

        # copy comm?
        if copy_comm:
            params["comm"] = self.comm

        # copy timezone, location, vfs, and observer, if not exists
        if isinstance(config_or_object, dict):
            for p in ["timezone", "location", "vfs", "observer"]:
                if self.__config_or_object_get_param(config_or_object, p) is None:
                    params[p] = getattr(self, p)

        # get it
        return get_object(config_or_object, object_class, **params)

    def __config_or_object_get_param(self, config_or_object: dict[str, Any], param: str) -> Any:
        """Checks, whether a config_or_object has the given parameter.

        Args:
            config_or_object: Dict config or object.
            param: Parameter name to check.

        Returns:

        """
        is_dict = isinstance(config_or_object, dict)
        if is_dict and param in config_or_object:
            return config_or_object[param]
        if not is_dict and hasattr(config_or_object, param):
            return getattr(config_or_object, param)
        return None

    @overload
    def get_safe_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: Type[ObjectClass],
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> Optional[ObjectClass]: ...

    @overload
    def get_safe_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> Optional[Any]: ...

    def get_safe_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: type[ObjectClass] | None = None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass | Any | None:
        """Calls get_object in a safe way and returns None, if an exceptions thrown."""
        try:
            return self.get_object(config_or_object, object_class=object_class, copy_comm=copy_comm, **kwargs)
        except Exception:
            log.exception("test")
            return None

    @overload
    def add_child_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: type[ObjectClass],
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass: ...

    @overload
    def add_child_object(
        self, config_or_object: type[ObjectClass], object_class: None = None, copy_comm: bool = True, **kwargs: Any
    ) -> ObjectClass: ...

    @overload
    def add_child_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> Any: ...

    def add_child_object(
        self,
        config_or_object: dict[str, Any] | ObjectClass | type[ObjectClass] | Any,
        object_class: Optional[Type[ObjectClass]] = None,
        copy_comm: bool = True,
        **kwargs: Any,
    ) -> ObjectClass:
        """Create a new sub-module, which will automatically be opened and closed.

        Args:
            config_or_object: Module definition
            object_class: Class for new module
            copy_comm: Copy comm from this object to the new one.

        Returns:
            The created module.
        """

        # get object
        obj = self.get_object(config_or_object, object_class=object_class, copy_comm=copy_comm, **kwargs)

        # add to list
        self._child_objects.append(obj)

        # return it
        return obj

    @overload
    async def proxy(self, name_or_object: str | object, obj_type: type[ProxyType]) -> ProxyType: ...

    @overload
    async def proxy(self, name_or_object: str | object, obj_type: type[ProxyType] | None = None) -> Any: ...

    async def proxy(
        self, name_or_object: str | object, obj_type: type[ProxyType] | None = None
    ) -> Union[Any, ProxyType]:
        """Returns object directly if it is of given type. Otherwise get proxy of client with given name and check type.

        If name_or_object is an object:
            - If it is of type (or derived), return object.
            - Otherwise raise exception.
        If name_name_or_object is string:
            - Create proxy from name and raise exception, if it doesn't exist.
            - Check type and raise exception if wrong.
            - Return object.

        Args:
            name_or_object: Name of object or object itself.
            obj_type: Expected class of object.

        Returns:
            Object or proxy to object.

        Raises:
            ValueError: If proxy does not exist or wrong type.
        """
        return await self.comm.proxy(name_or_object, obj_type)


__all__ = ["get_object", "get_class_from_string", "create_object", "Object"]
