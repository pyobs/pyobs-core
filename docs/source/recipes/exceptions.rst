.. _exceptions:

Exceptions across modules
=========================

A call to another module (``await telescope.move_radec(...)``) can fail on the other side, and the
exception has to get back to the caller. This page describes what the caller receives, how to catch it, and
how to define your own errors in a driver so that callers can still handle them. All exceptions live in
:mod:`pyobs.utils.exceptions`, see :doc:`/api/utils/exceptions` for the list.

.. note::

   Parts of this page describe behaviour that is merged but not released yet. It will ship with the first
   release after 2.14.2. These parts are marked "not in 2.14.2" below.


Hierarchy and which class to catch
----------------------------------

Everything derives from :class:`~pyobs.utils.exceptions.PyobsError`. There are two independent groups:

* **Domain errors** say that the operation failed for a reason: :class:`~pyobs.utils.exceptions.MotionError`
  (with :class:`~pyobs.utils.exceptions.InitError`, :class:`~pyobs.utils.exceptions.ParkError` and
  :class:`~pyobs.utils.exceptions.MoveError`), :class:`~pyobs.utils.exceptions.FocusError`,
  :class:`~pyobs.utils.exceptions.GrabImageError`, :class:`~pyobs.utils.exceptions.AbortedError`, and so on.
  They are kept fine-grained on purpose, so that a caller can react differently to each of them.
* **Transport errors** under :class:`~pyobs.utils.exceptions.RemoteError` say that the call itself did not go
  through, e.g. :class:`~pyobs.utils.exceptions.RemoteTimeoutError` or
  :class:`~pyobs.utils.exceptions.ForbiddenError` (the ACL of the other module rejected you).

A few classes describe what the caller should do, not where the error came from:
:class:`~pyobs.utils.exceptions.DeviceBusyError` and :class:`~pyobs.utils.exceptions.ModuleStartingError`
mean "try again later", :class:`~pyobs.utils.exceptions.NotSupportedError` and
:class:`~pyobs.utils.exceptions.InvalidArgumentError` mean "do not retry this request".

Catch the most specific class that you really handle differently, and nothing broader:

.. code-block:: python

   from pyobs.interfaces import IFocuser
   from pyobs.utils import exceptions as exc

   async with self.proxy("focuser", IFocuser) as focuser:
       try:
           await focuser.set_focus(12.3)
       except exc.AbortedError:
           raise                      # somebody asked us to stop
       except exc.FocusError as e:
           log.warning("Could not focus: %s", e)


What crosses the wire and what the caller receives
---------------------------------------------------

When a method of a module raises a :class:`~pyobs.utils.exceptions.PyobsError`, the module sends three things
to the caller: the fully qualified name of the class (e.g. ``pyobs.utils.exceptions.FocusError``), the message,
and the names of the classes it derives from (nearest first, without ``PyobsError`` itself). The list of base
classes is not in 2.14.2. The caller then raises the following:

========================================================  ===========================================================
The caller...                                             ...raises
========================================================  ===========================================================
has the class (it is imported in the caller's process)    The class itself, e.g. ``FocusError``.
does not have the class, but one of its base classes      The nearest base class it knows, e.g. ``MotionError`` for
                                                          a driver's own ``MyDriverTimeout(MotionError)``. The
                                                          name of the original class is kept in ``original_type``.
                                                          Not in 2.14.2, there you get ``UnclassifiedError``.
does not have the class, and no base class except         :class:`~pyobs.utils.exceptions.UnclassifiedError`, with
``PyobsError``                                            the name in ``original_type``.
the error was not a ``PyobsError`` at all (a builtin,     :class:`~pyobs.utils.exceptions.UnclassifiedError`, with
or an exception of a vendor SDK)                          the name in ``original_type``.
========================================================  ===========================================================

Over XMPP, whatever is raised carries a few attributes that help with debugging:

* ``remote_module``: the name of the module the error came from.
* ``call_id``: the same id that the other module wrote into its log, so that you can jump from the exception
  to the matching log line there.
* ``original_type``: the name of the class that was really raised. It is only set if that differs from the
  class you got, so read it with ``getattr(e, "original_type", None)`` unless you caught
  ``UnclassifiedError``.
* ``message``: the raw message. ``str(e)`` adds the class name in front, e.g. ``<MotionError> timeout``.

With ``LocalComm`` (all modules in one process) nothing is sent: the caller gets the very exception object
that was raised, without ``remote_module``.

A class is only known to the caller if its module has been imported there. Core never imports a module
because a peer names it in an error: importing runs the module's code, and driver modules load vendor
libraries, so a caller would get hardware side effects, or could be made to import anything by a bad
message.

.. note::

   **Three errors of the core modules.** :class:`~pyobs.modules.telescope.BaseTelescope` raises
   ``AltitudeLimitError`` (in ``pyobs.modules.telescope.basetelescope``), the weather module raises
   ``WeatherResponseError`` (in ``pyobs.modules.weather.weather``), and the script runner raises
   ``ScriptError`` (in ``pyobs.robotic.scripts.exceptions``). In 2.14.2 they derive from ``PyobsError``
   directly, so a caller that did not import their module receives them as ``UnclassifiedError``; check
   ``original_type`` if you need to tell them apart. From the first release after 2.14.2 they derive from
   :class:`~pyobs.utils.exceptions.PointingLimitError` (``AltitudeLimitError``) and
   :class:`~pyobs.utils.exceptions.GeneralError` (the other two), so a caller that did not import their
   module receives that class, with the name in ``original_type``.


Defining your own error in a driver
-----------------------------------

Subclass the closest class of :mod:`pyobs.utils.exceptions`, not ``PyobsError`` itself:

.. code-block:: python

   from pyobs.utils import exceptions as exc


   class ShutterJammedError(exc.MotionError):
       """The shutter did not reach its position in time."""

From the first release after 2.14.2, a caller that never imported your package then still catches
``except exc.MotionError``, and a caller that did import it can catch ``ShutterJammedError`` itself. If you
derive from ``PyobsError`` directly, only callers that import your module can recognise the error, everyone
else gets ``UnclassifiedError``.

Classes register themselves when they are defined, by their fully qualified name, so there is nothing else to
do. Declare the errors a method raises with ``pyobs.modules.raises``, which is documentation only:

.. code-block:: python

   from pyobs.modules import raises


   @raises(exc.AbortedError, exc.MotionError)
   async def init(self, **kwargs: Any) -> None:
       ...

Errors that are not a ``PyobsError`` (a ``ValueError``, an exception of a vendor library) never reach the
caller as themselves, they arrive as ``UnclassifiedError``. Convert the ones you expect into a ``PyobsError``
in your driver.

The same holds for events: from the first release after 2.14.2, an event class defined in your package is
found through a registry as well, but only once it has been imported in the receiving process. Up to 2.14.2,
only event classes in ``pyobs.events`` work.


Catching and escalating
-----------------------

Besides ``except`` around a call, a module can count repeated errors and react to them, with
``Module._register_exception()`` in its ``__init__``:

.. code-block:: python

   self._register_exception(exc.GrabImageError, 3, timespan=600, callback=self._on_grab_failures)

Only errors that leave one of this module's own methods called by another module are counted. An error
you catch with ``except``, or one raised in a background task, is not. The callback is called as soon as 3
such errors were raised by this module itself within 600 seconds. To count the errors of another module that
pass through your methods, give its name with ``module=``:

.. code-block:: python

   self._register_exception(exc.MotionError, 3, timespan=600, module="telescope", callback=self._on_failures)

Handlers without ``module=`` only see errors raised locally, handlers with ``module=`` only see errors that
came from that module over XMPP (they need ``remote_module``, see above). A handler for ``exc.RemoteError``
with ``module=`` counts *every* error that came from that module, whatever its class.

Every domain error that leaves a method of a module is logged by that module as a quiet INFO line
(:class:`~pyobs.utils.exceptions.ForbiddenError` as WARNING). Errors that happen so often that even this is
too much can be silenced with ``Module._disable_exception_logging(exc.SomeError)``.
:class:`~pyobs.utils.exceptions.ModuleError` and :class:`~pyobs.utils.exceptions.UnclassifiedError` are
always logged as ERROR with a traceback and cannot be silenced, trying it raises a ``ValueError``.


Mixed versions
--------------

The list of base classes is an optional part of the message, so modules of different versions still work
together. A caller that is too old ignores it and behaves as before, and a callee that is too old does not
send it, so the caller falls back to ``UnclassifiedError`` as before. "Old" means 2.14.2 or earlier, "new"
means the first release after 2.14.2 or later.

=======================  ===============================  ==============================================
\                        Old caller                       New caller
=======================  ===============================  ==============================================
**Old callee**           Class or ``UnclassifiedError``   Class or ``UnclassifiedError``
**New callee**           Class or ``UnclassifiedError``   Class, nearest known base class or
                                                          ``UnclassifiedError``
=======================  ===============================  ==============================================

The nearest-base-class fallback therefore only works once both sides are up to date.


Worked examples
---------------

**A driver error, caught by a scheduler** (not in 2.14.2). ``ShutterJammedError`` from above is defined in the
driver package ``my_driver`` and raised by the roof module's ``init()``. The scheduler does not have that
package installed:

.. code-block:: python

   from pyobs.interfaces import IRoof

   async with self.proxy("roof", IRoof) as roof:
       try:
           await roof.init()
       except exc.MotionError as e:
           # here: type(e) is MotionError, e.original_type == "my_driver.ShutterJammedError"
           # with my_driver installed: type(e) is ShutterJammedError, no original_type
           log.warning("Roof failed (%s): %s", getattr(e, "original_type", type(e).__name__), e)

**An expected condition.** The telescope raises ``AltitudeLimitError`` for a target below its limit. It is
not a ``MotionError`` on purpose: nothing was attempted, so it must not count as a motion failure. A caller
that did not import the telescope module still catches it as ``PointingLimitError`` (from the first release
after 2.14.2, see the note above; in 2.14.2 it arrives as ``UnclassifiedError``):

.. code-block:: python

   try:
       await telescope.move_radec(ra, dec)
   except exc.PointingLimitError:
       ...  # the target is not reachable right now, pick another one
