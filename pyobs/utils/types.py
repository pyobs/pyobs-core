from inspect import BoundArguments, Signature, Parameter
from enum import Enum
from typing import Any
import xml.sax.saxutils


def cast_bound_arguments_to_simple(bound_arguments: BoundArguments):
    """Cast the requested parameters, which are of simple types, to the types required by the method.

    Args:
        bound_arguments: Incoming parameters.
    """
    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # special cases
        if isinstance(value, str):
            # escape strings
            bound_arguments.arguments[key] = xml.sax.saxutils.escape(value)
        elif isinstance(value, Enum):
            # get value of enum
            bound_arguments.arguments[key] = value.value


def cast_bound_arguments_to_real(bound_arguments: BoundArguments, signature: Signature):
    """Cast the requested parameters to simple types.

    Args:
        bound_arguments: Incoming parameters.
        signature: Signature of method.
    """
    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # get type of parameter
        annotation = signature.parameters[key].annotation

        # special cases
        if value is None or annotation == Parameter.empty or annotation == Any:
            # if value is None or no annotation is given, just copy it
            bound_arguments.arguments[key] = value
        elif annotation == Enum:
            # cast to enum
            bound_arguments.arguments[key] = value if annotation == Parameter.empty else annotation(value)
        elif annotation == str:
            # unescape strings
            bound_arguments.arguments[key] = xml.sax.saxutils.unescape(value)
        else:
            # cast to type
            bound_arguments.arguments[key] = annotation(value)


def cast_response_to_real(response: Any, signature: Signature) -> Any:
    """Cast a response from simple to the method's real types.

    Args:
        response: Response of method call.
        signature: Signature of method.

    Returns:
        Same as input response, but with only simple types.
    """

    # get return annotation
    annotation = signature.return_annotation

    # TODO: For future Python versions (3.9?)
    # - use get_origin() instead of __origin__
    # - handle dicts and tuples

    # any annotations?
    if response is None or annotation == Parameter.empty or annotation == Any:
        # no response or no annotation at all or Any
        return response
    elif hasattr(annotation, '__origin__') and annotation.__origin__ == tuple or isinstance(annotation, tuple):
        # parse tuple
        # return tuple([None if res is None else annot(res) for res, annot in zip(response, annotation)])
        return response
    elif hasattr(annotation, '__origin__') and annotation.__origin__ in [dict]:
        # just return it
        return response
    else:
        # type cast response
        return annotation(response)


def cast_response_to_simple(response: Any) -> Any:
    """Cast a response from a method to only simple types.

    Args:
        response: Response of method call.

    Returns:
        Same as input response, but with only simple types.
    """

    # tuple, enum or something else
    if isinstance(response, tuple):
        return tuple([cast_response_to_simple(r) for r in response])
    elif isinstance(response, Enum):
        return response.value
    else:
        return response
