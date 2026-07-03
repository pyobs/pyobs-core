from slixmpp.plugins.xep_0009 import XEP_0009 as XEP_0009_original
from slixmpp.xmlstream import ET


class XEP_0009(XEP_0009_original):
    """Small fix for the original XEP_0009 plugin."""

    def handle_error(self, iq):
        """Route RPC-level errors (e.g. forbidden, item-not-found) through the same
        jabber_rpc_error event as transport-level errors, instead of being silently
        dropped -- the base class's own name for this hook, previously shadowed by a
        same-but-underscored no-op that never actually overrode it."""
        self.xmpp.event("jabber_rpc_error", iq)

    def extract_method(self, stanza):
        xml = ET.fromstring(f"{stanza}")
        return xml.find("./{jabber:iq:rpc}methodCall/{jabber:iq:rpc}methodName").text

    def item_not_found(self, iq):
        """Expose method to public."""
        return self._item_not_found(iq)

    def forbidden(self, iq):
        """Expose method to public."""
        return self._forbidden(iq)

    def send_fault(self, iq, fault_xml):
        """Expose method to public."""
        return self._send_fault(iq, fault_xml)

    def make_iq_method_call(self, pto, pmethod, params):
        iq = self.xmpp.make_iq_set()
        iq["to"] = pto
        iq["from"] = self.xmpp.boundjid.full
        iq.enable("rpc_query")
        iq["rpc_query"]["method_call"]["method_name"] = pmethod
        iq["rpc_query"]["method_call"]["params"] = params
        return iq

    def make_iq_method_response(self, pid, pto, params):
        iq = self.xmpp.make_iq_result(pid)
        iq["to"] = pto
        iq["from"] = self.xmpp.boundjid.full
        iq.enable("rpc_query")
        iq["rpc_query"]["method_response"]["params"] = params
        return iq

    def make_iq_method_response_fault(self, pid, pto, params):
        iq = self.xmpp.make_iq_result(pid)
        iq["to"] = pto
        iq["from"] = self.xmpp.boundjid.full
        iq.enable("rpc_query")
        iq["rpc_query"]["method_response"]["params"] = None
        iq["rpc_query"]["method_response"]["fault"] = params
        return iq
