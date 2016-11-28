import json
import logging

import requests


class LatexCompilationRequest(object):
  """A request, containing all the source code of the project,
     e.g. .mm, .png files
  """

  def __init__(self):
    self.files_map = {}         # Filename, content mapping


class LatexCompilationResponse(object):

  def __init__(self):
    self.status = ""            # "SUCESS", "ERROR", "EMBEDDED", "CANNOTFIX"
    self.source_code = ""       # The source code of the first attempt
    self.compilation_log = ""   # The compilation log of the first attempt
    self.pdf_content = ""       # The pdf file content


class LatexCompilationStub(object):
  """Wrapper for the underlying json request.
  """

  def __init__(self, server_address):
    self._server_address = server_address

  def _RPCCall(self, method_name, *params):
    """Make JSON RPC call.
    """
    url = "http://{}".format(self._server_address)
    headers = {'content-type': 'application/json'}

    payload = {
      "method": method_name,
      "params": params,
      "jsonrpc": "2.0",
      "id": 0,
    }

    http_response = requests.post(
      url, data=json.dumps(payload), headers=headers)
    json_format = http_response.json()

    return json_format['result']

  def Compile(self, compilation_request):
    json_response = self._RPCCall(
      "CompileMindmapPackage",
      compilation_request.files_map)

    response = LatexCompilationResponse()
    response.status = json_response.get("status", "")
    response.source_code = json_response.get("source_code", "")
    response.compilation_log = json_response.get("compilation_log", "")
    # TODO(xuehuichao): use a better encoding/decoding scheme, because eval is
    # very dangerous.
    response.pdf_content = eval(json_response.get("pdf_content", "''"))

    return response

  def CheckHealthy(self):
    try:
      return self._RPCCall("Healthz") == "ok"
    except requests.exceptions.RequestException as e:
      logging.error(
        "Error checking healthz at %s: %s",
        self._server_address,
        str(e))
      return False
