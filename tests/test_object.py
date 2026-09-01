from unittest.mock import AsyncMock

import pytest

import pyobs
from pyobs.object import Object, create_object


def test_add_background_task():
    obj = Object()
    test_function = AsyncMock()

    task = obj.add_background_task(test_function, False, False)

    assert task._func == test_function
    assert task._restart is False

    assert obj._background_tasks[0] == (task, False)


def test_perform_background_task_autostart(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.start")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, True)
    obj._perform_background_task_autostart()

    pyobs.background_task.BackgroundTask.start.assert_called_once()


def test_perform_background_task_no_autostart(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.start")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, False)
    obj._perform_background_task_autostart()

    pyobs.background_task.BackgroundTask.start.assert_not_called()


def test_stop_background_task(mocker):
    mocker.patch("pyobs.background_task.BackgroundTask.stop")

    obj = Object()
    test_function = AsyncMock()

    obj.add_background_task(test_function, False, False)
    obj._stop_background_tasks()

    pyobs.background_task.BackgroundTask.stop.assert_called_once()


def test_create_object_pydantic_rejects_positional_args():
    with pytest.raises(TypeError, match="positional args"):
        create_object({"class": "pyobs.robotic.task.Task"}, "unexpected_positional")


def test_create_object_pydantic_rejects_kwarg_config_collision():
    with pytest.raises(TypeError, match="name"):
        create_object({"class": "pyobs.robotic.task.Task", "name": "from_config"}, name="from_kwarg")


def test_unrecognized_kwarg_raises_typeerror_naming_class_and_kwarg():
    """Object.__init__'s cooperative super().__init__(**kwargs) call eventually reaches the real
    object.__init__() if nothing in the chain claims a kwarg, but that raises a generic,
    contextless TypeError. Object wraps it so the message actually names the class and kwarg."""
    with pytest.raises(TypeError, match=r"Object\(\) got unexpected keyword argument\(s\) \['bogus_kwarg'\]"):
        Object(bogus_kwarg="whatever")


def test_unrecognized_kwarg_error_chains_original_typeerror():
    with pytest.raises(TypeError) as exc_info:
        Object(bogus_kwarg="whatever")
    assert isinstance(exc_info.value.__cause__, TypeError)
    assert "object.__init__() takes exactly one argument" in str(exc_info.value.__cause__)


def test_mixin_after_object_in_mro_still_claims_its_own_kwargs():
    """Regression guard for the wrapped super().__init__(**kwargs) call: a subclass with a mixin
    listed after Object in its bases (e.g. BaseRoof(Module, WeatherAwareMixin, ...)) must still be
    able to consume kwargs cooperatively -- the wrap must not turn Object into a premature
    terminal point for the chain."""

    class _AfterObjectMixin:
        def __init__(self, mixin_only_kwarg: str | None = None, **kwargs):
            self.mixin_only_kwarg = mixin_only_kwarg
            super().__init__(**kwargs)

    class _ObjectThenMixin(Object, _AfterObjectMixin):
        pass

    obj = _ObjectThenMixin(mixin_only_kwarg="claimed-downstream")
    assert obj.mixin_only_kwarg == "claimed-downstream"


def test_unrecognized_kwarg_message_excludes_downstream_consumed_kwargs():
    """Object's own kwargs is the leftover *before* consumption by mixins later in the MRO -- a
    downstream mixin claiming its own kwarg alongside a genuine typo must not get reported as
    unconsumed too, or the message actively misleads about which kwarg is the real problem."""

    class _AfterObjectMixin:
        def __init__(self, mixin_only_kwarg: str | None = None, **kwargs):
            self.mixin_only_kwarg = mixin_only_kwarg
            super().__init__(**kwargs)

    class _ObjectThenMixin(Object, _AfterObjectMixin):
        pass

    with pytest.raises(TypeError) as exc_info:
        _ObjectThenMixin(mixin_only_kwarg="legitimately-consumed", bogus_kwarg="typo")

    message = str(exc_info.value)
    assert "bogus_kwarg" in message
    assert "mixin_only_kwarg" not in message


def test_get_object_keeps_childs_own_vfs_over_parents():
    """Regression test for #837: get_object's inherit-if-not-set check for vfs/timezone/observer
    looked for the underscore-prefixed attribute name ("_vfs") in the config dict, but a YAML/dict
    config keys on the constructor param name ("vfs"), so the check always missed and the parent's
    own vfs silently overwrote a child's explicitly configured one."""
    parent = Object(vfs={"class": "pyobs.vfs.VirtualFileSystem"})
    child_cfg = {
        "class": "pyobs.object.Object",
        "vfs": {
            "class": "pyobs.vfs.VirtualFileSystem",
            "roots": {"cache": {"class": "pyobs.vfs.LocalFile", "root": "/tmp"}},
        },
    }

    child = parent.get_object(child_cfg, copy_comm=False)

    assert child.vfs is not parent.vfs
    assert "cache" in child.vfs._roots
