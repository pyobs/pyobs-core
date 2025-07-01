import inspect
from functools import wraps
from types import MethodType

import asyncio
from typing import no_type_check_decorator

from dbus_next import Message, SignatureTree
from dbus_next._private.util import parse_annotation
from dbus_next.service import ServiceInterface
from dbus_next.aio import MessageBus
from dbus_next.message_bus import BaseMessageBus
import dbus_next.service
from dbus_next import introspection as intr


def patch() -> None:
    """
    Patches dbus-next to allow for a providing the sender name. Probably a bad idea, but better than using
    a fork of the project.
    """
    MessageBus._make_method_handler = _aio_make_method_handler
    BaseMessageBus._make_method_handler = _make_method_handler
    dbus_next.service._Method.__init__ = _method__init__
    dbus_next.service.method = _method


def _aio_make_method_handler(self, interface, method):
    if not asyncio.iscoroutinefunction(method.fn):
        return BaseMessageBus._make_method_handler(self, interface, method)

    def handler(msg, send_reply):
        def done(fut):
            with send_reply:
                result = fut.result()
                body, unix_fds = ServiceInterface._fn_result_to_body(result, method.out_signature_tree)
                send_reply(Message.new_method_return(msg, method.out_signature, body, unix_fds))

        args = ServiceInterface._msg_body_to_args(msg)
        kwargs = {method.sender_keyword: msg.sender} if method.sender_keyword else {}
        fut = asyncio.ensure_future(method.fn(interface, *args, **kwargs))
        fut.add_done_callback(done)

    return handler


def _make_method_handler(self, interface, method):
    def handler(msg, send_reply):
        args = ServiceInterface._msg_body_to_args(msg)
        kwargs = {method.sender_keyword: msg.sender} if method.sender_keyword else {}
        result = method.fn(interface, *args, **kwargs)
        body, fds = ServiceInterface._fn_result_to_body(result, signature_tree=method.out_signature_tree)
        send_reply(Message.new_method_return(msg, method.out_signature, body, fds))

    return handler


def _method__init__(self, fn, name, disabled=False, sender_keyword=None):
    in_signature = ""
    out_signature = ""

    inspection = inspect.signature(fn)
    in_args = []
    for i, param in enumerate(inspection.parameters.values()):
        if i == 0:
            # first is self
            continue
        if sender_keyword and param.name == sender_keyword:
            # ignore sender_keyword
            continue
        annotation = parse_annotation(param.annotation)
        if not annotation:
            raise ValueError("method parameters must specify the dbus type string as an annotation")
        in_args.append(intr.Arg(annotation, intr.ArgDirection.IN, param.name))
        in_signature += annotation
    out_args = []
    out_signature = parse_annotation(inspection.return_annotation)
    if out_signature:
        for type_ in SignatureTree._get(out_signature).types:
            out_args.append(intr.Arg(type_, intr.ArgDirection.OUT))
    self.name = name
    self.fn = fn
    self.disabled = disabled
    self.introspection = intr.Method(name, in_args, out_args)
    self.in_signature = in_signature
    self.out_signature = out_signature
    self.in_signature_tree = SignatureTree._get(in_signature)
    self.out_signature_tree = SignatureTree._get(out_signature)
    self.sender_keyword = sender_keyword


def _method(name: str = None, disabled: bool = False, sender_keyword: str = None):
    if name is not None and type(name) is not str:
        raise TypeError("name must be a string")
    if type(disabled) is not bool:
        raise TypeError("disabled must be a bool")

    @no_type_check_decorator
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            fn(*args, **kwargs)

        fn_name = name if name else fn.__name__
        wrapped.__dict__["__DBUS_METHOD"] = dbus_next.service._Method(
            fn, fn_name, disabled=disabled, sender_keyword=sender_keyword
        )

        return wrapped

    return decorator


patch()
