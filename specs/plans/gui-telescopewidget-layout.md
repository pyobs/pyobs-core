# Plan: `pyobs-gui` TelescopeWidget layout — width floor investigation & design notes

Status: proposed — exploratory, not yet implemented.
Repos: pyobs-gui (all implementation here, `pyobs_gui/telescopewidget.py`,
`pyobs_gui/qt/telescopewidget.ui`, and the composed widgets it embeds (`CompassMoveWidget`,
`FilterWidget`, `FocusWidget`, `TemperaturesWidget`))

## Problem statement

`TelescopeWidget` has a large minimum width (~830px). The top-level layout
(`horizontalLayout_7` in `telescopewidget.ui`) places four groupboxes side by
side in one `QHBoxLayout`:

- `groupStatus` (~184px)
- `groupBox_5` — "Move", containing `stackedMove`, a `QStackedWidget` with one
  page per coordinate type (~339px, set by the widest page)
- `groupBox` — "Offsets" (~179px)
- `compassmovewidget` — the jog/compass control (~270px)

A `QHBoxLayout` needs room for all four simultaneously, so the minimum width
is roughly the sum of their individual minimums.

## What the current code actually does

Before proposing changes, we read the real source rather than guessing at the
structure. Key findings:

### Coordinate-type selection is already a combobox, not tabs

`comboMoveType` is a `QComboBox` (`telescopewidget.ui:183`) driving
`stackedMove`. It's populated conditionally in `open()` based on which
interfaces the module implements:

```python
if IPointingRaDec in self._interfaces:
    self.comboMoveType.addItem(COORDS.EQUITORIAL.value)
if IPointingAltAz in self._interfaces:
    self.comboMoveType.addItem(COORDS.HORIZONTAL.value)
if IPointingHGS in self._interfaces or IPointingHelioprojective in self._interfaces:
    self.comboMoveType.addItem(COORDS.HELIOGRAPHIC_STONYHURST.value)
    ...
```
(`telescopewidget.py:147-156`)

This already scales fine to more coordinate types — a combobox doesn't care
whether it has 5 items or 50. Adding new coordinate systems in the future is
not, by itself, a layout risk.

### Each coordinate-type page has a fixed, hand-built field set

`pageMoveEquatorial` (RA/Dec + Simbad/JPL/solar-system lookups),
`pageMoveHorizontal` (Alt/Az), and `pageMoveOrbitElements` (7 orbital
elements in a 4-column grid, the widest page) are each individually authored
`.ui` pages, not generated from a schema. "Variable content depending on
module capabilities" does not mean per-field dynamic generation within a
page — it means *which whole pages/sections appear at all*.

### Capability-driven visibility is handled by toggling pre-built sections on/off

- `groupEquatorialOffsets` / `groupHorizontalOffsets` inside the "Offsets"
  groupbox are each `setVisible()`'d independently based on `IOffsetsRaDec` /
  `IOffsetsAltAz` (`telescopewidget.py:159-160`). They stack vertically in a
  `QVBoxLayout`, so this variability affects height, not width — already the
  right shape.
- `FilterWidget`, `FocusWidget`, `TemperaturesWidget` are conditionally added
  to a **separate sidebar area** via `add_to_sidebar()`, not the
  four-groupbox row (`telescopewidget.py:163-168`). They don't contribute to
  the row's minimum width at all.

### One widget already does genuine dynamic-field generation

`TemperaturesWidget`'s `formLayout` starts **empty** in the `.ui` file, and
rows are added at runtime, one per sensor reported in `ITemperatures` state:

```python
for key in sorted(self._temps.keys()):
    if key not in self._widgets:
        widget = QtWidgets.QLineEdit()
        ...
        layout.addRow(key + ":", widget)
        self._widgets[key] = widget
```
(`temperatureswidget.py:44-52`)

This is a working precedent for a genuinely capability-driven field count,
just for sensor readings rather than coordinate fields.

### Filter, Focus, and the offsets rows are structurally duplicated

`FilterWidget` (current value + `set...`, plus status) and `FocusWidget`
(current value, base + `set...`, offset + `set...` + `reset`, plus status)
are separately hand-laid-out `QFormLayout`s that implement the same idiom as
each other and as the offsets rows (`textOffsetRA` + `buttonSetRaOffset` +
`buttonResetEquatorialOffsets`). Three (at least) independently maintained
implementations of "labeled value with an optional settable target and
reset."

## Root cause of the width floor

`QStackedWidget` sizes itself to the **largest** of all its pages, not the
currently visible one — by design, to avoid the window jumping around when
the user switches pages. That's why `pageMoveOrbitElements`'s ~339px sets
the floor even when a narrower page (e.g. Horizontal) is selected.

This matters more than it might seem, precisely *because* adding new
coordinate types is easy (see above): every new page — a satellite/TLE page,
an Alt/Az-with-refraction page, anything — permanently raises this floor for
every module using this widget, forever, even though only one page is ever
shown at a time.

## Recommended fixes (roughly in order of leverage vs. effort)

### 1. Make the stacked widget size to the current page, not the widest one

```python
class MoveStack(QtWidgets.QStackedWidget):
    def sizeHint(self) -> QtCore.QSize:
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self) -> QtCore.QSize:
        return self.currentWidget().minimumSizeHint()
```

Call `self.stackedMove.updateGeometry()` inside `select_coord_type()` when
the index changes. Trade-off: the window will visibly resize when someone
switches coordinate type. Given that's a deliberate, infrequent action, this
seems like a reasonable trade against permanently reserving width for pages
that usually aren't shown — and it directly future-proofs against new
coordinate-type pages ratcheting the floor up further.

### 2. Adopt a width convention for future coordinate-type pages

Until/unless (1) is done, hold new pages to the existing Orbit Elements
page's 4-column grid convention (the current widest page) rather than
letting each new page grow independently.

### 3. `QFormLayout::setRowWrapPolicy()` on the individual form pages

`WrapLongRows` (or `WrapAllRows`) makes each label/field pair drop the field
below its label when the row doesn't fit, instead of the row forcing extra
width. Applies directly to `pageMoveEquatorial`, `FilterWidget`, and
`FocusWidget`, all of which already use `QFormLayout`. Low-risk, no
structural change, adopt regardless of anything else here.

### 4. Resize-driven reparenting for the four-groupbox row

Build two pre-constructed layouts (current wide row, and a two-row grouping
— e.g. Status + Compass on top, Move + Offsets below) and swap widgets
between them on `resizeEvent()`:

```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    narrow = self.width() < 700
    if narrow != self._is_narrow:
        self._is_narrow = narrow
        target_layout = self.narrow_layout if narrow else self.wide_layout
        for w in (self.groupBox_5, self.groupBox):
            w.setParent(None)
            target_layout.addWidget(w)
```

This is the practical way to get "reflow at a breakpoint" in `QtWidgets` —
there's no declarative CSS-media-query equivalent, so this has to be written
by hand and is easy to get subtly wrong (reparenting order, stale size
hints) if not careful. Only worth doing if (1)–(3) don't get the floor low
enough on their own.

## Longer-term / larger-scope ideas (not committed, worth discussing before building)

- **A shared `PropertyRow` component** (label, read-only current value,
  optional target field, optional `set`/`reset` buttons) to replace the
  duplicated idiom in `FilterWidget`, `FocusWidget`, and the offsets rows.
  Less duplicated layout code, more visual consistency.
- **Extend the `TemperaturesWidget` dynamic-row pattern** to other
  capability-driven panels if/when they need a variable field count, since
  it's already proven to work here.
- **Unifying Status/Filter/Focus/Temperatures into one sidebar visual
  language** — appealing, but `add_to_sidebar()` may be a generic mechanism
  shared by other module-type widgets (cameras, domes, etc.), not just
  telescopes. Worth reading `base.py` and checking who else calls
  `add_to_sidebar()` before restyling it just for this widget, to avoid
  creating visual inconsistency elsewhere in the app.

## Open questions to resolve before implementing anything above

- **Compass icon direction**: `buttonOffsetEast` uses
  `arrow-alt-circle-left-solid.svg` and `buttonOffsetWest` uses
  `arrow-alt-circle-right-solid.svg` (`compassmovewidget.ui:19-56`) — east
  points left, west points right. Could be intentional (some
  telescope/eyepiece/guider views mirror east-west), could be a leftover
  icon swap. Worth checking against actual finder/guider view orientation
  before touching this widget.
- What's the realistic upper bound on fields for a single coordinate-type
  page, looking at the actual `IPointing*` interfaces? If orbit elements (7
  fields) is close to the ceiling, the fixed-page approach is fine
  long-term. If future interfaces could need significantly more fields, a
  more dynamic form-generation approach (schema-driven, à la
  `TemperaturesWidget`) might be worth the extra investment after all.
