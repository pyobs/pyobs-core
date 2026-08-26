Configuration utilities (pyobs.utils.config)
--------------------------------------------

.. automodule:: pyobs.utils.config

.. autofunction:: pyobs.utils.config.pre_process_yaml


Structured config schema (pyobs.utils.config_schema)
------------------------------------------------------

.. automodule:: pyobs.utils.config_schema

:class:`~pyobs.utils.config_schema.ConfigSchema` is the type :class:`~pyobs.interfaces.IStructuredConfig`
publishes as its ``capabilities`` value, describing a module's structured, UI-editable configuration
fields.

.. autoclass:: pyobs.utils.config_schema.ConfigSchema
   :members:

.. autoclass:: pyobs.utils.config_schema.ConfigFieldSchema
   :members:
