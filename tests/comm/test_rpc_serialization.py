"""Tests for RPC parameter serialization/deserialization."""

from __future__ import annotations

import pytest
from slixmpp.xmlstream import ET

from pyobs.comm.xmpp.rpc import (
    _NS,
    _PYOBS_NS,
    fault_to_xml,
    params_to_xml,
    reconstruct_fault,
    xml_to_fault,
    xml_to_fault_bases,
    xml_to_params,
)
from pyobs.utils import exceptions as exc


class TestXmlToParams:
    """Test xml_to_params deserialization."""

    def test_round_trip(self) -> None:
        params_elem = params_to_xml(["x", "y"], [1, 2], {"x": int, "y": int})
        assert xml_to_params(params_elem, ["x", "y"], {"x": int, "y": int}) == [1, 2]

    def test_missing_value_element_raises(self) -> None:
        params = ET.Element(f"{{{_NS}}}params")
        param = ET.Element(f"{{{_NS}}}param")
        params.append(param)
        with pytest.raises(ValueError, match="missing <value>"):
            xml_to_params(params, ["x"], {"x": int})

    def test_missing_pyobs_namespace_raises(self) -> None:
        # Simulates a client serializer (e.g. Strophe's hand-rolled Builder)
        # that fails to emit the required xmlns on the value wrapper: the
        # <value> element is present but has no properly-namespaced
        # <pyobs:value> child, so it must never be silently treated as None.
        params = ET.Element(f"{{{_NS}}}params")
        param = ET.Element(f"{{{_NS}}}param")
        value_elem = ET.Element(f"{{{_NS}}}value")
        # child present, but without the urn:pyobs:rpc:1 namespace
        unnamespaced_value = ET.Element("value")
        unnamespaced_value.append(ET.Element("int"))
        value_elem.append(unnamespaced_value)
        param.append(value_elem)
        params.append(param)
        with pytest.raises(ValueError, match=_PYOBS_NS):
            xml_to_params(params, ["x"], {"x": int})


class TestFaultXml:
    """Test fault_to_xml/xml_to_fault, and that the round-tripped name resolves via the registry."""

    def test_round_trip_uses_fully_qualified_name(self) -> None:
        fault_elem = fault_to_xml(exc.FocusError("could not focus"))
        exc_name, msg = xml_to_fault(fault_elem)
        assert exc_name == "pyobs.utils.exceptions.FocusError"
        assert msg == "could not focus"
        assert exc.PyobsError.resolve(exc_name) is exc.FocusError

    def test_round_trip_message_is_raw_not_str_formatted(self) -> None:
        # str(exception) is "<ClassName> message" -- serializing that instead of the raw message
        # would double up once the caller's own __str__ formats the reconstructed instance again
        fault_elem = fault_to_xml(exc.FocusError("could not focus"))
        _, msg = xml_to_fault(fault_elem)
        reconstructed = exc.FocusError(msg, remote_module="camera")
        assert str(reconstructed) == "<FocusError> could not focus"

    def test_unclassified_error_serializes_original_type_not_its_own_class_name(self) -> None:
        # Module.execute() wraps a non-PyobsError as UnclassifiedError(original_type=...) before
        # it ever reaches rpc.py -- the wire must carry the *original* type, not "UnclassifiedError"
        # itself, or original_type is silently lost for the caller (it's not a wire-serialized
        # attribute, only the class name and message are)
        wrapped = exc.UnclassifiedError("Invalid destination", original_type="builtins.IndexError")
        fault_elem = fault_to_xml(wrapped)
        exc_name, msg = xml_to_fault(fault_elem)
        assert exc_name == "builtins.IndexError"
        assert msg == "Invalid destination"
        assert exc.PyobsError.resolve(exc_name) is None  # builtins are never registered

        # caller-side reconstruction (mirroring _on_jabber_rpc_method_fault's fallback branch)
        reconstructed = exc.UnclassifiedError(msg, original_type=exc_name, remote_module="camera")
        assert reconstructed.original_type == "builtins.IndexError"

    def test_missing_value_element_falls_back_to_remote_error(self) -> None:
        fault = ET.Element(f"{{{_NS}}}fault")
        exc_name, msg = xml_to_fault(fault)
        assert exc_name == "pyobs.utils.exceptions.RemoteError"
        assert msg == "Unknown error"
        assert exc.PyobsError.resolve(exc_name) is exc.RemoteError

    def test_unresolvable_name_has_no_registry_entry(self) -> None:
        # a builtin, or a domain type whose defining module was never imported here
        assert exc.PyobsError.resolve("builtins.ValueError") is None
        assert exc.PyobsError.resolve("some.module.that.was.never.imported.WeatherDataError") is None


class _PluginTimeout(exc.MotionError):
    """Stands in for a driver error whose module the caller never imported."""


class _PluginMoveFailed(exc.MoveError):
    pass


class _PluginOnlyPyobs(exc.PyobsError):
    pass


@pytest.fixture
def forget_plugin_errors():
    """Remove the plugin errors from the registry, as if the caller never imported their module."""
    names = [f"{c.__module__}.{c.__qualname__}" for c in (_PluginTimeout, _PluginMoveFailed, _PluginOnlyPyobs)]
    saved = {n: exc.PyobsError._registry.pop(n) for n in names}
    yield {c: n for c, n in zip((_PluginTimeout, _PluginMoveFailed, _PluginOnlyPyobs), names)}
    exc.PyobsError._registry.update(saved)


def _bases(exception: Exception) -> list[str]:
    return xml_to_fault_bases(fault_to_xml(exception))


class TestFaultBases:
    """<bases> lets a caller that never imported an exception's module fall back to its nearest known ancestor."""

    def test_leaf_lists_ancestors_without_pyobserror(self) -> None:
        assert _bases(_PluginTimeout("x")) == ["pyobs.utils.exceptions.MotionError"]

    def test_multi_level_leaf_lists_nearest_first(self) -> None:
        assert _bases(_PluginMoveFailed("x")) == [
            "pyobs.utils.exceptions.MoveError",
            "pyobs.utils.exceptions.MotionError",
        ]

    def test_direct_pyobserror_subclass_has_no_bases(self) -> None:
        assert _bases(_PluginOnlyPyobs("x")) == []

    def test_unclassified_error_has_no_bases(self) -> None:
        assert _bases(exc.UnclassifiedError("x", original_type="builtins.IndexError")) == []

    def test_ancestor_resolved_error_lists_itself_first(self) -> None:
        # second hop: the exception is a MotionError that was resolved for "plugin.X"
        forwarded = exc.MotionError("x", original_type="plugin.X")
        fault_elem = fault_to_xml(forwarded)
        assert xml_to_fault(fault_elem)[0] == "plugin.X"
        assert xml_to_fault_bases(fault_elem) == ["pyobs.utils.exceptions.MotionError"]

    def test_missing_bases_element_gives_empty_list(self) -> None:
        fault_elem = fault_to_xml(_PluginTimeout("x"))
        pyobs_fault = fault_elem.find(f"{{{_NS}}}value").find(f"{{{_PYOBS_NS}}}fault")
        pyobs_fault.remove(pyobs_fault.find("bases"))
        assert xml_to_fault_bases(fault_elem) == []
        assert xml_to_fault(fault_elem)[1] == "x"

    def test_xml_to_fault_still_returns_two_values(self) -> None:
        assert len(xml_to_fault(fault_to_xml(_PluginTimeout("x")))) == 2

    def test_no_value_element_gives_empty_list(self) -> None:
        assert xml_to_fault_bases(ET.Element(f"{{{_NS}}}fault")) == []


class TestReconstructFault:
    def test_registered_leaf_is_raised_as_itself(self) -> None:
        e = reconstruct_fault(
            f"{_PluginTimeout.__module__}.{_PluginTimeout.__qualname__}",
            "timeout",
            ["pyobs.utils.exceptions.MotionError"],
            "camera",
        )
        assert type(e) is _PluginTimeout
        assert e.remote_module == "camera"
        assert not hasattr(e, "original_type")

    def test_unimported_leaf_becomes_nearest_registered_ancestor(self, forget_plugin_errors) -> None:
        name = forget_plugin_errors[_PluginMoveFailed]
        e = reconstruct_fault(
            name, "stuck", ["pyobs.utils.exceptions.MoveError", "pyobs.utils.exceptions.MotionError"], "telescope"
        )
        assert type(e) is exc.MoveError
        assert isinstance(e, exc.MotionError)
        assert e.original_type == name
        assert e.remote_module == "telescope"
        assert e.message == "stuck"
        assert str(e) == "<MoveError> stuck"

    def test_unregistered_base_is_skipped(self, forget_plugin_errors) -> None:
        e = reconstruct_fault(
            forget_plugin_errors[_PluginMoveFailed],
            "x",
            ["other.package.Missing", "pyobs.utils.exceptions.MotionError"],
            "telescope",
        )
        assert type(e) is exc.MotionError

    def test_leaf_with_only_pyobserror_ancestor_is_unclassified(self, forget_plugin_errors) -> None:
        name = forget_plugin_errors[_PluginOnlyPyobs]
        e = reconstruct_fault(name, "x", [], "telescope")
        assert type(e) is exc.UnclassifiedError
        assert e.original_type == name

    def test_old_peer_without_bases_is_unclassified(self, forget_plugin_errors) -> None:
        name = forget_plugin_errors[_PluginTimeout]
        e = reconstruct_fault(name, "x", [], "telescope")
        assert type(e) is exc.UnclassifiedError
        assert not isinstance(e, exc.MotionError)
        assert e.original_type == name

    def test_unclassified_base_is_skipped(self, forget_plugin_errors) -> None:
        e = reconstruct_fault(
            forget_plugin_errors[_PluginTimeout], "x", ["pyobs.utils.exceptions.UnclassifiedError"], "t"
        )
        assert type(e) is exc.UnclassifiedError

    def test_round_trip_through_the_wire(self, forget_plugin_errors) -> None:
        fault_elem = fault_to_xml(_PluginTimeout("timeout"))
        name, msg = xml_to_fault(fault_elem)
        e = reconstruct_fault(name, msg, xml_to_fault_bases(fault_elem), "camera")
        assert type(e) is exc.MotionError
        assert e.original_type == forget_plugin_errors[_PluginTimeout]
        assert e.message == "timeout"

    def test_second_hop_keeps_the_ancestor(self, forget_plugin_errors) -> None:
        # hop 1: caller resolves the leaf to MotionError and forwards it over another RPC call
        name = forget_plugin_errors[_PluginTimeout]
        first = reconstruct_fault(name, "timeout", ["pyobs.utils.exceptions.MotionError"], "camera")
        fault_elem = fault_to_xml(first)
        second = reconstruct_fault(*xml_to_fault(fault_elem), xml_to_fault_bases(fault_elem), "gateway")
        assert type(second) is exc.MotionError
        assert second.original_type == name


class TestCoreModuleErrors:
    """The module-specific errors of core derive from a core class, so a caller that never imported their module
    still gets that class (#952 item 8)."""

    def test_altitude_limit_error_is_a_pointing_limit_error_but_not_a_motion_error(self) -> None:
        from pyobs.modules.telescope.basetelescope import AltitudeLimitError

        assert issubclass(AltitudeLimitError, exc.PointingLimitError)
        # guards BaseTelescope's _register_exception(exc.MotionError, ...) escalation
        assert not issubclass(AltitudeLimitError, exc.MotionError)
        assert not issubclass(exc.PointingLimitError, exc.MotionError)

    def test_weather_and_script_errors_are_general_errors_not_module_errors(self) -> None:
        from pyobs.modules.weather.weather import WeatherResponseError
        from pyobs.robotic.scripts.exceptions import ScriptError

        for cls in (WeatherResponseError, ScriptError):
            assert issubclass(cls, exc.GeneralError)
            assert not issubclass(cls, exc.ModuleError)

    @pytest.mark.parametrize(
        ("module", "name", "expected"),
        [
            ("pyobs.modules.telescope.basetelescope", "AltitudeLimitError", exc.PointingLimitError),
            ("pyobs.modules.weather.weather", "WeatherResponseError", exc.GeneralError),
            ("pyobs.robotic.scripts.exceptions", "ScriptError", exc.GeneralError),
        ],
    )
    def test_unimported_core_error_arrives_as_its_core_base(self, module: str, name: str, expected: type) -> None:
        import importlib

        cls = getattr(importlib.import_module(module), name)
        qualified_name = f"{cls.__module__}.{cls.__qualname__}"
        # the wire name does not change, so old peers resolve it as before
        assert qualified_name == f"{module}.{name}"

        fault_elem = fault_to_xml(cls("boom"))
        saved = exc.PyobsError._registry.pop(qualified_name)
        try:
            e = reconstruct_fault(*xml_to_fault(fault_elem), xml_to_fault_bases(fault_elem), "telescope")
        finally:
            exc.PyobsError._registry[qualified_name] = saved

        assert type(e) is expected
        assert e.original_type == qualified_name
        assert e.message == "boom"
