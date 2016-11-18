#!/usr/bin/env python

"""Command-line tool for compiling freemind document into a pdf document.

Usage:
  Run "freemindlatex" in a directory.

  It will create the freemind file for you, launch freemind and evince, then
  recompile the freemind file into slides upon your modifications.
"""

import subprocess
import sys
import time
import codecs
import collections
import re
import os
import shutil
import tempfile
import convert
import gflags
import logging
import platform

gflags.DEFINE_integer("seconds_between_rechecking", 1,
                      "Time between checking if files have changed.")
gflags.DEFINE_string("latex_error_log_filename", "latex.log",
                     "Log file for latex compilation errors.")


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
    "../../../../share/freemindlatex/example")
  shutil.copyfile(
    os.path.join(
      example_dir, "mindmap.mm"), os.path.join(
      directory, "mindmap.mm"))


class LatexCompilationResult(object):

  def __init__(self):
    self.status = ""            # "SUCESS" or "ERROR" or "EMBEDDED" or "CANNOTFIX"
    self.source_code = ""       # The source code of the first attempt
    self.compilation_log = ""   # The compilation log of the first attempt
    self.pdf_content = ""       # The pdf file content


def _CompileLatexAtDir(working_dir, filename,
                       content_tex_filename="mindmap.tex"):
  """Runs pdflatex at the working directory.

  Args:
    working_dir: the working directory of the freemindlatex project, e.g. /tmp/123
    filename: the main .tex file by parsing the .mm file.
    content_tex_filename: the filename of .tex file containing the main content

  Returns:
    An LatexCompilationResult, whose status is either "SUCCESS" or "ERROR"
  """
  proc = subprocess.Popen(
    ["pdflatex", "-interaction=nonstopmode",
     filename], cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  return_code = proc.returncode

  result = LatexCompilationResult()
  result.compilation_log = stdout
  result.source_code = open(
    os.path.join(
      working_dir,
      content_tex_filename)).read()
  result.status = (return_code == 0) and "SUCCESS" or "ERROR"
  if return_code == 0:
    result.pdf_content = open(
      os.path.join(working_dir, "{}.pdf".format(
        os.path.splitext(filename)[0]))).read()

  return result


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


def _ParseNodeIdAndErrorMessageMapping(
    latex_content, latex_compilation_error_msg):
  """Parse the latex compilation error message, to see which frames have errors.

  Args:
    latex_content: the mindmap.tex file content, including frames' node markers.
      We use it to extract mappings between line numbers and frames
    latex_compilation_error_msg: the latex compilation error message, containing
      line numbers and error messages.

  Returns:
    A map of frame IDs and the compilation errors within it. For example:
    { "node12345" : ["nested too deep"] }
  """
  result = collections.defaultdict(list)

  lineno_frameid_map = {}

  frame_node_id = None
  for line_no, line in enumerate(latex_content.split("\n")):
    line_no = line_no + 1
    if line.startswith("%%frame: "):
      frame_node_id = re.match(r'%%frame: (.*)%%', line).group(1)

    if frame_node_id is not None:
      lineno_frameid_map[line_no] = frame_node_id

  lineno_and_errors = []
  error_message = None
  for line in latex_compilation_error_msg.split("\n"):
    if line.startswith("! "):
      error_message = line[2:]
    mo = re.match(r'l.(\d+)', line)
    if mo is not None:
      lineno_and_errors.append((int(mo.group(1)), error_message))

  for lineno, error in lineno_and_errors:
    frame_id = lineno_frameid_map[lineno]
    result[frame_id].append(error)

  return result


def _LatexCompileOrTryEmbedErrorMessage(org, work_dir):
  """Try compiling for the first time. If fails, try to embed the error message into frame.

  Args:
    org: the in-memory slides organization
    work_dir: Directory containing the running files: mindmap.mm, and the image files.

  Returns:
    A LatexCompilationResult object.
  """
  output_tex_file_loc = os.path.join(work_dir, "mindmap.tex")
  org.OutputToBeamerLatex(output_tex_file_loc)

  # First attempt
  result = _CompileLatexAtDir(work_dir, "slides.tex")

  if result.status == "SUCCESS":
    return result

  # Second attempt
  frame_and_error_message_map = _ParseNodeIdAndErrorMessageMapping(
    result.source_code, result.compilation_log)
  org.LabelErrorsOnFrames(frame_and_error_message_map)
  org.OutputToBeamerLatex(output_tex_file_loc)

  second_attempt_result = _CompileLatexAtDir(work_dir, "slides.tex")
  if second_attempt_result.status == "SUCCESS":
    result.status = "EMBEDDED"

  else:
    result.status = "CANNOTFIX"
  return result


def _CompileInWorkingDirectory(work_dir):
  """Compiles files in a working dir (temporary) to produce the final PDF.

  Args:
    work_dir: Directory containing the running files: mindmap.mm, and the image files.

  Returns:
    A LatexCompilationResult with the final pdf content.
  """
  org = convert.Organization(
    codecs.open(
      os.path.join(
        work_dir,
        "mindmap.mm"),
      'r',
      'utf8').read())

  initial_compilation_result = _LatexCompileOrTryEmbedErrorMessage(
    org, work_dir)
  if initial_compilation_result.status == "CANNOTFIX":
    return initial_compilation_result

  try:
    _CompileBibtexAtDir(work_dir, "slides")
  except BibtexCompilationError as e:
    pass
  _CompileLatexAtDir(work_dir, "slides.tex")
  final_compilation_result = _CompileLatexAtDir(work_dir, "slides.tex")

  result = initial_compilation_result
  result.pdf_content = final_compilation_result.pdf_content
  return result


def CompileDir(directory):
  """Compiles the files in user's directory, and copy the resulting pdf file back.

  The function will build a temporary directory, prepare its content, and compile.
  When there is a latex compilation error, we will put the latex error log at latex.log
  (or anything else specified by latex_error_log_filename).

  Returns: boolean indicating if the compilation was successful.
    When unceccessful, leaves log files.

  Args:
    directory: directory where user's files locate
  """

  compile_dir = tempfile.mkdtemp()
  work_dir = os.path.join(compile_dir, "working")
  logging.info("Compiling at %s", work_dir)
  target_pdf_loc = os.path.join(directory, "slides.pdf")

  # Preparing the temporary directory content
  shutil.copytree(directory, work_dir)
  static_file_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)),
    "../../../../share/freemindlatex/static_files")
  for filename in os.listdir(static_file_dir):
    shutil.copyfile(
      os.path.join(
        static_file_dir, filename), os.path.join(
          work_dir, filename))

  # Compile
  result = _CompileInWorkingDirectory(work_dir)
  if result.pdf_content:
    open(target_pdf_loc, 'w').write(result.pdf_content)

  if result.status != "SUCCESS":
    latex_log_file = os.path.join(
      directory, gflags.FLAGS.latex_error_log_filename)
    with open(latex_log_file, 'w') as ofile:
      ofile.write(result.compilation_log)

  shutil.rmtree(compile_dir)

  return result.status == "SUCCESS"


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


def _LaunchViewerProcess(filename):
  """Launch the viewer application under the current platform

  Args:
    filename: the filename of the pdf file to view
  Returns:
    The subprocess of the viewer
  """
  launch_base_command = []
  if platform.system() == "Darwin":  # MacOSX
    launch_base_command = ["open", "-W", "-a", "Skim"]
  elif platform.system() == "Linux":
    launch_base_command = ["evince"]

  return subprocess.Popen(launch_base_command + [filename])


def RunEditingEnvironment(directory):
  """Start the editing/previewing environment, monitor file changes,
  and re-compile accordingly.
  """
  mindmap_file_loc = os.path.join(directory, 'mindmap.mm')
  if not os.path.exists(mindmap_file_loc):
    print "Empty directory... Initializing it"
    InitDir(directory)

  CompileDir(directory)
  viewer_proc = _LaunchViewerProcess(os.path.join(directory, 'slides.pdf'))

  freemind_sh_path = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)),
    "../../../../share/freemindlatex/freemind/freemind.sh")
  freemind_log_path = os.path.join(directory, 'freemind.log')
  freemind_log_file = open(freemind_log_path, 'w')
  freemind_proc = subprocess.Popen(
    ['sh', freemind_sh_path, mindmap_file_loc], stdout=freemind_log_file, stderr=freemind_log_file)
  mtime_list = _GetMTimeListForDir(directory)
  try:
    while True:
      time.sleep(gflags.FLAGS.seconds_between_rechecking)
      if freemind_proc.poll() is not None or viewer_proc.poll() is not None:
        raise UserExitedEditingEnvironment

      new_mtime_list = _GetMTimeListForDir(directory)
      if new_mtime_list != mtime_list:
        mtime_list = new_mtime_list
        CompileDir(directory)

  except KeyboardInterrupt as e:
    logging.info("User exiting with ctrl-c.")

  except UserExitedEditingEnvironment as e:
    logging.info("Exiting because one editing window has been closed.")

  finally:
    logging.info("Exiting freemindlatex ...")
    freemind_log_file.close()
    try:
      freemind_proc.kill()
    except OSError:
      pass
    try:
      viewer_proc.kill()
    except OSError:
      pass


def main():
  if len(sys.argv) != 1:
    print "freemindlatex does not take parameters"
    print __doc__
    sys.exit(1)

  logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(threadName)s %(message)s')
  gflags.FLAGS(sys.argv)
  cwd = os.getcwd()
  RunEditingEnvironment(cwd)

if __name__ == "__main__":
  main()
