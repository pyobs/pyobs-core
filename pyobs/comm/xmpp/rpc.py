from __future__ import annotations

import copy
import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import slixmpp
import slixmpp.exceptions
from slixmpp.xmlstream import ET

import pyobs.utils.exceptions as exc
from pyobs.modules import Module
from pyobs.utils.parallel import Future

from .serializer import PYOBS_NS as _PYOBS_NS
from .serializer import value_to_xml, xml_to_value

if TYPE_CHECKING:
    from .xmppcomm import XmppComm

log = logging.getLogger(__name__)

_NS = "jabber:iq:rpc"


def params_to_xml(names: list[str], values: list[Any], types: dict[str, Any]) -> ET.Element:
    """Serialize a parameter list to <params><param><value><pyobs:value>...</pyobs:value></value></param></params>."""
    params = ET.Element(f"{{{_NS}}}params")
    for name, value in zip(names, values):
        type_hint = types.get(name, Any)
        param = ET.Element(f"{{{_NS}}}param")
        value_elem = ET.Element(f"{{{_NS}}}value")
        pyobs_value = ET.Element(f"{{{_PYOBS_NS}}}value")
        pyobs_value.append(value_to_xml(value, type_hint))
        value_elem.append(pyobs_value)
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
            raise ValueError(f"Malformed RPC param '{name}': missing <value> element.")
        pyobs_value = value_elem.find(f"{{{_PYOBS_NS}}}value")
        if pyobs_value is None:
            raise ValueError(
                f"Malformed RPC param '{name}': missing <value> element in namespace '{_PYOBS_NS}' "
                f"(sender may have serialized it without the required xmlns)."
            )
        children = list(pyobs_value)
        result.append(xml_to_value(children[0], type_hint) if children else None)
    return result


def return_to_xml(value: Any, type_hint: Any) -> ET.Element:
    """Serialize a return value to <params><param><value><pyobs:value>...</pyobs:value></value></param></params>."""
    params = ET.Element(f"{{{_NS}}}params")
    if value is None or type_hint is type(None):
        return params  # void return: empty <params/>
    param = ET.Element(f"{{{_NS}}}param")
    value_elem = ET.Element(f"{{{_NS}}}value")
    pyobs_value = ET.Element(f"{{{_PYOBS_NS}}}value")
    pyobs_value.append(value_to_xml(value, type_hint))
    value_elem.append(pyobs_value)
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
    children = list(pyobs_value)
    return xml_to_value(children[0], type_hint) if children else None


def fault_to_xml(exception: Exception) -> ET.Element:
    """Serialize an exception to <fault><value><pyobs:fault>...</pyobs:fault></value></fault>."""
    fault = ET.Element(f"{{{_NS}}}fault")
    value_elem = ET.Element(f"{{{_NS}}}value")
    pyobs_fault = ET.Element(f"{{{_PYOBS_NS}}}fault")
    exc_elem = ET.Element("exception")
    # fully-qualified name, not the bare class name -- domain exceptions can live anywhere,
    # not just in pyobs.utils.exceptions (see PyobsError._registry / resolve())
    exc_elem.text = f"{type(exception).__module__}.{type(exception).__qualname__}"
    msg_elem = ET.Element("message")
    msg_elem.text = str(exception)
    pyobs_fault.append(exc_elem)
    pyobs_fault.append(msg_elem)
    value_elem.append(pyobs_fault)
    fault.append(value_elem)
    return fault


def xml_to_fault(fault_elem: ET.Element) -> tuple[str, str]:
    """Parse <fault> and return (exception_qualified_name, message)."""
    _fallback_name = f"{exc.RemoteError.__module__}.{exc.RemoteError.__qualname__}"
    value_elem = fault_elem.find(f"{{{_NS}}}value")
    if value_elem is None:
        return _fallback_name, "Unknown error"
    pyobs_fault = value_elem.find(f"{{{_PYOBS_NS}}}fault")
    if pyobs_fault is None:
        return _fallback_name, "Unknown error"
    exc_el = pyobs_fault.find("exception")
    msg_el = pyobs_fault.find("message")
    exc_name = (exc_el.text if exc_el is not None else None) or _fallback_name
    msg = (msg_el.text if msg_el is not None else None) or ""
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
        future = Future(annotation=annotation)
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
                    response = self._client.plugin["xep_0009_timeout"].make_iq_method_timeout(  # type: ignore[typeddict-item]
                        iq["id"], iq["from"], int(timeout)
                    )
                    response.send()

            # Call method
            return_value = await self._handler.execute(pmethod, *params, sender=iq["from"].user)

            # Serialize return value
            return_type = hints.get("return", type(None))
            response_params = return_to_xml(return_value, return_type)
            self._client.plugin["xep_0009"].make_iq_method_response(iq["id"], iq["from"], response_params).send()

        except exc.ForbiddenError as e:
            e.log(log, "WARNING", f"Forbidden call to {pmethod}: {e}")
            self._client.plugin["xep_0009"].forbidden(iq).send()

        except Exception as e:
            if isinstance(e, exc.PyobsError):
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

        sender = iq["from"].node
        exception_class = exc.PyobsError.resolve(exc_name)
        if exception_class is not None:
            # real registered type (e.g. FocusError) -- raised as itself, not wrapped
            exception: exc.PyobsError = exception_class(msg, remote_module=sender)
        else:
            # unresolvable: never a PyobsError to begin with, or its defining module was never
            # imported in this process -- the qualified name string still survives as original_type
            exception = exc.UnclassifiedError(msg, original_type=exc_name, remote_module=sender)

        if not future.done():
            future.set_exception(exception)

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
            "item-not-found": exc.RemoteError(f"No remote handler for {pmethod} at {iq['from']}!", module=sender),
            "forbidden": exc.RemoteError(f"Forbidden to invoke {pmethod} at {iq['from']}!", module=sender),
            "undefined-condition": exc.RemoteError(
                f"Unexpected problem invoking {pmethod} at {iq['from']}!", module=sender
            ),
            "service-unavailable": exc.RemoteError(f"Service at {iq['from']} is unavailable.", module=sender),
            "remote-server-not-found": exc.RemoteError(
                f"Could not find remote server for {iq['from']}.", module=sender
            ),
        }.get(condition, exc.RemoteError(f"Unexpected exception at {iq['from']}!", module=sender))

        callback.set_exception(e)


__all__ = ["RPC"]
