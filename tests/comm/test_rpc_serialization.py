"""Tests for RPC parameter serialization/deserialization."""

from __future__ import annotations

import pytest
from slixmpp.xmlstream import ET

from pyobs.comm.xmpp.rpc import _NS, _PYOBS_NS, params_to_xml, xml_to_params


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
