from slixmpp.plugins.xep_0009 import XEP_0009 as XEP_0009_original
from slixmpp.xmlstream import ET


class XEP_0009(XEP_0009_original):
    """Small fix for the original XEP_0009 plugin."""

    def _handle_error(self, iq):
        pass

    def extract_method(self, stanza):
        xml = ET.fromstring("%s" % stanza)
        return xml.find("./{jabber:iq:rpc}methodCall/{jabber:iq:rpc}methodName").text

    def item_not_found(self, iq):
        """Expose method to public."""
        return self._item_not_found(iq)

    def send_fault(self, iq, fault_xml):
        """Expose method to public."""
        return self._send_fault(iq, fault_xml)
