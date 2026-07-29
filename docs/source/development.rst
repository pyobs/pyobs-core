.. _development:

Developing pyobs
================

For the development of *pyobs*, i.e. working on packages like *pyobs-core* or *pyobs-gui*, it is highly recommended
to use the official workflow using *uv* (https://docs.astral.sh/uv/ ). Some packages are using Cython for integrating
the driver, and for those *poetry* (https://python-poetry.org/ ) is used instead of *uv*. You can easily decide which
one is used by looking for the corresponding lock files, i.e. `uv.lock` and `poetry.lock`.

If you are using an IDE like PyCharm, please make sure that it uses the virtual environment in
`~/pyobs/pyobs-core/.venv`. You should create one and use it for every single package.

Although packages like *pyobs-gui* will install *pyobs-core* as a dependency, you can still override this in PyCharm
by setting a dependency to the locally cloned *pyobs-core*.


Install uv
----------
The easiest way to install *uv* is the official install script
(see https://docs.astral.sh/uv/getting-started/installation/ )::

    curl -LsSf https://astral.sh/uv/install.sh | sh

*pyobs* currently uses Python 3.11 as its base version (which is always the Python version of the latest stable Debian
release), so you should install it, if it doesn't exist::

    uv python install python3.11


Install poetry
--------------
Like *uv*, *poetry* can easiest be installed using the official install script
(see https://python-poetry.org/docs/#installation )::

    curl -sSL https://install.python-poetry.org | python3 -

You should configure poetry to install the virtual environment within the project directory (like uv does)::

    poetry config virtualenvs.in-project true


Setting up development for pyobs-core
-------------------------------------
As an example, we use *pyobs-core* here, but this works for all other packages as well.

Ideally, you should have a directory that will contain all your pyobs source, e.g. `~/pyobs`, so let's create it::

    cd
    mkdir pyobs
    cd pyobs

Clone pyobs-core:

    git clone git@github.com:pyobs/pyobs-core.git

This only works with an SSH key. You might want to use the HTTP method::

    git clone https://github.com/pyobs/pyobs-core.git

Go into that directory::

    cd pyobs-core

Change the git branch to develop:

    git checkout develop


Using uv
^^^^^^^^
Install packages::

    uv sync --locked --all-extras --no-install-project --python 3.11

We also use black to automatically format Python files and flake8 as a syntax checker. This will be done automatically
on each commit after installing pre-commit::

    uv run pre-commit install


Using poetry
^^^^^^^^^^^^
Select Python version::

    poetry env use python3.11

Install packages::

    poetry sync --no-root --all-extras --all-groups

We also use black to automatically format Python files and flake8 as a syntax checker. This will be done automatically
on each commit after installing pre-commit::

    poetry run pre-commit install


Release tooling
----------------
A couple of standalone scripts under :file:`scripts/` (top level, not :file:`scripts/xmpp/` — see
:ref:`xmpp-diagnostics` for those) support the release process itself, rather than pyobs at runtime.

``check_changelog.sh`` is run by CI against a release tag, and fails if a minor/major release is being
tagged without a matching entry in :file:`CHANGELOG.rst` (dev pre-releases and patch releases are exempt
— see the script's own header comment for the exact rules)::

    ./scripts/check_changelog.sh v1.54.0

``check_pyobs_releases.sh`` is a maintainer convenience: it lists the latest GitHub release — including
pre-releases, which the GitHub web UI hides by default — for every public repo in the ``pyobs`` org, or
for a specific list of them. Useful for spot-checking that a round of releases (e.g. after
``do-python-release``) actually landed everywhere it should have. Requires the GitHub CLI (``gh``),
authenticated::

    ./scripts/check_pyobs_releases.sh                        # every public repo in the org
    ./scripts/check_pyobs_releases.sh pyobs-core pyobs-gui    # just these

