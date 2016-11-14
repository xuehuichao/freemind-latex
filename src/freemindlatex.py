#!/usr/bin/env python

"""Command-line tool for compiling freemind document into a pdf document.

Usage:
  Run "freemindlatex edit" in a directory.

  It will create the freemind file for you, launch freemind and evince, then
  recompile the freemind file into slides upon your modifications.
"""

import subprocess
import sys
import time
import codecs
import os
import shutil
import tempfile
import convert
import gflags

gflags.DEFINE_integer("seconds_between_rechecking", 1,
                      "Time between checking if files have changed.")


class LatexCompilationError(Exception):
  pass


class BibtexCompilationError(Exception):
  pass


class UserExitedEditingEnvironment(Exception):
  pass


def InitDir(directory):
  """Initializing the directory with example original content

  Args:
    directory: directory where we initialize the content.
  """
  example_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)),
    "../example")
  shutil.copyfile(
    os.path.join(
      example_dir, "mindmap.mm"), os.path.join(
      directory, "mindmap.mm"))


def _CompileLatexAtDir(working_dir, filename):
  """Runs pdflatex at the working directory.

  Args:
    working_dir: the working directory of the freemindlatex project, e.g. /tmp/123
    filename: the generated .tex file by parsing the .mm file.

  Raises:
    LatexCompilationError: when the pdflatex command does not work.
  """
  proc = subprocess.Popen(
    ["pdflatex", "-interaction=nonstopmod",
     filename], cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode != 0:
    raise LatexCompilationError(stdout)


def _CompileBibtexAtDir(working_dir, filename_prefix="slides"):
  """Runs bibtex at the working directory.

  Args:
    working_dir: the working directory of the freemindlatex project, e.g. /tmp/123
    filename_prefix: the prefix of the .tex, .aux file names of the final generated .pdf file.

  Raises:
    BibtexCompilationError: when bibtex compilation encounters some errors or warnings
  """
  proc = subprocess.Popen(
    ["bibtex",
     filename_prefix], cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  if proc.returncode != 0:
    raise BibtexCompilationError(stdout)


def CompileDir(directory):
  """Compiles the files in user's directory, and copy the resulting pdf file back.

  Args:
    directory: directory where user's files locate
  """

  compile_dir = tempfile.mkdtemp()
  work_dir = os.path.join(directory, "working")
  shutil.copytree(directory, work_dir)
  static_file_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)),
    "../static_files")
  for filename in os.listdir(static_file_dir):
    shutil.copyfile(
      os.path.join(
        static_file_dir, filename), os.path.join(
        work_dir, filename))
  org = convert.Organization(
    codecs.open(
      os.path.join(
        work_dir,
        "mindmap.mm"),
      'r',
      'utf8').read())
  org.OutputToBeamerLatex(os.path.join(work_dir, "mindmap.tex"))

  _CompileLatexAtDir(work_dir, "slides.tex")
  try:
    _CompileBibtexAtDir(work_dir, "slides")
  except BibtexCompilationError as e:
    pass
  _CompileLatexAtDir(work_dir, "slides.tex")
  _CompileLatexAtDir(work_dir, "slides.tex")

  shutil.copyfile(
    os.path.join(
      work_dir, "slides.pdf"), os.path.join(
      directory, "slides.pdf"))
  shutil.rmtree(work_dir)


def _GetMTime(filename):
  """Get the time of the last modification
  """
  try:
    return os.path.getmtime(filename)
  except Exception as e:
    print e
    return None


def _GetMTimeListForDir(directory, suffixes=['.mm', '.png', '.jpg']):
  """Getting the modification time for all user files in a directory.

  Returns: a sorted list of pairs in form of ('/file1', 1234567)
  """
  mtime_list = []
  for dirpath, dirnames, filenames in os.walk(directory):
    for filename in [f for f in filenames if any(
        f.endswith(suf) for suf in suffixes)]:
      filepath = os.path.join(dirpath, filename)
      mtime_list.append((filepath, _GetMTime(filepath)))
  return sorted(mtime_list)


def RunEditingEnvironment(directory):
  """Start the editing/previewing environment, monitor file changes,
  and re-compile accordingly.
  """
  mindmap_file_loc = os.path.join(directory, 'mindmap.mm')
  if not os.path.exists(mindmap_file_loc):
    print "Empty directory... Initializing it"
    InitDir(directory)

  CompileDir(directory)
  evince_proc = subprocess.Popen(
    ['evince', os.path.join(directory, 'slides.pdf')])

  freemind_sh_path = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)), '../freemind/freemind.sh')
  freemind_proc = subprocess.Popen(
    ['sh', freemind_sh_path, mindmap_file_loc])
  mtime_list = _GetMTimeListForDir(directory)
  try:
    while True:
      time.sleep(gflags.FLAGS.seconds_between_rechecking)
      if freemind_proc.poll() is not None or evince_proc.poll() is not None:
        raise UserExitedEditingEnvironment

      new_mtime_list = _GetMTimeListForDir(directory)
      if new_mtime_list != mtime_list:
        mtime_list = new_mtime_list
        try:
          print "re-compiling..."
          CompileDir(directory)
        except LatexCompilationError as e:
          print "Error during latex compilation"
          print e

  except KeyboardInterrupt as e:
    print "User exiting with ctrl-c."

  except UserExitedEditingEnvironment as e:
    print "Exiting because one editing window has been closed."

  finally:
    print "Exiting freemindlatex ..."
    try:
      freemind_proc.kill()
    except OSError:
      pass
    try:
      evince_proc.kill()
    except OSError:
      pass


def main():
  if len(sys.argv) != 2:
    print "Incorrect number of parameters"
    print __doc__
    sys.exit(1)

  cwd = os.getcwd()
  if sys.argv[1] == 'init':
    InitDir(cwd)
  elif sys.argv[1] == 'compile':
    CompileDir(cwd)
  elif sys.argv[1] == 'edit':
    RunEditingEnvironment(cwd)
  else:
    print "Unrecognized commandline option"
    print __doc__
    sys.exit(1)

if __name__ == "__main__":
  main()
