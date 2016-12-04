"""Using the script on existing mm files"""

import logging
import os
import shutil
import subprocess
import tempfile
import time
import unittest

import portpicker
import PyPDF2
import timeout_decorator
from freemindlatex import run_app


class ClientSideTestFixture(unittest.TestCase):
  """Base test that setups the testing directory and server.
  """

  def setUp(self):
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)
    self._server_port = portpicker.pick_unused_port()
    self._compilation_server_proc = subprocess.Popen(
      ["freemindlatex", "--port", str(self._server_port), "server"])
    self._server_address = "127.0.0.1:{}".format(self._server_port)
    # TODO(xuehuichao): move this compilation client to its own module
    self._compilation_client = run_app.LatexCompilationClient(
      self._server_address)

    retries = 0
    while not self._compilation_client.CheckHealthy() and retries < 5:
      retries += 1
      logging.info("Compilation server not healthy yet (%d's retry)", retries)
      time.sleep(1)

    self.assertTrue(self._compilation_client.CheckHealthy())

  def tearDown(self):
    shutil.rmtree(self._test_dir)
    self._compilation_server_proc.kill()


class TestBasicUsecase(ClientSideTestFixture):
  """Our program compiles in working directories."""

  def testCompilingInitialDirectory(self):
    """In a new directory, we will prepare an empty content to start with."""
    run_app.InitDir(self._test_dir)
    # Compilation successful
    self.assertTrue(
      self._compilation_client.CompileDir(self._test_dir))

    slides_file_loc = os.path.join(self._test_dir, "slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))
    self.assertEquals(4, pdf_file.getNumPages())
    self.assertIn("Author", pdf_file.getPage(0).extractText())


class TestHandlingErrors(ClientSideTestFixture):

  def _AssertErrorOnSecondPage(self, error_msg):
    slides_file_loc = os.path.join(self._test_dir, "slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))

    self.assertEquals(4, pdf_file.getNumPages())

    # Error message should appear on the 2nd page
    # Note that the extracted text don't have spaces, so I have to trim the
    # spaces
    self.assertIn(
      "".join(
        error_msg.split()),
      pdf_file.getPage(1).extractText())

    # Other pages should remain intact
    self.assertIn("Author", pdf_file.getPage(0).extractText())
    self.assertIn("Secondslide", pdf_file.getPage(2).extractText())

  @timeout_decorator.timeout(5)
  def testOnMissingDollarSign(self):
    """Missing dollar sign causes Latex to error."""
    run_app.InitDir(self._test_dir)
    shutil.copy("tests/data/additional_dollar.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    print os.path.join(self._test_dir, "mindmap.mm")

    self.assertFalse(self._compilation_client.CompileDir(self._test_dir))
    self.assertIn(
      "Missing $ inserted",
      open(
        os.path.join(
          self._test_dir,
          "latex.log")).read())

    self._AssertErrorOnSecondPage("Missing $ inserted")

  @timeout_decorator.timeout(5)
  def testOnFourLayersOfNestedEnums(self):
    """Latex does not support multi-layered enums.
    """
    run_app.InitDir(self._test_dir)
    shutil.copy("tests/data/multi_layered_enums.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    self.assertFalse(self._compilation_client.CompileDir(self._test_dir))
    self.assertIn(
      "Too deeply nested",
      open(
        os.path.join(
          self._test_dir,
          "latex.log")).read())

    self._AssertErrorOnSecondPage("Too deeply nested")

if __name__ == "__main__":
  unittest.main()
