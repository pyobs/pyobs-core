import copy
import inspect
import logging
from threading import RLock
from typing import Dict, Optional, Any, Callable, Tuple

import sleekxmpp
import sleekxmpp.exceptions
from sleekxmpp.plugins.xep_0009.binding import fault2xml, xml2fault, xml2py, py2xml

from pyobs.modules import Module
from pyobs.comm.exceptions import *
from pyobs.utils.threads.future import Future, BaseFuture

log = logging.getLogger(__name__)


class RPC(object):
    """RPC wrapper around XEP0009."""

    def __init__(self, client: sleekxmpp.ClientXMPP, handler: Optional[Module] = None):
        """Create a new RPC wrapper.

        Args:
            client: XMPP client tu use for communication.
            handler: pyobs module that handles function calls.
        """

        # store
        self._client = client
        self._lock = RLock()
        self._futures: Dict[str, BaseFuture] = {}
        self._handler = handler
        self._methods: Dict[str, Tuple[Callable[[], Any], inspect.Signature]] = {}

        # set up callbacks
        client.add_event_handler('jabber_rpc_method_call', self._on_jabber_rpc_method_call, threaded=True)
        client.add_event_handler('jabber_rpc_method_timeout', self._on_jabber_rpc_method_timeout)
        client.add_event_handler('jabber_rpc_method_response', self._on_jabber_rpc_method_response)
        client.add_event_handler('jabber_rpc_method_fault', self._on_jabber_rpc_method_fault)
        client.add_event_handler('jabber_rpc_error', self._on_jabber_rpc_error)

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

    def call(self, target_jid: str, method: str, signature: inspect.Signature, *args: Any) -> BaseFuture:
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
        iq = self._client.plugin['xep_0009'].make_iq_method_call(target_jid, method, py2xml(*args))

        # create a future for this
        pid = iq['id']
        future = Future[signature.return_annotation](signature=signature)
        self._futures[pid] = future

        # send request
        try:
            iq.send(block=False)
        except sleekxmpp.exceptions.IqError:
            # we handle exceptions elsewhere
            pass

        # don't wait for response, just return future
        return future

    def _on_jabber_rpc_method_call(self, iq: Any) -> None:
        """React on remote method call.

        Args:
            iq: Received XMPP message.
        """

        # get method and parameters
        iq.enable('rpc_query')
        params = xml2py(iq['rpc_query']['method_call']['params'])
        pmethod = iq['rpc_query']['method_call']['method_name']

        try:
            # no handler?
            if self._handler is None:
                raise ValueError('No handler specified.')

            # get method
            with self._lock:
                try:
                    method, signature = self._methods[pmethod]
                except KeyError:
                    log.error("No handler available for %s!", pmethod)
                    self._client.plugin['xep_0009'].item_not_found(iq).send()
                    return

            # bind parameters
            ba = signature.bind(*params)
            ba.apply_defaults()

            # do we have a timeout?
            if hasattr(method, 'timeout'):
                timeout = getattr(method, 'timeout')(self._handler, **ba.arguments)
                if timeout:
                    # yes, send it!
                    response = self._client.plugin['xep_0009_timeout'].\
                        make_iq_method_timeout(iq['id'], iq['from'], int(timeout))
                    response.send()

            # call method
            return_value = self._handler.execute(pmethod, *params, sender=iq['from'].user)
            return_value = () if return_value is None else (return_value,)

            # send response
            self._client.plugin['xep_0009'].make_iq_method_response(iq['id'], iq['from'], py2xml(*return_value)).send()

        except InvocationException as ie:
            # could not invoke method
            fault = {'code': 500, 'string': ie.get_message()}
            self._client.plugin['xep_0009'].send_fault(iq, fault2xml(fault))

        except Exception as e:
            # something else went wrong
            log.warning('Error during call to %s: %s', pmethod, str(e), exc_info=True)

            # send response
            fault = dict()
            fault['code'] = 500
            fault['string'] = str(e)
            self._client.plugin['xep_0009'].send_fault(iq, fault2xml(fault))

    def _on_jabber_rpc_method_response(self, iq: Any) -> None:
        """Received a response for a method call.

        Args:
            iq: Received XMPP message.
        """

        # get message
        iq.enable('rpc_query')
        try:
            args = xml2py(iq['rpc_query']['method_response']['params'])
        except ValueError:
            log.error('Could not parse method response: %s', iq)
            return

        # get future
        pid = iq['id']
        with self._lock:
            if pid not in self._futures:
                return
            future = self._futures[pid]
            del self._futures[pid]

        # set result of future
        if len(args) > 0:
            future.set_value(args[0])
        else:
            future.set_value(None)

    def _on_jabber_rpc_method_timeout(self, iq: Any) -> None:
        """Method call timed out.

        Args:
            iq: Received XMPP message.
        """
        iq.enable('rpc_query')
        timeout = iq['rpc_query']['method_timeout']['timeout']
        pid = iq['id']
        self._futures[pid].set_timeout(timeout)

    def _on_jabber_rpc_method_fault(self, iq: Any) -> None:
        """Communication to host failed.

        Args:
            iq: Received XMPP message.
        """

        # get message
        iq.enable('rpc_query')
        fault = xml2fault(iq['rpc_query']['method_response']['fault'])

        # get future
        pid = iq['id']
        with self._lock:
            future = self._futures[pid]
            del self._futures[pid]

        # set error
        future.cancel_with_error(InvocationException(fault['string']))

    def _on_jabber_rpc_error(self, iq: Any) -> None:
        """Method invocation failes.

        Args:
            iq: Received XMPP message.
        """

        # get message
        pmethod = self._client.plugin['xep_0009'].extract_method(iq['rpc_query'])
        condition = iq['error']['condition']

        # get future
        pid = iq['id']
        with self._lock:
            callback = self._futures[pid]
            del self._futures[pid]

        # set error
        e = {
            'item-not-found':
                RemoteException("No remote handler available for %s at %s!" % (pmethod, iq['from'])),
            'forbidden':
                AuthorizationException("Forbidden to invoke remote handler for %s at %s!" % (pmethod, iq['from'])),
            'undefined-condition':
                RemoteException("An unexpected problem occured trying to invoke %s at %s!" % (pmethod, iq['from'])),
            'service-unavailable':
                RemoteException("The service at %s is unavailable." % iq['from']),
            'remote-server-not-found':
                RemoteException("Could not find remote server for %s." % iq['from'])
        }[condition]
        if e is None:
            RemoteException("An unexpected exception occurred at %s!" % iq['from'])
        callback.cancel_with_error(e)


__all__ = ['RPC']
