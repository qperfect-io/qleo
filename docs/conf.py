# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import os
import sys
import qleo
from qleo import __version__

import sphinx.ext.doctest

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "QLEO (by MIMIQ)"
copyright = f"2023-{datetime.date.today().year}, QPerfect"
author = "Quobly"
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinx.ext.doctest",
    "recommonmark",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Tell Sphinx to look for markdown files
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}
master_doc = "index"

# -- Options for LaTeX output -------------------------------------------------

latex_engine = "xelatex"
latex_elements = {
    "preamble": r"\usepackage{physics}",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "pydata_sphinx_theme"
html_logo = "_static/quobly_logo_white.svg"
html_static_path = ["_static"]
html_theme_options = {
    "show_toc_level": 1,
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".pytest_cache"]
