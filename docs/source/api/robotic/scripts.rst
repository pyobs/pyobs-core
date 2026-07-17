Scripts (pyobs.robotic.scripts)
--------------------------------

A :class:`~pyobs.robotic.scripts.Script` is the leaf of the robotic system — it contains the actual
observing logic. Scripts are pydantic models (not :class:`~pyobs.modules.Module` subclasses), so they
have no async lifecycle of their own. Instead, they receive runtime context (``comm``, ``vfs``,
``observer``) injected at instantiation time, and they are created fresh for each task execution.


Writing a script
^^^^^^^^^^^^^^^^^

Subclass :class:`~pyobs.robotic.scripts.Script` and implement two async methods::

    import logging
    from typing import TYPE_CHECKING
    from pyobs.interfaces import ICamera, IPointingRaDec
    from pyobs.robotic.scripts import Script

    if TYPE_CHECKING:
        from pyobs.robotic.task import TaskData

    log = logging.getLogger(__name__)


    class ObserveScript(Script):
        camera: str = "camera"
        telescope: str = "telescope"
        exposure_time: float = 30.0
        num_exposures: int = 1

        async def can_run(self, data: TaskData | None) -> bool:
            try:
                await self.comm.proxy(self.camera, ICamera)
                await self.comm.proxy(self.telescope, IPointingRaDec)
            except ValueError:
                return False
            return True

        async def run(self, data: TaskData | None) -> None:
            if data is None or data.task.target is None:
                raise ValueError("No target.")

            camera = await self.comm.proxy(self.camera, ICamera)
            telescope = await self.comm.proxy(self.telescope, IPointingRaDec)

            from pyobs.utils.time import Time
            target = data.task.target.coordinates(Time.now())

            log.info("Moving telescope to %s...", data.task.target.name)
            await telescope.move_radec(target.ra.deg, target.dec.deg)

            for i in range(self.num_exposures):
                log.info("Taking exposure %d/%d...", i + 1, self.num_exposures)
                await camera.set_exposure_time(self.exposure_time)
                await camera.grab_data(broadcast=True)

**``can_run(data)``** is called by the scheduler before each scheduling cycle. Return ``False`` if
required hardware is offline or conditions are not met. The scheduler will exclude tasks whose
script returns ``False`` from the current slot.

**``run(data)``** is called by the mastermind when the task's scheduled time arrives. The
:class:`~pyobs.robotic.task.TaskData` argument gives access to the current task, the
``ObservationArchive``, and the ``TaskArchive``. Raise ``InterruptedError`` to signal that the
script was aborted cleanly.

The script is configured in the task YAML under the ``script`` key::

    script:
      class: myobs.scripts.ObserveScript
      camera: camera
      telescope: telescope
      exposure_time: 60.0
      num_exposures: 3


Runtime context
^^^^^^^^^^^^^^^^

Scripts have access to the same runtime properties as :class:`~pyobs.object.Object` via
``PrivateAttrMixin``:

- ``self.comm`` — :class:`~pyobs.comm.Comm` for calling other modules
- ``self.vfs`` — :class:`~pyobs.vfs.VirtualFileSystem` for file I/O
- ``self.observer`` — :class:`~astroplan.Observer` with the observatory location
- ``self.location`` — :class:`~astropy.coordinates.EarthLocation`
- ``self.timezone`` — :class:`~datetime.tzinfo`

These are injected automatically when the script is created via
:meth:`~pyobs.object.Object.pyobs_model_validate`. They are never set during ``__init__`` or
pydantic validation — they are only available when the script is instantiated at runtime from
within an :class:`~pyobs.object.Object` context.


TaskData
^^^^^^^^^

:class:`~pyobs.robotic.task.TaskData` is passed to both ``can_run`` and ``run``. It is a simple
dataclass that bundles references to the relevant parts of the robotic system::

    @dataclass
    class TaskData:
        task: Task
        observation_archive: ObservationArchive | None = None
        task_archive: TaskArchive | None = None

Most scripts only need ``data.task`` (for the target and duration). Scripts that need to record
results or look up task history can use ``data.observation_archive``.


Script base class
^^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.robotic.scripts.Script
   :members:
   :show-inheritance:

.. autoexception:: pyobs.robotic.scripts.ScriptError
   :members:
   :show-inheritance:


Built-in scripts
^^^^^^^^^^^^^^^^^

Observing
"""""""""

.. autoclass:: pyobs.robotic.scripts.imaging.imaging.ImagingScript
   :members:
   :show-inheritance:

*The default script for science exposures: moves to the target, optionally acquires and
guides on it, then works through one or more* ``instrument_configs`` *(binning, window,
exposure time, filter, image type), each repeated* ``count`` *times, for* ``repeats`` *full
passes.*

.. autoclass:: pyobs.robotic.scripts.imaging.transitimaging.TransitImagingScript
   :members:
   :show-inheritance:

*An* :class:`~pyobs.robotic.scripts.imaging.imaging.ImagingScript` *subclass that repeats its
instrument configurations for as long as a transit window is open, instead of a fixed number
of times. Requires a* :class:`~pyobs.robotic.scheduler.merits.TransitMerit` *on the task.*

.. autoclass:: pyobs.robotic.scripts.imaging.autofocus.AutoFocusScript
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scripts.calibration.darkbias.DarkBiasScript
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scripts.calibration.skyflats.SkyFlatsScript
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scripts.calibration.pointing.PointingScript
   :members:
   :show-inheritance:

*Points the telescope at the sky position configured for flat-fielding (via a*
:class:`~pyobs.robotic.utils.skyflats.pointing.SkyFlatsBasePointing`\\ *), without taking any
exposures itself — typically run just before a* :class:`~pyobs.robotic.scripts.calibration.skyflats.SkyFlatsScript`.


Control flow
"""""""""""""

These scripts do not perform observations themselves — they compose other scripts into more complex
execution patterns. They can be nested arbitrarily.

.. autoclass:: pyobs.robotic.scripts.control.sequential.SequentialRunner
   :members:
   :show-inheritance:

*Run a list of scripts one after the other. By default, checks that all scripts can run before
starting. Set ``check_all_can_run: false`` to only check the first.*

.. autoclass:: pyobs.robotic.scripts.control.parallel.ParallelRunner
   :members:
   :show-inheritance:

*Run a list of scripts concurrently using* ``asyncio.gather``. *Useful for simultaneously
operating two independent hardware systems.*

.. autoclass:: pyobs.robotic.scripts.control.conditional.ConditionalRunner
   :members:
   :show-inheritance:

*Evaluate a Python expression and run either a ``true`` or ``false`` sub-script. The expression
context provides ``now`` as a UTC* ``datetime``.

.. autoclass:: pyobs.robotic.scripts.control.cases.CasesRunner
   :members:
   :show-inheritance:

*Evaluate an expression and select a sub-script from a dict of cases. Supports an ``else`` key
for a default.*

.. autoclass:: pyobs.robotic.scripts.control.selector.SelectorScript
   :members:
   :show-inheritance:

*Switch a module implementing* :class:`~pyobs.interfaces.IMode` *to a specified mode.*

.. autoclass:: pyobs.robotic.scripts.utils.callmodule.CallModuleScript
   :members:
   :show-inheritance:

*Call an arbitrary method on any module by name. Useful for one-off actions without writing a
full script class.*

.. autoclass:: pyobs.robotic.scripts.utils.log.LogScript
   :members:
   :show-inheritance:

*Evaluate a Python expression and log the result. Useful for debugging.*

.. autoclass:: pyobs.robotic.scripts.utils.debugtrigger.DebugTriggerScript
   :members:
   :show-inheritance:

*Sets its own* ``triggered`` *flag to* ``True`` *when run and does nothing else. Useful as a
minimal, dependency-free script for testing scheduling and task-runner behavior without any
real hardware.*


Sky flat utilities
^^^^^^^^^^^^^^^^^^

These classes support the :class:`~pyobs.robotic.scripts.calibration.skyflats.SkyFlatsScript` script and are configured as
nested objects within it.

.. autoclass:: pyobs.robotic.utils.skyflats.FlatFielder
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.skyflats.pointing.SkyFlatsBasePointing
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.skyflats.pointing.SkyFlatsStaticPointing
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.skyflats.priorities.SkyflatPriorities
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.skyflats.priorities.ConstSkyflatPriorities
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.skyflats.priorities.ArchiveSkyflatPriorities
   :members:
   :show-inheritance: