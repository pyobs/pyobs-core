# Plan: `pyobs-gui` IAutoFocus widget

Status: implemented, closed. `AutoFocusWidget` shipped in pyobs-gui (`4d6a48c`, 2026-07-05).
Repos: pyobs-gui (widget), pyobs-core (`IAutoFocus`/`AutoFocusSeries` changes proposed here)

## Current state (pyobs-core, `develop`)

`IAutoFocus` (`pyobs/interfaces/IAutoFocus.py:30`) inherits only `IAbortable`, not `IRunning`:

```python
class IAutoFocus(IAbortable, metaclass=ABCMeta):
    state = AutoFocusState  # points: list[AutoFocusPoint], time
```

`AutoFocusState.points` (`IAutoFocus.py:25`) grows during a run — the sole implementation,
`AutoFocusSeries` (`pyobs/modules/focus/focusseries.py`), calls
`set_state(IAutoFocus, AutoFocusState(points=...))` once per focus step (`focusseries.py:224`)
after resetting the series at the start of `_auto_focus()`.

The module tracks a `self._running` flag locally (`focusseries.py:68`, set `True`/`False` around
the run at `126`/`131`) but never publishes it — there is no live "is this thing running" signal on
the wire. The only completion signal is `FocusFoundEvent` (`pyobs/events/focusfound.py`), sent once
on success; nothing is sent on failure or abort.

## Gap

A widget that didn't itself trigger the run (e.g. the scheduler ran an autofocus) has no way to know
a run started, and no way to know a run ended in *failure* — points just stop growing, silently.

## Proposed pyobs-core change

Add `IRunning` to `IAutoFocus`'s bases, and have `AutoFocusSeries` actually publish it:

```python
# IAutoFocus.py
from .IRunning import IRunning, RunningState

class IAutoFocus(IRunning, IAbortable, metaclass=ABCMeta):
    ...
```

```python
# focusseries.py
async def auto_focus(self, count: int, step: float, exposure_time: float, **kwargs: Any) -> AutoFocusResult:
    try:
        self._running = True
        await self.comm.set_state(IRunning, RunningState(running=True))
        focus, error = await self._auto_focus(count, step, exposure_time, **kwargs)
        return AutoFocusResult(focus=focus, focus_err=error)
    finally:
        self._running = False
        await self.comm.set_state(IRunning, RunningState(running=False))

async def is_running(self, **kwargs: Any) -> bool:
    return self._running
```

`AutoFocusState` and `RunningState` are independent pubsub topics (`set_state`/`subscribe_state` key
off the interface class passed in — confirmed against `pyobs/comm/comm.py:468,544`), so this
doesn't conflict with the existing points state, and mirrors the pattern `FocusWidget` already uses
for `IFocuser` + `IMotion`.

## Widget design (pyobs-gui)

A focus/value scatter plot, matplotlib-in-a-frame the same way `TemperaturesPlotWidget` does it
(`pyobs_gui/temperaturesplotwidget.py`), plus run controls.

Layout:
- `framePlot` — matplotlib canvas, x = focus, y = metric
- `spinCount` / `spinStep` / `spinExposureTime` — the three `auto_focus()` params
- `buttonRunAutoFocus` (green) / `buttonAbort` (red)
- `labelStatus` — Idle / Running... / `Focus: 12.345 ± 0.012 mm`

```python
class AutoFocusWidget(BaseWidget, Ui_AutoFocusWidget):
    signal_update_gui = QtCore.Signal()

    def __init__(self, **kwargs: Any):
        BaseWidget.__init__(self, **kwargs)
        self.setupUi(self)

        self._points: list[AutoFocusPoint] = []
        self._running = False
        self._last_result: tuple[float, float] | None = None

        self.figure, self.ax = plt.subplots()
        layout = QtWidgets.QVBoxLayout(self.framePlot)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.signal_update_gui.connect(self.update_gui)
        self.buttonRunAutoFocus.clicked.connect(self._run_auto_focus)
        self.buttonAbort.clicked.connect(self._abort)
        self.colorize_button(self.buttonRunAutoFocus, QtCore.Qt.GlobalColor.green)
        self.colorize_button(self.buttonAbort, QtCore.Qt.GlobalColor.red)

    async def _init(self) -> None:
        await self.comm.subscribe_state(self.module, IRunning, self._on_running_state)
        await self.comm.subscribe_state(self.module, IAutoFocus, self._on_autofocus_state)
        await self.comm.register_event(FocusFoundEvent, self._on_focus_found)

    def _on_running_state(self, state: RunningState) -> None:
        if state.running and not self._running:
            # rising edge -> a new run started (possibly triggered elsewhere), clear the plot
            self._points = []
            self._last_result = None
        self._running = state.running
        self.signal_update_gui.emit()

    def _on_autofocus_state(self, state: AutoFocusState) -> None:
        self._points = state.points
        self.signal_update_gui.emit()

    def _on_focus_found(self, event: FocusFoundEvent, sender: str) -> None:
        if sender != self.module:
            return
        self._last_result = (event.focus, event.error or 0.0)
        self.signal_update_gui.emit()

    def update_gui(self) -> None:
        self.buttonRunAutoFocus.setEnabled(not self._running)
        self.buttonAbort.setEnabled(self._running)
        self.labelStatus.setText(
            "Running..." if self._running
            else f"Focus: {self._last_result[0]:.3f} ± {self._last_result[1]:.3f} mm" if self._last_result
            else "Idle"
        )

        self.ax.clear()
        if self._points:
            self.ax.scatter([p.focus for p in self._points], [p.value for p in self._points], color="tab:blue")
        if self._last_result and not self._running:
            self.ax.axvline(self._last_result[0], color="tab:green", linestyle="--", label="fitted focus")
            self.ax.legend()
        self.ax.set_xlabel("Focus [mm]")
        self.ax.set_ylabel("Metric")
        self.ax.grid(linestyle=":", alpha=0.5)
        self.ax.set_axisbelow(True)
        self.canvas.draw()

    @qasync.asyncSlot()  # type: ignore
    async def _run_auto_focus(self) -> None:
        async with self.comm.proxy(self.module, IAutoFocus) as proxy:
            await proxy.auto_focus(self.spinCount.value(), self.spinStep.value(), self.spinExposureTime.value())

    @qasync.asyncSlot()  # type: ignore
    async def _abort(self) -> None:
        async with self.comm.proxy(self.module, IAutoFocus) as proxy:
            await proxy.abort()
```

The widget is entirely state-driven: `_run_auto_focus`/`_abort` just fire RPCs, and the display
updates purely from what the module publishes — correct with multiple GUI instances open, or a
scheduler-triggered run, unlike a design that tracks "am I running" as local widget state.

## Open questions

- `FocusFoundEvent` still isn't sent on failure/abort — with `RunningState` in place the widget at
  least knows the run *ended*, but not *why*. Worth a follow-up event (`FocusFailedEvent`?) or just
  leaving "Idle" as the catch-all for "not running, no success yet" and letting the operator check
  logs for failures.
- Should the fitted-focus vertical line persist across the next run's points, or clear immediately
  on the next rising edge? Current design clears it on rising edge (new run hides the old fit).
