import shutil
import subprocess
import tempfile
import unittest

import portpicker
from freemindlatex import compilation_client_lib


class ClientServerIntegrationTestFixture(unittest.TestCase):
  """Base test that setups the testing directory and server.
  """

  def setUp(self):
    self._test_dir = tempfile.mkdtemp()
    self.assertIsNotNone(self._test_dir)
    self._server_port = portpicker.pick_unused_port()
    self._compilation_server_proc = subprocess.Popen(
      ["freemindlatex", "--port", str(self._server_port), "server"])
    self._server_address = "127.0.0.1:{}".format(self._server_port)
    self._compilation_client = compilation_client_lib.LatexCompilationClient(
      self._server_address)

    compilation_client_lib.WaitTillHealthy(self._server_address)
    self.assertTrue(self._compilation_client.CheckHealthy())

  def tearDown(self):
    shutil.rmtree(self._test_dir)
    self._compilation_server_proc.kill()
