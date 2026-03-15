# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "ccsds-ndm"
copyright = "2020-2026, Egemen Imre"
author = "Egemen Imre"

# Version Info
# ------------
# The short X.Y version.
version = "3.1.1"
# The full version, including alpha/beta/rc tags.
release = "3.1.1"

# -- General configuration ---------------------------------------------------
# By default, highlight as Python 3.
highlight_language = "python3"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "autoapi.extension",
    "sphinx.ext.autodoc",  # auto api generation
    "sphinx.ext.autosummary",  # summary tables for modules/classes/methods etc
    # "sphinx_autodoc_typehints",  # Automatically document param types
    # typehints cause a lot of forward reference errors and is therefore turned off
    "sphinx.ext.napoleon",  # numpy support
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx",  # Link mapping to external projects
    "sphinx.ext.mathjax",  # LaTex style math
    "sphinx.ext.graphviz",  # Dependency diagrams
    "sphinx.ext.viewcode",  # links to highlighted source code
    "sphinx_copybutton",
    "notfound.extension",
    # "hoverxref.extension",  # incompatible with Sphinx 9
    # "sphinx.ext.githubpages",
    "sphinx.ext.doctest",  # Doctest
    "myst_parser",  # MyST parser
    "nbsphinx",  # Jupyter notebook support
    # "sphinx_rtd_theme",  # read the docs theme
]


# The suffix of source filenames.
source_suffix = [".rst", ".md"]

# The root toctree document.
root_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Suppress reference warnings
suppress_warnings = ["ref.python"]

# -- Options for napoleon -------------------------------------------------
# return type explicit in rst
napoleon_use_rtype = False

# convert the type definitions in the docstrings as references.
napoleon_preprocess_types = True

# -- Options for numpydoc -------------------------------------------------

numpydoc_show_class_members = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_rtd_theme"
html_theme_path = ["_themes"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# -- Options for Intersphinx -------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # "numpy": ("https://numpy.org/doc/stable/", None),
    # "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    # currently not needed    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# -- Options for nbsphinx -------------------------------------------------

if os.environ.get("READTHEDOCS") == "True":
    nbsphinx_execute = "never"
else:
    nbsphinx_execute = "always"

# Controls when a cell will time out (defaults to 30; use -1 for no timeout):
nbsphinx_timeout = 1000

# -- Options for autosummary and autodoc ------------------------------------------

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
autodoc_default_options = {
    "members": True,
    # "undoc-members": True, # This causes a lot of duplicate object errors
}
html_show_sourcelink = (
    False  # Remove 'view source code' from top of page (for html, not python)
)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable imports for sphinx_autodoc_typehints
nbsphinx_allow_errors = True  # Continue through Jupyter errors
add_module_names = False  # Remove namespaces from class/method signatures

# render type annotations as parameter types and return types.

# Sphinx-native method. Not as good as sphinx_autodoc_typehints
autodoc_typehints = "description"

# -- Options for Myst -------------------------------------------

myst_heading_anchors = 3  # generate labels for heading anchors
myst_enable_extensions = [
    "dollarmath",  # parse $...$ as equations
    "amsmath",  # LaTex math
    "substitution",  # substitutions
]

myst_substitutions = {
    "pint_quantity": "[`Quantity`](https://pint.readthedocs.io/en/stable/api/base.html#pint.Quantity)",
}

# Render all links (including html) as external. Prevents download of marimo htmls.
# To apply selectively to specific links, you can enable the attrs_inline extension,
# then add an external class to the link. For example,
# [my-external-link](my-external-link){.external} becomes my-external-link.
myst_all_links_external = True


# -- Options for hoverxref -------------------------------------------
hoverxref_auto_ref = True
hoverxref_mathjax = True
hoverxref_intersphinx = ["numpy", "scipy", "matplotlib", "pint"]

# -- Options for copybutton -------------------------------------------

# exclude traditional Python prompts from the copied code
copybutton_prompt_text = ">>> "
