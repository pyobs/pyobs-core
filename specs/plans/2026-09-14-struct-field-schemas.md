# Plan: Publish struct field schemas in disco#info

Status: not started (pyobs-core#898)

`enum(Name)`-typed params/fields already publish their possible values in disco#info's
`<types>` block (`_wire_type()` records `enums[hint.__name__] = hint` as it walks a schema), so a
schema-driven client can build a populated `<select>` with no hardcoded per-interface knowledge.
`struct<Name>`-typed params get no equivalent treatment: `_wire_type()`
(`pyobs/comm/xmpp/serializer.py:428-430`) only ever emits the struct's name on the wire. A client
has no way to build an input form for a struct param from schema alone.

This is live, not hypothetical: `BaseTelescope.track_orbital_elements(elements: OrbitalElements)`
is a real struct-typed command on the dummy telescopes, reachable via pyobs-web-client's
`telescope.yaml` test fixtures, and neither its Shell nor pyobs-gui's generic command-caller can
build a form for it today.

Checked against the code (2026-09-14): the only real struct-typed command param in the repo today
is `OrbitalElements` (`pyobs/interfaces/IPointingOrbitalElements.py:13`), and it's flat — no field
is itself a dataclass. No consumer inside pyobs-core parses the `<types>` block back (only
produces it), and there's no existing test coverage of `_wire_type`/`_interface_schema_to_xml` to
account for. Client-side consumption (pyobs-web-client's `pyobs-codec.ts` parser,
`ParamForm.vue`/`ShellView.vue` nested-form case) is tracked separately in that repo's
`specs/plans/2026-08-03-struct-typed-command-params.md` and is out of scope here.

## Design

### `pyobs/comm/xmpp/serializer.py`

- `_wire_type()` gains a `structs: dict[str, list[tuple[str, str, str | None]]]` parameter,
  threaded alongside `enums` through all four call sites (`_interface_schema_to_xml`'s command-param
  loop and state-field loop, `_event_schema_to_xml`'s field loop, and `_wire_type`'s own recursive
  calls for `Annotated`/`Union`/`list`).
- New `depth: int = 0` parameter on `_wire_type`, incremented on entry to the dataclass branch.
  A struct is walked (its fields collected into `structs`) only when `depth <= 1` — i.e. the
  top-level struct and one level of struct-typed field nesting, matching the issue's "structs
  containing structs (one level of nesting)" scope. Beyond that, `_wire_type` still returns
  `struct<Name>` for the type string but does not add an entry to `structs`, so a client sees an
  unexpanded struct reference rather than the walk failing or looping.
  - This depth cap is the entire cycle-safety mechanism — no separate "seen" set is needed. A
    self-referential or mutually-recursive dataclass simply stops expanding after depth 1,
    the same as any other over-depth struct.
  - `structs` is keyed by name (like `enums`), so a struct referenced from multiple places is only
    walked/stored once — matching existing enum dedup behavior.
- New helper (name TBD, e.g. `_collect_struct_fields(cls, enums, structs, depth)`) that calls
  `get_type_hints(cls, include_extras=True)` + `dataclasses.fields(cls)` and appends
  `(field_name, type_str, unit_str)` tuples to `structs[cls.__name__]` — mirrors the existing
  state-field loop in `_interface_schema_to_xml` (lines 480-490) closely enough to justify
  factoring that loop to call the same helper, but that's a nice-to-have, not required for
  correctness.
- `_interface_schema_to_xml()` and `_event_schema_to_xml()`: after the existing `<enum>` block
  inside `<types>`, add one `<struct name="...">` element per entry in `structs` (sorted by name,
  same as enums), each containing `<field name="..." type="..." unit="...">` children in
  declaration order.

### Wire shape (example, `OrbitalElements`)

```xml
<types>
  <struct name="OrbitalElements">
    <field name="epoch" type="datetime"/>
    <field name="semi_major_axis" type="float64" unit="AU"/>
    <field name="eccentricity" type="float64"/>
    <field name="inclination" type="float64" unit="DEGREES"/>
    <field name="longitude_ascending_node" type="float64" unit="DEGREES"/>
    <field name="argument_of_periapsis" type="float64" unit="DEGREES"/>
    <field name="mean_anomaly" type="optional&lt;float64&gt;" unit="DEGREES"/>
    <field name="perihelion_time" type="optional&lt;datetime&gt;"/>
  </struct>
</types>
```

## Non-goals

- **Client-side parsing/forms** — pyobs-web-client and pyobs-gui work, tracked in their own repos
  (see above). Not touched here.
- **Arbitrary-depth struct nesting** — capped at one level per the issue and current real usage;
  revisit if a genuinely deep struct shows up.
- **Refactoring the three near-duplicate param/field/state-walking loops** in
  `_interface_schema_to_xml`/`_event_schema_to_xml` into one shared function — tempting given the
  new helper, but out of scope for this change; only pull the struct-field-walking piece out.

## Test plan

- [ ] New `tests/comm/test_xmpp_serializer_schema.py` covering `_wire_type`/`_interface_schema_to_xml`
      directly (no coverage exists today):
  - Flat struct param (`OrbitalElements`-shaped fixture) → `<types>` gets a `<struct>` with all
    fields, correct `type`/`unit` attribs, including an `optional<...>` field.
  - Struct field that is itself a dataclass (depth 1) → nested struct also appears in `<types>`.
  - Struct field nested two levels deep → inner-most struct type string is still `struct<Name>`,
    but no corresponding `<struct>` entry is emitted for it.
  - Self-referential dataclass (field typed as its own class) → schema build completes (no
    `RecursionError`/hang), outer struct's own fields are still fully expanded.
  - Struct containing an enum field → both `<enum>` and `<struct>` appear under the same `<types>`
    block, enum still deduped correctly.
  - Existing enum-only case (no structs involved) is unaffected — no empty `<struct>`/`<types>`
    noise when there are no structs to report.
- [ ] `tests/integration/test_xmpp_dummy_camera.py` (or wherever `track_orbital_elements`'s live
      disco#info is already exercised, if anywhere) — spot-check the real `OrbitalElements` schema
      end-to-end, not just via synthetic fixtures.
