#!/usr/bin/env python
"""
This file contains parameters to fill settings in setup.py,
the top-level docstring, and for building the docs.
In setup.py we execute this file, so it cannot import the package.
"""

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
__version__ = '0.1.0'

CLASSIFIERS = ["Development Status :: Alpha",
               "Environment :: Console",
               "Intended Audience :: Science/Research",
               "License :: OSI Approved :: Apache v2.0",
               "Operating System :: Linux",
               "Programming Language :: Python 3",
               "Topic :: Scientific/Engineering"]

description  = "Code to convert mental health spreadsheets to RDF data."

# Note: this long_description is actually a copy/paste from the top-level
# README.rst, so that it shows up nicely on PyPI.  So please remember to edit
# it only in one place and sync it correctly.
long_description = """
======================
Mental Health Database
======================

MHDB is a software package for automating conversion of mental health
spreadsheets to RDF data, licensed under the terms of the Apache v2.0 license.
Current information can always be found on the Github main repository,
http://github.com/ChildMindInstitute/mhdb.

"""

# Main setup parameters
NAME                = 'MHDB'
MAINTAINER          = "Arno Klein"
MAINTAINER_EMAIL    = "arno@childmind.org"
DESCRIPTION         = description
LONG_DESCRIPTION    = long_description
URL                 = "http://mentalhealth.tech/"
DOWNLOAD_URL        = "http://mentalhealth.tech/"
LICENSE             = "Apache v2.0"
CLASSIFIERS         = CLASSIFIERS
AUTHOR              = "Arno Klein"
AUTHOR_EMAIL        = "arno@childmind.org"
PLATFORMS           = "Linux"
VERSION             = __version__
PROVIDES            = ["mhdb"]
