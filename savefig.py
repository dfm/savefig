#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function

import os
import json
import logging
from tempfile import NamedTemporaryFile
from subprocess import check_output, CalledProcessError, PIPE

from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages

# Optional write dependencies:
try:
    from PIL import Image, PngImagePlugin
except ImportError:
    Image = None
try:
    from PyPDF2 import PdfFileReader
except ImportError:
    PdfFileReader = None

# Python 3
try:
    basestring
except NameError:
    basestring = (str, bytes)

__all__ = ["savefig"]


# Save a reference to the matplotlib savefig implementation.
mpl_savefig = Figure.savefig


def get_git_info():
    # Check the status to see if there are any uncommitted changes.
    try:
        diff = check_output("git diff", shell=True, stderr=PIPE).decode()
    except CalledProcessError:
        return None

    # Get the commit information.
    cmd = "git log -1 --date=iso8601 --format=\"format:%H || %ad || %an\""
    try:
        result = check_output(cmd, shell=True, stderr=PIPE).decode()
    except CalledProcessError:
        return None

    # Build the results dictionary and include changes if there are any.
    ret = dict(zip(["git-hash", "git-date", "git-author"],
                   result.split(" || ")))
    if len(diff):
        ret["git-diff"] = diff

    return ret


def savefig_png(self, fn, *args, **kwargs):
    # This is a hack to deal with filenames without extensions. Not sure why
    # this is necessary.
    fn = os.path.splitext(fn)[0] + ".png"

    # We'll start by saving the figure because the metadata is going to be
    # inserted after the fact.
    ret = mpl_savefig(self, fn, *args, **kwargs)

    # If PIL isn't installed, we'll just call the standard savefig.
    if Image is None:
        logging.warn(
            "PIL or pillow must be installed to add metadata to PNG files.")
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


def get_file_info(fn):
    """
    Get the metadata stored in an image file returning ``None`` on failure.

    """
    ext = os.path.splitext(fn)[1].lower()
    if ext == ".png":
        if Image is None:
            raise ImportError("PIL or pillow must be installed to read "
                              "metadata from PNG files.")
        img = Image.open(fn)
        return img.info
    if ext == ".pdf":
        if PdfFileReader is None:
            raise ImportError("PyPDF2 must be installed to read "
                              "metadata from PDF files.")
        with open(fn, "rb") as f:
            pdf = PdfFileReader(f)
            di = pdf.getDocumentInfo()
            if "/Keywords" not in di:
                return None
            try:
                return json.loads(di["/Keywords"])
            except ValueError:
                return None
    return None


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
        info = get_file_info(fn)
        assert all([v == info[k] for k, v in git_info.items()])

    # Now try without a file extension.
    with NamedTemporaryFile(suffix=".png") as f:
        fn = f.name
        pl.savefig(os.path.splitext(fn)[0], format="png")
        info = get_file_info(fn)
        assert all([v == info[k] for k, v in git_info.items()])

    # If the default file-type is PNG, test that too.
    if not rcParams["savefig.format"].lower() == "png":
        return
    with NamedTemporaryFile(suffix=".png") as f:
        fn = f.name
        pl.savefig(os.path.splitext(fn)[0])
        info = get_file_info(fn)
        assert all([v == info[k] for k, v in git_info.items()])


def test_pdf():
    monkey_patch()
    import matplotlib.pyplot as pl

    # Get the current git info.
    git_info = get_git_info()

    # Save an empty figure to a temporary file and check that the git info
    # gets stored correctly.
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            fn = f.name
        pl.savefig(fn)
        info = get_file_info(fn)
        assert all([v == info[k] for k, v in git_info.items()])
    finally:
        os.unlink(fn)

    # Now try without a file extension.
    try:
        with NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            fn = f.name
        pl.savefig(os.path.splitext(fn)[0], format="pdf")
        info = get_file_info(fn)
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
        info = get_file_info(fn)
        assert all([v == info[k] for k, v in git_info.items()])
    finally:
        os.unlink(fn)


if __name__ == "__main__":
    import sys
    import argparse

    # Testing.
    if "--test" in sys.argv:
        print("Testing PNG support...")
        test_png()
        print("Testing PDF support...")
        test_pdf()
        sys.exit(0)

    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The file to inspect")
    parser.add_argument("-d", "--diff", action="store_true",
                        help="Get the diff.")
    args = parser.parse_args()

    # Get the file info.
    info = get_file_info(args.filename)
    if info is None:
        print("Couldn't get info from file: {0}".format(args.filename))
        sys.exit(0)

    # Show the diff if that was requested.
    if args.diff:
        if "git-diff" in info:
            print(info["git-diff"])
            sys.exit(0)
        print("No diff found.")

    # Print the summary.
    keys = ["git-hash", "git-date", "git-author"]
    for k in keys:
        v = info.get(k, None)
        if v is None:
            print("Missing key: '{0}'".format(k))
        else:
            print("{0}: {1}".format(k, v))
