Quickstart
==========

Install *pyobs*
---------------

1. Create virtual environment::

    python3 -m venv venv
    source ./venv/bin/activate

2. Install pyobs::

    pip install pyobs-core


Run simple config
-----------------
Create a new file **standalone.yaml** with the following content::

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10

And run it::

    pyobs standalone.yaml

Now you should get some output about starting the module, and every 10 seconds a message like this should appear::

    [INFO] standalone.py:38 Hello world

You can shutdown pyobs via crtl+c.
