import logging
from sleekxmpp.plugins import BasePlugin
from sleekxmpp.plugins.xep_0009.stanza.RPC import RPCQuery
from sleekxmpp.xmlstream import register_stanza_plugin
from sleekxmpp.xmlstream.handler import Callback
from sleekxmpp.xmlstream.matcher import MatchXPath

from . import stanza


log = logging.getLogger(__name__)


class XEP_0009_timeout(BasePlugin):
    """A plugin for SleekXMPP, adding a timeout to RPC calls."""

    name = 'xep_0009_timeout'
    description = 'XEP-0009-timeout: Jabber-RPC timeout extension'
    dependencies = set(['xep_0009'])
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(RPCQuery, stanza.MethodTimeout)

        self.xmpp.register_handler(
            Callback('RPC Call', MatchXPath('{%s}iq/{%s}query/{%s}methodTimeout' % (self.xmpp.default_ns,
                                                                                    RPCQuery.namespace,
                                                                                    RPCQuery.namespace)),
                     self._handle_method_timeout)
        )

        self.xmpp.add_event_handler('jabber_rpc_method_timeout', self._on_jabber_rpc_method_timeout, threaded=True)

    def make_iq_method_timeout(self, pid, pto, timeout):
        iq = self.xmpp.makeIqResult(pid)
        iq.attrib['to'] = pto
        iq.attrib['from'] = self.xmpp.boundjid.full
        iq.enable('rpc_query')
        iq['rpc_query']['method_timeout']['timeout'] = timeout
        return iq

    def _handle_method_timeout(self, iq):
        log.debug("Incoming Jabber-RPC timeout from %s", iq['from'])
        self.xmpp.event('jabber_rpc_method_timeout', iq)

    def _on_jabber_rpc_method_timeout(self, iq, forwarded=False):
        """A default handler for Jabber-RPC method timeout. If another handler is registered,
        this one will defer and not run.

        If this handler is called by your own custom handler with forwarded set to True, then it will run as normal.
        """
        if not forwarded and self.xmpp.event_handled('jabber_rpc_method_timeout') > 1:
            return

        # Reply with error by default
        error = self.xmpp['xep_0009']._item_not_found(iq)
        error.send()
