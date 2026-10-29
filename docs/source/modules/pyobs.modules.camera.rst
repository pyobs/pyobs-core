Cameras (pyobs.modules.camera)
------------------------------

.. automodule:: pyobs.modules.camera

BaseCamera
^^^^^^^^^^

.. autoclass:: pyobs.modules.camera.BaseCamera
   :members:
   :show-inheritance:

BaseData
^^^^^^^^

.. autoclass:: pyobs.modules.camera.BaseData
   :members:
   :show-inheritance:

BaseSpectrograph
^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.camera.BaseSpectrograph
   :members:
   :show-inheritance:

BaseVideo
^^^^^^^^^

.. autoclass:: pyobs.modules.camera.BaseVideo
   :members:
   :show-inheritance:

DummyCamera
^^^^^^^^^^^

.. autoclass:: pyobs.modules.camera.DummyCamera
   :members:
   :show-inheritance:

DummySpectrograph
^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.camera.DummySpectrograph
   :members:
   :show-inheritance:

PipelineCamera
^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.camera.PipelineCamera
   :members:
   :show-inheritance:


Selecting FITS header providers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cameras using ``FitsHeaderMixin`` can select remote header providers at startup:

.. code-block:: yaml

   class: pyobs.modules.camera.DummyCamera
   fits_header_modules: [telescope1, mastermind1, filterwheel1, focuser1]

Use the communication names of your actual modules. Only modules implementing
``IFitsHeaderBefore`` or ``IFitsHeaderAfter`` contribute in the respective phase.
Include the mastermind for observation/task cards and separate filter/focuser
providers for their cards. The default, ``null`` (or omitting the option), requests
all discovered providers. ``[]`` requests none; local camera headers still apply.
The list selects membership, not merge priority. Unknown/offline names contribute
nothing, and selected slow providers retain the existing header timeout.

Unselected providers receive no FITS header RPCs. Capability checks still inspect
interface caches and may wait for background discovery; the header collection
timeout does not bound that setup step.

Provider selection does not resolve overlapping cards from intentionally selected
modules. Telescope namespace mappings can additionally define keyword ownership;
see :doc:`pyobs.modules.telescope`.
