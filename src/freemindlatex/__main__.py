#!/usr/bin/env python

"""Command-line tool for compiling freemind document into a pdf document.

Basic usage:
  Run "freemindlatex" in your working directory.

  It will create the freemind file for you, launch freemind and evince, then
  recompile the freemind file into slides upon your modifications.

Advanced usages:
  freemindlatex --port 8000 server # Start the latex compilation server at a
    selected port
  freemindlatex --using_server localhost:8000 client # Compiles documents
    with a remote server.
"""

import logging
import grpc
import os
import platform
import shutil
import subprocess
import sys
import time

import gflags
import portpicker
from freemindlatex import compilation_server
from freemindlatex import compilation_service_pb2

from google.apputils import app

gflags.DEFINE_string(
  "using_server",
  "",
  "The latex compilation server address, ip:port. When not specified, "
  "will start the server at an unused port.")
gflags.DEFINE_integer("seconds_between_rechecking", 1,
                      "Time between checking if files have changed.")
gflags.DEFINE_string("latex_error_log_filename", "latex.log",
                     "Log file for latex compilation errors.")
gflags.DEFINE_string("watched_file_extensions", "mm,png,jpg",
                     "Files extensions to watch for LaTeX compilation.")
gflags.DEFINE_integer(
  "port",
  None,
  "Port to listen to, for the compilation request. "
  "When not set, will pick a random port.")


class UserExitedEditingEnvironment(Exception):
  pass


def InitDir(directory):
  """Initializing the directory with example original content

  Args:
    directory: directory where we initialize the content.
  """
  example_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(sys.modules[__name__].__file__)),
    "../../../../share/freemindlatex/example")
  shutil.copyfile(
    os.path.join(
      example_dir, "mindmap.mm"), os.path.join(
      directory, "mindmap.mm"))


class LatexCompilationClient(object):
  """Client-side of latex compilation.
  """

  def __init__(self, server_address):
    self._channel = grpc.insecure_channel(server_address)
    self._healthz_stub = compilation_service_pb2.HealthStub(self._channel)
    self._compilation_stub = compilation_service_pb2.LatexCompilationStub(
      self._channel)

  def CheckHealthy(self):
    try:
      response = self._healthz_stub.Check(compilation_service_pb2.HealthCheckRequest()
                                          )
    except:
      return False
    return response.status == compilation_service_pb2.HealthCheckResponse.SERVING

  def CompileDir(self, directory):
    """Compiles the files in user's directory, and update the pdf file.

    The function will prepare the directory content, send it over for
    compilation. When there is a latex compilation error, we will put
    the latex error log at latex.log (or anything else specified by
    latex_error_log_filename).

    Returns: boolean indicating if the compilation was successful.
      When unceccessful, leaves log files.

    Args:
      directory: directory where user's files locate
    """

    target_pdf_loc = os.path.join(directory, 'slides.pdf')
    filename_and_mtime_list = _GetMTimeListForDir(directory)
    compilation_request = compilation_service_pb2.LatexCompilationRequest()
    for filename, _ in filename_and_mtime_list:
      with open(os.path.join(directory, filename)) as infile:
        new_file_info = compilation_request.file_infos.add()
        new_file_info.filepath = filename
        new_file_info.content = infile.read()

    response = self._compilation_stub.CompilePackage(compilation_request)
    if response.pdf_content:
      open(target_pdf_loc, 'w').write(response.pdf_content)

    if response.status != compilation_service_pb2.LatexCompilationResponse.SUCCESS:
      latex_log_file = os.path.join(
        directory, gflags.FLAGS.latex_error_log_filename)
      with open(latex_log_file, 'w') as ofile:
        ofile.write(response.compilation_log)

    return response.status == compilation_service_pb2.LatexCompilationResponse.SUCCESS


def _GetMTime(filename):
  """Get the time of the last modification.
  """
  try:
    return os.path.getmtime(filename)
  except OSError as _:          # file does not exist.
    return None


def _GetMTimeListForDir(directory):
  """Getting the modification time for all user files in a directory.

  Returns: a sorted list of pairs in form of ('file1', 1234567), where the paths
    are relative paths
  """
  suffixes = [
    '.%s' %
    i for i in gflags.FLAGS.watched_file_extensions.split(',')]
  mtime_list = []
  for dirpath, _, filenames in os.walk(directory):
    for filename in [f for f in filenames if any(
        f.endswith(suf) for suf in suffixes)]:
      filepath = os.path.join(dirpath, filename)
      mtime_list.append(
        (os.path.relpath(
          filepath,
          directory),
          _GetMTime(filepath)))
  return sorted(mtime_list)


def _LaunchViewerProcess(filename, log_file):
  """Launch the viewer application under the current platform

  Args:
    filename: the filename of the pdf file to view
    log_file: an already open, writable file object to write logs in.
  Returns:
    The subprocess of the viewer
  """
  launch_base_command = []
  if platform.system() == "Darwin":  # MacOSX
    launch_base_command = ["open", "-W", "-a", "Skim"]
  elif platform.system() == "Linux":
    launch_base_command = ["evince"]

  return subprocess.Popen(launch_base_command +
                          [filename], stdout=log_file, stderr=log_file)


def RunEditingEnvironment(directory, server_address):
  """Start the editing/previewing/compilation environment, monitor file changes.

  Args:
    directory: the directory user is editing at
    server_address: address of latex compilation server,
      e.g. http://127.0.0.1:8000
  """
  mindmap_file_loc = os.path.join(directory, 'mindmap.mm')
  if not os.path.exists(mindmap_file_loc):
    logging.info("Empty directory... Initializing it")
    InitDir(directory)

  latex_client = LatexCompilationClient(server_address)

  latex_client.CompileDir(directory)
  freemind_log_path = os.path.join(directory, 'freemind.log')
  freemind_log_file = open(freemind_log_path, 'w')

  viewer_log_path = os.path.join(directory, 'viewer.log')
  viewer_log_file = open(viewer_log_path, 'w')

  viewer_proc = _LaunchViewerProcess(
    os.path.join(
      directory,
      'slides.pdf'),
    viewer_log_file)

  freemind_sh_path = os.path.join(
    os.path.dirname(
      os.path.realpath(sys.modules[__name__].__file__)),
    "../../../../share/freemindlatex/freemind/freemind.sh")
  freemind_proc = subprocess.Popen(
    ['sh', freemind_sh_path, mindmap_file_loc],
    stdout=freemind_log_file, stderr=freemind_log_file)

  mtime_list = _GetMTimeListForDir(directory)
  try:
    while True:
      time.sleep(gflags.FLAGS.seconds_between_rechecking)
      if freemind_proc.poll() is not None or viewer_proc.poll() is not None:
        raise UserExitedEditingEnvironment

      new_mtime_list = _GetMTimeListForDir(directory)
      if new_mtime_list != mtime_list:
        mtime_list = new_mtime_list
        latex_client.CompileDir(directory)

  except KeyboardInterrupt as _:
    logging.info("User exiting with ctrl-c.")

  except UserExitedEditingEnvironment as _:
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


def main(argv):
  logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(threadName)s %(message)s')

  directory = os.getcwd()

  if argv[1:] == ['server']:
    port = gflags.FLAGS.port or portpicker.pick_unused_port()
    compilation_server.RunServerAtPort(port)

  elif argv[1:] == ['client']:
    if not gflags.FLAGS.using_server:
      logging.fatal(
        "Please specify the server address when running in the client mode "
        "via --using_server")
    RunEditingEnvironment(directory, server_address=gflags.FLAGS.using_server)

  elif argv[1:] == []:
    port = gflags.FLAGS.port or portpicker.pick_unused_port()
    server_proc = subprocess.Popen(
      [os.path.realpath(sys.modules[__name__].__file__),
       "--port", str(port), "server"])
    try:
      RunEditingEnvironment(
        directory,
        server_address='127.0.0.1:{}'.format(port))
    finally:
      try:
        logging.info("Terminating latex compilation server.")
        server_proc.kill()
      except OSError:
        pass

  else:
    print "Unable to recognize command %r" % argv
    print __doc__
    sys.exit(1)


if __name__ == "__main__":
  app.run()
