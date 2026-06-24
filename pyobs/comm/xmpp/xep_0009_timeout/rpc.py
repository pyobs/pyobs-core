import logging

from slixmpp.plugins.base import BasePlugin
from slixmpp.plugins.xep_0009.stanza import RPCQuery
from slixmpp.xmlstream.handler import Callback
from slixmpp.xmlstream.matcher import MatchXMLMask
from slixmpp.xmlstream.stanzabase import register_stanza_plugin

from . import stanza

log = logging.getLogger(__name__)


class XEP_0009_timeout(BasePlugin):
    """A plugin for SleekXMPP, adding a timeout to RPC calls."""

    name = "xep_0009_timeout"
    description = "XEP-0009-timeout: Jabber-RPC timeout extension"
    dependencies = {"xep_0009"}
    stanza = stanza

    def plugin_init(self):
        register_stanza_plugin(RPCQuery, stanza.MethodTimeout)

        self.xmpp.register_handler(
            Callback(
                "RPC Timeout",
                MatchXMLMask(
                    f"<iq xmlns='{self.xmpp.default_ns}'>"
                    f"<query xmlns='{RPCQuery.namespace}'>"
                    f"<methodTimeout /></query></iq>"
                ),
                self._handle_method_timeout,
            )
        )

    def make_iq_method_timeout(self, pid, pto, timeout):
        iq = self.xmpp.make_iq_result(pid)
        iq["to"] = pto
        iq["from"] = self.xmpp.boundjid.full
        iq.enable("rpc_query")
        iq["rpc_query"]["method_timeout"]["timeout"] = timeout
        return iq

    def _handle_method_timeout(self, iq):
        log.debug("Incoming Jabber-RPC timeout from %s", iq["from"])
        self.xmpp.event("jabber_rpc_method_timeout", iq)
