#!/usr/bin/env python
#
# Copyright (C) 2015  ycmd contributors
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

from ycmd.utils import ToUtf8IfNeeded
from ycmd.completers.completer import Completer
from ycmd import responses, utils, hmac_utils

import logging, urlparse, requests, subprocess, httplib, json, tempfile, base64
import binascii, threading, os

from os import path as p

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.abspath( p.join( DIR_OF_THIS_SCRIPT,
                             '..', '..', '..', 'third_party' ) )
RACERD = p.join( DIR_OF_THIRD_PARTY, 'racerd', 'target', 'release', 'racerd' )
RACERD_HMAC_HEADER = 'x-racerd-hmac'
HMAC_SECRET_LENGTH = 16

class RustCompleter( Completer ):
  """
  A completer for the rust programming language backed by racerd.
  https://github.com/jwilm/racerd
  """

  def __init__( self, user_options ):
    super( RustCompleter, self ).__init__( user_options )
    self._racerd_host = None
    self._logger = logging.getLogger( __name__ )
    self._lock = threading.Lock()
    self._keep_logfiles = user_options[ 'server_keep_logfiles' ]
    self._hmac_secret = ''
    with self._lock:
      self._StartServerNoLock()


  def _GetRustSrcPath( self ):
    """
    Attempt to read user option for rust_src_path. Fallback to environment
    variable if it's not provided.
    """
    rust_src_path  = self.user_options[ 'rust_src_path' ]

    # Early return if user provided config
    if rust_src_path != '':
      return rust_src_path

    # Fall back to environment variable
    env_key = 'RUST_SRC_PATH'
    if os.environ.has_key( env_key ):
      return os.environ[ env_key ]

    self._logger.warn( 'No path provided for the rustc source. Please set the '
                       'ycm_rust_src_path option' )
    return None


  def SupportedFiletypes( self ):
    return [ 'rust' ]


  def _ComputeRequestHmac( self, method, path, body ):
    hmac = hmac_utils.CreateRequestHmac( method, path, body, self._hmac_secret )
    return binascii.hexlify( hmac )


  def _GetResponse( self, handler, request_data = None, method = 'POST' ):
    """
    Query racerd via HTTP

    racerd returns JSON with 200 OK responses. 204 No Content responses occur
    when no errors were encountered but no completions, definitions, or errors
    were found.
    """
    self._logger.info( 'RustCompleter._GetResponse' )
    url = urlparse.urljoin( self._racerd_host, handler )
    parameters = self._TranslateRequest( request_data )
    body = json.dumps( parameters )
    request_hmac = self._ComputeRequestHmac( method, handler, body )

    extra_headers = { 'content-type': 'application/json' }
    extra_headers[ RACERD_HMAC_HEADER ] = request_hmac

    response = requests.request( method,
                                 url,
                                 data = body,
                                 headers = extra_headers )

    response.raise_for_status()

    if response.status_code is httplib.NO_CONTENT:
      return None

    return response.json()


  def _TranslateRequest( self, request_data ):
    """
    Transform ycm request into racerd request
    """
    if request_data is None:
      return None

    file_path = request_data[ 'filepath' ]
    buffers = []
    for path, obj in request_data[ 'file_data' ].items():
        buffers.append( {
            'contents': obj[ 'contents' ],
            'file_path': path
        } )

    line = request_data[ 'line_num' ]
    col = request_data[ 'column_num' ] - 1

    return {
        'buffers': buffers,
        'line': line,
        'column': col,
        'file_path': file_path
    }


  def _GetExtraData( self, completion ):
      location = {}
      if completion[ 'file_path' ]:
        location[ 'filepath' ] = ToUtf8IfNeeded( completion[ 'file_path' ] )
      if completion[ 'line' ]:
        location[ 'line_num' ] = completion[ 'line' ]
      if completion[ 'column' ]:
        location[ 'column_num' ] = completion[ 'column' ] + 1

      if location:
        extra_data = {}
        extra_data[ 'location' ] = location
        return extra_data
      else:
        return None


  def ComputeCandidatesInner( self, request_data ):
    completions = self._FetchCompletions( request_data )
    if completions is None:
      return []

    return [ responses.BuildCompletionData(
                insertion_text = ToUtf8IfNeeded( completion[ 'text' ] ),
                kind = ToUtf8IfNeeded( completion[ 'kind' ] ),
                extra_menu_info = ToUtf8IfNeeded( completion[ 'context' ] ),
                extra_data = self._GetExtraData( completion ) )
             for completion in completions ]


  def _FetchCompletions( self, request_data ):
    return self._GetResponse( '/list_completions', request_data )


  def _WriteSecretFile( self, secret ):
    """
    Write a file containing the `secret` argument. The path to this file is
    returned.

    Note that racerd consumes the file upon reading; removal of the temp file is
    intentionally not handled here.
    """

    # Make temp file
    secret_fd, secret_path = tempfile.mkstemp( text=True )

    # Write secret
    secret_file = os.fdopen( secret_fd, 'w' )
    secret_file.write( secret )
    secret_file.close()

    return secret_path


  def _StartServerNoLock( self ):
    """
    Start racerd. `self._lock` must be held when this is called.
    """
    self._logger.info( 'RustCompleter using RACERD = ' + RACERD )

    self._hmac_secret = self._CreateHmacSecret()
    secret_file_path = self._WriteSecretFile( self._hmac_secret )

    args = [ RACERD, 'serve', '--port=0', '--secret-file', secret_file_path ]

    rust_src_path = self._GetRustSrcPath()
    if rust_src_path is not None:
      args.extend( [ '--rust-src-path', rust_src_path ] )

    self._racerd_phandle = utils.SafePopen( args, stdout = subprocess.PIPE )

    # The first line output by racerd includes the host and port the server is
    # listening on.
    host = self._racerd_phandle.stdout.readline()
    self._logger.info( 'RustCompleter using host = ' + host )
    host = host.split()[3]
    self._racerd_host = 'http://' + host


  def ServerIsRunningNoLock( self ):
    """
    Check racerd status. `self._lock` must be held when this is called.
    """
    if self._racerd_host is None or self._racerd_phandle is None:
      return False

    try:
      self._GetResponse( '/ping', method = 'GET' )
      return True
    except requests.HTTPError:
      self._StopServerNoLock()
      return False


  def _StopServerNoLock( self ):
    """
    Stop racerd. `self._lock` must be held when this is called.
    """
    if self._racerd_phandle:
      self._racerd_phandle.terminate()
      self._racerd_phandle = None
      self._racerd_host = None


  def _StopServer( self ):
    with self._lock:
      self._StopServerNoLock()


  def _RestartServer( self ):
    """
    Thread safe server restart
    """
    self._logger.debug( 'RustCompleter restarting racerd' )

    with self._lock:
      if self.ServerIsRunningNoLock():
        self._StopServerNoLock()
      self._StartServerNoLock()

    self._logger.debug( 'RustCompleter has restarted racerd' )


  def GetSubcommandsMap( self ):
    return {
      'GoTo' : ( lambda self, request_data, args:
                 self._GoToDefinition( request_data ) ),
      'GoToDefinition' : ( lambda self, request_data, args:
                           self._GoToDefinition( request_data ) ),
      'GoToDeclaration' : ( lambda self, request_data, args:
                           self._GoToDefinition( request_data ) ),
      'StopServer' : ( lambda self, request_data, args:
                           self._StopServer() ),
      'RestartServer' : ( lambda self, request_data, args:
                           self._RestartServer() ),
    }


  def _GoToDefinition( self, request_data ):
    try:
      definition =  self._GetResponse( '/find_definition', request_data )
      return responses.BuildGoToResponse( definition[ 'file_path' ],
                                          definition[ 'line' ],
                                          definition[ 'column' ] + 1 )
    except Exception:
      raise RuntimeError( 'Can\'t jump to definition.' )


  def Shutdown( self ):
    self._StopServer()


  def _CreateHmacSecret( self ):
    return base64.b64encode( os.urandom( HMAC_SECRET_LENGTH ) )
