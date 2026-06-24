from __future__ import annotations

import copy
import dataclasses
import inspect
import logging
from collections.abc import Callable
from enum import StrEnum
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin

import slixmpp
import slixmpp.exceptions
from slixmpp.xmlstream import ET

import pyobs.utils.exceptions as exc
from pyobs.modules import Module
from pyobs.utils.parallel import Future

if TYPE_CHECKING:
    from .xmppcomm import XmppComm

log = logging.getLogger(__name__)

_NS = "jabber:iq:rpc"
_PYOBS_NS = "urn:pyobs:rpc:1"


# ---------------------------------------------------------------------------
# Serializer — params ↔ XML
# ---------------------------------------------------------------------------


def _value_to_xml(value: Any, type_hint: Any) -> ET.Element:
    """Serialize a single value to a <pyobs:value> element."""
    pyobs_value = ET.Element(f"{{{_PYOBS_NS}}}value")

    # Unwrap Annotated[T, ...]
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]

    # None / void
    if value is None:
        return pyobs_value  # empty element

    # bool (before int — bool is subclass of int)
    if isinstance(value, bool):
        child = ET.Element("boolean")
        child.text = "true" if value else "false"
        pyobs_value.append(child)

    # int
    elif isinstance(value, int):
        child = ET.Element("int")
        child.text = str(value)
        pyobs_value.append(child)

    # float
    elif isinstance(value, float):
        child = ET.Element("double")
        child.text = repr(value)
        pyobs_value.append(child)

    # str
    elif isinstance(value, str):
        child = ET.Element("string")
        child.text = value
        pyobs_value.append(child)

    # StrEnum
    elif isinstance(value, StrEnum):
        child = ET.Element("string")
        child.text = value.value
        pyobs_value.append(child)

    # dataclass (State objects, etc.)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        # Use _dataclass_to_xml with the pyobs:rpc namespace
        from .xmppcomm import XmppComm

        dc_elem = XmppComm._dataclass_to_xml(value, _PYOBS_NS)
        pyobs_value.append(dc_elem)

    # list
    elif isinstance(value, list):
        items_elem = ET.Element("items")
        item_type = get_args(type_hint)[0] if type_hint and get_origin(type_hint) is list else Any
        for item in value:
            item_elem = ET.Element("item")
            item_elem.append(_value_to_xml(item, item_type))
            items_elem.append(item_elem)
        pyobs_value.append(items_elem)

    # tuple
    elif isinstance(value, tuple):
        tuple_elem = ET.Element("tuple")
        item_types = get_args(type_hint) if type_hint and get_origin(type_hint) is tuple else []
        for i, item in enumerate(value):
            item_type = item_types[i] if i < len(item_types) else Any
            item_elem = ET.Element("item")
            item_elem.append(_value_to_xml(item, item_type))
            tuple_elem.append(item_elem)
        pyobs_value.append(tuple_elem)

    # dict
    elif isinstance(value, dict):
        dict_elem = ET.Element("dict")
        key_type, val_type = get_args(type_hint)[:2] if type_hint and get_origin(type_hint) is dict else (Any, Any)
        for k, v in value.items():
            entry = ET.Element("entry")
            key_elem = ET.Element("key")
            key_elem.append(_value_to_xml(k, key_type))
            val_elem = ET.Element("val")
            val_elem.append(_value_to_xml(v, val_type))
            entry.append(key_elem)
            entry.append(val_elem)
            dict_elem.append(entry)
        pyobs_value.append(dict_elem)

    else:
        # fallback: stringify
        child = ET.Element("string")
        child.text = str(value)
        pyobs_value.append(child)

    return pyobs_value


def _xml_to_value(pyobs_value: ET.Element, type_hint: Any) -> Any:
    """Deserialize a <pyobs:value> element to a Python value."""
    # Unwrap Annotated[T, ...]
    if get_origin(type_hint) is Annotated:
        type_hint = get_args(type_hint)[0]

    # Unwrap Optional[T] → T
    if get_origin(type_hint) is type(None):
        return None
    args = get_args(type_hint)
    if type(None) in args:
        non_none = [a for a in args if a is not type(None)]
        type_hint = non_none[0] if non_none else Any

    children = list(pyobs_value)
    if not children:
        return None  # void / None

    child = children[0]
    # Strip namespace if present — ejabberd re-serializes plain child elements
    # with the parent's namespace (e.g. <double> becomes <{urn:pyobs:rpc:1}double>)
    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

    if tag == "boolean":
        return child.text == "true"

    elif tag == "int":
        return int(child.text)

    elif tag == "double":
        return float(child.text)

    elif tag == "string":
        text = child.text or ""
        # try to cast to enum if type_hint is an enum
        if type_hint and inspect.isclass(type_hint) and issubclass(type_hint, StrEnum):
            return type_hint(text)
        return text

    elif tag == "items":
        item_type = get_args(type_hint)[0] if type_hint and get_origin(type_hint) is list else Any
        result = []
        for item_elem in child.findall("item"):
            pv = list(item_elem)[0] if list(item_elem) else item_elem
            result.append(_xml_to_value(pv, item_type))
        return result

    elif tag == "tuple":
        item_types = get_args(type_hint) if type_hint and get_origin(type_hint) is tuple else []
        result = []
        for i, item_elem in enumerate(child.findall("item")):
            item_type = item_types[i] if i < len(item_types) else Any
            pv = list(item_elem)[0] if list(item_elem) else item_elem
            result.append(_xml_to_value(pv, item_type))
        return tuple(result)

    elif tag == "dict":
        key_type, val_type = get_args(type_hint)[:2] if type_hint and get_origin(type_hint) is dict else (Any, Any)
        result = {}
        for entry in child.findall("entry"):
            key_pv = list(entry.find("key"))[0]
            val_pv = list(entry.find("val"))[0]
            k = _xml_to_value(key_pv, key_type)
            v = _xml_to_value(val_pv, val_type)
            result[k] = v
        return result

    else:
        # dataclass / State — child is a <{ns}state> or similar element
        from .xmppcomm import XmppComm

        if type_hint and dataclasses.is_dataclass(type_hint):
            return XmppComm._xml_to_dataclass(child, type_hint)
        return child.text


def params_to_xml(names: list[str], values: list[Any], types: dict[str, Any]) -> ET.Element:
    """Serialize a parameter list to <params><param><value><pyobs:value>...</pyobs:value></value></param></params>."""
    params = ET.Element(f"{{{_NS}}}params")
    for name, value in zip(names, values):
        type_hint = types.get(name, Any)
        param = ET.Element(f"{{{_NS}}}param")
        value_elem = ET.Element(f"{{{_NS}}}value")
        value_elem.append(_value_to_xml(value, type_hint))
        param.append(value_elem)
        params.append(param)
    return params


def xml_to_params(params_elem: ET.Element, names: list[str], types: dict[str, Any]) -> list[Any]:
    """Deserialize <params> to a list of Python values."""
    result = []
    param_elems = params_elem.findall(f"{{{_NS}}}param")
    for name, param_elem in zip(names, param_elems):
        type_hint = types.get(name, Any)
        value_elem = param_elem.find(f"{{{_NS}}}value")
        if value_elem is None:
            result.append(None)
            continue
        pyobs_value = value_elem.find(f"{{{_PYOBS_NS}}}value")
        if pyobs_value is None:
            result.append(None)
            continue
        result.append(_xml_to_value(pyobs_value, type_hint))
    return result


def return_to_xml(value: Any, type_hint: Any) -> ET.Element:
    """Serialize a return value to <params><param><value><pyobs:value>...</pyobs:value></value></param></params>."""
    params = ET.Element(f"{{{_NS}}}params")
    if value is None or type_hint is type(None):
        return params  # void return: empty <params/>
    param = ET.Element(f"{{{_NS}}}param")
    value_elem = ET.Element(f"{{{_NS}}}value")
    value_elem.append(_value_to_xml(value, type_hint))
    param.append(value_elem)
    params.append(param)
    return params


def xml_to_return(params_elem: ET.Element, type_hint: Any) -> Any:
    """Deserialize <params> for a return value."""
    param_elems = params_elem.findall(f"{{{_NS}}}param")
    if not param_elems:
        return None
    value_elem = param_elems[0].find(f"{{{_NS}}}value")
    if value_elem is None:
        return None
    pyobs_value = value_elem.find(f"{{{_PYOBS_NS}}}value")
    if pyobs_value is None:
        return None
    return _xml_to_value(pyobs_value, type_hint)


def fault_to_xml(exception: Exception) -> ET.Element:
    """Serialize an exception to <fault><value><pyobs:fault>...</pyobs:fault></value></fault>."""
    fault = ET.Element(f"{{{_NS}}}fault")
    value_elem = ET.Element(f"{{{_NS}}}value")
    pyobs_fault = ET.Element(f"{{{_PYOBS_NS}}}fault")
    exc_elem = ET.Element("exception")
    exc_elem.text = type(exception).__name__
    msg_elem = ET.Element("message")
    msg_elem.text = str(exception)
    pyobs_fault.append(exc_elem)
    pyobs_fault.append(msg_elem)
    value_elem.append(pyobs_fault)
    fault.append(value_elem)
    return fault


def xml_to_fault(fault_elem: ET.Element) -> tuple[str, str]:
    """Parse <fault> and return (exception_class_name, message)."""
    value_elem = fault_elem.find(f"{{{_NS}}}value")
    if value_elem is None:
        return "RemoteError", "Unknown error"
    pyobs_fault = value_elem.find(f"{{{_PYOBS_NS}}}fault")
    if pyobs_fault is None:
        return "RemoteError", "Unknown error"
    exc_el = pyobs_fault.find("exception")
    msg_el = pyobs_fault.find("message")
    exc_name = exc_el.text if exc_el is not None else "RemoteError"
    msg = msg_el.text if msg_el is not None else ""
    return exc_name, msg


# ---------------------------------------------------------------------------
# RPC class
# ---------------------------------------------------------------------------


class RPC:
    """RPC wrapper around XEP-0009 using pyobs 2.0 payload encoding (urn:pyobs:rpc:1)."""

    def __init__(self, comm: XmppComm, client: slixmpp.ClientXMPP, handler: Module | None = None):
        self._comm = comm
        self._client = client
        self._futures: dict[str, Future] = {}
        self._handler = handler
        self._methods: dict[str, tuple[Callable[..., Any], inspect.Signature, dict[Any, Any]]] = {}

        client.add_event_handler("jabber_rpc_method_call", self._on_jabber_rpc_method_call)
        client.add_event_handler("jabber_rpc_method_timeout", self._on_jabber_rpc_method_timeout)
        client.add_event_handler("jabber_rpc_method_response", self._on_jabber_rpc_method_response)
        client.add_event_handler("jabber_rpc_method_fault", self._on_jabber_rpc_method_fault)
        client.add_event_handler("jabber_rpc_error", self._on_jabber_rpc_error)

        self.set_handler(handler)

    def set_handler(self, handler: Module | None = None) -> None:
        self._handler = handler
        self._methods = copy.copy(handler.methods) if handler else {}

    async def call(self, target_jid: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        # Build param names and types from annotation (skip 'return' and 'kwargs')
        param_names = [k for k in annotation if k not in ("return", "kwargs")]
        param_types = {k: annotation[k] for k in param_names}

        iq = self._client.plugin["xep_0009"].make_iq_method_call(
            target_jid, method, params_to_xml(param_names, list(args), param_types)
        )

        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        future = Future(annotation=annotation, comm=self._comm)
        self._futures[jid] = future

        await iq.send()
        return await future

    async def _on_jabber_rpc_method_call(self, iq: Any) -> None:
        iq.enable("rpc_query")
        pmethod = iq["rpc_query"]["method_call"]["method_name"]

        try:
            if self._handler is None:
                return

            try:
                method, signature, hints = self._methods[pmethod]
            except KeyError:
                log.error("No handler available for %s!", pmethod)
                self._client.plugin["xep_0009"].item_not_found(iq).send()
                return

            # Extract param names and types (skip self, **kwargs)
            param_names = []
            param_types = {}
            for p_name, p in signature.parameters.items():
                if p_name in ("self", "kwargs"):
                    continue
                param_names.append(p_name)
                param_types[p_name] = hints.get(p_name, Any)

            # Deserialize parameters from XML
            raw_params_xml = iq["rpc_query"]["method_call"]["params"]
            params = xml_to_params(raw_params_xml, param_names, param_types)

            # Bind parameters
            ba = signature.bind(*params)
            ba.apply_defaults()

            # Handle timeout
            if hasattr(method, "timeout"):
                timeout = await getattr(method, "timeout")(self._handler, **ba.arguments)
                if timeout:
                    response = self._client.plugin["xep_0009_timeout"].make_iq_method_timeout(
                        iq["id"], iq["from"], int(timeout)
                    )
                    response.send()

            # Call method
            return_value = await self._handler.execute(pmethod, *params, sender=iq["from"].user)

            # Serialize return value
            return_type = hints.get("return", type(None))
            response_params = return_to_xml(return_value, return_type)
            self._client.plugin["xep_0009"].make_iq_method_response(iq["id"], iq["from"], response_params).send()

        except Exception as e:
            if isinstance(e, exc.PyObsError):
                e.log(log, "ERROR", f"Exception in call to {pmethod}: {e}", exc_info=True)
            else:
                log.exception("Unexpected exception in %s.", pmethod)
            self._client.plugin["xep_0009"].send_fault(iq, fault_to_xml(e))

    async def _on_jabber_rpc_method_response(self, iq: Any) -> None:
        iq.enable("rpc_query")

        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        if jid not in self._futures:
            return
        future = self._futures.pop(jid)

        if future.done():
            return

        try:
            raw_params_xml = iq["rpc_query"]["method_response"]["params"]
            return_type = future.annotation.get("return", type(None)) if future.annotation else type(None)
            result = xml_to_return(raw_params_xml, return_type)
            future.set_result(result)
        except Exception as e:
            log.error("Could not parse method response: %s", e)
            future.set_result(None)

    async def _on_jabber_rpc_method_timeout(self, iq: Any) -> None:
        iq.enable("rpc_query")
        timeout = iq["rpc_query"]["method_timeout"]["timeout"]
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        self._futures[jid].set_timeout(timeout)

    async def _on_jabber_rpc_method_fault(self, iq: Any) -> None:
        iq.enable("rpc_query")

        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        if jid not in self._futures:
            return
        future = self._futures.pop(jid)

        fault_elem = iq["rpc_query"]["method_response"]["fault"]
        exc_name, msg = xml_to_fault(fault_elem)

        exception_class = getattr(exc, exc_name, None)
        if exception_class is None or not issubclass(exception_class, Exception):
            exception_class = exc.RemoteError

        sender = iq["from"].node
        if issubclass(exception_class, exc.RemoteError):
            exception = exception_class(message=msg, module=sender)
        else:
            exception = exception_class(message=msg)

        if not future.done():
            future.set_exception(exc.InvocationError(module=sender, exception=exception))

    async def _on_jabber_rpc_error(self, iq: Any) -> None:
        pmethod = self._client.plugin["xep_0009"].extract_method(iq["rpc_query"])
        condition = iq["error"]["condition"]

        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        if jid not in self._futures:
            return
        callback = self._futures.pop(jid)

        sender = iq["from"].node
        e = {
            "item-not-found": exc.RemoteError(sender, f"No remote handler for {pmethod} at {iq['from']}!"),
            "forbidden": exc.RemoteError(sender, f"Forbidden to invoke {pmethod} at {iq['from']}!"),
            "undefined-condition": exc.RemoteError(sender, f"Unexpected problem invoking {pmethod} at {iq['from']}!"),
            "service-unavailable": exc.RemoteError(sender, f"Service at {iq['from']} is unavailable."),
            "remote-server-not-found": exc.RemoteError(sender, f"Could not find remote server for {iq['from']}."),
        }.get(condition, exc.RemoteError(sender, f"Unexpected exception at {iq['from']}!"))

        callback.set_exception(e)


__all__ = ["RPC"]
