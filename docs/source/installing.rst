Installing pyobs
****************

For installing, you first have to clone the pyobs repository::

    git clone git@gitlab.gwdg.de:thusser/pyobs.git pyobs

Then you can simply install it::

    cd pyobs
    python setup.py install

Recommended environment
=======================

For using all features of pyobs, it is recommended to use a standardized installation.
You first have to create a new user. On Linux systems, this usually works like this (as root)::

    adduser pyobs --home /opt/pyobs

Note that we've set the user's home directory to /opt/pyobs.

Change into the new user, and checkout and install pyobs::

    su pyobs
    mkdir /opt/pyobs/src
    cd /opt/pyobs/src
    git clone git@gitlab.gwdg.de:thusser/pyobs.git pyobs

Now create new directories for configuration files, log files and PID files::

    mkdir /opt/pyobs/config
    mkdir /opt/pyobs/log
    mkdir /opt/pyobs/run


Docker
======

Build Docker image::

    docker build --tag=pyobs .

And run it::

    docker run -v $(pwd)/camera.yaml:/pyobs.yaml -v $(pwd)/camera.log:/pyobs.log pyobs
