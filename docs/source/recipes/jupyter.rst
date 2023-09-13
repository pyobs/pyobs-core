Minimal working setup for pyobs inside a Jupyter notebook
=========================================================

Introduction
------------

This is a short introduction to using pyobs inside a Jupyter notebook.
If you are already familiar with pyobs, you will find that the only big
difference is the setup process and how you interact with and manage
your own module. If you are new to pyobs, this notebook should give you
a good first introduction for writing code which interacts with pyobs.

Setup
-----

Preparations
~~~~~~~~~~~~

The following code (and pyobs in general) depends on the ``asyncio``
event loop running. If the following code returns ``False`` you will
need to upgrade your Jupyter version, as older versions don’t support
``asyncio``.

.. code:: ipython3

    import asyncio
    asyncio.get_event_loop().is_running()

Before we start with the actual setup, we have to redirect the loggin
output to ``stdout``, so that is displayed inside the cell output. If
you want to disable error/warning messages, you can skip this step.

.. code:: ipython3

    import logging
    import sys
    logging.basicConfig(stream=sys.stdout)

Credentials
~~~~~~~~~~~

This is not specific to pyobs itself, but is general advice: **NEVER**
commit credentials to a git repository. In the case of the normal pyobs
``yaml`` configuration files pyobs allows other config files config
files to be imported, in which the credentials can be stored, while the
config file containing the credentials can be added to the
``.gitignore`` file. In the case of Jupyter notebooks I recommend using
``.env`` files, which can be simmilarly excluded from the repo by adding
them to the ``.gitignore`` file. This also allow you to share the
credentials between multiple notebooks in the same probject.

For this to work, simply add a ``.env`` file to your project root and
add the following lines:

.. code:: env

   COMM_JID = "[USERNAME]@iag50srv.astro.physik.uni-goettingen.de"
   COMM_PWD = "[PASSWORD]"

You want to replace the username and password with your credentials and
if you are not at the IAG, replace the address after the ``@`` with the
one of your institute. After adding this, the ``load_dotenv()`` below,
shoud return ``True``

.. code:: ipython3

    import os
    from dotenv import load_dotenv
    
    load_dotenv()

.. code:: ipython3

    COMM_JID = os.getenv('COMM_JID')
    COMM_PWD = os.getenv('COMM_PWD')

Comm
~~~~

For our pyobs module to work, it needs a valid `comm
module <https://docs.pyobs.org/en/latest/overview.html#communication-between-modules>`__
to communicate with other modules (telescopes, cameras, etc.). In a
production environment, XMPP is used for this communication, so a
``XmppComm`` module is created with the credentials, that where
previously loaded.

.. code:: ipython3

    from pyobs.comm.xmpp import XmppComm
    comm = XmppComm(jid=COMM_JID, password=COMM_PWD, use_tls=True)

Virtual File System (VFS)
~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to work with a camera, the module also needs access to the
`pyobs virtual
filesystem <https://docs.pyobs.org/en/latest/overview.html#virtual-file-system>`__.
Again if you are not at the IAG, you will need to replace the download
address below, with your own address.

.. code:: ipython3

    from pyobs.vfs import VirtualFileSystem
    vfs = VirtualFileSystem(
        roots={
            "cache": 
            {
                "class": "pyobs.vfs.HttpFile", 
                "download": "https://iag50srv.astro.physik.uni-goettingen.de/pyobs/filecache/"
        }})

Opening the module
~~~~~~~~~~~~~~~~~~

Finally we can create the module with the comm and vfs modules.

.. code:: ipython3

    from pyobs.modules import Module
    module = Module(comm=comm, vfs=vfs)

Opening the module connects it to the pyobs network via the supplied
comm module. If everything works, ``module.opened()`` should return
``True``.

.. code:: ipython3

    await module.open()
    module.opened

Closing the module
~~~~~~~~~~~~~~~~~~

At the end of a session, the module should be closed again. This signals
to the rest of the network, that the module is not longer available.

.. code:: ipython3

    module.close()
    module.opened

Usage
-----

Telescope
~~~~~~~~~

The module can now be used to control other modules on the network.
First we create a proxy object for a telescope. The proxy object is a
local representation of the remote module, but can be controlled using
its usual methods. The ``proxy`` method needs the “username” of the
module which it is proxying, in this case, the name of the telescope.

.. code:: ipython3

    from pyobs.interfaces import ITelescope
    
    TELESCOPE_NAME = "telescope"
    telescope = await module.proxy(TELESCOPE_NAME, ITelescope)

The proxy telescope then can be used to get the orientation of the
telescope…

.. code:: ipython3

    await telescope.get_radec(), await telescope.get_altaz()

and to move it in altaz coordinates…

.. code:: ipython3

    await telescope.move_altaz(alt=60, az=180)

or radec coordiantes (both in degrees).

.. code:: ipython3

    await telescope.move_radec(ra=60, dec=25)

Camera
~~~~~~

A camera can be used in the same way, as a telescope. First, we create a
proxy for a module with the “username” ``"sbig6303e"`` as the camera.

.. code:: ipython3

    from pyobs.interfaces import ICamera
    
    CAMERA_NAME = "sbig6303e"
    camera = await module.proxy(CAMERA_NAME, ICamera)

With the proxy object, we then can set the exposure time and image type.

.. code:: ipython3

    from pyobs.interfaces import IExposureTime
    from pyobs.interfaces import IImageType
    from pyobs.utils.enums import ImageType
    
    if isinstance(camera, IExposureTime):
        await camera.set_exposure_time(2)
        
    if isinstance(camera, IImageType):
        await camera.set_image_type(ImageType.OBJECT)

``grab_data`` then starts the exposure and returns the path to the image
in the virtual filesystem. This path is then supplied to the ``vfs``
module to retrieve the image.

.. code:: ipython3

    image_name = await camera.grab_data(broadcast=False)
    img = await vfs.read_image(image_name)

Now we can look at the header…

.. code:: ipython3

    img.header

and at the image itself.

.. code:: ipython3

    import matplotlib.pyplot as plt
    
    plt.imshow(img.data, cmap="gray")
    plt.show()

We can also save the image as a file.

.. code:: ipython3

    img.writeto("image_test.fits")
