.. _installing:

Installing pyobs
================

Setting up *pyobs* most of the time also requires an XMPP server, so here we show the complete installation of
ejabberd and *pyobs*.

.. _installing-ejabberd:

Setting up ejabberd
-------------------
In case you already have a working XMPP server, skip this step.

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

Every configuration YAML file in the *config* directory will now automatically show up in the *pyobsd* tool.
Logs will be written into the *log* directory, and PID files for each process into *run*.
