Telescopes (pyobs.modules.telescope)
------------------------------------

.. automodule:: pyobs.modules.telescope

BaseTelescope
^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.telescope.BaseTelescope
   :members:
   :show-inheritance:

DummyRaDecTelescope
^^^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.telescope.DummyRaDecTelescope
   :members:
   :show-inheritance:

DummyAltAzTelescope
^^^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.telescope.DummyAltAzTelescope
   :members:
   :show-inheritance:

DummySolarTelescope
^^^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.telescope.DummySolarTelescope
   :members:
   :show-inheritance:


Routing FITS header keywords
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``BaseTelescope`` supports provider-side ``FitsNamespaceMixin`` configuration.
For example, route all telescope cards to its own camera:

.. code-block:: yaml

   class: pyobs.modules.telescope.DummyRaDecTelescope
   fits_namespaces:
     camera1: null

This mapping is distinct from a camera's ``fits_namespaces`` list. A provider
returns the union of keywords mapped to the RPC sender and explicitly requested
namespace names. A mapping value of ``null`` includes all keywords; a keyword
list selects those cards, and ``[]`` includes none. An absent or empty mapping
preserves the complete header. Unknown names contribute nothing when a mapping
exists. Direct local calls without a sender match only explicitly requested
namespaces (unless an empty-string namespace is configured).

For two telescope/camera pairs, map telescope1's cards to ``camera1`` and
telescope2's cards to ``camera2``, and
configure each camera's ``fits_header_modules`` to select its telescope and any
shared observation/filter/focuser providers. Deploying without those ownership
settings preserves the existing broadcast/pass-through behavior.

The dummy telescope keeps ``TEL-FOCU`` and filters it after adding it. Driver
subclasses that append cards after calling the base must forward ``namespaces``
and sender metadata and apply final namespace filtering to their own additions.
