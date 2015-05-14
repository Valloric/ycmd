from .cs_handlers_test import StopAllOmniSharpServers

def teardown_package():
  StopAllOmniSharpServers()
