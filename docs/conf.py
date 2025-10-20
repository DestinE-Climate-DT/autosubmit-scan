# Configuration file for Sphinx documentation builder
# This file is used by Read the Docs and can also be used for standalone Sphinx builds
# Jupyter Book will override many of these settings with _config.yml

import os
import sys
from pathlib import Path

# Add src directory to Python path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Project information
project = "autosubmit-scan"
copyright = "2024, DestinE Climate Digital Twin, Paul Gierz & Contributors"
author = "Paul Gierz"
release = "0.1.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_togglebutton",
    "sphinxcontrib.mermaid",
    "myst_nb",
]

# Templates path
templates_path = ["_templates"]

# Exclude patterns
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**.ipynb_checkpoints",
    "**/README.md",
]

# HTML output options
html_theme = "sphinx_book_theme"
html_static_path = ["_static"]
html_title = "autosubmit-scan Documentation"

html_theme_options = {
    "repository_url": "https://github.com/DestinE-Climate-DT/autosubmit-scan",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "logo": {
        "text": "autosubmit-scan",
    },
    "home_page_in_navbar": True,
    "navigation_with_keys": True,
    "show_navbar_depth": 2,
    "collapse_navigation": False,
}

# Napoleon settings for NumPy/Google style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
    "inherited-members": False,
}

autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_member_order = "groupwise"
autodoc_typehints_format = "short"
python_use_unqualified_type_names = True
add_module_names = False

# Autosummary settings
autosummary_generate = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
    "fsspec": ("https://filesystem-spec.readthedocs.io/en/latest/", None),
    "snakemake": ("https://snakemake.readthedocs.io/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/8.1.x/", None),
    "jinja2": ("https://jinja.palletsprojects.com/en/3.1.x/", None),
}

# MyST-NB settings
nb_execution_mode = "off"  # Don't execute notebooks during build
nb_execution_timeout = 180
nb_execution_allow_errors = False

# MyST parser settings
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

myst_url_schemes = ["http", "https", "ftp", "mailto", "ssh", "sftp", "s3"]
myst_heading_anchors = 3

# Copybutton settings
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True

# Todo settings
todo_include_todos = False

# Pygments style
pygments_style = "sphinx"
