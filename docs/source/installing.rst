Installing pytel
****************

For installing, you first have to clone the pytel repository::

    git clone git@gitlab.gwdg.de:thusser/pytel.git pytel

Then you can simply install it::

    cd pytel
    python setup.py install

Recommended environment
=======================

For using all features of pytel, it is recommended to use a standardized installation.
You first have to create a new user. On Linux systems, this usually works like this (as root)::

    adduser pytel --home /opt/pytel

Note that we've set the user's home directory to /opt/pytel.

Change into the new user, and checkout and install pytel::

    su pytel
    mkdir /opt/pytel/src
    cd /opt/pytel/src
    git clone git@gitlab.gwdg.de:thusser/pytel.git pytel

Now create new directories for configuration files, log files and PID files::

    mkdir /opt/pytel/config
    mkdir /opt/pytel/log
    mkdir /opt/pytel/run


Docker
======

Build Docker image::

    docker build --tag=pytel .

And run it::

    docker run -v $(pwd)/camera.yaml:/pytel.yaml -v $(pwd)/camera.log:/pytel.log pytel
