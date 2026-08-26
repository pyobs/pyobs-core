Auto-guiding (pyobs.modules.pointing)
-------------------------------------

.. automodule:: pyobs.modules.pointing

BasePointing
^^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing._base.BasePointing
   :members:
   :show-inheritance:

Acquisition
^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing.Acquisition
   :members:
   :show-inheritance:

BaseGuiding
^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing.BaseGuiding
   :members:
   :show-inheritance:

GuidingStatistics
^^^^^^^^^^^^^^^^^

``BaseGuiding``'s ``guiding_statistic`` parameter takes a
:class:`~pyobs.modules.pointing.guidingstatistics.guidingstatistics.GuidingStatistics` subclass
(e.g. ``GuidingStatisticsSkyOffset``, ``GuidingStatisticsPixelOffset``, ``GuidingStatisticsUptime``).

.. autoclass:: pyobs.modules.pointing.guidingstatistics.guidingstatistics.GuidingStatistics
   :members:

AutoGuiding
^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing.AutoGuiding
   :members:
   :show-inheritance:

ScienceFrameAutoGuiding
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing.ScienceFrameAutoGuiding
   :members:
   :show-inheritance:

DummyAutoGuiding
^^^^^^^^^^^^^^^^

.. autoclass:: pyobs.modules.pointing.DummyAutoGuiding
   :members:
   :show-inheritance:

