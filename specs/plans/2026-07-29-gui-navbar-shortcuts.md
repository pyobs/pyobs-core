# Plan: `pyobs-gui` navbar keyboard shortcuts

Status: implemented, closed.

Repos: pyobs-gui (all implementation here, `pyobs_gui/mainwindow.py`)

## Motivation

The module sidebar (`listPages` in `pyobs_gui/mainwindow.py`) is mouse-only today. As more
modules connect, switching pages means scrolling/scanning a growing list. Strategy games solve
the analogous "many things, pick one fast" problem with control groups: select something, hit
a modifier+number to bind it to slot `N`, then a (lighter) modifier+number always jumps back to
it. This doc proposes the same scheme for the navbar.

## Key scheme

All shortcuts always require at least `Ctrl`, deliberately — see "Why Ctrl always, not bare
digits" below.

- **Fixed, non-reassignable**: `Ctrl+1` = Shell, `Ctrl+2` = Events, `Ctrl+3` = Status. These are
  the three always-present "Tools" pages (each individually optional via the `show_shell`/
  `show_events`/`show_status` constructor flags). If a page wasn't created, its key simply does
  nothing.
- **User-assignable**: `4, 5, 6, 7, 8, 9, 0` (7 slots). While any page is selected in the navbar,
  `Ctrl+Alt+N` binds that page to slot `N`. Afterwards, pressing `Ctrl+N` switches to whichever
  page is currently bound to slot `N`. Rebinding (`Ctrl+Alt+N` while a different page is selected)
  silently overwrites the previous binding for that slot — no confirmation, matching game
  convention. Binding a Tools page is allowed too (e.g. `Ctrl+Alt+4` while "Shell" is selected just
  means both `Ctrl+1` and `Ctrl+4` now go to Shell) — no special-casing needed.
- **Session-only**: bindings live only in memory for the lifetime of the running `MainWindow`;
  nothing is persisted to disk. No settings-persistence mechanism (`QSettings` or otherwise)
  exists anywhere in pyobs-gui today, and none is needed for this.

## Why `Ctrl` always, not bare digits

An earlier version of this design used bare digit keys (`4` to recall, `Ctrl+4` to bind), and an
empirical test (see the git history of this doc / prior discussion) confirmed that actually works
correctly for every widget checked (`QLineEdit`, `QSpinBox`, `QListWidget`'s own type-ahead search,
`QPushButton`) — Qt's `QEvent.Type.ShortcutOverride` mechanism means text/numeric-entry widgets
already claim digit keypresses for themselves before shortcut dispatch runs. But that guarantee is
per-widget-type and was only checked for the widget types known to exist in this app today; a
future or third-party custom widget could plausibly bind raw digit keys for its own purpose
without implementing that protection correctly. Requiring `Ctrl` (or `Ctrl+Alt`) sidesteps the
question entirely: no text-entry or numeric-entry widget anywhere treats `Ctrl+3` as "type a 3",
so there is nothing to verify per-widget — the guarantee is structural, not empirical. The
tradeoff is one extra key for recall (`Ctrl+N` instead of bare `N`), which still fits the
strategy-game feel closely enough.

## State

```python
# module-level, next to the existing _PAGE_ORDER
_FIXED_SHORTCUTS: Dict[str, str] = {"1": "Shell", "2": "Events", "3": "Status"}
_ASSIGNABLE_SLOTS: List[str] = ["4", "5", "6", "7", "8", "9", "0"]
```

```python
# in __init__, near the existing self._widgets: Dict[str, QtWidgets.QWidget] = {}
self._slot_bindings: Dict[str, str] = {}   # e.g. {"4": "camera", "0": "Status"}
```

Keys are the literal key-character strings (`"4"`, `"0"`, …), not ints — avoids ambiguity around
slot `"0"` and lets `QKeySequence(digit)` / `QKeySequence(f"Ctrl+{digit}")` be built directly from
the same string.

## Binding is by page name, not by widget or list-item instance

Module pages are dynamic — they appear when a module connects (`ModuleOpenedEvent` ->
`_client_connected`) and disappear when it disconnects (`ModuleClosedEvent` ->
`_client_disconnected`). Storing `self._slot_bindings` as slot -> page *name* rather than a
widget/item reference means a module that disconnects and reconnects later in the same session
automatically keeps its old binding: `_client_disconnected` deletes `self._widgets[client]` but
never touches `self._slot_bindings`, so `_recall_slot` for that slot just sees its bound name is
no longer in `self._widgets` and silently no-ops; on reconnect, `_client_connected` repopulates
`self._widgets[client]` under the same name and the old binding "comes back to life" with zero
extra bookkeeping. **No changes needed to `_client_connected`/`_client_disconnected` at all.**

## Visual badge — a colored circle with the digit inside, via a custom item delegate

The user wants a persistent, colored badge next to the name: a filled circle containing the slot
digit, sized to match the row's font (not tiny). An initial version used a raised Unicode
superscript digit instead; superseded by this circle design per explicit follow-up feedback.

A Unicode "negative circled digit" glyph (`❶❷❸...`, U+2776–U+277F) was considered as a
lower-code alternative to manually drawing the circle, and empirically confirmed to render
correctly (as a solid disc with the digit as a "hole" showing whatever's behind it) in this
environment's font-fallback chain. Rejected anyway, for the same reason the shortcut scheme
requires `Ctrl` everywhere rather than relying on verified-but-still-per-widget/per-font behavior:
that glyph's availability isn't guaranteed across every font this GUI might end up running under,
whereas a manually-drawn ellipse renders identically regardless of font support. It also gives
exact control over the circle's size (`fm.height()`, guaranteed to track the row's actual font)
rather than whatever proportions a fallback font's glyph design happens to use.

`QListWidgetItem.text()` is currently overloaded as *both* the displayed label and the canonical
identity key used everywhere (`_change_page`'s `client = item.text()` lookup into `self._widgets`,
`_client_disconnected`'s text-scan removal, `PagesListWidgetItem.__lt__`'s text-based sort).
Baking a badge into `.text()` itself would require refactoring all of those to a separate
`UserRole`-based identity key first. A `QStyledItemDelegate` avoids that refactor entirely: paint
the badge as an overlay at render time, while `.text()` stays exactly what it is today (the plain
name, still the canonical identity key everywhere).

```python
class NavPageItemDelegate(QtWidgets.QStyledItemDelegate):
    """Paints listPages rows normally, then overlays a small colored circular badge (digit
    inside a filled circle, sized to match the row's font) right after the name for any page
    currently bound to a slot. Reads slot_bindings live (not a snapshot), so it always reflects
    the latest bindings without needing to be reconstructed."""

    def __init__(self, slot_bindings: Dict[str, str], parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._slot_bindings = slot_bindings  # same dict instance MainWindow mutates

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem,
              index: QtCore.QModelIndex | QtCore.QPersistentModelIndex) -> None:
        super().paint(painter, option, index)  # unchanged icon + name + selection rendering

        name = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        slot = next((s for s, bound_name in self._slot_bindings.items() if bound_name == name), None)
        if slot is None:
            return

        # position the badge just after the rendered name
        fm = option.fontMetrics
        has_icon = index.data(QtCore.Qt.ItemDataRole.DecorationRole) is not None
        icon_w = option.decorationSize.width() + 4 if has_icon else 0
        text_x = option.rect.left() + icon_w + 4
        text_w = fm.horizontalAdvance(name)

        # circle diameter matches the row's font size
        diameter = fm.height()
        cx = text_x + text_w + 4 + diameter / 2
        cy = option.rect.center().y()

        # on a selected row, the row background itself is painted in the Highlight color, so a
        # Highlight-filled circle there would blend in -- swap the fill/text colors so the badge
        # still stands out against a Highlight-colored row background
        is_selected = bool(option.state & QtWidgets.QStyle.StateFlag.State_Selected)
        fill_role = QtGui.QPalette.ColorRole.HighlightedText if is_selected else QtGui.QPalette.ColorRole.Highlight
        text_role = QtGui.QPalette.ColorRole.Highlight if is_selected else QtGui.QPalette.ColorRole.HighlightedText

        painter.save()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(option.palette.color(fill_role))
        painter.drawEllipse(QtCore.QPointF(cx, cy), diameter / 2, diameter / 2)

        painter.setFont(option.font)
        painter.setPen(option.palette.color(text_role))
        circle_rect = QtCore.QRectF(cx - diameter / 2, cy - diameter / 2, diameter, diameter)
        painter.drawText(circle_rect, QtCore.Qt.AlignmentFlag.AlignCenter, slot)
        painter.restore()
```

**Bug found during verification, now fixed**: an earlier version always used the palette's
`Highlight` role for the badge's fill color. That's invisible on the *currently selected* row,
since Qt already paints the selected row's background in that same `Highlight` color —
confirmed visually via an offscreen render before being caught. Fixed by checking
`option.state & QtWidgets.QStyle.StateFlag.State_Selected` and swapping the fill/text color pair
(`Highlight`/`HighlightedText`) so the badge always contrasts against the row background,
selected or not.

Install once in `__init__`, after `setupUi`:

```python
self.listPages.setItemDelegate(NavPageItemDelegate(self._slot_bindings, self))
```

Since the delegate holds a reference to the *same* `self._slot_bindings` dict `_bind_slot` mutates
(not a copy), no extra syncing is needed — but Qt still needs to be told to repaint after a
binding changes, since nothing else triggers that automatically. Add one line to `_bind_slot`:

```python
self.listPages.viewport().update()
```

Colors use the palette's `Highlight`/`HighlightedText` roles so the badge adapts to the active Qt
theme instead of a hardcoded color. The status-bar toast in `_bind_slot` (see below) stays as a
complementary "just happened" confirmation alongside the persistent badge.

## Shortcut wiring

17 `QShortcut` objects total (`QtGui.QShortcut`/`QtGui.QKeySequence` — **not** `QtWidgets`, that's
a Qt5-ism), created once in `__init__` via a new `self._setup_shortcuts()` call (after `setupUi`
and the new state above): 3 fixed (`Ctrl+1/2/3`) + 7 `Ctrl+N` recall + 7 `Ctrl+Alt+N` bind. Each is
a long-lived object whose handler does a *dynamic* lookup at press-time — module pages come and
go, but slot numbers are fixed for the app's lifetime, so shortcuts are never recreated.

```python
def _setup_shortcuts(self) -> None:
    self._shortcuts: List[QtGui.QShortcut] = []

    for key, name in _FIXED_SHORTCUTS.items():
        sc = QtGui.QShortcut(QtGui.QKeySequence(f"Ctrl+{key}"), self)
        sc.activated.connect(lambda name=name: self._go_to_page(name))
        self._shortcuts.append(sc)

    for slot in _ASSIGNABLE_SLOTS:
        recall = QtGui.QShortcut(QtGui.QKeySequence(f"Ctrl+{slot}"), self)
        recall.activated.connect(lambda slot=slot: self._recall_slot(slot))
        self._shortcuts.append(recall)

        bind = QtGui.QShortcut(QtGui.QKeySequence(f"Ctrl+Alt+{slot}"), self)
        bind.activated.connect(lambda slot=slot: self._bind_slot(slot))
        self._shortcuts.append(bind)
```

**Gotcha**: the `slot=slot`/`name=name` default-argument capture is required — without it, every
lambda in the loop closes over the same loop variable and all shortcuts end up firing for the
*last* value (`"0"`). `self._shortcuts` is kept mainly so the objects are inspectable/debuggable;
Qt's parent-child ownership (`self` as parent) would keep them alive either way.

Default `QShortcut` context is `Qt.ShortcutContext.WindowShortcut` (fires whenever the window is
active, regardless of which child widget has focus) — exactly right here, no `setContext(...)`
needed.

```python
def _go_to_page(self, name: str) -> None:
    """Fixed Ctrl+1/2/3 handler. No-ops if the page was never created."""
    if name not in self._widgets:
        return
    self._select_page_by_name(name)

def _select_page_by_name(self, name: str) -> None:
    """Selects the listPages row for `name`; selection change drives the existing
    currentRowChanged -> _change_page path, so this never touches stackedWidget directly."""
    for row in range(self.listPages.count()):
        item = self.listPages.item(row)
        if item is not None and item.text() == name:
            self.listPages.setCurrentRow(row)
            return

def _bind_slot(self, slot: str) -> None:
    """Ctrl+Alt+N: binds the currently selected page to slot N, silently overwriting any
    previous binding for that slot."""
    item = self.listPages.currentItem()
    if item is None:
        return
    name = item.text()
    if name not in self._widgets:  # defensive; headers are NoItemFlags and unselectable anyway
        return
    self._slot_bindings[slot] = name
    self.statusBar().showMessage(f"Bound Ctrl+{slot} to '{name}'", 3000)

def _recall_slot(self, slot: str) -> None:
    """Ctrl+N: switches to whatever is bound to slot N. No-ops if unbound or disconnected."""
    name = self._slot_bindings.get(slot)
    if name is None or name not in self._widgets:
        return
    self._select_page_by_name(name)
```

Place these four methods right after `_change_page`, since they're the same "navbar page
switching" cluster.

**Conflict safety**: since every shortcut here requires at least `Ctrl`, there's no need for the
per-widget-type empirical verification a bare-digit scheme would need (see "Why Ctrl always,
not bare digits" above) — no text/numeric-entry widget anywhere treats `Ctrl+3` or `Ctrl+Alt+3`
as ordinary input, so this is safe by construction rather than by testing each widget type. Still
worth a quick manual sanity check after implementation (see Verification below), mainly to confirm
nothing *else* in the app (e.g. a future custom widget) has already claimed one of these
combinations for something unrelated.

## File changes

Everything lives in `pyobs_gui/mainwindow.py` — new constants near `_PAGE_ORDER`, new
`self._slot_bindings` state and `self._setup_shortcuts()` call in `__init__`, and five new
methods (`_setup_shortcuts`, `_go_to_page`, `_select_page_by_name`, `_bind_slot`, `_recall_slot`).
No `.ui` changes.

## Verification (once implemented)

1. Start `test/full.yaml`. Confirm `Ctrl+1`/`Ctrl+2`/`Ctrl+3` jump to Shell/Events/Status. Confirm
   they no-op (no crash, no switch) when a page was disabled (e.g. `show_shell: false` in the YAML
   config).
2. Focus the Shell command-input line edit, type a command containing digits (e.g. `status 123`);
   confirm the digits appear as typed text and no page switch happens. Repeat with a numeric spin
   box (e.g. Camera's exposure time) — this should already be a non-issue given the `Ctrl`
   requirement, but worth a quick check anyway.
3. Select the "camera" page, press `Ctrl+Alt+4`; confirm the status-bar toast and the superscript
   badge appear, and that `Ctrl+4` returns to it from anywhere else in the app.
4. Stop the dummy camera module (triggers `ModuleClosedEvent`); confirm its nav entry disappears
   and pressing `Ctrl+4` does nothing (no exception). Reconnect it under the same name; confirm its
   nav entry reappears (badge included) and `Ctrl+4` immediately works again, with no need to
   re-press `Ctrl+Alt+4`.
5. With slot `4` still bound to "camera", select "telescope" and press `Ctrl+Alt+4`; confirm the
   toast shows the new binding with no confirmation prompt, the badge moves to "telescope", and
   `Ctrl+4` now goes to telescope.
6. ruff + pyrefly on `mainwindow.py`.
