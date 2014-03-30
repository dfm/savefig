#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

__all__ = ["savefig"]

import os
import json
import logging
from tempfile import NamedTemporaryFile
from subprocess import check_output, CalledProcessError, PIPE

from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages

try:
    from PIL import Image, PngImagePlugin
except ImportError:
    Image = None


# Save a reference to the matplotlib savefig implementation.
mpl_savefig = Figure.savefig


def get_git_info():
    cmd = "git log -1 --date=iso8601 --format=\"format:%H || %ad || %an\""
    try:
        result = check_output(cmd, shell=True, stderr=PIPE)
    except CalledProcessError:
        return None
    return dict(zip(["git-hash", "git-date", "git-author"],
                    result.split(" || ")))


def savefig_png(self, fn, *args, **kwargs):
    # This is a hack to deal with filenames without extensions. Not sure why
    # this is necessary.
    fn = os.path.splitext(fn)[0] + ".png"

    # We'll start by saving the figure because the metadata is going to be
    # inserted after the fact.
    ret = mpl_savefig(self, fn, *args, **kwargs)

    # If PIL isn't installed, we'll just call the standard savefig.
    if Image is None:
        logging.warn("PIL must be installed to add metadata to PNG files.")
        return ret

    # Get the git commit information.
    git_info = get_git_info()
    if git_info is None:
        return ret

    # Inject the git info into the figure as metadata.
    img = Image.open(fn)
    meta = PngImagePlugin.PngInfo()
    for k, v in git_info.items():
        meta.add_text(k, v)
    img.save(fn, "png", pnginfo=meta)

    return ret


def savefig_pdf(self, fn, *args, **kwargs):
    # Get the git commit information.
    git_info = get_git_info()
    if git_info is None:
        return mpl_savefig(self, fn, *args, **kwargs)

    # Build the PDF object that will take the metadata.
    fn = os.path.splitext(fn)[0] + ".pdf"
    kwargs["format"] = "pdf"
    fig = PdfPages(fn)

    # Save the figure.
    ret = mpl_savefig(self, fig, *args, **kwargs)

    # Add the metadata.
    metadata = fig.infodict()
    metadata["Keywords"] = json.dumps(git_info, sort_keys=True)

    # Commit the changes.
    fig.close()

    return ret


def savefig(self, fn, *args, **kwargs):
    if not isinstance(fn, basestring):
        logging.warn("The savefig module only supports filenames.")
        return mpl_savefig(self, fn, *args, **kwargs)

    # Figure out the format.
    ext = os.path.splitext(fn)[1]
    fmt = kwargs.get("format", None)
    fmt = (fmt if fmt is not None
           else ext[1:] if len(ext)
           else rcParams["savefig.format"]).lower()

    # Deal with the different formats.
    if fmt == "png":
        return savefig_png(self, fn, *args, **kwargs)
    if fmt == "pdf":
        return savefig_pdf(self, fn, *args, **kwargs)

    # Fall back on the standard savefig if we don't know how to deal with the
    # format.
    logging.warn("Unsupported savefig format: '{0}'".format(fmt))
    return mpl_savefig(self, fn, *args, **kwargs)


def monkey_patch():
    # Monkey patch matplotlib to call our savefig instead of the standard
    # version.
    savefig.__doc__ = mpl_savefig.__doc__
    Figure.savefig = savefig


def test_png():
    monkey_patch()
    import matplotlib.pyplot as pl

    # Get the current git info.
    git_info = get_git_info()

    # Save an empty figure to a temporary file and check that the git info
    # gets stored correctly.
    with NamedTemporaryFile(suffix=".png") as f:
        fn = f.name
        pl.savefig(fn)
        img = Image.open(fn)
        info = img.info
        assert all([v == info[k] for k, v in git_info.items()])

    # Now try without a file extension.
    with NamedTemporaryFile(suffix=".png") as f:
        fn = f.name
        pl.savefig(os.path.splitext(fn)[0], format="png")
        img = Image.open(fn)
        info = img.info
        assert all([v == info[k] for k, v in git_info.items()])

    # If the default file-type is PNG, test that too.
    if not rcParams["savefig.format"].lower() == "png":
        return
    with NamedTemporaryFile(suffix=".png") as f:
        fn = f.name
        pl.savefig(os.path.splitext(fn)[0])
        img = Image.open(fn)
        info = img.info
        assert all([v == info[k] for k, v in git_info.items()])


def test_pdf():
    monkey_patch()
    import matplotlib.pyplot as pl
    from PyPDF2 import PdfFileReader

    # Get the current git info.
    git_info = get_git_info()

    # Save an empty figure to a temporary file and check that the git info
    # gets stored correctly.
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            fn = f.name
        pl.savefig(fn)
        pdf = PdfFileReader(open(fn, "rb"))
        info = json.loads(pdf.getDocumentInfo()["/Keywords"])
        assert all([v == info[k] for k, v in git_info.items()])
    finally:
        os.unlink(fn)

    # Now try without a file extension.
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            fn = f.name
        pl.savefig(os.path.splitext(fn)[0], format="pdf")
        pdf = PdfFileReader(open(fn, "rb"))
        info = json.loads(pdf.getDocumentInfo()["/Keywords"])
        assert all([v == info[k] for k, v in git_info.items()])
    finally:
        os.unlink(fn)

    # If the default file-type is PNG, test that too.
    if not rcParams["savefig.format"].lower() == "pdf":
        return
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            fn = f.name
        pl.savefig(os.path.splitext(fn)[0])
        pdf = PdfFileReader(open(fn, "rb"))
        info = json.loads(pdf.getDocumentInfo()["/Keywords"])
        assert all([v == info[k] for k, v in git_info.items()])
    finally:
        os.unlink(fn)


if __name__ == "__main__":
    test_png()
    test_pdf()
