#!/bin/bash
pip install Pygments setuptools docutils mock pillow alabaster commonmark recommonmark mkdocs
mkdocs build --clean --site-dir _build/html --theme readthedocs