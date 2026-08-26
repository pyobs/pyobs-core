Image pipeline (pyobs.utils.pipeline)
--------------------------------------

.. automodule:: pyobs.utils.pipeline

.. autoclass:: pyobs.utils.pipeline.Pipeline
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.pipeline.Reduction
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.pipeline.reduction_base.ReductionBase
   :members:
   :show-inheritance:

``Reduction``'s ``progress_callback`` reports each step as a
:class:`~pyobs.utils.pipeline.progress.MasterCalibCreated` or
:class:`~pyobs.utils.pipeline.progress.ScienceFrameProcessed` event.

.. autoclass:: pyobs.utils.pipeline.progress.MasterCalibCreated
   :members:

.. autoclass:: pyobs.utils.pipeline.progress.ScienceFrameProcessed
   :members:
