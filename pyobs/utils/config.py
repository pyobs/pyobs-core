import os
import re


def pre_process_yaml(config: str) -> str:
    # read config
    with open(config, 'r') as f:
        content = f.read()

    # get path of config
    path = os.path.dirname(os.path.abspath(config))

    # find all include statements
    matches = re.findall('(\{include (.*)\})', content)
    for match, filename in matches:
        content = content.replace(match, pre_process_yaml(os.path.join(path, filename)))

    # return new yaml
    return content


__all__ = ['pre_process_yaml']
