*Remember that time where you tried to remake a figure for your paper and
couldn't seem to get the same results? We've all been there. Well not
anymore!*

This module monkey patches the ``savefig`` command from `matplotlib
<http://matplotlib.org/>`_ and inserts your current git commit hash into
the metadata of the saved file. Currently it supports PNG and PDF figures.

.. image:: https://travis-ci.org/dfm/savefig.svg?branch=master
        :target: https://travis-ci.org/dfm/savefig

Usage
-----

First, install the module `from PyPI <https://pypi.python.org/pypi/savefig>`_::

    pip install savefig

or `from source <https://github.com/dfm/savefig>`_::

    git clone https://github.com/dfm/savefig.git
    cd savefig
    python setup.py install

Then in all your code just add the following lines before importing matplotlib::

    from savefig import monkey_patch
    monkey_patch()

To read the metadata from an existing image file, run::

    python -m savefig /path/to/figure.png

which will give you something like::

    git-hash: 192a639c4a9eb7523e9becd23f359fd7d96e833f
    git-date: 2014-03-29 21:30:27 -0400
    git-author: Dan F-M

You can also get the diff between the saved commit hash and the version used
to make the figure by running::

    python -m savefig /path/to/figure.png --diff


License
-------

Copyright 2014 Dan Foreman-Mackey

Available under the MIT License.
