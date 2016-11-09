"""Users should compile files in their local directory by a simple command."""

import os
import subprocess
import unittest
import shutil
import tempfile
import PyPDF2


class TestCompilingExampleDir(unittest.TestCase):

  def setUp(self):
    root_dir = os.getcwd()
    self._scripts_dir = os.path.join(root_dir, "bin")
    self._script_path = os.path.join(self._scripts_dir, "freemindlatex")
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)

    proc = subprocess.Popen([self._script_path, "init"], cwd=self._test_dir)
    proc.wait()
    self.assertEquals(0, proc.returncode)

  def tearDown(self):
    shutil.rmtree(self._test_dir)

  def testCompilingDirectory(self):
    proc = subprocess.Popen(
      [self._script_path, "compile"], cwd=self._test_dir)
    stdout, stderr = proc.communicate()
    self.assertEquals(0, proc.returncode)

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
