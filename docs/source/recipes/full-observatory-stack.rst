.. _full-observatory-stack:

Setting up a full observatory web stack
=========================================

*pyobs-core* and the driver-module repos give you the hardware/control side of an observatory: a
fleet of *modules* talking to each other over XMPP (see :ref:`installing-ejabberd`). That's
everything a single-telescope, script-driven setup needs. A multi-telescope or remote-operated
setup usually also wants a browser-facing layer on top — and that layer lives in a handful of
separate repos, each its own standalone web service with its own deployment.

This page is a map of that layer: what each service does, how it connects to your *pyobs* fleet,
and where to go for the real install steps. It deliberately doesn't reproduce those steps here —
each repo's own Docker Compose setup, environment variables, and configuration options are
documented on its own docs site (see :ref:`Affiliated projects`), and a second copy of that here
would just drift out of sync with it.

The services
------------

Each entry below links straight to that repo's own installation instructions (Docker Compose,
environment variables, migrations).

`pyobs-portal installation <https://docs.pyobs.org/projects/pyobs-portal/en/latest/installation.html>`_
    Web backend and UI for multi-telescope task/observation queue management.
    A *pyobs* fleet talks to it by using
    :class:`~pyobs.robotic.storage.portal.PortalTaskArchive` and
    :class:`~pyobs.robotic.storage.portal.PortalObservationArchive` in place of the local
    YAML-file task archive — see :doc:`/api/robotic/scheduling` for the classes and
    :doc:`/recipes/robotic` for a minimal robotic-mode setup you can point at a portal instead of
    local files.

    .. image:: /_static/screenshots/portal-task-editor.jpg
       :alt: Task editor showing target fields and a Constraints panel with Airmass, Moon
             Separation, and Solar Elevation constraints.
       :width: 80%

`pyobs-archive installation <https://docs.pyobs.org/projects/pyobs-archive/en/latest/installation.html>`_
    Webservice for an archive of astronomical images, implementing most of the
    `Las Cumbres Observatory archive interfaces <https://developers.lco.global/#archive>`_. A
    *pyobs* fleet talks to it via :class:`~pyobs.robotic.utils.archive.PyobsArchive`. Can
    optionally restrict frame access to project members through a pyobs-portal connection.

    .. image:: /_static/screenshots/archive-frame-list.jpg
       :alt: Frame browser showing a filter sidebar and a sortable table of BIAS, DARK, SKYFLAT,
             and EXPOSE frames.
       :width: 80%

`pyobs-web-admin installation <https://docs.pyobs.org/projects/pyobs-web-admin/en/latest/installation.html>`_
    Web GUI for monitoring and managing the modules in a running fleet.

    .. image:: /_static/screenshots/web-admin-dashboard.jpg
       :alt: Dashboard showing modules grouped under Stopped and Deactivated headings, with
             summary tiles and per-row quick-action buttons.
       :width: 80%

`pyobs-pipeline installation <https://docs.pyobs.org/projects/pyobs-pipeline/en/latest/installation.html>`_
    Web-based monitoring and configuration for *pyobs* data-reduction pipelines: status, logs,
    retriggering reduction periods, and a guided builder for pipeline steps.

    .. image:: /_static/screenshots/pipeline-dashboard.jpg
       :alt: Dashboard showing two site cards with last period, next trigger, and input/output
             status, plus a table of recent reduction periods.
       :width: 80%

`pyobs-weather installation <https://docs.pyobs.org/projects/pyobs-weather/en/latest/installation.html>`_
    Weather data aggregator. A *pyobs* fleet talks to it via
    :class:`pyobs.modules.weather.Weather`, pointed at the running instance's URL.

`pyobs-auth installation <https://docs.pyobs.org/projects/pyobs-auth/en/latest/installation.html>`_
    Not a deployed service on its own: a shared Django/OIDC client library that pyobs-portal,
    pyobs-archive, pyobs-web-admin, and pyobs-pipeline each use for Keycloak-based single sign-on.
    You still need an actual OIDC identity provider (e.g. Keycloak) running somewhere for these
    apps to authenticate against — pyobs-auth is the client integration, not the identity
    provider. Its own docs cover adding it to a Django project, not a standalone deployment.

Suggested order
----------------

Since the four deployed web apps all depend on pyobs-auth for login, and pyobs-core's own modules
are typically pointed *at* portal/archive/weather rather than the other way around, it's usually
least friction to bring things up identity-provider-first: your OIDC provider, then the web apps
that authenticate against it, then finally reconfigure your *pyobs* module fleet (task archive,
frame archive, weather module) to point at the running services instead of local files.

Where to go next
-----------------

The installation links above land you in each service's own docs site; from there its
``configuration`` and ``architecture`` pages cover environment variables and how it fits into the
rest of the fleet in more detail than belongs here. The full list of affiliated projects, with
links to each one's docs home, is at :ref:`Affiliated projects`.
