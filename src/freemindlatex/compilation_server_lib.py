import codecs
import collections
import errno
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time

import grpc
from concurrent import futures
from freemindlatex import compilation_service_pb2, convert

_LATEX_MAIN_FILE_BASENAME = "slides"
_LATEX_CONTENT_TEX_FILE_NAME = "mindmap.tex"


def _MkdirP(directory):
  """Makes sure the directory exists. Otherwise, will try creating it.

  Args:
    directory: the directory to make sure exist

  Returns:
    Nothing

  Raises:
    OSError, when encounter problems creating the directory.
  """

  try:
    os.makedirs(directory)
  except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(directory):
      pass
    else:
      raise


def _CompileLatexAtDir(working_dir):
  """Runs pdflatex at the working directory.

  Args:
    working_dir: the working directory of the freemindlatex compilation process.
      Normally a temporary directory (e.g. /tmp/123).

  Returns:
    A compilation_service_pb2.LatexCompilationResponse, whose status is either
    compilation_service_pb2.LatexCompilationResponse.SUCCESS
    or compilation_service_pb2.LatexCompilationResponse.ERROR
  """
  proc = subprocess.Popen(
    ["pdflatex", "-interaction=nonstopmode",
     "{}.tex".format(_LATEX_MAIN_FILE_BASENAME)], cwd=working_dir,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  stdout, _ = proc.communicate()
  return_code = proc.returncode

  result = compilation_service_pb2.LatexCompilationResponse()
  result.compilation_log = stdout
  result.source_code = open(
    os.path.join(
      working_dir,
      _LATEX_CONTENT_TEX_FILE_NAME)).read()
  result.status = (
    (return_code == 0)
    and compilation_service_pb2.LatexCompilationResponse.SUCCESS
    or compilation_service_pb2.LatexCompilationResponse.ERROR)
  if return_code == 0:
    result.pdf_content = open(
      os.path.join(working_dir, "{}.pdf".format(
        _LATEX_MAIN_FILE_BASENAME))).read()

  return result


class BibtexCompilationError(Exception):
  pass


def _CompileBibtexAtDir(working_dir):
  """Runs bibtex at the working directory.

  Args:
    working_dir: the working directory of the freemindlatex project,
      e.g. /tmp/123

  Raises:
    BibtexCompilationError: when bibtex compilation encounters some errors
      or warnings
  """
  proc = subprocess.Popen(
    ["bibtex",
     _LATEX_MAIN_FILE_BASENAME], cwd=working_dir, stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
  stdout, _ = proc.communicate()
  if proc.returncode != 0:
    raise BibtexCompilationError(stdout)


def _ParseNodeIdAndErrorMessageMapping(
    latex_content, latex_compilation_error_msg):
  """Parse the latex compilation error message, to see which frames have errors.

  Args:
    latex_content: the mindmap.tex file content, including frames'
      node markers. We use it to extract mappings between line numbers and
      frames
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
  """Try compiling. If fails, try embedding error messages into the frame.

  Args:
    org: the in-memory slides organization
    work_dir: Directory containing the running files: mindmap.mm,
      and the image files.

  Returns:
    A compilation_service_pb2.LatexCompilationResponse object.
  """
  output_tex_file_loc = os.path.join(work_dir, "mindmap.tex")
  org.OutputToBeamerLatex(output_tex_file_loc)

  # First attempt
  result = _CompileLatexAtDir(work_dir)

  if result.status == compilation_service_pb2.LatexCompilationResponse.SUCCESS:
    return result

  # Second attempt
  frame_and_error_message_map = _ParseNodeIdAndErrorMessageMapping(
    result.source_code, result.compilation_log)
  org.LabelErrorsOnFrames(frame_and_error_message_map)
  org.OutputToBeamerLatex(output_tex_file_loc)

  second_attempt_result = _CompileLatexAtDir(work_dir)
  if (second_attempt_result.status ==
      compilation_service_pb2.LatexCompilationResponse.SUCCESS):
    result.status = compilation_service_pb2.LatexCompilationResponse.EMBEDDED

  else:
    result.status = compilation_service_pb2.LatexCompilationResponse.CANNOTFIX
  return result


def _PrepareCompilationBaseDirectory(directory):
  """Copies the template (slides.tex) into the empty directory.
  """
  static_file_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(__file__)),
    "../../../../share/freemindlatex/static_files")
  for filename in os.listdir(static_file_dir):
    shutil.copyfile(
      os.path.join(
        static_file_dir, filename), os.path.join(
          directory, filename))


class CompilationServer(compilation_service_pb2.LatexCompilationServicer):

  def CompilePackage(self, request, context):
    """Compile the mindmap along with the files attached in the request.

    We will create a working directory, prepare its content, and compile.
    When there is a latex compilation error, we will put the latex error log
    into the response.

    Returns:
      A compilation_service_pb2.LatexCompilationResponse object.

    Args:
      A compilation_service_pb2.LatexCompilationRequest object, containing
      all the involved file content.
    """
    compile_dir = tempfile.mkdtemp()
    work_dir = os.path.join(compile_dir, "working")
    logging.info("Compiling at %s", work_dir)
    _MkdirP(work_dir)

    # Preparing the temporary directory content
    _PrepareCompilationBaseDirectory(work_dir)
    for file_info in request.file_infos:
      target_loc = os.path.join(work_dir, file_info.filepath)
      dirname = os.path.dirname(target_loc)
      _MkdirP(dirname)
      with open(target_loc, 'w') as ofile:
        ofile.write(file_info.content)

    # Compile
    org = convert.Organization(
      codecs.open(
        os.path.join(
          work_dir,
          "mindmap.mm"),
        'r',
        'utf8').read())

    initial_compilation_result = _LatexCompileOrTryEmbedErrorMessage(
      org, work_dir)
    if (initial_compilation_result.status ==
        compilation_service_pb2.LatexCompilationResponse.CANNOTFIX):
      return initial_compilation_result

    try:
      _CompileBibtexAtDir(work_dir)
    except BibtexCompilationError as _:
      pass
    _CompileLatexAtDir(work_dir)
    final_compilation_result = _CompileLatexAtDir(work_dir)

    result = initial_compilation_result
    result.pdf_content = final_compilation_result.pdf_content

    # Clean-up
    shutil.rmtree(compile_dir)

    return result


class HealthzServer(compilation_service_pb2.HealthServicer):

  def Check(self, request, context):
    response = compilation_service_pb2.HealthCheckResponse()
    response.status = compilation_service_pb2.HealthCheckResponse.SERVING
    return response


def RunServerAtPort(port):
  """Run the latex compilation server at port, and wait till termination.
  """
  logging.info("Running the LaTeX compilation server at port %d", port)

  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  compilation_service_pb2.add_LatexCompilationServicer_to_server(
    CompilationServer(), server)
  compilation_service_pb2.add_HealthServicer_to_server(
    HealthzServer(), server)
  server.add_insecure_port('[::]:%d' % port)
  server.start()
  try:
    while True:
      time.sleep(60 * 60 * 24)
  except KeyboardInterrupt:
    server.stop(0)
