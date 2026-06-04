# Slixmpp: The Slick XMPP Library
# Copyright (C) 2011 Nathanael C. Fritz, Dann Martens (TOMOTON).
# This file is part of Slixmpp.
# See the file LICENSE for copying permission.
from typing import Any
from slixmpp.xmlstream import ET
import base64
import logging
import time

log = logging.getLogger(__name__)

_namespace = "jabber:iq:rpc"


def fault2xml(code: int, message: str) -> ET.Element:
    value: dict[str, Any] = dict()
    value["faultCode"] = code
    value["faultString"] = message
    fault = ET.Element("fault", {"xmlns": _namespace})
    fault.append(_py2xml((value,)))
    return fault


def xml2fault(params: ET.Element) -> dict[str, Any]:
    vals = []
    for value in params.findall(f"{{{_namespace}}}value"):
        vals.append(_xml2py(value)[0])
    fault = dict()
    fault["code"] = vals[0]["faultCode"]
    fault["string"] = vals[0]["faultString"]
    return fault


def py2xml(*args: Any) -> ET.Element:
    params = ET.Element(f"{{{_namespace}}}params")
    for x in args:
        param = ET.Element(f"{{{_namespace}}}param")
        param.append(_py2xml(x))
        params.append(param)  # <params><param>...
    return params


def _py2xml(*args: Any) -> ET.Element:
    for x in args:
        val = ET.Element(f"{{{_namespace}}}value")
        if x is None:
            nil = ET.Element(f"{{{_namespace}}}nil")
            val.append(nil)
        elif type(x) is int:
            i4 = ET.Element(f"{{{_namespace}}}i4")
            i4.text = str(x)
            val.append(i4)
        elif type(x) is bool:
            boolean = ET.Element(f"{{{_namespace}}}boolean")
            boolean.text = str(int(x))
            val.append(boolean)
        elif type(x) is str:
            string = ET.Element(f"{{{_namespace}}}string")
            string.text = x
            val.append(string)
        elif type(x) is float:
            double = ET.Element(f"{{{_namespace}}}double")
            double.text = str(x)
            val.append(double)
        elif type(x) is rpcbase64:
            b64 = ET.Element(f"{{{_namespace}}}base64")
            b64.text = x.encoded()
            val.append(b64)
        elif type(x) is rpctime:
            iso = ET.Element(f"{{{_namespace}}}dateTime.iso8601")
            iso.text = str(x)
            val.append(iso)
        elif type(x) in (list, tuple):
            array = ET.Element(f"{{{_namespace}}}array")
            data = ET.Element(f"{{{_namespace}}}data")
            for y in x:
                data.append(_py2xml(y))
            array.append(data)
            val.append(array)
        elif type(x) is dict:
            struct = ET.Element(f"{{{_namespace}}}struct")
            for y in x.keys():
                member = ET.Element(f"{{{_namespace}}}member")
                name = ET.Element(f"{{{_namespace}}}name")
                name.text = y
                member.append(name)
                member.append(_py2xml(x[y]))
                struct.append(member)
            val.append(struct)
        return val


def xml2py(params: ET.Element) -> list[Any]:
    namespace = "jabber:iq:rpc"
    vals: list[Any] = []
    for param in params.findall(f"{{{namespace}}}param"):
        vals.append(_xml2py(param.find(f"{{{namespace}}}value")))
    return vals


def _xml2py(value: ET) -> Any:
    namespace = "jabber:iq:rpc"
    find_value = value.find
    if find_value(f"{{{namespace}}}nil") is not None:
        return None
    if find_value(f"{{{namespace}}}i4") is not None:
        return int(find_value(f"{{{namespace}}}i4").text)
    if find_value(f"{{{namespace}}}int") is not None:
        return int(find_value(f"{{{namespace}}}int").text)
    if find_value(f"{{{namespace}}}boolean") is not None:
        return bool(int(find_value(f"{{{namespace}}}boolean").text))
    if find_value(f"{{{namespace}}}string") is not None:
        return find_value(f"{{{namespace}}}string").text
    if find_value(f"{{{namespace}}}double") is not None:
        return float(find_value(f"{{{namespace}}}double").text)
    if find_value(f"{{{namespace}}}base64") is not None:
        return rpcbase64(find_value(f"{{{namespace}}}base64").text.encode())
    if find_value(f"{{{namespace}}}Base64") is not None:
        # Older versions of XEP-0009 used Base64
        return rpcbase64(find_value(f"{{{namespace}}}Base64").text.encode())
    if find_value(f"{{{namespace}}}dateTime.iso8601") is not None:
        return rpctime(find_value(f"{{{namespace}}}dateTime.iso8601").text)
    if find_value(f"{{{namespace}}}struct") is not None:
        struct = {}
        for member in find_value(f"{{{namespace}}}struct").findall(f"{{{namespace}}}member"):
            struct[member.find(f"{{{namespace}}}name").text] = _xml2py(member.find(f"{{{namespace}}}value"))
        return struct
    if find_value(f"{{{namespace}}}array") is not None:
        array = []
        for val in find_value(f"{{{namespace}}}array").find(f"{{{namespace}}}data").findall(f"{{{namespace}}}value"):
            array.append(_xml2py(val))
        return array
    raise ValueError()


class rpcbase64:
    def __init__(self, data: bytes):
        # base 64 encoded string
        self.data = data

    def decode(self) -> bytes:
        return base64.b64decode(self.data)

    def __str__(self) -> str:
        return self.decode().decode()

    def encoded(self) -> str:
        return self.data.decode()


class rpctime:
    def __init__(self, data: Any | None = None):
        # assume string data is in iso format YYYYMMDDTHH:MM:SS
        if type(data) is str:
            self.timestamp = time.strptime(data, "%Y%m%dT%H:%M:%S")
        elif type(data) is time.struct_time:
            self.timestamp = data
        elif data is None:
            self.timestamp = time.gmtime()
        else:
            raise ValueError()

    def iso8601(self) -> str:
        # return a iso8601 string
        return time.strftime("%Y%m%dT%H:%M:%S", self.timestamp)

    def __str__(self) -> str:
        return self.iso8601()
