#!/usr/bin/env python
# vim: ts=2 sw=2 cc=80 tw=79
#
# Copyright (C) 2011, 2012  Stephen Sugden <me@stephensugden.com>
#                           Google Inc.
#                           Stanislav Golovanov <stgolovanov@gmail.com>
#
# This file is part of YouCompleteMe.
#
# YouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# YouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with YouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

from ycmd.utils import ToUtf8IfNeeded
from ycmd.completers.completer import Completer
from ycmd import responses, utils

import logging
import urlparse
import requests
import subprocess

import sys
import os

from os import path as p

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.abspath( p.join( DIR_OF_THIS_SCRIPT,
                             '..', '..', '..', 'third_party' ) )
RACERD = p.join( DIR_OF_THIRD_PARTY, 'racerd', 'target', 'release', 'racerd' )

class RustCompleter( Completer ):
  """
  A completer for the rust programming language backed by racerd.
  https://github.com/jwilm/racerd
  """

  def _GetRustSrcPath( self ):
    """
    Provide path to rust source directory for use by the completer.

    This could just be passed through by the environment, but it may be moved
    into editor configuration or some other location in which case this would
    become necessary anyways.
    """
    src_key = 'RUST_SRC_PATH'
    if not os.environ.has_key(src_key):
      raise RuntimeError( src_key + ' environment variable is not set' )

    return os.environ[src_key]


  def __init__( self, user_options ):
    super( RustCompleter, self ).__init__( user_options )
    self._racerd_host = None
    self._logger = logging.getLogger( __name__ )
    self._logger.info('building RustCompleter')
    self._keep_logfiles = user_options[ 'server_keep_logfiles' ]
    self._StartServer()


  def SupportedFiletypes( self ):
    return [ 'rust' ]


  def _GetResponse( self, handler, request_data = {} ):
    """
    Query racerd via HTTP

    racerd returns JSON with 200 OK responses. 204 No Content responses occur
    when no errors were encountered but no completions, definitions, or errors
    were found.
    """
    self._logger.info('RustCompleter._GetResponse')
    target = urlparse.urljoin( self._racerd_host, handler )
    parameters = self._TranslateRequest( request_data )
    response = requests.post( target, json = parameters )
    response.raise_for_status()

    if response.status_code is 204:
      return None

    return response.json()


  def _TranslateRequest( self, request_data ):
    """
    Transform ycm request into racerd request
    """
    if not request_data:
      return {}

    file_path = request_data[ 'filepath' ]
    buffers = []
    for path, obj in request_data[ 'file_data' ].items():
        buffers.append({
            'contents': obj['contents'],
            'file_path': path
        })

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
    self._logger.info( 'rust ComputeCandidatesInner' )
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

  def _StartServer( self ):
    self._logger.info('_StartServer using RACERD = ' + RACERD)
    self._racerd_phandle = utils.SafePopen( [
        RACERD, 'serve', '--port=0', '--secret-file=not_supported',
                '--rust-src-path=' + self._GetRustSrcPath()
      ], stdout = subprocess.PIPE )

    # The first line output by racerd includes the host and port the server is
    # listening on.
    host = self._racerd_phandle.stdout.readline()
    self._logger.info('_StartServer using host = ' + host)
    host = host.split()[3]
    self._racerd_host = 'http://' + host

  def DefinedSubcommands( self ):
    return [
      'GoTo',
      'GoToDefinition'
      'RestartServer',
      'StopServer',
    ]

  def ServerIsRunning( self ):
    self._GetResponse( '/ping', { 'ping': True } )

  def _StopServer( self ):
    self._racerd_phandle.terminate()
    self._racerd_phandle = None

  def RestartServer( self ):
    self._StopServer()
    self._StartServer()

  def _RestartServer( self, request_data ):
    # TODO request_data
    self._RestartServer()

  # TODO
  # def OnFileReadyToParse( self, request_data ):
  #   if not self.ServerIsRunning():
  #     self._StartServer( request_data )

  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command_map = {
      'GoTo' : {
        'method': self._GoToDefinition,
        'args': { 'request_data': request_data }
      },
      'GoToDefinition' : {
        'method': self._GoToDefinition,
        'args': { 'request_data': request_data }
      },
      'GoToDeclaration' : {
        'method': self._GoToDefinition,
        'args': { 'request_data': request_data }
      },
      'StopServer' : {
        'method': self._StopServer,
        'args': { 'request_data': request_data }
      },
      'RestartServer' : {
        'method': self._RestartServer,
        'args': { 'request_data': request_data }
      }
    }

    try:
      command_def = command_map[ arguments[ 0 ] ]
    except KeyError:
      raise ValueError( self.UserCommandsHelpMessage() )

    return command_def[ 'method' ]( **( command_def[ 'args' ] ) )


  def _GoToDefinition( self, request_data ):
    try:
      definition =  self._GetResponse( '/find_definition', request_data )
      return responses.BuildGoToResponse( definition[ 'file_path' ],
                                          definition[ 'line' ],
                                          definition[ 'column' ] + 1 )
    except Exception:
      raise RuntimeError( 'Can\'t jump to definition.' )

  def Shutdown( self ):
    self._racerd_phandle.terminate()
