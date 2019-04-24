"""Using the script on existing mm files"""

import os
import shutil

import PyPDF2
import timeout_decorator

import integration_test_lib
from absl.testing import absltest
from freemindlatex import compilation_service_pb2, init_dir_lib


class TestBasicUsecase(
    integration_test_lib.ClientServerIntegrationTestFixture):
  """Our program compiles in working directories."""

  def testCompilingInitialDirectory(self):
    """In a new directory, we will prepare an empty content to start with."""
    doc_dir = os.path.join(self._test_dir, 'test_slides')
    os.mkdir(doc_dir)
    mode = compilation_service_pb2.LatexCompilationRequest.BEAMER
    init_dir_lib.InitDir(doc_dir, mode)
    # Compilation successful
    self.assertTrue(
      self._compilation_client.CompileDir(doc_dir, mode))

    slides_file_loc = os.path.join(doc_dir, "test_slides.pdf")
    self.assertTrue(os.path.exists(slides_file_loc))
    pdf_file = PyPDF2.PdfFileReader(open(slides_file_loc, "rb"))
    self.assertEquals(4, pdf_file.getNumPages())
    self.assertIn("Author", pdf_file.getPage(0).extractText())

  @timeout_decorator.timeout(5)
  def testCompilingReports(self):
    """When compiling in the report mode, renders report.pdf
    """
    doc_dir = os.path.join(self._test_dir, 'test_report')
    os.mkdir(doc_dir)
    mode = compilation_service_pb2.LatexCompilationRequest.REPORT
    init_dir_lib.InitDir(doc_dir, mode)
    self.assertTrue(
      self._compilation_client.CompileDir(doc_dir, mode)
    )

    report_file_loc = os.path.join(doc_dir, "test_report.pdf")
    self.assertTrue(os.path.exists(report_file_loc))

    pdf_file = PyPDF2.PdfFileReader(open(report_file_loc, "rb"))
    self.assertEquals(1, pdf_file.getNumPages())
    self.assertIn("Author", pdf_file.getPage(0).extractText())


class TestHandlingErrors(
    integration_test_lib.ClientServerIntegrationTestFixture):

  def _AssertErrorOnSecondPage(self, slides_file_loc, error_msg):
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
    mode = compilation_service_pb2.LatexCompilationRequest.BEAMER
    doc_dir = os.path.join(self._test_dir, 'test_slides')
    os.mkdir(doc_dir)
    init_dir_lib.InitDir(doc_dir, mode)
    shutil.copy(os.path.join(
      os.environ["TEST_SRCDIR"],
      "__main__/freemindlatex/test_data/additional_dollar.mm"),
      os.path.join(doc_dir, "mindmap.mm"))

    self.assertFalse(self._compilation_client.CompileDir(doc_dir, mode))
    self.assertIn(
      "Missing $ inserted",
      open(
        os.path.join(
          doc_dir,
          "latex.log")).read())

    self._AssertErrorOnSecondPage(
      os.path.join(doc_dir, "test_slides.pdf"),
      "Missing $ inserted")

  @timeout_decorator.timeout(5)
  def testOnFourLayersOfNestedEnums(self):
    """Latex does not support multi-layered enums.
    """
    doc_dir = os.path.join(self._test_dir, 'test_slides')
    os.mkdir(doc_dir)
    mode = compilation_service_pb2.LatexCompilationRequest.BEAMER
    init_dir_lib.InitDir(doc_dir, mode)
    shutil.copy(
      os.path.join(
        os.environ["TEST_SRCDIR"],
        "__main__/freemindlatex/test_data/multi_layered_enums.mm"),
      os.path.join(doc_dir, "mindmap.mm"))
    self.assertFalse(
      self._compilation_client.CompileDir(doc_dir, mode))
    self.assertIn(
      "Too deeply nested",
      open(
        os.path.join(
          doc_dir,
          "latex.log")).read())

    self._AssertErrorOnSecondPage(
      os.path.join(
        doc_dir,
        "test_slides.pdf"),
      "Too deeply nested")


if __name__ == "__main__":
  absltest.main()
