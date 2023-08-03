import os
import re

import yaml
from io import StringIO


def pre_process_yaml(config: str) -> str:
    """
    Replaces blocks of the form {include <source.yaml> <key>} in the loaded config file.
    This allows to use (parts of) another config file.
    Args:
        config: directory of the main yaml file
    Returns:
        content: modified version of input config file with replaced include-blocks.
    """
    path = os.path.dirname(os.path.abspath(config))

    # read config
    with open(config, "r") as f:
        content = f.read()

    # find all include statements and its indentation level
    pattern = r"((\s*)?(-\s*)?\{include (\S*)( \S*)?\})"
    matches = re.findall(pattern, content)
    for match, indent, tick, filename, key in matches:
        with StringIO(pre_process_yaml(path + "/" + filename)) as f:
            include_full = yaml.safe_load(f)
            include = include_parts(include_full, key)
        include = yaml.dump(include, default_flow_style=False, indent=2)

        # ensure indentation level to be conserved
        if tick != "":
            include = tick + include
        if indent != "":
            indent_newline = indent + " " * len(tick)
            include = indent + include.replace("\n", indent_newline)
        matches_anchor = reload_anchors(path + "/" + filename)
        content = content.replace(match, include)
        content = replace_aliases(matches_anchor, path + "/" + filename, content)

    # return new yaml
    print(content)
   # with open('yaml_temp.yaml', 'w') as f:
   #     f.write(content)
   # with StringIO(content) as f:
   #     content = yaml.safe_load(f)
   #     content = yaml.dump(content, default_flow_style=False, indent=2)
   #     print(content)
    return content


def include_parts(include: dict, keys: str) -> dict:
    """
    Include nested contents from another yaml file.
    Args:
        include: dictionary based on yaml file from which the content is included.
        keys: keys of the included dictionary, where dots indicate the layer
    Returns:
        include: only the aimed layer of the original dictionary
    """
    if keys is None or keys == "":
        return include
    # parse key and get corresponding part of config
    keys = keys.strip()
    keys = keys.split(".")
    for key in keys:
        include = include[key]
    return include


def reload_anchors(filename: str) -> list:
    """
    Finds anchors ('&') in the included file.
    Args:
        filename: name of the file with the anchor.
    Returns:
        matches: list of (keyword, anchor) pairs from reload_anchors.
    """
    pattern = r"(\S*): &(\S*)"
    with open(filename, "r") as f:
        include_full_string = f.read()
        matches = re.findall(pattern, include_full_string)
    return matches


def replace_aliases(matches: list, anchor_filename: str, alias_string: str) -> str:
    """
    Replaces aliases ('<<: *...') in the main file by the anchor in the included file.
    Args:
        matches: list of (keyword, anchor) pairs from reload_anchors.
        anchor_filename: name of the file in which the anchor is set.
        alias_string: string with the alias that shall be replaced by the anchor.
    Returns:
        alias_string: Final string with replaced aliases.
    """
    with StringIO(pre_process_yaml(anchor_filename)) as f:
        dict_anchor = yaml.safe_load(f)
    for keyword, anchor in matches:
        indent = re.findall(r"(\s*)<<: \*" + anchor, alias_string)
        include = yaml.dump(dict_anchor[keyword], default_flow_style=False, indent=2)
        if len(indent) != 0 and indent[0] != "":
            include = include.replace("\n", indent[0])
        alias_string = alias_string.replace("<<: *" + anchor, include)
    return alias_string


__all__ = ["pre_process_yaml"]
