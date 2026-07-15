Setting up a *pyobs* system with simulated telescope and camera
---------------------------------------------------------------

.. note::
    This recipe requires three accounts on your XMPP server (see :ref:`Setting up ejabberd`): ``telescope``, ``camera``,
    and ``gui``.

.. note::
    Several configuration files in this recipe use the ``{include <filename>}`` syntax. This is a *pyobs*
    preprocessing feature: before a YAML file is parsed, *pyobs* replaces any ``{include <filename>}`` block
    with the contents of the referenced file, resolved relative to the including file's directory. This lets
    you share common settings (like observatory location) across multiple configuration files without
    repetition. An optional key can be appended to include only a specific section:
    ``{include shared.yaml some.nested.key}``.

Setting up the venv
^^^^^^^^^^^^^^^^^^^

For this recipe, we start with a fresh new virtual environment in a new directory of your choice and install
``pyobs-core`` and ``pyobs-gui``::

    cd /path/to/test
    python3 -m venv venv
    source venv/bin/activate
    pip install pyobs-core pyobs-gui

Remember that in every new terminal you need to activate the venv first::

    cd /path/to/test
    source venv/bin/activate


Simulated telescope
^^^^^^^^^^^^^^^^^^^

*pyobs* contains classes for simulated telescopes and cameras, called :class:`~pyobs.modules.camera.DummyCamera` and
:class:`~pyobs.modules.telescope.DummyRaDecTelescope` (there are also :class:`~pyobs.modules.telescope.DummyAltAzTelescope`
and :class:`~pyobs.modules.telescope.DummySolarTelescope` variants, for testing Alt/Az-offset and solar-pointing
setups specifically), respectively.

Starting with the telescope, create a file ``telescope.yaml`` with the following content::

    {include _environment.yaml}

    class: pyobs.modules.telescope.DummyRaDecTelescope

    comm:
        class: pyobs.comm.xmpp.XmppComm
        jid: telescope@localhost
        password: pyobs

With the ``class`` keyword we define the previously mentioned class for the dummy telescope. For communicating with
other modules, it also needs a Comm object, which we define under ``comm``.

.. note::
    For the Comm configurations given in this recipe, remember to adjust JIDs and passwords according to your setup.

Since the location for all modules will be the same, we outsourced it into a file ``_environment.yaml``, which is
included in the first line, and has the following content (for this example, this is the location of the SAAO in
Sutherland, South Africa)::

    timezone: Africa/Johannesburg
    location:
        longitude: 20.810808
        latitude: -32.375823
        elevation: 1798.

You can now simply run the configuration by calling ``pyobs telescope.yaml``. The last line of the produced output
should contain ``Started successfully``. You can shutdown the module via ``Ctrl-c``.


Simulated camera
^^^^^^^^^^^^^^^^

Open a new terminal and activate the venv. Then create a new file ``camera.yaml`` with the following content::

    {include _environment.yaml}

    class: pyobs.modules.camera.DummyCamera

    comm:
        class: pyobs.comm.xmpp.XmppComm
        jid: camera@localhost
        password: pyobs

Again, start the module via ``pyobs camera.yaml``. Congratulations, you have set up your first *pyobs* system!


Graphical user interface
^^^^^^^^^^^^^^^^^^^^^^^^

In order to get a graphical user interface (GUI) to the system, we can employ the ``pyobs-gui`` package. Again, open a
new terminal and activate the venv. Then create a file callen ``gui.yaml``::

    {include _environment.yaml}

    class: pyobs_gui.GUI

    comm:
        class: pyobs.comm.xmpp.XmppComm
        jid: gui@localhost
        password: pyobs

Start the module (``pyobs gui.yaml``) and you should see a window open with two entries on the left side for
``telescope`` and ``camera``. Clicking on those will give you controls to move the telescope and take images
with the camera.


Virtual file system
^^^^^^^^^^^^^^^^^^^

Now, while most buttons should work nicely, when taking an image you will get an error message like this::

    ValueError: Could not find root cache for file.

This happens, because *pyobs* does not now where to store your images.

For this to work, we need to add a :mod:`~pyobs.vfs` for both ``camera`` and ``gui``, i.e. the two modules
that need to access the files. Simply add the following to both configuration files::

    vfs:
        class: pyobs.vfs.VirtualFileSystem
        roots:
            cache:
                class: pyobs.vfs.LocalFile
                root: .

Restart both modules and take an image. You will see that the GUI now shows it to you after the exposure is finished.