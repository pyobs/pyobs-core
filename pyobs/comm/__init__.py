from .comm import Comm
from .exceptions import *

import logging


log = logging.getLogger(__name__)


def remote(timeout=None, overhead=0):
    """Decorates a method with information for an remote call.

    :param timeout:  Integer or string that specifies the timeout.
                     If string, a kwargs of that name is used for the timeout
    :param overhead: Additional overhead that is added to the timeout.
    """
    def _intercept(method):
        def _timeout(**kwargs):
            try:
                tmp = int(kwargs[timeout]) if isinstance(timeout, str) and timeout in kwargs else int(timeout)
                return tmp + overhead
            except TypeError:
                return 0

        def _resolver(instance, *args, **kwargs):
            log.debug("Locally calling %s with arguments %s.", method.__name__, args)
            try:
                value = method(instance, *args, **kwargs)
                if value == NotImplemented:
                    raise InvocationException("Local handler does not implement %s!" % method.__name__)
                return value
            except InvocationException:
                raise
            except Exception as e:
                raise InvocationException("A problem occured calling %s!" % method.__name__, e)
        setattr(_resolver, '_rpc_timeout', _timeout)
        return _resolver
    return _intercept


__all__ = ['Comm', 'http', 'xmpp', 'RemoteException', 'InvocationException', 'TimeoutException', 'remote']
