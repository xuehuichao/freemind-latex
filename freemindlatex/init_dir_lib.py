import os
import shutil
import sys

from freemindlatex import compilation_service_pb2

_TEMPLATE_BASENAME_MAPPING = {
  compilation_service_pb2.LatexCompilationRequest.BEAMER: "slides.mm",
  compilation_service_pb2.LatexCompilationRequest.REPORT: "report.mm",
  compilation_service_pb2.LatexCompilationRequest.HTML: "report.mm",
}


def InitDir(directory, mode):
  """Initializing the directory with a template content

  Args:
    directory: directory where we initialize the content.
    mode: the way we initialize the dir. Could be beamer/report/html,
      e.g. compilation_service_pb2.LatexCompilationRequest.BEAMER.
  """
  example_dir = os.path.join(
    os.path.dirname(
      os.path.realpath(sys.modules[__name__].__file__)),
    "example")
  base_name = _TEMPLATE_BASENAME_MAPPING[mode]
  shutil.copyfile(
    os.path.join(
      example_dir, base_name), os.path.join(
      directory, "mindmap.mm"))
