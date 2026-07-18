"""Tests for RPC parameter serialization/deserialization."""

from __future__ import annotations

import pytest
from slixmpp.xmlstream import ET

from pyobs.comm.xmpp.rpc import _NS, _PYOBS_NS, fault_to_xml, params_to_xml, xml_to_fault, xml_to_params
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
