from __future__ import annotations

import pytest
import yaml

from pyobs.utils.config import include_parts, pre_process_yaml, reload_anchors

# ── include_parts ─────────────────────────────────────────────────────────────


def test_include_parts_empty_key_returns_full() -> None:
    d = {"a": {"b": 1}}
    assert include_parts(d, "") == d


def test_include_parts_none_key_returns_full() -> None:
    d = {"a": 1}
    assert include_parts(d, None) == d


def test_include_parts_single_key() -> None:
    d = {"a": {"b": 1}, "c": 2}
    assert include_parts(d, "a") == {"b": 1}


def test_include_parts_nested_key() -> None:
    d = {"a": {"b": {"c": 42}}}
    assert include_parts(d, "a.b") == {"c": 42}


def test_include_parts_deep_nested_key() -> None:
    d = {"a": {"b": {"c": {"d": "value"}}}}
    assert include_parts(d, "a.b.c") == {"d": "value"}


def test_include_parts_strips_whitespace() -> None:
    d = {"a": 1}
    assert include_parts(d, " a ") == 1


def test_include_parts_missing_key_raises() -> None:
    d = {"a": 1}
    with pytest.raises(KeyError):
        include_parts(d, "b")


# ── reload_anchors ────────────────────────────────────────────────────────────


def test_reload_anchors_finds_anchors(tmp_path) -> None:
    yaml_file = tmp_path / "anchors.yaml"
    yaml_file.write_text("camera: &cam_anchor\n  type: DummyCamera\n")
    matches = reload_anchors(str(yaml_file))
    assert ("camera", "cam_anchor") in matches


def test_reload_anchors_empty_file(tmp_path) -> None:
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("no_anchor: value\n")
    assert reload_anchors(str(yaml_file)) == []


def test_reload_anchors_multiple_anchors(tmp_path) -> None:
    yaml_file = tmp_path / "multi.yaml"
    yaml_file.write_text("a: &anchor_a\n  x: 1\nb: &anchor_b\n  y: 2\n")
    matches = reload_anchors(str(yaml_file))
    assert len(matches) == 2


# ── pre_process_yaml ──────────────────────────────────────────────────────────


def test_pre_process_yaml_simple(tmp_path) -> None:
    """A plain YAML file with no includes is returned unchanged."""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("camera:\n  type: DummyCamera\n")
    result = pre_process_yaml(str(yaml_file))
    assert "DummyCamera" in result


def test_pre_process_yaml_include(tmp_path) -> None:
    """Include block is replaced by the contents of the included file."""
    included = tmp_path / "camera.yaml"
    included.write_text("type: DummyCamera\nexposure_time: 1.0\n")

    main = tmp_path / "config.yaml"
    main.write_text("camera:\n  {include camera.yaml}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["camera"]["type"] == "DummyCamera"
    assert parsed["camera"]["exposure_time"] == 1.0


def test_pre_process_yaml_include_with_key(tmp_path) -> None:
    """Include block with key extracts only the specified section."""
    included = tmp_path / "modules.yaml"
    included.write_text("camera:\n  type: DummyCamera\ntelescope:\n  type: DummyTelescope\n")

    main = tmp_path / "config.yaml"
    main.write_text("cam:\n  {include modules.yaml camera}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["cam"]["type"] == "DummyCamera"
    assert "telescope" not in str(parsed.get("cam", {}))


def test_pre_process_yaml_include_nested_key(tmp_path) -> None:
    """Include with dotted key traverses nested dict."""
    included = tmp_path / "nested.yaml"
    included.write_text("a:\n  b:\n    value: 42\n")

    main = tmp_path / "config.yaml"
    main.write_text("result:\n  {include nested.yaml a.b}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["result"]["value"] == 42


def test_pre_process_yaml_recursive_include(tmp_path) -> None:
    """Included files can themselves include other files."""
    deep = tmp_path / "deep.yaml"
    deep.write_text("value: deep\n")

    mid = tmp_path / "mid.yaml"
    mid.write_text("mid_val: 1\ndeep:\n  {include deep.yaml}\n")

    main = tmp_path / "config.yaml"
    main.write_text("root:\n  {include mid.yaml}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["root"]["deep"]["value"] == "deep"


def test_pre_process_yaml_preserves_indentation(tmp_path) -> None:
    """Included content is properly indented."""
    included = tmp_path / "sub.yaml"
    included.write_text("x: 1\ny: 2\n")

    main = tmp_path / "config.yaml"
    main.write_text("outer:\n  inner:\n    {include sub.yaml}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["outer"]["inner"]["x"] == 1
    assert parsed["outer"]["inner"]["y"] == 2


# ── anchor/alias resolution (comm_cfg pattern) ──────────────────────────────────


def test_pre_process_yaml_alias_resolves_to_anchor_value(tmp_path) -> None:
    """`<<: *anchor` pulls in the anchor-holder's value from the included file.

    This is the `comm.shared.yaml` pattern: a shared file defines `comm_cfg: &comm {...}`, and
    consuming files write `comm:\n  <<: *comm\n  user: ...`. `replace_aliases` (config.py) is what
    performs this substitution; until this test, it had no coverage at all.
    """
    shared = tmp_path / "comm.shared.yaml"
    shared.write_text("comm_cfg: &comm\n  class: pyobs.comm.xmpp.XmppComm\n  domain: example.com\n")

    main = tmp_path / "config.yaml"
    main.write_text("{include comm.shared.yaml}\n\ncomm:\n  <<: *comm\n  user: imagedb\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["comm"]["class"] == "pyobs.comm.xmpp.XmppComm"
    assert parsed["comm"]["domain"] == "example.com"
    assert parsed["comm"]["user"] == "imagedb"


def test_pre_process_yaml_keyed_include_of_anchor_holder_is_kept(tmp_path) -> None:
    """A key-selected include of the anchor-holder's own key must still return its value.

    Only a whole-file `{include file}` (no key selector) is the accidental-leak shape; explicitly
    selecting the anchor-holder's key is a deliberate direct use and must not be stripped by a future
    fix that drops anchor-holder keys from whole-file splices.
    """
    shared = tmp_path / "comm.shared.yaml"
    shared.write_text("comm_cfg: &comm\n  class: pyobs.comm.xmpp.XmppComm\n  domain: example.com\n")

    main = tmp_path / "config.yaml"
    main.write_text("direct:\n  {include comm.shared.yaml comm_cfg}\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert parsed["direct"]["class"] == "pyobs.comm.xmpp.XmppComm"


def test_pre_process_yaml_whole_file_include_does_not_leak_anchor_holder_key(tmp_path) -> None:
    """A whole-file include must not leave the anchor-holder key as a top-level leftover.

    Regression test for the `comm_cfg` leak documented in
    `specs/plans/2026-08-09-object-kwarg-validation.md`: `{include comm.shared.yaml}` (no key
    selector) used to splice the *entire* file, including `comm_cfg` itself, even though its only
    purpose is to be aliased via `<<: *comm` elsewhere. `comm_cfg` then survived as an unconsumed
    top-level key that reached `Object.__init__`'s `**kwargs` and was silently dropped there.
    """
    shared = tmp_path / "comm.shared.yaml"
    shared.write_text("comm_cfg: &comm\n  class: pyobs.comm.xmpp.XmppComm\n  domain: example.com\n")

    main = tmp_path / "config.yaml"
    main.write_text("{include comm.shared.yaml}\n\ncomm:\n  <<: *comm\n  user: imagedb\n")

    result = pre_process_yaml(str(main))
    parsed = yaml.safe_load(result)
    assert "comm_cfg" not in parsed, (
        "comm_cfg leaked into the top-level config dict from a whole-file include -- "
        "see specs/plans/2026-08-09-object-kwarg-validation.md"
    )
