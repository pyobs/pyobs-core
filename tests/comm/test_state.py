"""Tests for state serialization and deserialization in XMPP backend."""

from __future__ import annotations

import pytest

from pyobs.comm.xmpp.xmppcomm import XmppComm
from pyobs.interfaces import ICooling
from pyobs.interfaces.ICooling import CoolingState


class TestStateXmlSerialization:
    """Test XML serialization of state dataclasses."""

    def test_cooling_state_to_xml(self) -> None:
        """Test CoolingState → XML."""
        state = CoolingState(temperature=15.5, setpoint=20.0, power=75, enabled=True)
        namespace = f"urn:pyobs:state:{ICooling.__name__}:{ICooling.version}"
        xml = XmppComm._dataclass_to_xml(state, namespace)

        assert xml.tag == f"{{{namespace}}}state"
        assert len(xml) == 4  # 4 fields

        # Check field order and values
        children = {child.tag: child.text for child in xml}
        assert children["temperature"] == "15.5"
        assert children["setpoint"] == "20.0"
        assert children["power"] == "75"
        assert children["enabled"] == "true"

    def test_cooling_state_bool_true(self) -> None:
        """Test boolean True serialization."""
        state = CoolingState(temperature=10.0, setpoint=15.0, power=50, enabled=True)
        namespace = "urn:pyobs:state:ICooling:1"
        xml = XmppComm._dataclass_to_xml(state, namespace)

        enabled_elem = xml.find("enabled")
        assert enabled_elem is not None
        assert enabled_elem.text == "true"

    def test_cooling_state_bool_false(self) -> None:
        """Test boolean False serialization."""
        state = CoolingState(temperature=10.0, setpoint=15.0, power=50, enabled=False)
        namespace = "urn:pyobs:state:ICooling:1"
        xml = XmppComm._dataclass_to_xml(state, namespace)

        enabled_elem = xml.find("enabled")
        assert enabled_elem is not None
        assert enabled_elem.text == "false"

    def test_cooling_state_numeric_types(self) -> None:
        """Test that float and int are serialized as strings."""
        state = CoolingState(temperature=3.14159, setpoint=100, power=0, enabled=False)
        namespace = "urn:pyobs:state:ICooling:1"
        xml = XmppComm._dataclass_to_xml(state, namespace)

        temp = xml.find("temperature")
        setpoint = xml.find("setpoint")
        power = xml.find("power")

        assert temp is not None and temp.text == "3.14159"
        assert setpoint is not None and setpoint.text == "100"
        assert power is not None and power.text == "0"


class TestStateXmlDeserialization:
    """Test XML deserialization to state dataclasses."""

    def test_cooling_state_from_xml(self) -> None:
        """Test XML → CoolingState."""
        # Create XML the way it would arrive
        state_orig = CoolingState(temperature=15.5, setpoint=20.0, power=75, enabled=True)
        namespace = f"urn:pyobs:state:{ICooling.__name__}:{ICooling.version}"
        xml = XmppComm._dataclass_to_xml(state_orig, namespace)

        # Deserialize
        state = XmppComm._xml_to_dataclass(xml, CoolingState)

        assert isinstance(state, CoolingState)
        assert state.temperature == 15.5
        assert state.setpoint == 20.0
        assert state.power == 75
        assert state.enabled is True

    def test_cooling_state_bool_deserialization(self) -> None:
        """Test boolean deserialization from 'true'/'false' strings."""
        state_true = CoolingState(temperature=10.0, setpoint=15.0, power=50, enabled=True)
        state_false = CoolingState(temperature=10.0, setpoint=15.0, power=50, enabled=False)
        namespace = "urn:pyobs:state:ICooling:1"

        xml_true = XmppComm._dataclass_to_xml(state_true, namespace)
        xml_false = XmppComm._dataclass_to_xml(state_false, namespace)

        result_true = XmppComm._xml_to_dataclass(xml_true, CoolingState)
        result_false = XmppComm._xml_to_dataclass(xml_false, CoolingState)

        assert result_true.enabled is True
        assert result_false.enabled is False

    def test_cooling_state_numeric_deserialization(self) -> None:
        """Test that numeric strings are converted back to int/float."""
        state_orig = CoolingState(temperature=3.14, setpoint=25, power=100, enabled=True)
        namespace = "urn:pyobs:state:ICooling:1"
        xml = XmppComm._dataclass_to_xml(state_orig, namespace)

        state = XmppComm._xml_to_dataclass(xml, CoolingState)

        assert isinstance(state.temperature, float)
        assert isinstance(state.setpoint, float)  # setpoint is Annotated[float, ...]
        assert isinstance(state.power, int)
        assert state.temperature == 3.14
        assert state.setpoint == 25.0
        assert state.power == 100

    def test_cooling_state_missing_fields_raises(self) -> None:
        """Test that missing required fields raise TypeError (as expected without defaults)."""
        # Create minimal XML with only temperature
        import xml.etree.ElementTree as ET

        xml = ET.Element("state")
        ET.SubElement(xml, "temperature").text = "10.0"
        # Intentionally omit other required fields

        # Should fail since CoolingState has no defaults for setpoint, power, enabled
        with pytest.raises(TypeError, match="missing.*required positional arguments"):
            XmppComm._xml_to_dataclass(xml, CoolingState)


class TestStateRoundTrip:
    """Test round-trip serialization and deserialization."""

    def test_cooling_state_roundtrip_all_values(self) -> None:
        """Test CoolingState round-trip with various values."""
        original = CoolingState(temperature=18.7, setpoint=22.5, power=42, enabled=True)
        namespace = f"urn:pyobs:state:{ICooling.__name__}:{ICooling.version}"

        # Serialize
        xml = XmppComm._dataclass_to_xml(original, namespace)

        # Deserialize
        recovered = XmppComm._xml_to_dataclass(xml, CoolingState)

        # Verify
        assert recovered.temperature == original.temperature
        assert recovered.setpoint == original.setpoint
        assert recovered.power == original.power
        assert recovered.enabled == original.enabled

    def test_cooling_state_roundtrip_disabled(self) -> None:
        """Test round-trip with disabled cooling."""
        original = CoolingState(temperature=5.0, setpoint=0.0, power=0, enabled=False)
        namespace = "urn:pyobs:state:ICooling:1"

        xml = XmppComm._dataclass_to_xml(original, namespace)
        recovered = XmppComm._xml_to_dataclass(xml, CoolingState)

        assert recovered == original

    def test_cooling_state_roundtrip_edge_values(self) -> None:
        """Test round-trip with edge case numeric values."""
        original = CoolingState(temperature=-273.15, setpoint=0.0, power=100, enabled=True)
        namespace = "urn:pyobs:state:ICooling:1"

        xml = XmppComm._dataclass_to_xml(original, namespace)
        recovered = XmppComm._xml_to_dataclass(xml, CoolingState)

        assert recovered.temperature == -273.15
        assert recovered.setpoint == 0.0
        assert recovered.power == 100
        assert recovered.enabled is True


class TestStateNamespaceAndNode:
    """Test state namespace and node generation helpers."""

    def test_state_namespace_generation(self) -> None:
        """Test _state_namespace generates correct namespace."""
        namespace = XmppComm._state_namespace(ICooling)
        assert namespace == f"urn:pyobs:state:ICooling:{ICooling.version}"

    def test_state_node_generation(self) -> None:
        """Test _state_node generates correct node path."""
        node = XmppComm._state_node("camera_module", ICooling)
        assert node == f"pyobs:state:camera_module:ICooling:{ICooling.version}"

    def test_state_node_with_special_module_name(self) -> None:
        """Test _state_node with module names containing underscores/hyphens."""
        node = XmppComm._state_node("my-camera_01", ICooling)
        assert "my-camera_01" in node
        assert "ICooling" in node


__all__ = [
    "TestStateXmlSerialization",
    "TestStateXmlDeserialization",
    "TestStateRoundTrip",
    "TestStateNamespaceAndNode",
]
