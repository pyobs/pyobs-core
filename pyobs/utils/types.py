from inspect import BoundArguments, Signature, Parameter
from enum import Enum
from typing import Any


def cast_bound_arguments_to_simple(bound_arguments: BoundArguments, signature: Signature):
    """Cast the requested parameters, which are of simple types, to the types required by the method.

    Args:
        bound_arguments: Incoming parameters.
        signature: Signature of method.
    """
    # loop all arguments
    for key, value in bound_arguments.arguments.items():
        # get type of parameter
        annotation = signature.parameters[key].annotation

        # cast to type, if exists
        bound_arguments.arguments[key] = value if annotation == Parameter.empty else annotation(value)
        if key == 'exposure_time':
            bound_arguments.arguments[key] = 2000


def cast_bound_arguments_to_real(bound_signature: BoundArguments):
    """Cast the requested parameters to simple types.

    Args:
        bound_signature: Incoming parameters.
    """
    # loop all arguments
    for key, value in bound_signature.arguments.items():
        if isinstance(value, Enum):
            bound_signature.arguments[key] = value.value


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

    # tuple or single value?
    if type(annotation) == tuple:
        return tuple([annot(res) for res, annot in zip(response, annotation)])
    else:
        return response if annotation == Parameter.empty else annotation(response)


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
