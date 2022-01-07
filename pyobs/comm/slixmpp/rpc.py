import copy
import inspect
import logging
from threading import RLock
from typing import Dict, Optional, Any, Callable, Tuple
import slixmpp
import slixmpp.exceptions

from pyobs.modules import Module
from pyobs.comm.exceptions import *
from pyobs.utils.parallel import Future
from pyobs.comm.slixmpp.xep_0009.binding import fault2xml, xml2fault, xml2py, py2xml

log = logging.getLogger(__name__)


class RPC(object):
    """RPC wrapper around XEP0009."""

    def __init__(self, client: slixmpp.ClientXMPP, handler: Optional[Module] = None):
        """Create a new RPC wrapper.

        Args:
            client: XMPP client tu use for communication.
            handler: pyobs module that handles function calls.
        """

        # store
        self._client = client
        self._lock = RLock()
        self._futures: Dict[str, Future] = {}
        self._handler = handler
        self._methods: Dict[str, Tuple[Callable[[], Any], inspect.Signature]] = {}

        # set up callbacks
        client.add_event_handler("jabber_rpc_method_call", self._on_jabber_rpc_method_call)
        client.add_event_handler("jabber_rpc_method_timeout", self._on_jabber_rpc_method_timeout)
        client.add_event_handler("jabber_rpc_method_response", self._on_jabber_rpc_method_response)
        client.add_event_handler("jabber_rpc_method_fault", self._on_jabber_rpc_method_fault)
        client.add_event_handler("jabber_rpc_error", self._on_jabber_rpc_error)

        # register handler
        self.set_handler(handler)

    def set_handler(self, handler: Optional[Module] = None) -> None:
        """Set the handler for remote procedure calls to this client.

        Args:
            handler: Handler object.
        """

        # store handler
        self._handler = handler

        # update methods
        self._methods = copy.copy(handler.methods) if handler else {}

    async def call(self, target_jid: str, method: str, signature: inspect.Signature, *args: Any) -> Any:
        """Call a method on a remote host.

        Args:
            target_jid: Target JID to call method on.
            method: Name of method to call.
            signature: Method signature.
            *args: Parameters for method.

        Returns:
            Future for response.
        """

        # create the method call
        iq = self._client.plugin["xep_0009"].make_iq_method_call(target_jid, method, py2xml(*args))

        # create a future for this
        pid = iq["id"]
        future = Future(signature=signature)
        self._futures[pid] = future

        # send request
        try:
            await iq.send()
        except slixmpp.exceptions.IqError:
            raise RemoteException("Could not send command.")
        except slixmpp.exceptions.IqTimeout:
            raise TimeoutException()

        # don't wait for response, just return future
        return await future

    async def _on_jabber_rpc_method_call(self, iq: Any) -> None:
        """React on remote method call.

        Args:
            iq: Received XMPP message.
        """

        # get method and parameters
        iq.enable("rpc_query")
        params = xml2py(iq["rpc_query"]["method_call"]["params"])
        pmethod = iq["rpc_query"]["method_call"]["method_name"]

        try:
            # no handler?
            if self._handler is None:
                return
                # raise ValueError('No handler specified.')

            # get method
            with self._lock:
                try:
                    method, signature = self._methods[pmethod]
                except KeyError:
                    log.error("No handler available for %s!", pmethod)
                    self._client.plugin["xep_0009"].item_not_found(iq).send()
                    return

            # bind parameters
            ba = signature.bind(*params)
            ba.apply_defaults()

            # do we have a timeout?
            if hasattr(method, "timeout"):
                timeout = await getattr(method, "timeout")(self._handler, **ba.arguments)
                if timeout:
                    # yes, send it!
                    response = self._client.plugin["xep_0009_timeout"].make_iq_method_timeout(
                        iq["id"], iq["from"], int(timeout)
                    )
                    response.send()

            # call method
            return_value = await self._handler.execute(pmethod, *params, sender=iq["from"].user)
            return_value = () if return_value is None else (return_value,)

            # send response
            self._client.plugin["xep_0009"].make_iq_method_response(iq["id"], iq["from"], py2xml(*return_value)).send()

        except InvocationException as ie:
            # could not invoke method
            self._client.plugin["xep_0009"].send_fault(iq, fault2xml(500, ie.get_message()))

        except Exception as e:
            # something else went wrong
            log.warning("Error during call to %s: %s", pmethod, str(e), exc_info=True)

            # send response
            self._client.plugin["xep_0009"].send_fault(iq, fault2xml(500, str(e)))

    async def _on_jabber_rpc_method_response(self, iq: Any) -> None:
        """Received a response for a method call.

        Args:
            iq: Received XMPP message.
        """

        # get message
        iq.enable("rpc_query")
        try:
            args = xml2py(iq["rpc_query"]["method_response"]["params"])
        except ValueError:
            log.error("Could not parse method response: %s", iq)
            return

        # get future
        pid = iq["id"]
        with self._lock:
            if pid not in self._futures:
                return
            future = self._futures[pid]
            del self._futures[pid]

        # set result of future, if it's not set already (probably with an exception)
        if not future.done():
            if len(args) > 0:
                future.set_result(args[0])
            else:
                future.set_result(None)

    async def _on_jabber_rpc_method_timeout(self, iq: Any) -> None:
        """Method call timed out.

        Args:
            iq: Received XMPP message.
        """
        iq.enable("rpc_query")
        timeout = iq["rpc_query"]["method_timeout"]["timeout"]
        pid = iq["id"]
        self._futures[pid].set_timeout(timeout)

    async def _on_jabber_rpc_method_fault(self, iq: Any) -> None:
        """Communication to host failed.

        Args:
            iq: Received XMPP message.
        """

        # get message
        iq.enable("rpc_query")
        fault = xml2fault(iq["rpc_query"]["method_response"]["fault"])

        # get future
        pid = iq["id"]
        with self._lock:
            future = self._futures[pid]
            del self._futures[pid]

        # set error
        if not future.done():
            future.set_exception(InvocationException(fault["string"]))

    async def _on_jabber_rpc_error(self, iq: Any) -> None:
        """Method invocation failes.

        Args:
            iq: Received XMPP message.
        """

        # get message
        pmethod = self._client.plugin["xep_0009"].extract_method(iq["rpc_query"])
        condition = iq["error"]["condition"]

        # get future
        pid = iq["id"]
        with self._lock:
            callback = self._futures[pid]
            del self._futures[pid]

        # set error
        e = {
            "item-not-found": RemoteException("No remote handler available for %s at %s!" % (pmethod, iq["from"])),
            "forbidden": AuthorizationException(
                "Forbidden to invoke remote handler for %s at %s!" % (pmethod, iq["from"])
            ),
            "undefined-condition": RemoteException(
                "An unexpected problem occured trying to invoke %s at %s!" % (pmethod, iq["from"])
            ),
            "service-unavailable": RemoteException("The service at %s is unavailable." % iq["from"]),
            "remote-server-not-found": RemoteException("Could not find remote server for %s." % iq["from"]),
        }[condition]
        if e is None:
            RemoteException("An unexpected exception occurred at %s!" % iq["from"])
        callback.set_exception(e)


__all__ = ["RPC"]
