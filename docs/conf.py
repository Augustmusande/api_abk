import os
import sys
from pathlib import Path

# Insert project root on sys.path so autodoc can import project modules
SETTINGS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SETTINGS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# -- Project information -----------------------------------------------------
project = 'coopec'
author = 'Volonté Mukovi'
release = '0.1'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']
