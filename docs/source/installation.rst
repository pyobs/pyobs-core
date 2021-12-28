.. _installing:

Installation
============

Python version
--------------

*pyobs* needs at Python version 3.7 or higher to work. It likes running on Linux (and a few modules will only run
there), but it can also live in a Windows or MacOS environment.


Dependencies
------------

These dependencies will be installed together with *pyobs-core*:

- `APLpy <https://aplpy.github.io/>`_ is the Astronomical Plotting Library in Python.
- `Astropy <https://www.astropy.org/>`_ is a set of interoperable astronomy packages.
- `astroplan <https://astroplan.readthedocs.io/>`_ is an Astropy affiliated package for observation planning.
- `colour <https://github.com/vaab/colour>`_ converts and manipulates common color representation.
- `lmfit <https://lmfit.github.io/lmfit-py/>`_ is a package for Non-Linear Least-Squares Minimization and Curve-Fitting.
- `matplotlib <https://matplotlib.org/>`_ is a plotting library.
- `NumPy <https://numpy.org/>`_ is a package for scientific computing.
- `pandas <https://pandas.pydata.org/>`_ is a library for table handling.
- `paramiko <http://www.paramiko.org/>`_ is a Python implementation of the SSHv2 protocol.
- `photutils <https://photutils.readthedocs.io/en/stable/>`_ is an AstroPy package for Photometry.
- `pillow <https://python-pillow.org/>`_ is the Python Image Library.
- `py-expression-eval <https://github.com/Axiacore/py-expression-eval>`_ is an evaluator for mathematical expressions.
- `pyinotify <https://github.com/seb-m/pyinotify>`_ monitors filesystem events on Linux with inotify.
- `python-daemon <https://pagure.io/python-daemon/>`_ daemonizes a process on Linux.
- `pytz <https://pythonhosted.org/pytz/>`_ is a timezone database.
- `PyYAML <https://pyyaml.org/>`_ is a YAML framework.
- `Requests <https://requests.readthedocs.io/>`_ is a HTTP library.
- `SciPy <https://photutils.readthedocs.io/en/stable/>`_ is a fundamental library for scientific computing.
- `SEP <https://sep.readthedocs.io/>`_ is a library for source extraction and photometry.
- `SleekXMPP <http://sleekxmpp.com/>`_ is an XMPP library.
- `Tornado <https://www.tornadoweb.org/>`_ is a Python web framework.

Additional modules and affiliated projects might install one or more of the following dependencies:

- `Cython <https://cython.org/>`_ compiles Python-like code into C and provides an easy way to include C libraries.
- `PyQt5 <https://www.riverbankcomputing.com/software/pyqt/intro>`_ provides bindings for Qt5.
- `pySerial <https://pythonhosted.org/pyserial/>`_ encapsulates access to the serial port.
- `QFitsView <https://github.com/thusser/qfitsview>`_ is a Qt5 widget for displaying FITS files.


Installing *pyobs*
------------------

Installing *pyobs* is as simple as calling pip::

    pip3 install pyobs-core


.. _installing-ejabberd:

Setting up ejabberd
-------------------
*pyobs* modules use XMPP for communication with each other. In case you already have a working XMPP server,
skip this step.

1. Download ejabberd from https://www.process-one.net/en/ejabberd/downloads/ and install it. Or on Linux use your
   package manager to do so.

2. Since the allowed packet sizes are by default a little too small, find the ejabberd config file **ejabberd.yml**
   and find and edit the "shaper" part::

    shaper:
      normal: 100000
      fast: 5000000

3. Start ejabberd server using::

    ejabberdctl start

4. Add a Shared Roster Group so that all clients are in each others roster (replace <host> with local hostname)::

    ejabberdctl srg_create all <host> all all all
    ejabberdctl srg_user_add @all@ <host> all <host>

5. Register users (may skip for now), e.g.::

    ejabberdctl register <name> <host> <password>


Using the pyobsd tool
---------------------

*pyobs* comes with its own little tool called *pyobsd* for starting and stopping *pyobs* modules
(see :ref:`cli-pyobsd`). On Linux systems, you should create a new user "pyobs"::

    adduser pyobs --home /opt/pyobs

Note that we've set the user's home directory to /opt/pyobs.

Change into the new user, and create some directories::

    su pyobs
    mkdir -p /opt/pyobs/config
    mkdir -p /opt/pyobs/log
    mkdir -p /opt/pyobs/run

Every configuration YAML file in the *config* directory will now automatically show up in the *pyobsd* tool.
Logs will be written into the *log* directory, and PID files for each process into *run*.
