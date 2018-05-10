import unittest

from freemindlatex import compilation_client_lib


class TestGettingCompiledDocPath(unittest.TestCase):
  def testGettingCompiledDocPath(self):
    self.assertEquals(
      '/tmp/testdir/testdir.pdf',
      compilation_client_lib.LatexCompilationClient.GetCompiledDocPath(
        '/tmp/testdir'))


if __name__ == "__main__":
  unittest.main()
