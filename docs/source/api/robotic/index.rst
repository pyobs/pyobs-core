Robotic mode (pyobs.robotic)
----------------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   scheduling
   scripts
   serialization

*pyobs* can operate a telescope fully autonomously. In robotic mode, a pool of pending observation
tasks is continuously scheduled and executed without human intervention. This section describes the
architecture of the robotic system and how its components fit together.


Architecture
^^^^^^^^^^^^

The robotic system is built around five concepts:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Concept
     - Role
   * - **Task**
     - A unit of work: what to observe, how long it takes, when it may run, and what script to execute.
   * - **Observation**
     - A scheduled instance of a task: a task assigned a concrete start and end time.
   * - **Scheduler**
     - Evaluates the pool of tasks and calculates which should run next, producing a sequence of
       ``Observation`` objects.
   * - **Mastermind**
     - Watches the schedule and, at the right moment, hands each ``Observation`` to the ``TaskRunner``
       for execution.
   * - **Script**
     - The observing logic itself: move the telescope, take exposures, save images.

The flow through the system looks like this:

.. code-block:: none

                      ┌─────────────┐
                      │ TaskArchive │  ← task pool (files, backend, LCO portal)
                      └──────┬──────┘
                             │ schedulable tasks
                             ▼
   ┌──────────────────────────────────────────────┐
   │  Scheduler module                            │
   │                                              │
   │   for each time slot:                        │
   │     evaluate Constraints  → gate (yes/no)    │
   │     evaluate Merits       → rank (0..N)      │
   │     pick highest-ranked eligible task        │
   └──────────────────┬───────────────────────────┘
                      │ Observation (task + start + end)
                      ▼
             ┌─────────────────────┐
             │ ObservationArchive  │  ← persists the schedule
             └──────────┬──────────┘
                        │ next pending Observation
                        ▼
   ┌────────────────────────────────────┐
   │  Mastermind module                 │
   │                                    │
   │   at scheduled time:               │
   │     TaskRunner.run_task(task)      │
   └────────────────┬───────────────────┘
                    │
                    ▼
             ┌─────────────┐
             │   Script    │  ← the actual observing logic
             └─────────────┘


Module layer vs. robotic layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It helps to distinguish two layers:

The **module layer** (``pyobs.modules.robotic``) contains the long-running *pyobs* processes you
start from YAML config files — :class:`~pyobs.modules.robotic.Scheduler` and
:class:`~pyobs.modules.robotic.Mastermind`. These are full :class:`~pyobs.modules.Module` subclasses
with ``comm``, background tasks, and event subscriptions.

The **robotic layer** (``pyobs.robotic``) contains the data and logic objects that the modules
orchestrate — ``Task``, ``Script``, ``Constraint``, ``Merit``, ``OnDemandScheduler``, and the
archive classes. These are either :class:`~pyobs.object.Object` subclasses or pydantic models,
not modules, and are configured as nested objects inside the module YAML.

This means a typical deployment YAML for the scheduler module looks like::

    class: pyobs.modules.robotic.Scheduler    # ← module layer

    scheduler:
      class: pyobs.robotic.scheduler.OnDemandScheduler  # ← robotic layer
      twilight: astronomical

    tasks:
      class: pyobs.robotic.filesystem.YamlTaskArchive   # ← robotic layer
      path: /robotic/tasks/

    schedule:
      class: pyobs.robotic.filesystem.YamlObservationArchive  # ← robotic layer
      path: /opt/pyobs/robotic/observations/


Tasks and scheduling
^^^^^^^^^^^^^^^^^^^^^

A :class:`~pyobs.robotic.task.Task` carries four kinds of information:

- **Identity** — ``id``, ``name``, ``project``, ``priority``
- **Scheduling metadata** — ``duration``, ``constraints``, ``merits``, ``target``
- **Script config** — the ``script`` block that defines what to do when the task runs
- **State** — tracked indirectly via ``Observation`` objects in the ``ObservationArchive``

**Constraints** answer a binary question: *may this task run right now?* If any constraint returns
``False``, the task is excluded from consideration for that time slot entirely. Examples: airmass
too high, sun still up, outside the allowed time window.

**Merits** answer a continuous question: *how desirable is it to run this task right now?* All merit
values for a task are multiplied together (along with ``priority`` and project priority) to produce
a single score. The task with the highest score in each time slot wins. Examples: transit timing,
time since last observation, distance from a preferred window.

The clean separation between constraints (hard gates) and merits (soft ranking) means you can
express complex scheduling policies entirely in YAML without writing any code. See
:doc:`scheduling` for the full list of built-in constraints and merits.


Scheduler re-triggering
^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~pyobs.modules.robotic.Scheduler` module recalculates the schedule whenever
``_need_update`` is set. This happens automatically in several situations:

- The task pool changes (a task is added, removed, or modified in the ``TaskArchive``)
- A :class:`~pyobs.events.GoodWeatherEvent` arrives, carrying an ETA for when observing can resume
- A :class:`~pyobs.events.TaskStartedEvent` arrives (if ``trigger_on_task_started: true``)
- A :class:`~pyobs.events.TaskFinishedEvent` arrives (if ``trigger_on_task_finished: true``)
- The ``run()`` method is called manually (e.g. from the GUI)

To avoid submitting a stale schedule while a new one is being calculated, the scheduler submits
the *first* task immediately as soon as it is found, then submits the rest once the full run
completes. If a new update is requested mid-run, the partial results are discarded.


Scripts
^^^^^^^^

A :class:`~pyobs.robotic.scripts.Script` is the leaf of the system — it does the actual work.
Scripts are pydantic models (not modules), so they are fully described by their YAML config and
have access to ``comm``, ``vfs``, and ``observer`` injected at runtime.

A ``Script`` has two methods:

- ``can_run(data)`` — called by the scheduler to check whether the script's hardware is currently
  available. Return ``False`` if a required module is offline.
- ``run(data)`` — called by the mastermind to execute the script. Receives a
  :class:`~pyobs.robotic.task.TaskData` object giving access to the current task, the
  ``ObservationArchive``, and the ``TaskArchive``.

Built-in scripts cover common observing tasks (autofocus, sky flats, dark/bias frames) and
control flow (sequential, parallel, conditional). See :doc:`scripts` for details.


Archive implementations
^^^^^^^^^^^^^^^^^^^^^^^^

Both ``TaskArchive`` and ``ObservationArchive`` are abstract base classes. *pyobs-core* ships
three concrete implementations:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Implementation
     - Use case
   * - ``pyobs.robotic.filesystem``
     - Tasks and observations stored as YAML files on disk. The simplest setup — no external
       services required. Good for single-telescope systems.
   * - ``pyobs.robotic.backend``
     - Tasks and observations managed by the *pyobs-robotic-backend* HTTP service. Enables
       multi-telescope coordination and a web UI for queue management.
   * - ``pyobs.robotic.lco``
     - Integration with the Las Cumbres Observatory observation portal. Used for LCO-connected
       telescopes.


Further reading
^^^^^^^^^^^^^^^

- :doc:`scheduling` — full API reference for ``Task``, ``Observation``, constraints, merits,
  targets, and scheduler implementations
- :doc:`scripts` — full API reference for ``Script`` and all built-in script classes
- :doc:`serialization` — how ``BaseModel`` and ``PolymorphicBaseModel`` enable YAML-driven
  instantiation of pydantic models
- :doc:`/recipes/robotic` — step-by-step recipe for setting up a minimal robotic system