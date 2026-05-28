Serialization (pyobs.robotic.utils.serialization)
--------------------------------------------------

The robotic subsystem uses pydantic models rather than :class:`~pyobs.object.Object` subclasses for
its data and logic objects. This page explains the two base classes that make this work and how they
fit into the broader *pyobs* configuration system.


Why pydantic models?
^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.object.Object` is the right base class for anything with an async lifecycle — modules,
hardware drivers, background tasks. But many robotic objects are pure data or stateless logic: a
``Task`` is just a validated config dict; a ``Constraint`` is a function; a ``Script`` runs once and
is discarded. These map naturally onto pydantic models, which give you field validation, type
coercion, and YAML round-tripping for free, without the overhead of managing ``open()``/``close()``
lifecycles.

The two base classes in ``pyobs.robotic.utils.serialization`` bridge pydantic's validation machinery
with *pyobs*'s runtime context system.


BaseModel
^^^^^^^^^^

:class:`~pyobs.robotic.utils.serialization.BaseModel` is the pydantic equivalent of
:class:`~pyobs.object.Object` for non-polymorphic models. It adds the five runtime context
attributes as ``PrivateAttr`` fields and injects them from a validation context if one is present::

    from pyobs.robotic.utils.serialization import BaseModel

    class Task(BaseModel):
        name: str
        duration: float
        priority: float = 1.0

``Task``, ``Project``, and ``Observation`` all use ``BaseModel`` directly — they are always
instantiated as their concrete type, never dispatched via a ``class:`` key.

The runtime context (``_comm``, ``_vfs``, ``_observer``, ``_timezone``, ``_location``) is
populated in two ways:

1. **Via validation context** — when :meth:`~pyobs.object.Object.pyobs_model_validate` is called
   from within an :class:`~pyobs.object.Object`, it passes the object's context to
   ``model_validate`` explicitly::

       script = self.pyobs_model_validate(Script, self.script, by_alias=True)

   Pydantic propagates this context down the full validation tree, so nested
   ``PolymorphicBaseModel`` instances (e.g. a ``TargetPicker`` inside a ``Script``) also receive
   it automatically via the ``_inject_context_into_children`` validator.

2. **Via ``pyobs_model_validate`` after the fact** — when ``BaseModel`` is used in a context where
   no validation context is available, ``pyobs_model_validate`` stamps the private attrs directly
   onto the model after validation.


PolymorphicBaseModel
^^^^^^^^^^^^^^^^^^^^^

:class:`~pyobs.robotic.utils.serialization.PolymorphicBaseModel` extends ``BaseModel`` for cases
where the concrete type is not known at parse time — the ``class:`` key in the YAML selects it
at runtime. ``Constraint``, ``Merit``, ``Target``, and ``Script`` are all polymorphic base classes.

It adds two model validators:

**Deserialization** (``retrieve_class_on_deserialization``) — a ``wrap`` validator that intercepts
the incoming dict, reads the ``class:`` key, resolves the class, and delegates to that class's own
``model_validate``. The validation context is forwarded so runtime injection reaches the concrete
type::

    # this YAML block:
    constraints:
      - class: pyobs.robotic.scheduler.constraints.AirmassConstraint
        max_airmass: 2.0

    # causes pydantic to call:
    AirmassConstraint.model_validate({"max_airmass": 2.0}, context=...)

**Serialization** (``inject_class_on_serialization``) — a ``wrap`` serializer that adds the
``class:`` key back into the serialised dict, so that a ``model_dump()`` followed by
``model_validate()`` round-trips correctly::

    constraint = AirmassConstraint(max_airmass=2.0)
    d = constraint.model_dump()
    # → {"class": "pyobs.robotic.scheduler.constraints.AirmassConstraint", "max_airmass": 2.0}


PrivateAttrMixin
^^^^^^^^^^^^^^^^^

The runtime context properties (``comm``, ``vfs``, ``observer``, ``location``, ``timezone``) are
defined on :class:`~pyobs.object.PrivateAttrMixin`, which both :class:`~pyobs.object.Object` and
:class:`~pyobs.robotic.utils.serialization.BaseModel` inherit from. This ensures that scripts,
constraints, merits, and targets all expose the same property interface as full ``Object``
subclasses, even though they are pydantic models::

    class ObserveScript(Script):
        async def run(self, data):
            camera = await self.comm.proxy("camera", ICamera)  # same as in any Module
            image = await self.vfs.read_image("/cache/last.fits")

See :doc:`/api/object` for the full list of properties.


API reference
^^^^^^^^^^^^^^

.. autoclass:: pyobs.robotic.utils.serialization.BaseModel
   :members:
   :show-inheritance:

.. autoclass:: pyobs.robotic.utils.serialization.PolymorphicBaseModel
   :members:
   :show-inheritance:

.. autoclass:: pyobs.object.PrivateAttrMixin
   :members:
