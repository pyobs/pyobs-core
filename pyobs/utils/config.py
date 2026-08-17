import os
import re
from io import StringIO
from typing import Any

import yaml


def pre_process_yaml(config: str) -> str:
    """
    Replaces blocks of the form {include <source.yaml> <key>} in the loaded config file.
    This allows to use (parts of) another config file.
    Args:
        config: directory of the main YAML file
    Returns:
        content: modified version of the input config file with replaced include-blocks.
    """
    path = os.path.dirname(os.path.abspath(config))

    # read config
    with open(config) as f:
        content = f.read()

    # find all include statements and its indentation level
    pattern = r"((\s*)?(-\s*)?\{include (\S*)( \S*)?\})"
    matches = re.findall(pattern, content)
    for match, indent, tick, filename, key in matches:
        matches_anchor = reload_anchors(path + "/" + filename)
        with StringIO(pre_process_yaml(path + "/" + filename)) as f:
            include_full = yaml.safe_load(f)
            include_dict = include_parts(include_full, key)

        # a whole-file include (no key selector) would otherwise leak any key whose sole purpose
        # is holding an anchor for `<<: *anchor` use elsewhere (e.g. comm.shared.yaml's
        # `comm_cfg: &comm`) as an unconsumed top-level key in the final config. Drop those here;
        # `<<: *anchor` below still resolves correctly, since replace_aliases reads the anchor's
        # value from the original included file, not from this (possibly trimmed) copy.
        # Only top-level, unindented anchor holders count -- reload_anchors() matches an anchor
        # anywhere in the file regardless of nesting, so filtering by that directly would drop a
        # top-level key whose name happens to collide with an unrelated nested anchor holder.
        if not key.strip() and isinstance(include_dict, dict):
            anchor_keywords = top_level_anchor_keywords(path + "/" + filename)
            include_dict = {k: v for k, v in include_dict.items() if k not in anchor_keywords}

        if not key.strip() and isinstance(include_dict, dict) and not include_dict:
            # everything in this whole-file include was anchor-holder keys (e.g. a
            # comm.shared.yaml whose only top-level key is `comm_cfg: &comm`) -- nothing left to
            # splice in. yaml.dump({}) is "{}\n", a flow-style node that isn't a valid sibling to
            # the block-style mapping the rest of the file continues as, so drop the placeholder
            # entirely instead of inserting an empty mapping. Scoped to whole-file includes only --
            # a keyed include that legitimately selects an empty mapping (`{include file key}`
            # where `key`'s value is `{}`) must still emit `{}`, not be silently dropped.
            include = ""
        else:
            include = yaml.dump(include_dict, default_flow_style=False, indent=2)

            # ensure indentation level to be conserved
            if tick != "":
                include = tick + include
            if indent != "":
                indent_newline = indent + " " * len(tick)
                include = indent + include.replace("\n", indent_newline)
        content = content.replace(match, include)
        content = replace_aliases(matches_anchor, path + "/" + filename, content)

    # return new YAML
    return content


def include_parts(include: dict[str, Any], keys: str) -> dict[str, Any]:
    """
    Include nested contents from another YAML file.
    Args:
        include: dictionary based on YAML file from which the content is included.
        keys: keys of the included dictionary, where dots indicate the layer
    Returns:
        include: only the aimed layer of the original dictionary
    """
    if keys is None or keys == "":
        return include
    # parse key and get corresponding part of config
    keys = keys.strip()
    for key in keys.split("."):
        include = include[key]
    return include


def top_level_anchor_keywords(filename: str) -> set[str]:
    """
    Finds keys that hold an anchor ('&') at the top level (no leading whitespace) of the given
    file -- used to decide which keys are safe to drop from a whole-file include, without
    accidentally matching a nested key that happens to share its name with an unrelated anchor
    holder elsewhere in the file (`reload_anchors` matches anchors at any nesting depth).
    Args:
        filename: name of the file to scan.
    Returns:
        keywords: set of top-level keys that carry an anchor.
    """
    pattern = r"^(\S*): &(?:\S*)"
    with open(filename) as f:
        content = f.read()
    return set(re.findall(pattern, content, re.MULTILINE))


def reload_anchors(filename: str) -> list[tuple[str, str]]:
    """
    Finds anchors ('&') in the included file.
    Args:
        filename: name of the file with the anchor.
    Returns:
        matches: list of (keyword, anchor) pairs from reload_anchors.
    """
    pattern = r"(\S*): &(\S*)"
    with open(filename) as f:
        include_full_string = f.read()
        matches = re.findall(pattern, include_full_string)
    return matches


def replace_aliases(matches: list[tuple[str, str]], anchor_filename: str, alias_string: str) -> str:
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
