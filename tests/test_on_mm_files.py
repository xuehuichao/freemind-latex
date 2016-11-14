"""Using the script on existing mm files"""

import os
import subprocess
import unittest
import shutil
import tempfile
import PyPDF2
import timeout_decorator
from freemindlatex import __main__


class TestBasicUsecase(unittest.TestCase):
  """Our program compiles in working directories."""

  def setUp(self):
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)

  def tearDown(self):
    shutil.rmtree(self._test_dir)

  def testCompilingInitialDirectory(self):
    """In a new directory, we will prepare an empty content to start with."""
    __main__.InitDir(self._test_dir)
    __main__.CompileDir(self._test_dir)

    slides_file_loc = os.path.join(self._test_dir, "slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))
    self.assertEquals(4, pdf_file.getNumPages())
    self.assertIn("Author", pdf_file.getPage(0).extractText())

  @timeout_decorator.timeout(5)
  def testDoesNotLingerOnMissingDollarSign(self):
    """When there is a missing dollar sign, finish compilation and produce logs."""
    __main__.InitDir(self._test_dir)
    shutil.copy("tests/data/additional_dollar.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    self.assertRaises(__main__.LatexCompilationError, __main__.CompileDir,
                      self._test_dir)


  @timeout_decorator.timeout(5)
  def testDoesNotLingerOnFourLayersOfNestedEnums(self):
    """Latex does not support multi-layered enums"""
    __main__.InitDir(self._test_dir)
    shutil.copy("tests/data/multi_layered_enums.mm",
                os.path.join(self._test_dir, "mindmap.mm"))
    self.assertRaises(__main__.LatexCompilationError, __main__.CompileDir,
                      self._test_dir)


if __name__ == "__main__":
  unittest.main()
