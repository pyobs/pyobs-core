from inspect import BoundArguments, Signature, Parameter
from enum import Enum
from typing import Any, get_origin, get_args, Callable, Tuple, Optional, Type
import xml.sax.saxutils


def iterate_params(
    value: Any,
    annotation: Optional[Type[Any]] = None,
    method: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Any:
    """Iterate annotations and call a given method.

    Args:
        value: value to iterate.
        annotation: Annotation for value.
        method: Method to run on each value. Should take one value and annotation and return a bool indicating whether
            iteration should stop here and a new value.

    Returns:
        Same structure as input, but converted by method.
    """

    # call provided method
    if method:
        stop_iter, value = method(value, annotation)
        if stop_iter:
            return value

    # okay, iterate value
    if value is None or annotation is None or annotation == Parameter.empty:
        # no response or no annotation at all or Any
        return value

    elif isinstance(value, tuple):
        # handle tuple
        if annotation:
            return tuple(iterate_params(v, a, method) for v, a in zip(value, get_args(annotation)))
        else:
            return tuple(iterate_params(v, None, method) for v in value)

    elif isinstance(value, list):
        # handle lists
        if annotation:
            typ = get_args(annotation)[0]
            return [iterate_params(v, typ, method) for v in value]
        else:
            return [iterate_params(v, None, method) for v in value]

    elif isinstance(value, dict):
        # handle dict
        if annotation:
            annk, annv = get_args(annotation)
            return {iterate_params(k, annk, method): iterate_params(v, annv, method) for k, v in value.items()}
        else:
            return {iterate_params(k, None, method): iterate_params(v, None, method) for k, v in value.items()}

    else:
        # just return it, maybe cast to annotation
        try:
            return annotation(value) if annotation else value
        except TypeError:
            return value


def cast_bound_arguments_to_simple(
    bound_arguments: BoundArguments,
    method: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> None:
    """Cast the requested parameters, which are of simple types, to the types required by the method.

    Args:
        bound_arguments: Incoming parameters.
        method: Method to run on each parameter.
    """

    def cast_to_simple(v: Any, a: Optional[Any] = None) -> Tuple[bool, Any]:
        # call provided method
        if method:
            stop_iter, v = method(v, a)
            if stop_iter:
                return True, v

        if isinstance(v, Enum):
            # get string name for Enums
            return True, v.value
        else:
            # continue iteration
            return False, v

    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # cast
        bound_arguments.arguments[key] = iterate_params(value, None, cast_to_simple)


def cast_bound_arguments_to_real(
    bound_arguments: BoundArguments,
    method: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> None:
    """Cast the requested parameters to real types.

    Args:
        bound_arguments: Incoming parameters.
        method: Method to run on each parameter.
    """

    def cast_to_real(v: Any, a: Optional[Any] = None) -> Tuple[bool, Any]:
        # call provided method
        if method:
            stop_iter, v = method(v, a)
            if stop_iter:
                return True, v

        if a == Enum:
            # get Enum from string
            return True, a(v)
        else:
            # continue iteration
            return False, v

    # get signature
    signature = bound_arguments.signature

    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # get type of parameter
        annotation = signature.parameters[key].annotation

        # cast
        bound_arguments.arguments[key] = iterate_params(value, annotation, cast_to_real)


def cast_response_to_simple(
    value: Any,
    annotation: Optional[Type[Any]] = None,
    method: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Any:
    """Cast a response from simple to the method's real types.

    Args:
        value: Response of method call.
        annotation: Annotation for return value.
        method: Method to call on each value.

    Returns:
        Same as input response, but with only simple types.
    """

    def cast_to_simple(v: Any, a: Optional[Any] = None) -> Tuple[bool, Any]:
        # call provided method
        if method:
            stop_iter, v = method(v, a)
            if stop_iter:
                return True, value

        if isinstance(v, Enum):
            # get string name for Enums
            return True, v.value
        else:
            # continue iteration
            return False, v

    # cast
    a = iterate_params(value, annotation, cast_to_simple)
    return a


def cast_response_to_real(
    value: Any,
    annotation: Optional[Type[Any]] = None,
    method: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Any:
    """Cast a response from simple to the method's real types.

    Args:
        value: Response of method call.
        annotation: Annotation of return value.
        method: Method to call for each parameter.

    Returns:
        Same as input response, but with only simple types.
    """

    def cast_to_real(v: Any, a: Optional[Any] = None) -> Tuple[bool, Any]:
        # call provided method
        if method:
            stop_iter, v = method(v, a)
            if stop_iter:
                return True, v

        if a == Enum:
            # get Enum from string
            return True, a(v)
        else:
            # continue iteration
            return False, v

    # cast
    return iterate_params(value, annotation, cast_to_real)


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
