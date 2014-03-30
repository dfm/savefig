*Remember that time where you tried to remake a figure for your paper and
couldn't seem to get the same results? We've all been there. Well not
anymore!*

This module monkey patches the ``savefig`` command from `matplotlib
<http://matplotlib.org/>`_ and inserts your current git commit hash into
the metadata of the saved file. Currently it supports PNG and PDF figures.

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

License
-------

Copyright 2014 Dan Foreman-Mackey

Available under the MIT License.
