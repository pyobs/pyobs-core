.. _installing:

Developing pyobs
================

For the development of *pyobs*, i.e. working on packages like *pyobs-core* or *pyobs-gui*, it is highly recommended
to use the official workflow using *uv* (https://docs.astral.sh/uv/).


Install uv
----------
The easiest way to install *uv* is the official install script
(see https://docs.astral.sh/uv/getting-started/installation/)::

    curl -LsSf https://astral.sh/uv/install.sh | sh

*pyobs* currently uses Python 3.11 as its base version (which is always the Python version of the latest stable Debian
release), so you should install it, if it doesn't exist::

    uv python install python3.11


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

Install packages::

    uv sync --locked --all-extras --no-install-project --python 3.11

We also use black to automatically format Python files and flake8 as a syntax checker. This will be done automatically
on each commit after installing pre-commit::

    uv run pre-commit install

If you are using an IDE like PyCharm, please make sure that it uses the virtual environment in
`~/pyobs/pyobs-core/.venv`. You should create one and use it for every single package.

Although packages like *pyobs-gui* will install *pyobs-core* as a dependency, you can still override this in PyCharm
by setting a dependency to the locally cloned *pyobs-core*.