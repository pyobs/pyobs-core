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
