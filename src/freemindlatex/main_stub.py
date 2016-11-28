"""Stub file for running the app via setup.py's entry point.
"""

from google.apputils import run_script_module


def main():
  import freemindlatex.__main__
  # The usage is documented at https://github.com/google/google-apputils
  run_script_module.RunScriptModule(freemindlatex.__main__)
