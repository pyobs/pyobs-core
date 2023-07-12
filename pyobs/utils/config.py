import os
import re

import yaml
from io import StringIO

def pre_process_yaml(config: str) -> str:
    # read config
    with open(config, "r") as f:
        content = f.read()

    # get path of config
    path = os.path.dirname(os.path.abspath(config))

    # find all include statements
    matches = re.findall("(\{include (.*)\})", content)
    for match, filename in matches:
        content = content.replace(match, pre_process_yaml(os.path.join(path, filename)))

    # find all include_key statements and its indentation level
    pattern = r"((\s*)\{include_(\w+) (.*)\})"
    matches = re.findall(pattern, content)
    for match, indent, key, filename in matches:
        with StringIO(pre_process_yaml(filename)) as f:
            include = yaml.safe_load(f)[key]
        #include = {key: include}
        include = yaml.dump(include, default_flow_style=False, indent=2)
        # ensure indentation level to be conserved
        include = indent + include.replace('\n', indent)
        content = content.replace(match, include)
    # return new yaml
    return content

__all__ = ["pre_process_yaml"]
