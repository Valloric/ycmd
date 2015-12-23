# Copyright (C) 2016 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from base64 import b64encode, b64decode
from hamcrest import assert_that, equal_to, greater_than, has_length, is_in
import collections
import httplib
import json
import os
import psutil
import requests
import subprocess
import sys
import tempfile
import time
import urlparse

from ycmd.hmac_utils import CreateHmac, CreateRequestHmac, SecureStringsEqual
from ycmd.tests.test_utils import BuildRequest
from ycmd.utils import ( GetUnusedLocalhostPort, PathToTempDir,
                         RemoveIfExists, SafePopen, ToUtf8Json )

HMAC_HEADER = 'X-Ycm-Hmac'
HMAC_SECRET_LENGTH = 16
DIR_OF_THIS_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )
PATH_TO_YCMD = os.path.join( DIR_OF_THIS_SCRIPT, '..' )


class Server_test( object ):

  def __init__( self ):
    self._location = None
    self._port = None
    self._hmac_secret = None
    self._stdout = None
    self._server = None
    self._subservers = []
    self._settings = self._DefaultSettings()


  def setUp( self ):
    self._hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
    self._settings[ 'hmac_secret' ] = b64encode( self._hmac_secret )


  def tearDown( self ):
    if self._server.is_running():
      self._server.terminate()
    if self._stdout:
      RemoveIfExists( self._stdout )
    if self._subservers:
      for subserver in self._subservers:
        if subserver.is_running():
          subserver.terminate()


  def ShutdownWithNoSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest( 'shutdown' )
    self._AssertResponse( response )

    self._AssertServerAndSubserversShutdown()


  def ShutdownWithSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._AssertResponse( response )

    self._subservers = self._GetSubservers()
    assert_that( self._subservers, has_length( greater_than( 0 ) ) )

    response = self._PostRequest( 'shutdown' )
    self._AssertResponse( response )

    self._AssertServerAndSubserversShutdown()


  def WatchdogWithNoSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()

    self._AssertServerAndSubserversShutdown()


  def WatchdogWithSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._AssertResponse( response )

    self._subservers = self._GetSubservers()
    assert_that( self._subservers, has_length( greater_than( 0 ) ) )

    self._AssertServerAndSubserversShutdown()


  def _Start( self, idle_suicide_seconds = 60,
              check_interval_seconds = 60 * 10 ):
    # The temp options file is deleted by ycmd during startup
    with tempfile.NamedTemporaryFile( delete = False ) as options_file:
      json.dump( self._settings, options_file )
      options_file.flush()
      self._port = GetUnusedLocalhostPort()
      self._location = 'http://127.0.0.1:' + str( self._port )

      # Define environment variable to enable subprocesses coverage. See:
      # http://coverage.readthedocs.org/en/coverage-4.0.3/subprocess.html
      env = os.environ.copy()
      env[ 'COVERAGE_PROCESS_START' ] = '.coveragerc'

      ycmd_args = [
        sys.executable,
        PATH_TO_YCMD,
        '--port={0}'.format( self._port ),
        '--options_file={0}'.format( options_file.name ),
        '--log=debug',
        '--idle_suicide_seconds={0}'.format( idle_suicide_seconds ),
        '--check_interval_seconds={0}'.format( check_interval_seconds ),
      ]

      self._stdout = os.path.join( PathToTempDir(), 'test.log' )
      with open( self._stdout, 'w' ) as stdout:
        _popen_handle = SafePopen( ycmd_args,
                                   stdin_windows = subprocess.PIPE,
                                   stdout = stdout,
                                   stderr = subprocess.STDOUT,
                                   env = env )
        self._server = psutil.Process( _popen_handle.pid )


  def _DefaultSettings( self ):
    default_settings_path = os.path.join( DIR_OF_THIS_SCRIPT,
                                          '..',
                                          'default_settings.json' )

    with open( default_settings_path ) as f:
      return json.loads( f.read() )


  def _GetSubservers( self ):
    return self._server.children()


  def _WaitUntilReady( self, timeout = 5 ):
    total_slept = 0
    while True:
      try:
        if total_slept > timeout:
          raise RuntimeError( 'waited for the server to be ready '
                              'for {0} seconds, aborting'.format(
                                timeout ) )

        if self._IsReady():
          return
      except requests.exceptions.ConnectionError:
        pass
      finally:
        time.sleep( 0.1 )
        total_slept += 0.1


  def _AssertServerAndSubserversShutdown( self, timeout = 5 ):
    _, alive = psutil.wait_procs( [ self._server ] + self._subservers,
                                  timeout = timeout )
    assert_that( alive, has_length( equal_to( 0 ) ) )


  def _IsReady( self ):
    if not self._server.is_running():
      return False
    response = self._GetRequest( 'ready' )
    response.raise_for_status()
    return response.json()


  def _GetRequest( self, handler, params = None ):
    return self._Request( 'GET', handler, params = params )


  def _PostRequest( self, handler, data = None ):
    return self._Request( 'POST', handler, data = data )


  def _Request( self, method, handler, data = None, params = None ):
    url = self._BuildURL( handler )
    if isinstance( data, collections.Mapping ):
      data = ToUtf8Json( data )
    headers = self._Headers( method,
                             urlparse.urlparse( url ).path,
                             data )
    response = requests.request( method,
                                 url,
                                 headers = headers,
                                 data = data,
                                 params = params )
    return response


  def _BuildURL( self, handler ):
    return urlparse.urljoin( self._location, handler )


  def _Headers( self, method, path, data ):
      return { 'content-type': 'application/json',
               HMAC_HEADER: self._HmacForRequest( method, path, data ) }


  def _HmacForRequest( self, method, path, body ):
    return b64encode( CreateRequestHmac( method,
                                         path,
                                         body,
                                         self._hmac_secret ) )

  def _AssertResponse( self, response ):
    assert_that( response.status_code, equal_to( httplib.OK ) )
    assert_that( HMAC_HEADER, is_in( response.headers ) )
    assert_that(
      self._ContentHmacValid( response.content,
                              b64decode( response.headers[ HMAC_HEADER ] ) ),
      equal_to( True )
    )


  def _ContentHmacValid( self, content, hmac ):
    return SecureStringsEqual( CreateHmac( content, self._hmac_secret ), hmac )
