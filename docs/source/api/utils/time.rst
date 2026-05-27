Time (pyobs.utils.time)
-----------------------

.. automodule:: pyobs.utils.time

:class:`~pyobs.utils.time.Time` is a thin subclass of :class:`astropy.time.Time` used throughout *pyobs*
instead of the astropy original. It adds two things: hashability (so ``Time`` objects can be used in sets
and as dict keys) and a testable clock via :meth:`~pyobs.utils.time.Time.now`.

Always use ``pyobs.utils.time.Time`` rather than ``astropy.time.Time`` in *pyobs* code — it is a drop-in
replacement and accepts all the same constructor arguments::

    from pyobs.utils.time import Time

    now = Time.now()
    t = Time("2024-06-01T22:00:00")
    t = Time(some_datetime_object, format="datetime", scale="utc")


Simulated time
^^^^^^^^^^^^^^

In simulation or testing scenarios, :meth:`~pyobs.utils.time.Time.set_offset_to_now` shifts what
``Time.now()`` returns without affecting the system clock::

    from astropy.time import TimeDelta
    import astropy.units as u

    # make Time.now() return a time 2 hours in the past
    Time.set_offset_to_now(TimeDelta(-2 * u.hour))

This is used by :class:`~pyobs.utils.simulation.SimWorld` to run the simulator at an arbitrary point
in time.


API reference
^^^^^^^^^^^^^

.. autoclass:: pyobs.utils.time.Time
   :members:
   :show-inheritance: