from typing import Union


def get_object(config_or_object: Union[dict, object], object_class=None, *args, **kwargs) -> object:
    """Creates object from config or returns object directly, both optionally after check of type.

    Args:
        config_or_object: A configuration dict or an object itself to create/check.
        object_class: Class to check object against.

    Returns:
        (New) object (created from config) that optionally passed class check.

    Raises:
        TypeError: If the object does not match the given class.
    """

    if config_or_object is None:
        # we return None directly
        return None

    elif isinstance(config_or_object, dict):
        # a dict is given, so create object
        obj = create_object(config_or_object, *args, **kwargs)

    else:
        # just use given object
        obj = config_or_object

    # do we need a type check and does the given object pass?
    if object_class is not None and not isinstance(obj, object_class):
        raise TypeError('Provided object is not of requested type %s.' % object_class.__name__)
    return obj


def get_class_from_string(class_name):
    parts = class_name.split('.')
    module_name = ".".join(parts[:-1])
    cls = __import__(module_name)
    for comp in parts[1:]:
        cls = getattr(cls, comp)
    return cls


def create_object(config: dict, *args, **kwargs):
    # get class name
    class_name = config['class']

    # create class
    klass = get_class_from_string(class_name)

    # create object
    return klass(*args, **config, **kwargs)


__all__ = ['get_object', 'get_class_from_string', 'create_object']
