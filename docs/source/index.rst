Welcome to *pyobs*!
===================

Overview
--------

**pyobs** is a Python framework for building and operating **autonomous, robotic, or remote astronomical observatories**.
It provides the software foundation to integrate and control telescopes, cameras, domes, weather sensors, and scheduling systems — all within a unified and modular environment.

The framework’s design philosophy emphasizes *flexibility* and *extensibility*: users configure observatory systems declaratively (typically in YAML) by combining reusable modules for hardware control, data processing, scheduling, and supervision.
pyobs allows a telescope to perform fully automated observation cycles, from calibration to data acquisition and archiving.

The main project, :code:`pyobs-core`, provides the central infrastructure and abstract interfaces.
Additional repositories (e.g. :code:`pyobs-asi`, :code:`pyobs-gui`, :code:`pyobs-alpaca`) implement specific hardware drivers or user interfaces.

Key Features
------------

* **Hardware abstraction and drivers** — Uniform interfaces for cameras, telescopes, domes, filter wheels, and other devices.
* **Automation and scheduling** — Enables robotic operation, observing task management, and integration with external schedulers such as Las Cumbres Observatory.
* **Data acquisition and processing** — Supports image calibration, photometry, source extraction, and catalog creation through configurable processing pipelines.
* **Distributed operation** — Modules can run across multiple machines and communicate via a networked messaging system.
* **Configuration-based architecture** — Observatory setups are defined in YAML files, reducing the need for custom programming.
* **Extensibility** — Users can develop their own modules or extend existing ones for new instruments, sensors, or observatory logic.
* **Integration ecosystem** — Companion packages add support for specific cameras (ASI, SBIG, QHYCCD), focusing motors, GUIs, weather interfaces, and astrometry services.

Architecture
------------

pyobs follows a **modular, event-driven design**.
Each *module* represents a component of the observatory — for example, a camera controller, a scheduler, or a weather monitor.
Modules communicate asynchronously, exchanging commands, data, and events across a network interface.

The architecture is guided by several principles:

* **Separation of concerns:** hardware drivers, control logic, and data handling are implemented as independent modules.
* **Asynchronous operation:** observing workflows (e.g., exposures, readout, dome movement) are non-blocking and concurrent.
* **Abstraction layers:** standardized interfaces define contracts for hardware and services, ensuring hardware independence.
* **Declarative configuration:** module connections and behaviors are defined via configuration files rather than code.

Ecosystem and Repositories
--------------------------

The pyobs organization on GitHub hosts a family of repositories:

- **pyobs-core** — The main framework providing interfaces, module management, and communication infrastructure.
- **pyobs-asi**, **pyobs-qhyccd**, **pyobs-sbig** — Drivers for various astronomical cameras.
- **pyobs-aravis** — Support for Aravis-compatible industrial cameras.
- **pyobs-zwoeaf** — Module for ZWO EAF focus motors.
- **pyobs-pilar** — Interface to the Pilar telescope control system.
- **pyobs-alpaca** — ASCOM Alpaca bridge for interoperability with other software.
- **pyobs-gui** — Graphical user interface for controlling and monitoring observatories.
- **pyobs-astrometry** — Web service wrapper for `astrometry.net` solve-field operations.

Together, these components form a complete, extensible observatory control system.

Use Cases
---------

pyobs can be employed in a wide variety of astronomical contexts:

1. **Fully autonomous telescopes**
   Execute entire observing nights automatically: select targets, take images, perform calibrations, and archive data.
2. **Remote operation**
   Allow human operators to control observatory components from remote locations through network interfaces or GUIs.
3. **Instrument prototyping**
   Rapidly integrate new instruments or devices by implementing small interface modules.
4. **Data-driven feedback**
   Integrate real-time image analysis (e.g., source detection or quality metrics) to influence scheduling or instrument control.
5. **Educational or small observatories**
   Run simplified setups for student projects or research with minimal overhead.

Limitations and Outlook
-----------------------

While powerful, pyobs remains an evolving system:

* Configuration files can become complex in large installations.
* Hardware-specific behavior may still require custom handling.
* Full test coverage across all modules is an ongoing effort.
* Performance tuning may be necessary for high-throughput environments.

Despite these caveats, pyobs continues to mature as a robust, open-source platform for observatory automation and control.

Telescopes
----------
*pyobs* currently runs on five telescopes around the world:

- **MONET/North** (McDonald Observatory, Texas) and **MONET/South** (SAAO, South Africa)
- **IAG 50cm** (Göttingen, Germany)
- **IAG VTT** (Göttingen, Germany)

.. image:: /_static/monet.png
   :height: 100px
.. image:: /_static/IAG_LogoRGB_small.gif
   :height: 100px

Further Reading
---------------

- Project site: https://github.com/pyobs/
- Core framework: https://github.com/pyobs/pyobs-core
- Documentation: https://docs.pyobs.org/
- Scientific reference: *Frontiers in Astronomy and Space Sciences* (2022), “pyobs: A Modular Control System for Astronomical Observatories”

Introduction
------------

.. toctree::
   :maxdepth: 1

   quickstart
   installing
   development
   overview
   cli

Recipes
-------

.. toctree::
   :maxdepth: 1

   recipes/simulation
   recipes/jupyter

Config Examples
---------------

.. toctree::
   :maxdepth: 1

   config_examples/iag50cm
   config_examples/iagvt

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api/index
   modules/index
   addmod/index


Affiliated projects
-------------------

.. toctree::
   :maxdepth: 1

   pyobs-weather <https://docs.pyobs.org/projects/pyobs-weather/en/latest/>
   pyobs-archive <https://docs.pyobs.org/projects/pyobs-archive/en/latest/>


Project details
---------------

.. toctree::
   :maxdepth: 1

   project/changelog
   Team <https://www.pyobs.org/team/>
   project/license
   project/3rdparty


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
