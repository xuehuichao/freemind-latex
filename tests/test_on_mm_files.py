"""Using the script on existing mm files"""

import os
import subprocess
import unittest
import shutil
import tempfile
import PyPDF2
import timeout_decorator
from freemindlatex import __main__


class BaseTest(unittest.TestCase):
  """Base test that setups the directory for testing at self._test_dir
  """

  def setUp(self):
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)

  def tearDown(self):
    shutil.rmtree(self._test_dir)


class TestBasicUsecase(BaseTest):
  """Our program compiles in working directories."""

  def testCompilingInitialDirectory(self):
    """In a new directory, we will prepare an empty content to start with."""
    __main__.InitDir(self._test_dir)
    self.assertTrue(
      __main__.CompileDir(
        self._test_dir))  # Compilation successful

    slides_file_loc = os.path.join(self._test_dir, "slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))
    self.assertEquals(4, pdf_file.getNumPages())
    self.assertIn("Author", pdf_file.getPage(0).extractText())


class TestHandlingErrors(BaseTest):

  def _AssertErrorOnSecondPage(self, error_msg):
    slides_file_loc = os.path.join(self._test_dir, "slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))

    self.assertEquals(4, pdf_file.getNumPages())

    # Error message should appear on the 2nd page
    self.asertIn(error_msg, pdf_file.getPage(0).extractText())

    # Other pages should remain intact
    self.assertIn("Author", pdf_file.getPage(0).extractText())
    self.assertIn("Second Slide", pdf_file.getPage(2).extractText())

  @timeout_decorator.timeout(5)
  def testOnMissingDollarSign(self):
    """Missing dollar sign causes Latex to error."""
    __main__.InitDir(self._test_dir)
    shutil.copy("tests/data/additional_dollar.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    self.assertFalse(__main__.CompileDir(self._test_dir))
    self.assertIn(
      "Missing $ inserted",
      open(
        os.path.join(
          self._test_dir,
          "latex.log")).read())

  @timeout_decorator.timeout(5)
  def testOnFourLayersOfNestedEnums(self):
    """Latex does not support multi-layered enums.
    """
    __main__.InitDir(self._test_dir)
    shutil.copy("tests/data/multi_layered_enums.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    self.assertFalse(__main__.CompileDir(self._test_dir))
    self.assertIn(
      "Too deeply nested",
      open(
        os.path.join(
          self._test_dir,
          "latex.log")).read())

    self._AssertErrorOnSecondPage("Too deeply nested")

if __name__ == "__main__":
  unittest.main()
