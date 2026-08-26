.. _installing:

Installing pyobs
================

Setting up *pyobs* most of the time also requires an XMPP server, so here we show the complete installation of
ejabberd and *pyobs*.

.. _installing-ejabberd:

Setting up ejabberd
-------------------
In case you already have a working XMPP server, skip this step.

Automated setup
~~~~~~~~~~~~~~~~
:file:`scripts/xmpp/install-ejabberd.sh` in the *pyobs-core* repository automates steps 1-5 below (and a
couple of extras: an HTTP API listener for *pyobs-web-admin*, and a raised shaper so a real fleet's
capability-fetch/state-push bursts don't run into `a known ejabberd bug
<https://github.com/processone/xmpp>`__ where a throttled connection's socket can fail to be reactivated).
It's idempotent — safe to re-run, e.g. to add a second vhost::

    sudo ./scripts/xmpp/install-ejabberd.sh <hostname>

Run it on the machine that will host ejabberd itself, as root (or via ``sudo``); it edits
:file:`/etc/ejabberd/ejabberd.yml` in place (backing it up first) and restarts the service. The manual
steps below are equivalent if you'd rather do it by hand, or need to understand what the script changes.

1. Download ejabberd from https://www.process-one.net/en/ejabberd/downloads/ and install it.

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

Troubleshooting: module hangs at "Opening module..."
------------------------------------------------------
If ``pyobs <config.yaml>`` hangs indefinitely right after logging ``Opening module...`` and
never reaches ``Started successfully.``, and your ejabberd server is *not* configured for TLS,
this is usually a STARTTLS mismatch between pyobs' XMPP client and ejabberd. Find
``starttls_required: true`` under the ``listen:`` section of **ejabberd.yml** and set it to
``false`` (or configure TLS on both ends instead, if you'd rather keep it required).

For other XMPP/ejabberd connectivity issues — a module failing to discover its peers, capability
fetches timing out, or wanting to inspect what's actually on the pubsub bus — see
:ref:`xmpp-diagnostics`, which covers the diagnostic scripts shipped in :file:`scripts/xmpp/`.

Install pyobs
------------------
First thing to decide is whether you want to install *pyobs* in a virtual environment. If you do, and most of the
times you should, you can create one via::

    python3 -m venv venv

Then you can activate it at any time using::

    source ./venv/bin/activate

And deactivate it again with::

    deactivate

Installation of *pyobs* is as simple as::

    pip3 install pyobs-core

Install all other required packages (e.g. *pyobs-sbig*, *pyobs-gui*, ...) the same way.

Alternatively, especially if you need the latest development version, you can clone the repository and install it from
there::

    git clone git@github.com:pyobs/pyobs-core.git
    cd pyobs-core
    pip3 install .

You now have the :program:`pyobs` (see :ref:`cli-pyobs`) executable available to start *pyobs* modules.


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
    mkdir -p /opt/pyobs/storage

Every configuration YAML file in the *config* directory will now automatically show up in the *pyobsd* tool.
Logs will be written into the *log* directory, and PID files for each process into *run*.

Instead of passing parameters like **--chuid** to :program:`pyobsd` on every call, you can instead put them into
:file:`/opt/pyobs/storage/pyobs.yaml`, e.g.::

    pyobsd:
      chuid: pyobs:pyobs

See :ref:`cli-config-file` for the full list of locations that :program:`pyobs` and :program:`pyobsd` check for such
a config file.
