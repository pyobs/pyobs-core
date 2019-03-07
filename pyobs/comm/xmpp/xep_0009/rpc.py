from sleekxmpp.plugins.xep_0009 import XEP_0009 as XEP_0009_original
from sleekxmpp.xmlstream import ET


class XEP_0009(XEP_0009_original):
    """Small fix for the original XEP_0009 plugin."""

    def _handle_error(self, iq):
        pass

    def extract_method(self, stanza):
        xml = ET.fromstring("%s" % stanza)
        return xml.find("./{jabber:iq:rpc}methodCall/{jabber:iq:rpc}methodName").text
