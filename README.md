pyobs
=====

http://www.pyobs.org/


Quick start
-----------

Create a directory and a virtual environment:

    mkdir test
    cd test
    python3 -m venv venv

Activate environment and install pyobs-core:

    source venv/bin/activate
    pip3 install pyobs-core

Create a test configuration test.yaml:

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10

And run it:

    pyobs test.yaml


Optional extras
----------------
A few features require additional dependencies that aren't installed by default:

    pip3 install "pyobs-core[full]"

adds support for things like INDI/telegram/matrix notifications, image processing (photutils, ccdproc, sep) and
a few other optional integrations.

    pip3 install "pyobs-core[gui]"

adds the PySide6/qfitswidget-based Qt widgets used by the camera GUIs shipped with the various `pyobs-*` camera
modules (e.g. `pyobs-asi`, `pyobs-qhyccd`).


CLI tools
---------
Installing *pyobs-core* provides three console scripts:

* `pyobs` runs a single module configuration in the foreground.
* `pyobsd` runs and manages one or more module configurations as background daemons.
* `pyobsw` is the Windows equivalent of `pyobs`.


Development
-----------
Clone the repository and install it with [uv](https://docs.astral.sh/uv/), including the dev dependency group:

    git clone https://github.com/pyobs/pyobs-core.git
    cd pyobs-core
    uv sync --all-extras --dev
