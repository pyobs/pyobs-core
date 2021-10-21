import inspect
import os
import typing

import pyobs.interfaces


def get_parents(interface):
    # get parent classes
    parents = inspect.getmro(interface)

    # filter self and object
    return list(filter(lambda i: i.__name__ not in [interface.__name__, 'object'], parents))


def annotation_to_str(annotation):
    if 'typing' in str(annotation):
        return str(annotation)
    elif 'None' in str(annotation):
        return 'None'
    else:
        return annotation.__name__


def get_used_types(methods):
    # get all used types
    used_types = []
    for _, method in methods:
        sig = inspect.signature(method)
        for param in sig.parameters:
            used_types.append(sig.parameters[param].annotation)
        used_types.append(sig.return_annotation)

    # make unique
    used_types = list(set(used_types))

    # find all that are from pyobs
    pyobs_types = list(filter(lambda t: hasattr(t, '__module__') and 'pyobs' in t.__module__, used_types))

    return pyobs_types

def main():
    # path for proxies
    ifaces_path = os.path.dirname(pyobs.interfaces.__file__)
    proxies_path = os.path.join(ifaces_path, 'proxies')

    # open init
    init_filename = os.path.join(proxies_path, '__init__.py')
    with open(init_filename, 'w') as init:

        # get all interfaces and loop them
        for interface_name, interface in inspect.getmembers(pyobs.interfaces, inspect.isclass):
            print(f'Working on {interface.__name__}...')
            if interface.__name__ == 'Interface':
                init.write(f'from .interfaceproxy import InterfaceProxy\n')
            else:
                init.write(f'from .{interface.__name__}Proxy import {interface.__name__}Proxy\n')

            # get parent classes
            parents = get_parents(interface)
            print('  Parent interfaces: ' + ', '.join([p.__name__ for p in parents]))

            # proxy name
            proxy_name = interface_name + 'Proxy'
            if interface_name == 'Interface':
                proxy_name = proxy_name.lower()

            # build filename
            filename = os.path.join(proxies_path, proxy_name + '.py')

            # open it
            print(f'  Writing to file {filename}')
            with open(filename, 'w') as py:
                # get all methods
                methods = inspect.getmembers(interface, inspect.isfunction)

                # write imports
                py.write('import typing\n\n')
                py.write('from pyobs.utils.threads import Future\n')

                # get all used types
                used_types = get_used_types(methods)
                for t in used_types:
                    py.write(f'from {t.__module__} import {t.__name__}\n')

                # and parents
                for p in parents:
                    if p.__name__ == 'Interface':
                        py.write(f'from .interfaceproxy import InterfaceProxy\n')
                    else:
                        py.write(f'from .{p.__name__}Proxy import {p.__name__}Proxy\n')
                py.write('\n\n')

                # class header
                py.write(f'class {interface_name}Proxy')
                if len(parents) > 0:
                    py.write('(' + ', '.join([p.__name__ + 'Proxy' for p in parents]) + ')')
                py.write(':\n')

                # loop methods
                for method_name, method in methods:
                    print(f'  Creating method {method_name}')
                    py.write(f'    def {method_name}(self')

                    # get signature
                    sig = inspect.signature(method)
                    params = list(filter(lambda p: p not in ['self', 'args', 'kwargs'], sig.parameters))
                    if len(params) > 0:
                        param_strings = []
                        for param in params:
                            ann = annotation_to_str(sig.parameters[param].annotation)
                            tmp = f'{param}: {ann}'
                            if '_empty' not in str(sig.parameters[param].default):
                                tmp += f' = {sig.parameters[param].default}'
                            param_strings.append(tmp)
                        py.write(', ' + ', '.join(param_strings))

                    # return annotation
                    return_annotation = annotation_to_str(sig.return_annotation)
                    py.write(f') -> Future[{return_annotation}]:\n        ...\n\n')

                # no methods?
                if len(methods) == 0:
                    py.write('    ...\n')


if __name__ == '__main__':
    main()
