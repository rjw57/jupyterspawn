Spawn Jupyter docker containers
===============================

This is a utility command I use for spawning Docker containers with a Python
scientific computing environment. See the
`rjw57/jupyter-container <https://github.com/rjw57/jupyter-container/>`_
repository.

Installation
------------

Installation is via pip::

    $ pip install git+https://github.com/rjw57/jupyterspawn

Usage
-----

The primary command is the ``juspawn`` command::

    juspawn - spawn a new compute container

    Usage:
        juspawn (-h | --help)
        juspawn [options] [<volumedir>...]

    Options:
        -h, --help          Show brief usage summary.
        -q, --quiet         Reduce logging verbosity.

        --ip=IP             Address to bind host port to. [default: 0.0.0.0]

        --user=USER         Username inside container.
        --uid=UID           User id inside container.

        <volumedir>         Each directory in <volumedir> will appear in
                            /data/ with the same basename.
