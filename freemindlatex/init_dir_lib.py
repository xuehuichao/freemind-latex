import os
import shutil
import sys


def InitDir(directory):
  """Initializing the directory with example original content

  Args:
    directory: directory where we initialize the content.
  """
  example_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(sys.modules[__name__].__file__)),
    "example")
  shutil.copyfile(
    os.path.join(
      example_dir, "mindmap.mm"), os.path.join(
      directory, "mindmap.mm"))
