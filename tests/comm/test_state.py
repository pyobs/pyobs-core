"""Tests for state serialization and deserialization."""

from __future__ import annotations

import dataclasses

import pytest
from slixmpp.xmlstream import ET

from pyobs.comm.xmpp.serializer import (
    _dataclass_to_xml,
    _xml_to_dataclass,
    value_to_xml,
)
from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import BinningState, CoolingState, IBinning, ICooling

NS = f"urn:pyobs:state:ICooling:{ICooling.version}"


class TestDataclassToXml:
    """Test _dataclass_to_xml serialization."""

    def test_root_element_namespace(self) -> None:
        state = CoolingState(setpoint=-20.0, power=65, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        assert xml.tag == f"{{{NS}}}state"

    def test_field_count(self) -> None:
        state = CoolingState(setpoint=-20.0, power=65, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        # One child per dataclass field (setpoint, power, enabled + time)
        assert len(xml) == len(dataclasses.fields(CoolingState))

    def test_bool_true_serialized_as_boolean_element(self) -> None:
        state = CoolingState(setpoint=0.0, power=0, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        enabled_elem = xml.find("enabled")
        assert enabled_elem is not None
        boolean_elem = list(enabled_elem)[0]
        assert boolean_elem.tag.split("}")[-1] == "boolean"
        assert boolean_elem.text == "true"

    def test_bool_false_serialized_as_boolean_element(self) -> None:
        state = CoolingState(setpoint=0.0, power=0, enabled=False)
        xml = _dataclass_to_xml(state, NS)
        enabled_elem = xml.find("enabled")
        assert enabled_elem is not None
        boolean_elem = list(enabled_elem)[0]
        assert boolean_elem.text == "false"

    def test_float_serialized_as_double_element(self) -> None:
        state = CoolingState(setpoint=-25.5, power=0, enabled=False)
        xml = _dataclass_to_xml(state, NS)
        setpoint_elem = xml.find("setpoint")
        assert setpoint_elem is not None
        double_elem = list(setpoint_elem)[0]
        assert double_elem.tag.split("}")[-1] == "double"
        assert float(double_elem.text) == pytest.approx(-25.5)

    def test_int_serialized_as_int_element(self) -> None:
        state = CoolingState(setpoint=0.0, power=75, enabled=False)
        xml = _dataclass_to_xml(state, NS)
        power_elem = xml.find("power")
        assert power_elem is not None
        int_elem = list(power_elem)[0]
        assert int_elem.tag.split("}")[-1] == "int"
        assert int(int_elem.text) == 75


class TestXmlToDataclass:
    """Test _xml_to_dataclass deserialization."""

    def test_basic_roundtrip(self) -> None:
        state = CoolingState(setpoint=-20.0, power=65, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        result = _xml_to_dataclass(xml, CoolingState)
        assert isinstance(result, CoolingState)
        assert result.setpoint == pytest.approx(-20.0)
        assert result.power == 65
        assert result.enabled is True

    def test_bool_false_roundtrip(self) -> None:
        state = CoolingState(setpoint=0.0, power=0, enabled=False)
        xml = _dataclass_to_xml(state, NS)
        result = _xml_to_dataclass(xml, CoolingState)
        assert result.enabled is False

    def test_correct_types_after_roundtrip(self) -> None:
        state = CoolingState(setpoint=25.0, power=100, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        result = _xml_to_dataclass(xml, CoolingState)
        assert isinstance(result.setpoint, float)
        assert isinstance(result.power, int)
        assert isinstance(result.enabled, bool)

    def test_missing_required_field_raises(self) -> None:
        xml = ET.Element(f"{{{NS}}}state")
        child = ET.Element("setpoint")
        child.append(value_to_xml(-10.0, float))
        xml.append(child)
        # power and enabled missing — should raise TypeError
        with pytest.raises(TypeError, match="missing.*required positional argument"):
            _xml_to_dataclass(xml, CoolingState)

    def test_namespaced_children_deserialized(self) -> None:
        """ejabberd re-serializes children with parent namespace — must still deserialize."""
        state = CoolingState(setpoint=-30.0, power=80, enabled=True)
        xml = _dataclass_to_xml(state, NS)
        # Simulate ejabberd namespace inheritance on vocabulary elements
        raw = ET.tostring(xml).decode()
        raw = raw.replace("<double>", f'<double xmlns="{NS}">')
        raw = raw.replace("<int>", f'<int xmlns="{NS}">')
        raw = raw.replace("<boolean>", f'<boolean xmlns="{NS}">')
        reparsed = ET.fromstring(raw)
        result = _xml_to_dataclass(reparsed, CoolingState)
        assert result.setpoint == pytest.approx(-30.0)
        assert result.power == 80
        assert result.enabled is True


class TestStateRoundTrip:
    """End-to-end serialization round-trips."""

    def test_cooling_state_roundtrip(self) -> None:
        original = CoolingState(setpoint=22.5, power=42, enabled=True)
        xml = _dataclass_to_xml(original, NS)
        recovered = _xml_to_dataclass(xml, CoolingState)
        assert recovered.setpoint == pytest.approx(original.setpoint)
        assert recovered.power == original.power
        assert recovered.enabled == original.enabled

    def test_cooling_state_roundtrip_disabled(self) -> None:
        original = CoolingState(setpoint=0.0, power=0, enabled=False)
        xml = _dataclass_to_xml(original, NS)
        recovered = _xml_to_dataclass(xml, CoolingState)
        assert recovered.setpoint == pytest.approx(0.0)
        assert recovered.power == 0
        assert recovered.enabled is False

    def test_binning_state_roundtrip(self) -> None:
        ns = f"urn:pyobs:state:IBinning:{IBinning.version}"
        original = BinningState(x=2, y=4)
        xml = _dataclass_to_xml(original, ns)
        recovered = _xml_to_dataclass(xml, BinningState)
        assert recovered.x == 2
        assert recovered.y == 4


class TestStateNamespaceAndNode:
    """Test namespace and node name generation helpers."""

    def test_state_namespace(self) -> None:
        assert XmppComm._state_namespace(ICooling) == f"urn:pyobs:state:ICooling:{ICooling.version}"

    def test_state_node(self) -> None:
        node = XmppComm._state_node("camera", ICooling)
        assert node == f"pyobs:state:camera:ICooling:{ICooling.version}"

    def test_state_node_special_chars(self) -> None:
        node = XmppComm._state_node("my-camera_01", ICooling)
        assert "my-camera_01" in node
        assert "ICooling" in node
