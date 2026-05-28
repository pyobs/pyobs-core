**TODO: Check functionality and add reference to this**

Setting up a minimal robotic observation system
-----------------------------------------------

This recipe shows how to configure a self-contained robotic observation system using only
*pyobs-core*. By the end you will have a working setup where:

- tasks are defined as YAML files on disk,
- the scheduler calculates which task to run next based on constraints and merits,
- the mastermind executes each task in sequence,
- and a custom script does the actual observing work.

The recipe deliberately avoids external services (no HTTP backend, no LCO portal) so you can
run it on a single machine with only a simulated telescope and camera.

.. note::
    This recipe builds on the simulation setup in :doc:`simulation`. Make sure you have a working
    ``telescope.yaml`` and ``camera.yaml`` before continuing.


Overview
^^^^^^^^

A robotic *pyobs* system has five moving parts:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Component
     - Role
   * - **TaskArchive**
     - Reads the pool of available tasks (from files, a database, or a remote service).
   * - **ObservationArchive**
     - Persists the computed schedule and tracks which observations are pending, running, or done.
   * - **Scheduler** module
     - Runs the :class:`~pyobs.robotic.scheduler.OnDemandScheduler` in a loop, calculating the
       next observation and writing it to the ``ObservationArchive``.
   * - **Mastermind** module
     - Watches the ``ObservationArchive`` and, at the right time, calls the ``TaskRunner`` to
       execute the next observation.
   * - **Script**
     - The actual observing logic: move telescope, expose camera, save image.


Step 1 — Write a task YAML file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tasks are the unit of work in the robotic system. Each task carries scheduling metadata
(constraints, merits, target) and a ``script`` block that defines what to do when it runs.

Create a directory ``/opt/pyobs/robotic/tasks/`` and save this as ``observe_m51.yaml``::

    name: Observe M51
    duration: 120.0
    priority: 1.0

    target:
      class: pyobs.robotic.scheduler.targets.SiderealTarget
      ra: 202.47
      dec: 47.20

    constraints:
      - class: pyobs.robotic.scheduler.constraints.AirmassConstraint
        max_airmass: 2.0

    merits:
      - class: pyobs.robotic.scheduler.merits.ConstantMerit
        merit: 1.0

    script:
      class: myobs.scripts.ObserveScript
      camera: camera
      telescope: telescope
      exposure_time: 30.0
      num_exposures: 3

``duration`` is in seconds and tells the scheduler how long to reserve for this task.
``constraints`` define when the task *may* run; ``merits`` influence which task among eligible
ones is chosen first. Both accept lists so multiple can be stacked.


Step 2 — Write a Script
^^^^^^^^^^^^^^^^^^^^^^^^

A :class:`~pyobs.robotic.scripts.Script` is a pydantic model that implements the actual
observing logic. Create ``myobs/scripts.py``::

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

            log.info("Done.")

Two things worth noting:

- ``can_run`` is called by the scheduler before each scheduling cycle to determine whether the
  task is currently executable. Return ``False`` if required hardware is unavailable.
- ``run`` has access to the full :class:`~pyobs.robotic.task.TaskData` including the
  ``ObservationArchive`` and ``TaskArchive``, if needed.


Step 3 — Configure the Scheduler module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~pyobs.modules.robotic.Scheduler` module runs the scheduling loop. Save as
``scheduler.yaml``::

    {include _environment.yaml}

    class: pyobs.modules.robotic.Scheduler

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: scheduler@my.observatory.org

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        robotic:
          class: pyobs.vfs.LocalFile
          root: /opt/pyobs/robotic/

    scheduler:
      class: pyobs.robotic.scheduler.OnDemandScheduler
      twilight: astronomical
      constraints:
        - class: pyobs.robotic.scheduler.constraints.SolarElevationConstraint
          max_solar_elevation: -12.0

    tasks:
      class: pyobs.robotic.filesystem.YamlTaskArchive
      path: /robotic/tasks/

    schedule:
      class: pyobs.robotic.filesystem.YamlObservationArchive
      path: /opt/pyobs/robotic/observations/

    schedule_range: 8.0
    safety_time: 60

The ``constraints`` block on ``OnDemandScheduler`` defines *global* constraints that apply to
every task, in addition to each task's own constraints. Here we require the sun to be at least
12° below the horizon. ``schedule_range`` limits how far into the future the scheduler plans
(in hours).


Step 4 — Configure the Mastermind module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~pyobs.modules.robotic.Mastermind` module watches the schedule and runs each
observation when its time comes. Save as ``mastermind.yaml``::

    {include _environment.yaml}

    class: pyobs.modules.robotic.Mastermind

    comm:
      class: pyobs.comm.xmpp.XmppComm
      jid: mastermind@my.observatory.org

    vfs:
      class: pyobs.vfs.VirtualFileSystem
      roots:
        robotic:
          class: pyobs.vfs.LocalFile
          root: /opt/pyobs/robotic/

    schedule:
      class: pyobs.robotic.filesystem.YamlObservationArchive
      path: /opt/pyobs/robotic/observations/

    runner:
      class: pyobs.robotic.TaskRunner

    tasks:
      class: pyobs.robotic.filesystem.YamlTaskArchive
      path: /robotic/tasks/

    allowed_late_start: 120
    allowed_overrun: 60

``allowed_late_start`` is how many seconds past a scheduled start time the mastermind will still
attempt to run a task. ``allowed_overrun`` is how far past the scheduled end time a running task
is allowed to continue before being aborted.


Step 5 — Run the system
^^^^^^^^^^^^^^^^^^^^^^^^

Start all five modules, each in its own terminal::

    pyobs telescope.yaml
    pyobs camera.yaml
    pyobs scheduler.yaml
    pyobs mastermind.yaml

Once the scheduler has run, check ``/opt/pyobs/robotic/observations/`` for a YAML file containing
the computed schedule. The mastermind will pick it up and begin executing tasks at the right time.

To trigger an immediate reschedule (e.g. after adding a new task file), call the scheduler's
``run`` method from the GUI or via the CLI.


Where to go next
^^^^^^^^^^^^^^^^

- Add more task YAML files to ``/robotic/tasks/`` to build up an observing queue.
- Implement more :class:`~pyobs.robotic.scripts.Script` subclasses for different observation
  types (flat fields, focus runs, spectroscopy).
- Replace ``YamlTaskArchive`` and ``YamlObservationArchive`` with
  :class:`~pyobs.robotic.backend.BackendTaskArchive` and
  :class:`~pyobs.robotic.backend.BackendObservationArchive` to use the *pyobs-robotic-backend*
  web service for multi-telescope coordination.
- Add :class:`~pyobs.robotic.scheduler.merits.TransitMerit` or
  :class:`~pyobs.robotic.scheduler.merits.TimeWindowMerit` to the task YAML files for more
  sophisticated scheduling.