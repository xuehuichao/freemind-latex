"""Installing utilities into personal directories.

It will build the utilities as zip files, copy the files into a package
directory, then put a commandline shortcut to them at bin.

Usage:

    bazel build install && bazel-bin/install/install

"""

import logging
import os
import shutil
import subprocess
import sys

import gflags

gflags.DEFINE_string(
  "package_directory",
  "~/Packages",
  "The location to place all packages.")
gflags.DEFINE_string(
  "bin_directory",
  "~/bin",
  "The location to place bin files.")

FLAGS = gflags.FLAGS

COMMAND_TARGETS = [("freemindlatex:freemindlatex_app_main", "freemindlatex"),
                   ]


def InstallTarget(target_name, package_dir, command_filename):
  """Install a build target as a commandline tool.

  It builds the target as a python zip file, copy it to a packaging directory,
  and then create a command line utility to point to it.

  Args:
    target_name: bazel target name, e.g. freemindlatex:freemindlatex_app_main
    package_dir: directory to put the build result into
    command_filename: the command file, e.g. ~/bin/freemindlatex

  Raises:
    RuntimeError: error during compiling.
  """
  logging.info("Building %s into %s.", target_name, package_dir)
  proc = subprocess.Popen(["bazel", "build", "-c", "opt",
                           target_name, "--build_python_zip"])
  if proc.wait() != 0:
    raise RuntimeError()
  build_target_path = "bazel-bin/%s.zip" % (
    "/".join(target_name.split(":")))

  basename = os.path.basename(build_target_path)
  target_path = os.path.join(package_dir, basename)
  if os.path.exists(target_path):
    os.remove(target_path)
  shutil.copyfile(
    build_target_path,
    target_path)

  logging.info(
    "Creating a commandline shortcut to %s as %s.",
    target_path,
    command_filename)
  with open(command_filename, 'w') as ofile:
    ofile.write("#!/bin/bash\npython2.7 %s $@\n" % (target_path))
  os.chmod(command_filename, 0o700)


def main():
  logging.basicConfig(level=logging.INFO)
  FLAGS(sys.argv)

  for build_target_name, command_name in COMMAND_TARGETS:
    InstallTarget(
      build_target_name,
      os.path.expanduser(
        FLAGS.package_directory),
      os.path.join(
        os.path.expanduser(
          FLAGS.bin_directory),
        command_name))


if __name__ == "__main__":
  main()
