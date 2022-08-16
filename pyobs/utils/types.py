from inspect import BoundArguments, Signature, Parameter
from enum import Enum
from typing import Any, get_origin, get_args
import xml.sax.saxutils


def cast_bound_arguments_to_simple(bound_arguments: BoundArguments) -> None:
    """Cast the requested parameters, which are of simple types, to the types required by the method.

    Args:
        bound_arguments: Incoming parameters.
    """
    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # cast
        bound_arguments.arguments[key] = cast_value_to_simple(value)


def cast_value_to_simple(value: Any) -> Any:
    """Cast a response from a method to only simple types.

    Args:
        value: Response of method call.

    Returns:
        Same as input response, but with only simple types.
    """

    # tuple, enum or something else
    if isinstance(value, tuple):
        return tuple([cast_value_to_simple(r) for r in value])
    elif isinstance(value, list):
        return [cast_value_to_simple(r) for r in value]
    elif isinstance(value, dict):
        return {cast_value_to_simple(k): cast_value_to_simple(v) for k, v in value.items()}
    elif isinstance(value, Enum):
        return value.value
    elif type(value) == str:
        return xml.sax.saxutils.escape(value)
    else:
        return value


def cast_bound_arguments_to_real(bound_arguments: BoundArguments, signature: Signature) -> None:
    """Cast the requested parameters to simple types.

    Args:
        bound_arguments: Incoming parameters.
        signature: Signature of method.
    """
    print("cast_bound_arguments_to_real", bound_arguments, signature)

    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # get type of parameter
        annotation = signature.parameters[key].annotation

        # cast
        bound_arguments.arguments[key] = _cast_value_to_real(value, annotation)


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

    # cast
    return _cast_value_to_real(response, annotation)


def _cast_value_to_real(value: Any, annotation: Any) -> Any:
    print("cast_response_to_real", value, annotation, type(annotation), get_origin(annotation), str(annotation))

    # any annotations?
    if value is None or annotation is None or annotation == Parameter.empty:
        # no response or no annotation at all or Any
        return value
    elif str(annotation) == "typing.Any" and type(value) == str:
        # try to guess type
        try:
            # try to convert to float
            f = float(value)
            # int?
            if f == int(f):
                return int(f)
            else:
                return f
        except ValueError:
            # no float, return as string
            return value
    elif (get_origin(annotation) == tuple) or isinstance(annotation, tuple):
        # parse tuple
        return tuple(_cast_value_to_real(v, a) for v, a in zip(value, get_args(annotation)))
    elif (get_origin(annotation) == list) or isinstance(annotation, list):
        # parse list
        typ = get_args(annotation)[0]
        return [_cast_value_to_real(v, typ) for v in value]
    elif (get_origin(annotation) == dict) or isinstance(annotation, dict):
        # parse dict
        annk, annv = get_args(annotation)
        return {_cast_value_to_real(k, annk): _cast_value_to_real(v, annv) for k, v in value.items()}
    elif annotation == str:
        return xml.sax.saxutils.unescape(value)
    else:
        # type cast response
        return annotation(value)
