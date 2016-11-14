"""Users should compile files in their local directory by a simple command."""

import os
import subprocess
import unittest
import shutil
import tempfile
import PyPDF2
import freemindlatex


class TestCompilingExampleDir(unittest.TestCase):

  def setUp(self):
    root_dir = os.getcwd()
    self._scripts_dir = os.path.join(root_dir, "src")
    self._script_path = os.path.join(self._scripts_dir, "freemindlatex")
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)

    freemindlatex.InitDir(self._test_dir)

  def tearDown(self):
    shutil.rmtree(self._test_dir)

  def testCompilingDirectory(self):
    freemindlatex.CompileDir(self._test_dir)

    slides_file_loc = os.path.join(
      self._test_dir,
      "slides.pdf")
    self.assertTrue(
      os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, 'rb'))
    self.assertEquals(4, pdf_file.getNumPages())
    self.assertIn('Author', pdf_file.getPage(0).extractText())


if __name__ == "__main__":
  unittest.main()
