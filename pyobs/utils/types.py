import functools
import inspect
from inspect import BoundArguments, Signature, Parameter
from enum import Enum, EnumMeta
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
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> None:
    """Cast the requested parameters, which are of simple types, to the types required by the method.

    Args:
        bound_arguments: Incoming parameters.
        pre: Method to call for each parameter before automatic handling.
        post: Method to call for each parameter after automatic handling.
    """

    def cast_to_simple(v: Any, a: Optional[Any] = None) -> Tuple[bool, Any]:
        stop_iter = False
        print("cast_bound_arguments_to_simple", v, a, type(a))

        # call provided pre-method
        if pre:
            stop_iter, v = pre(v, a)
            if stop_iter:
                return True, v

        if isinstance(v, Enum):
            # get string name for Enums
            stop_iter, v = True, v.value

        # call provided post-method
        if post:
            stop_iter, v = post(v, a)

        # stop iteration?
        return stop_iter, v

    # get signature
    signature = bound_arguments.signature

    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        if key in ["self", "args", "kwargs"]:
            continue

        # get type of parameter
        annotation = signature.parameters[key].annotation

        # cast
        bound_arguments.arguments[key] = iterate_params(value, annotation, cast_to_simple)


def cast_bound_arguments_to_real(
    bound_arguments: BoundArguments,
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> None:
    """Cast the requested parameters to real types.

    Args:
        bound_arguments: Incoming parameters.
        pre: Method to call for each parameter before automatic handling.
        post: Method to call for each parameter after automatic handling.
    """

    def cast_to_real(v: Any, a: Type[Any]) -> Tuple[bool, Any]:
        stop_iter = False
        print("cast_bound_arguments_to_real", v, a, type(a))

        # call provided pre-method
        if pre:
            stop_iter, v = pre(v, a)
            if stop_iter:
                return True, v

        if isinstance(type(a), Enum):
            # get Enum from string
            stop_iter, v = True, a(v)

        # call provided post-method
        if post:
            stop_iter, v = post(v, a)

        # stop iteration?
        return stop_iter, v

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
    annotation: Type[Any],
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Any:
    """Cast a response from simple to the method's real types.

    Args:
        value: Response of method call.
        annotation: Annotation for return value.
        pre: Method to call for each parameter before automatic handling.
        post: Method to call for each parameter after automatic handling.

    Returns:
        Same as input response, but with only simple types.
    """

    # cast
    cast_to_simple = functools.partial(__cast_to_simple, pre=pre, post=post)
    return iterate_params(value, annotation, cast_to_simple)


def cast_response_to_real(
    value: Any,
    annotation: Type[Any],
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Any:
    """Cast a response from simple to the method's real types.

    Args:
        value: Response of method call.
        annotation: Annotation of return value.
        pre: Method to call for each parameter before automatic handling.
        post: Method to call for each parameter after automatic handling.

    Returns:
        Same as input response, but with only simple types.
    """

    # cast
    cast_to_real = functools.partial(__cast_to_real, pre=pre, post=post)
    return iterate_params(value, annotation, cast_to_real)


def __cast_to_simple(
    v: Any,
    a: Type[Any],
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Tuple[bool, Any]:
    stop_iter = False
    print("cast_to_simple", v, a, type(a))

    # call provided pre-method
    if pre:
        stop_iter, v = pre(v, a)
        if stop_iter:
            return True, v

    if inspect.isclass(a) and issubclass(a, Enum):
        # get string name for Enums
        print("enum")
        stop_iter, v = True, v.value

    # call provided post-method
    if post:
        stop_iter_post, v = post(v, a)
        if stop_iter_post:
            return True, v

    # stop iteration?
    print("new value:", stop_iter, v)
    return stop_iter, v


def __cast_to_real(
    v: Any,
    a: Type[Any],
    pre: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
    post: Optional[Callable[[Any, Any], Tuple[bool, Optional[Any]]]] = None,
) -> Tuple[bool, Any]:
    # init
    stop_iter = False
    print("cast_to_real", v, a, type(a))

    # call provided pre-method
    if pre:
        stop_iter, v = pre(v, a)
        if stop_iter:
            return True, v

    if inspect.isclass(a) and issubclass(a, Enum):
        # get Enum from string
        print("enum")
        stop_iter, v = True, a(v)
        print(v)

    # call provided post-method
    if post:
        stop_iter_post, v = post(v, a)
        if stop_iter_post:
            return True, v

    # stop iteration?
    print("new value:", stop_iter, v)
    return stop_iter, v
