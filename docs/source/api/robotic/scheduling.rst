Scheduling (pyobs.robotic.scheduler)
-------------------------------------

This page documents the data model and scheduling logic of the robotic system. For a conceptual
overview see :doc:`index`. For a worked setup example see :doc:`/recipes/robotic`.


Task and Observation
^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.robotic.task.Task` is the fundamental unit of work. It is a pydantic model, so it is
fully described by its YAML representation and can be validated, serialised, and round-tripped
without any custom code::

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
      - class: pyobs.robotic.scheduler.merits.TransitMerit
        jd0: 2459000.5
        period: 3.14
        duration: 7200

    script:
      class: myobs.scripts.ObserveScript
      camera: camera
      telescope: telescope

An :class:`~pyobs.robotic.observation.Observation` is a scheduled instance of a task — it adds a
concrete ``start`` and ``end`` time, a ``priority`` score, and an
:class:`~pyobs.robotic.observation.ObservationState`. The scheduler produces ``Observation`` objects;
the mastermind consumes them.

.. autoclass:: pyobs.robotic.task.Task
   :members:

.. autoclass:: pyobs.robotic.task.Project
   :members:

.. autoclass:: pyobs.robotic.task.TaskData
   :members:

.. autoclass:: pyobs.robotic.observation.Observation
   :members:

.. autoclass:: pyobs.robotic.observation.ObservationState
   :members:


Targets
^^^^^^^^

A :class:`~pyobs.robotic.scheduler.targets.Target` defines where to point the telescope. It is a
:class:`~pyobs.robotic.utils.serialization.PolymorphicBaseModel`, so any subclass can appear in
the task YAML via the ``class:`` key.

The ``coordinates(time)`` method accepts a :class:`~pyobs.utils.time.Time` and returns a
:class:`~astropy.coordinates.SkyCoord`, which lets non-sidereal targets compute their position
on the fly::

    target:
      class: pyobs.robotic.scheduler.targets.SiderealTarget
      name: M51
      ra: 202.47
      dec: 47.20

.. autoclass:: pyobs.robotic.scheduler.targets.Target
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.targets.SiderealTarget
   :members:
   :show-inheritance:


Constraints
^^^^^^^^^^^^

A :class:`~pyobs.robotic.scheduler.constraints.Constraint` answers a binary question: *may this
task run at this time?* If any constraint returns ``False``, the task is excluded from scheduling
entirely for that slot.

Constraints appear in the task YAML under the ``constraints`` key (per-task) or under the
``OnDemandScheduler.constraints`` key (global, applied to every task).

To write a custom constraint, subclass :class:`~pyobs.robotic.scheduler.constraints.Constraint`
and implement ``__call__`` and ``to_astroplan``::

    from pyobs.robotic.scheduler.constraints import Constraint

    class MyConstraint(Constraint):
        min_elevation: float = 30.0

        def to_astroplan(self):
            return astroplan.AltitudeConstraint(min=self.min_elevation * u.deg)

        async def __call__(self, time, task, data) -> bool:
            if task.target is None:
                return False
            alt = data.observer.altaz(time, task.target).alt.deg
            return alt >= self.min_elevation

.. autoclass:: pyobs.robotic.scheduler.constraints.Constraint
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.constraints.AirmassConstraint
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.constraints.SolarElevationConstraint
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.constraints.MoonIlluminationConstraint
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.constraints.MoonSeparationConstraint
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.constraints.TimeConstraint
   :members:
   :show-inheritance:


Merits
^^^^^^^

A :class:`~pyobs.robotic.scheduler.merits.Merit` answers a continuous question: *how desirable is
it to run this task right now?* It returns a float in the range ``[0, N]``. All merit values for a
task are multiplied together along with the task's ``priority`` and the project's ``priority`` to
produce a single score. The task with the highest score wins each time slot.

A merit returning ``0.0`` has the same effect as a constraint returning ``False`` — the task is
excluded from that slot. This lets merits double as soft constraints when needed.

Every merit's ``__call__`` receives three arguments: ``time``, ``task``, and ``data``. The
``data`` argument is a :class:`~pyobs.robotic.scheduler.dataprovider.DataProvider` which gives
access to:

- ``data.observer`` — the :class:`~astroplan.Observer` for the site
- ``data.last_sunset(time)`` / ``data.last_sunrise(time)`` — cached sunrise/sunset times
- ``data.night(time)`` — the calendar date of the observing night
- ``data.archive`` — an :class:`~pyobs.robotic.scheduler.observationarchiveevolution.ObservationArchiveEvolution`
  that provides historical and simulated-future observations

To query past observations from within a merit, use ``data.archive.get_observations()`` rather
than accessing the archive directly. This ensures the lookahead cache is used during scheduling::

    from pyobs.robotic.scheduler.merits import Merit
    from pyobs.robotic.observation import ObservationState

    class MyMerit(Merit):
        min_days: float = 7.0

        async def __call__(self, time, task, data) -> float:
            from astropy.time import TimeDelta
            import astropy.units as u

            observations = await data.archive.get_observations(
                task=task,
                state=ObservationState.COMPLETED,
                start_after=time - TimeDelta(self.min_days * u.day),
            )
            return 0.0 if len(observations) > 0 else 1.0

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Returns 1.0 when…
   * - :class:`~pyobs.robotic.scheduler.merits.ConstantMerit`
     - Always. Useful as a baseline or placeholder.
   * - :class:`~pyobs.robotic.scheduler.merits.AfterTimeMerit`
     - The current time is after the configured time.
   * - :class:`~pyobs.robotic.scheduler.merits.BeforeTimeMerit`
     - The current time is before the configured time.
   * - :class:`~pyobs.robotic.scheduler.merits.TimeWindowMerit`
     - The current time falls within one of the configured windows.
   * - :class:`~pyobs.robotic.scheduler.merits.TransitMerit`
     - A transit is imminent (based on period and JD of first transit).
   * - :class:`~pyobs.robotic.scheduler.merits.IntervalMerit`
     - Enough time has passed since the last observation of this task.
   * - :class:`~pyobs.robotic.scheduler.merits.PerNightMerit`
     - The task has not yet reached its maximum observations-per-night count.
   * - :class:`~pyobs.robotic.scheduler.merits.FollowMerit`
     - A specified other task has already completed this night.
   * - :class:`~pyobs.robotic.scheduler.merits.RandomMerit`
     - Always (but with added Gaussian noise — useful for breaking ties randomly).

.. autoclass:: pyobs.robotic.scheduler.merits.Merit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.ConstantMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.AfterTimeMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.BeforeTimeMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.TimeWindowMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.TransitMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.IntervalMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.PerNightMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.FollowMerit
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.merits.RandomMerit
   :members:
   :show-inheritance:


Scheduler
^^^^^^^^^^

*pyobs-core* ships two :class:`~pyobs.robotic.scheduler.TaskScheduler` implementations. Both are
configured as a nested object inside the :class:`~pyobs.modules.robotic.Scheduler` module::

    scheduler:
      class: pyobs.robotic.scheduler.OnDemandScheduler  # or AstroplanScheduler
      twilight: astronomical
      constraints:
        - class: pyobs.robotic.scheduler.constraints.SolarElevationConstraint
          max_solar_elevation: -12.0

The ``constraints`` block defines *global* constraints applied to every task in addition to each
task's own constraints. Note that global constraints are only supported by
:class:`~pyobs.robotic.scheduler.OnDemandScheduler` — :class:`~pyobs.robotic.scheduler.AstroplanScheduler`
applies only per-task constraints.



.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Class
     - Strategy
   * - :class:`~pyobs.robotic.scheduler.OnDemandScheduler`
     - Greedy, on-demand scheduling. Evaluates constraints and merits at each time step and picks
       the highest-scoring task. Robust to interruptions — re-runs from the current moment.
       Supports merits, global constraints, and lookahead to avoid missing higher-priority tasks.
   * - :class:`~pyobs.robotic.scheduler.AstroplanScheduler`
     - Full-night planning via :mod:`astroplan`'s ``PriorityScheduler``. Computes a fixed schedule
       for the entire night in one pass, running the heavy computation in a separate process to
       avoid blocking the event loop. Only supports :class:`~pyobs.robotic.scheduler.targets.SiderealTarget`
       and per-task constraints (not merits). Use when you need a committed nightly plan rather
       than rolling on-demand decisions.

.. autoclass:: pyobs.robotic.scheduler.TaskScheduler
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.OnDemandScheduler
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.AstroplanScheduler
   :members:
   :show-inheritance:


Task and Observation archives
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.robotic.taskarchive.TaskArchive` and
:class:`~pyobs.robotic.observationarchive.ObservationArchive` are abstract base classes defining
the interface that the :class:`~pyobs.modules.robotic.Scheduler` and
:class:`~pyobs.modules.robotic.Mastermind` modules depend on. *pyobs-core* ships three concrete
implementations of each — see :ref:`archive-implementations` below.

.. autoclass:: pyobs.robotic.taskarchive.TaskArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.observationarchive.ObservationArchive
   :members:
   :show-inheritance:


.. _archive-implementations:

Archive implementations
""""""""""""""""""""""""

**Filesystem** (``pyobs.robotic.filesystem``)

Tasks are YAML files in a directory; observations are YAML files named by night. No external
services required — the simplest setup for a single telescope.

.. autoclass:: pyobs.robotic.filesystem.YamlTaskArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.filesystem.YamlObservationArchive
   :members:
   :show-inheritance:

**Backend** (``pyobs.robotic.backend``)

Tasks and observations are managed by the *pyobs-robotic-backend* HTTP service. Enables
multi-telescope coordination, a web UI for queue management, and centralised logging.

.. autoclass:: pyobs.robotic.backend.BackendTaskArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.backend.BackendObservationArchive
   :members:
   :show-inheritance:

**Las Cumbres Observatory** (``pyobs.robotic.lco``)

Integration with the `Las Cumbres Observatory <https://lco.global>`_ observation portal. Tasks are
fetched from the LCO portal API using an instrument type and authorisation token; observations are
read from and written back to the LCO schedule. Also includes
:class:`~pyobs.robotic.lco.LcoTaskRunner`, which maps LCO request configurations to the
appropriate :class:`~pyobs.robotic.scripts.Script` subclass based on a configurable scripts map.

.. autoclass:: pyobs.robotic.lco.LcoTaskArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.lco.LcoObservationArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.lco.LcoTaskRunner
   :members:
   :show-inheritance:

Image archives
^^^^^^^^^^^^^^

:class:`~pyobs.robotic.utils.archive.Archive` is the base class used by
:class:`~pyobs.robotic.utils.skyflats.priorities.ArchiveSkyflatPriorities` to query historical
observations when calculating flat-field priorities. Concrete implementations are configured via
the ``class:`` key like any other polymorphic model.

.. autoclass:: pyobs.robotic.utils.archive.Archive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.archive.PyobsArchive
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.archive.LocalArchive
   :members:
   :show-inheritance:

Scheduling internals
^^^^^^^^^^^^^^^^^^^^^

These classes are used internally by the scheduler and are relevant mainly when writing custom
merit functions.

:class:`~pyobs.robotic.scheduler.dataprovider.DataProvider` is passed to every
:class:`~pyobs.robotic.scheduler.merits.Merit` and
:class:`~pyobs.robotic.scheduler.constraints.Constraint` during a scheduling run. It provides
cached access to site geometry (sunrise, sunset, night boundaries) and to the observation
history via its ``archive`` attribute.

:class:`~pyobs.robotic.scheduler.observationarchiveevolution.ObservationArchiveEvolution` wraps
the real :class:`~pyobs.robotic.observationarchive.ObservationArchive` with two additions:

- **Caching** — observations for each task are fetched from the archive once per scheduling run
  and cached in memory, avoiding repeated HTTP requests during evaluation of many time slots.
- **Lookahead simulation** — as the scheduler plans ahead and tentatively assigns tasks to future
  slots, it calls ``evolve()`` to record those assignments. Subsequent merit evaluations for the
  same task then see those simulated observations, so ``IntervalMerit`` and ``PerNightMerit``
  correctly prevent the same task from being scheduled twice in one run.

.. autoclass:: pyobs.robotic.scheduler.dataprovider.DataProvider
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.scheduler.observationarchiveevolution.ObservationArchiveEvolution
   :members:
   :show-inheritance: