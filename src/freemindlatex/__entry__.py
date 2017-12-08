"""Stub file for running the app via setup.py's entry point.
"""

from __future__ import absolute_import

# pylint: disable=import-error, no-name-in-module
from google.apputils import run_script_module


def main():
  import freemindlatex.run_app
  # The usage is documented at https://github.com/google/google-apputils
  run_script_module.RunScriptModule(freemindlatex.run_app)
