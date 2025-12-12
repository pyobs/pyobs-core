from __future__ import annotations
import copy
import inspect
import logging
from typing import Any, Callable, TYPE_CHECKING
import slixmpp
import slixmpp.exceptions

from pyobs.modules import Module
from pyobs.utils.parallel import Future
from pyobs.comm.xmpp.xep_0009.binding import fault2xml, xml2fault, xml2py, py2xml
import pyobs.utils.exceptions as exc

if TYPE_CHECKING:
    from .xmppcomm import XmppComm


log = logging.getLogger(__name__)


class RPC(object):
    """RPC wrapper around XEP0009."""

    def __init__(self, comm: XmppComm, client: slixmpp.ClientXMPP, handler: Module | None = None):
        """Create a new RPC wrapper.

        Args:
            client: XMPP client tu use for communication.
            handler: pyobs module that handles function calls.
        """

        # store
        self._comm = comm
        self._client = client
        self._futures: dict[str, Future] = {}
        self._handler = handler
        self._methods: dict[str, tuple[Callable[..., Any], inspect.Signature, dict[Any, Any]]] = {}

        # set up callbacks
        client.add_event_handler("jabber_rpc_method_call", self._on_jabber_rpc_method_call)
        client.add_event_handler("jabber_rpc_method_timeout", self._on_jabber_rpc_method_timeout)
        client.add_event_handler("jabber_rpc_method_response", self._on_jabber_rpc_method_response)
        client.add_event_handler("jabber_rpc_method_fault", self._on_jabber_rpc_method_fault)
        client.add_event_handler("jabber_rpc_error", self._on_jabber_rpc_error)

        # register handler
        self.set_handler(handler)

    def set_handler(self, handler: Module | None = None) -> None:
        """Set the handler for remote procedure calls to this client.

        Args:
            handler: Handler object.
        """

        # store handler
        self._handler = handler

        # update methods
        self._methods = copy.copy(handler.methods) if handler else {}

    async def call(self, target_jid: str, method: str, annotation: dict[str, Any], *args: Any) -> Any:
        """Call a method on a remote host.

        Args:
            target_jid: Target JID to call method on.
            method: Name of method to call.
            annotation: Method annotation.
            *args: Parameters for method.

        Returns:
            Future for response.
        """

        # create the method call
        iq = self._client.plugin["xep_0009"].make_iq_method_call(target_jid, method, py2xml(*args))  # type: ignore

        # create a future for this
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        future = Future(annotation=annotation, comm=self._comm)
        self._futures[jid] = future

        # send request
        await iq.send()

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
            try:
                method, signature, _ = self._methods[pmethod]
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
                    response = self._client.plugin["xep_0009_timeout"].make_iq_method_timeout(  # type: ignore
                        iq["id"], iq["from"], int(timeout)
                    )
                    response.send()

            # call method
            return_value = await self._handler.execute(pmethod, *params, sender=iq["from"].user)
            return_value = () if return_value is None else (return_value,)

            # send response
            self._client.plugin["xep_0009"].make_iq_method_response(iq["id"], iq["from"], py2xml(*return_value)).send()  # type: ignore

        except Exception as e:
            # an exception was raised
            if isinstance(e, exc.PyObsError):
                e.log(log, "ERROR", f"Exception was raised in call to {pmethod}: {e}", exc_info=True)
            else:
                log.exception("Something unexpected happened.")
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
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        if jid not in self._futures:
            return
        future = self._futures[jid]
        del self._futures[jid]

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
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        self._futures[jid].set_timeout(timeout)

    async def _on_jabber_rpc_method_fault(self, iq: Any) -> None:
        """Communication to host failed.

        Args:
            iq: Received XMPP message.
        """

        # get message
        iq.enable("rpc_query")
        fault = xml2fault(iq["rpc_query"]["method_response"]["fault"])

        # get future
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        future = self._futures[jid]
        del self._futures[jid]

        # get exception and error
        s: str = fault["string"]

        if ">" in s:
            # a pyobs exception
            exception_name = s[1 : s.index(">")]
            exception_message = s[s.index(">") + 1 :].strip()
            exception_class = getattr(exc, exception_name)

        else:
            # some generic error, wrap it into a remote error
            exception_class = exc.RemoteError
            exception_message = s

        # and instantiate it
        if issubclass(exception_class, exc.RemoteError):
            exception = exception_class(message=exception_message, module=jid)
        else:
            exception = exception_class(message=exception_message)

        # sender
        sender = iq["from"].node

        # set error
        if not future.done():
            future.set_exception(exc.InvocationError(module=sender, exception=exception))

    async def _on_jabber_rpc_error(self, iq: Any) -> None:
        """Method invocation failes.

        Args:
            iq: Received XMPP message.
        """

        # get message
        pmethod = self._client.plugin["xep_0009"].extract_method(iq["rpc_query"])
        condition = iq["error"]["condition"]

        # get future
        jid: str | slixmpp.JID = iq["id"]
        if isinstance(jid, slixmpp.JID):
            jid = jid.node
        callback = self._futures[jid]
        del self._futures[jid]

        # sender
        sender = iq["from"].node

        # set error
        e = {
            "item-not-found": exc.RemoteError(sender, f"No remote handler available for {pmethod} at {iq['from']}'!"),
            "forbidden": exc.RemoteError(sender, f"Forbidden to invoke remote handler for {pmethod} at {iq['from']}!"),
            "undefined-condition": exc.RemoteError(
                sender, f"An unexpected problem occured trying to invoke {pmethod} at {iq['from']}!"
            ),
            "service-unavailable": exc.RemoteError(sender, f"The service at {iq['from']} is unavailable."),
            "remote-server-not-found": exc.RemoteError(sender, f"Could not find remote server for {iq['from']}."),
        }[condition]
        if e is None:
            exc.RemoteError(sender, f"An unexpected exception occurred at {iq['from']}!")
        callback.set_exception(e)


__all__ = ["RPC"]
