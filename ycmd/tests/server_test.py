#!/usr/bin/env python
#
# Copyright (C) 2015 ycmd contributors
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

from ycmd.utils import ( GetUnusedLocalhostPort, SafePopen, PathToTempDir,
                         RemoveIfExists )
from ycmd.hmac_utils import CreateHmac, CreateRequestHmac, SecureStringsEqual
from base64 import b64encode, b64decode
from hamcrest import ( assert_that, equal_to, greater_than, is_in,
                       less_than_or_equal_to )
from test_utils import BuildRequest
import collections
import sys
import json
import os
import tempfile
import requests
import time
import subprocess
import urlparse
import httplib
import psutil

HMAC_HEADER = 'X-Ycm-Hmac'
HMAC_SECRET_LENGTH = 16
DIR_OF_THIS_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )
PATH_TO_YCMD = os.path.join( DIR_OF_THIS_SCRIPT, '..' )


class Server_test( object ):

  def __init__( self ):
    self._popen_handle = None
    self._location = None
    self._port = None
    self._hmac_secret = None
    self._stdout = None
    self._children = None
    self._settings = self._DefaultSettings()


  def setUp( self ):
    self._hmac_secret = os.urandom( HMAC_SECRET_LENGTH )
    self._settings[ 'hmac_secret' ] = b64encode( self._hmac_secret )


  def tearDown( self ):
    if self._popen_handle and self._IsAlive():
      self._popen_handle.terminate()
    if self._stdout:
      RemoveIfExists( self._stdout )
    if self._children:
      for child in self._children:
        if child.is_running():
          child.terminate()


  def ShutdownWithNoSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest( 'shutdown' )
    self._CheckResponse( response )

    self._WaitUntilShutdown()

    assert_that( self._popen_handle.returncode, less_than_or_equal_to( 0 ) )


  def ShutdownWithSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._CheckResponse( response )

    self._children = self._GetChildren()
    assert_that( self._children, greater_than( 0 ) )

    response = self._PostRequest( 'shutdown' )
    self._CheckResponse( response )

    self._WaitUntilShutdown()

    assert_that( self._popen_handle.returncode, less_than_or_equal_to( 0 ) )
    for child in self._children:
      assert_that( child.is_running(), equal_to( False ) )


  def WatchdogWithNoSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()
    self._WaitUntilShutdown()

    assert_that( self._popen_handle.returncode, less_than_or_equal_to( 0 ) )


  def WatchdogWithSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._CheckResponse( response )

    self._children = self._GetChildren()
    assert_that( self._children, greater_than( 0 ) )

    self._WaitUntilShutdown()

    assert_that( self._popen_handle.returncode, less_than_or_equal_to( 0 ) )
    for child in self._children:
      assert_that( child.is_running(), equal_to( False ) )


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
        self._popen_handle = SafePopen( ycmd_args,
                                        stdin_windows = subprocess.PIPE,
                                        stdout = stdout,
                                        stderr = subprocess.STDOUT,
                                        env = env )


  def _DefaultSettings( self ):
    default_settings_path = os.path.join( DIR_OF_THIS_SCRIPT,
                                          '..',
                                          'default_settings.json' )

    with open( default_settings_path ) as f:
      return json.loads( f.read() )


  def _GetChildren( self ):
    children = []
    for proc in psutil.process_iter():
      if proc.ppid() == self._popen_handle.pid:
        children.append( proc )
    return children


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


  def _WaitUntilShutdown( self, timeout = 5 ):
    total_slept = 0
    while True:
      if total_slept > timeout:
        raise RuntimeError( 'waited for the server to be shutdown '
                            'for {0} seconds, aborting'.format(
                              timeout ) )

      if self._popen_handle.poll() is not None:
        return
      time.sleep( 0.1 )
      total_slept += 0.1


  def _IsAlive( self ):
    returncode = self._popen_handle.poll()
    # When the process hasn't finished yet, poll() returns None.
    return returncode is None


  def _IsReady( self ):
    if not self._IsAlive():
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
      data = self._ToUtf8Json( data )
    headers = self._Headers( method,
                             urlparse.urlparse( url ).path,
                             data )
    response = requests.request( method,
                                 url,
                                 headers = headers,
                                 data = data,
                                 params = params )
    return response


  def _ToUtf8Json( self, data ):
    return json.dumps( self._RecursiveEncodeUnicodeToUtf8( data ),
                       ensure_ascii = False,
                       # This is the encoding of INPUT str data
                       encoding = 'utf-8' )


  # Recurses through the object if it's a dict/iterable and converts all the
  # unicode objects to utf-8 strings.
  def _RecursiveEncodeUnicodeToUtf8( self, value ):
    if isinstance( value, unicode ):
      return value.encode( 'utf8' )
    if isinstance( value, str ):
      return value
    elif isinstance( value, collections.Mapping ):
      return dict( map( self._RecursiveEncodeUnicodeToUtf8,
                        value.iteritems() ) )
    elif isinstance( value, collections.Iterable ):
      return type( value )( map( self._RecursiveEncodeUnicodeToUtf8, value ) )
    else:
      return value


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

  def _CheckResponse( self, response ):
    assert_that( response.status_code, equal_to( httplib.OK ) )
    assert_that( HMAC_HEADER, is_in( response.headers ) )
    assert_that(
      self._ContentHmacValid( response.content,
                              b64decode( response.headers[ HMAC_HEADER ] ) ),
      equal_to( True )
    )


  def _ContentHmacValid( self, content, hmac ):
    return SecureStringsEqual( CreateHmac( content, self._hmac_secret ), hmac )
