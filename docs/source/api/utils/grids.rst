Pointing grids (pyobs.utils.grids)
------------------------------------

.. automodule:: pyobs.utils.grids

Used by :class:`~pyobs.modules.robotic.PointingSeries` to define a sequence of sky positions
(a grid) to point at in turn, optionally filtered/transformed by a chain of
:class:`~pyobs.utils.grids.filters.GridFilter` steps.

.. autoclass:: pyobs.utils.grids.gridnode.GridNode
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.grid.Grid
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.grid.RegularSphericalGrid
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.grid.GraticuleSphericalGrid
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.pipeline.GridPipeline
   :members:
   :show-inheritance:

GridFilter
^^^^^^^^^^

.. autoclass:: pyobs.utils.grids.filters.GridFilter
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.GridFilterValue
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.ConvertGridToSkyCoord
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.ConvertGridFrame
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.RandomizeGrid
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.AvoidMoon
   :members:
   :show-inheritance:

.. autoclass:: pyobs.utils.grids.filters.FromList
   :members:
   :show-inheritance:
