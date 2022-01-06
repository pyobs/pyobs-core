from sleekxmpp.xmlstream.stanzabase import ElementBase


class MethodTimeout(ElementBase):
    name = "methodTimeout"
    namespace = "jabber:iq:rpc"
    plugin_attrib = "method_timeout"
    interfaces = {"timeout"}
    subinterfaces = set(())
    plugin_attrib_map = {}
    plugin_tag_map = {}

    def get_timeout(self):
        return int(self._get_sub_text("timeout"))

    def set_timeout(self, timeout):
        return self._set_sub_text("timeout", str(timeout))
