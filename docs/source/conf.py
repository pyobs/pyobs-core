# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/stable/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))


# -- Project information -----------------------------------------------------

project = "pyobs"
copyright = "2021, Tim-Oliver Husser"
author = "Tim-Oliver Husser"

# The short X.Y version
version = "0.15"
# The full version, including alpha/beta/rc tags
release = "0.15alpha20"


# -- General configuration ---------------------------------------------------

add_module_names = False

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    # "sphinx_autodoc_typehints",
]

intersphinx_mapping = {"http://docs.python.org/3": None}

# napoleon settings
napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_ivar = True

# typehints
# set_type_checking_flag = True
# autodoc_typehints = "description"

# show c'tor parameters in class only
autoclass_content = "both"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# Be a little nitpicky
nitpicky = True
nitpick_ignore_regex = [
    (r"py:.*", r"numpy.*"),
    (r"py:.*", r"datetime.*"),
    (r"py:.*", r"aiohttp.*"),
    (r"py:.*", r"astropy.*"),
    (r"py:.*", r"astroplan.*"),
    (r"py:.*", r"pandas.*"),
    (r"py:.*", r"collections.*"),
    (r"py:.*", r"enum.*"),
    (r"py:.*", r"inspect.*"),
]
nitpick_ignore = [
    ("py:exc", "IndexError"),
    ("py:exc", "FileNotFoundException"),
    ("py:class", "ObjectClass"),
    ("py:class", "pyobs.object.ObjectClass"),
    ("py:class", "pyobs.object.ProxyType"),
    ("py:class", "pyobs.comm.comm.ProxyType"),
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "display_version": False,
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "titles_only": False,
    "style_nav_header_background": "#cccccc",
}
html_logo = "_static/pyobs.gif"
