#!/usr/bin/env python
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

import sys
import os


PYTHON_EXECUTABLE_PATH = sys.executable
PATH_TO_JEDIHTTP = os.path.join( os.path.abspath( os.path.dirname( __file__ ) ),
                                 '..', '..', '..',
                                 'third_party', 'JediHTTP', 'jedihttp' )

LOG_FILENAME_FORMAT = os.path.join( utils.PathToTempDir(),
                                    u'jedihttp_{port}_{std}.log' )


class JediCompleter( Completer ):
  """
  A Completer that uses the Jedi engine HTTP wrapper JediHTTP.
  https://jedi.readthedocs.org/en/latest/
  https://github.com/vheon/JediHTTP
  """

  def __init__( self, user_options ):
    super( JediCompleter, self ).__init__( user_options )
    self._jedihttp_port = None
    self._jedihttp_phandle = None
    self._logger = logging.getLogger( __name__ )
    self._logfile_stdout = None
    self._logfile_stderr = None
    self._keep_logfiles = user_options[ 'server_keep_logfiles' ]


  def SupportedFiletypes( self ):
    """ Just python """
    return [ 'python' ]


  def Shutdown( self ):
    if ( self.ServerIsRunning() ):
      self._StopServer()


  def ServerIsReady( self ):
    """ Check if JediHTTP server is ready. """
    try:
      return bool( self._GetResponse( '/ready' ) )
    except:
      return False


  def ServerIsRunning( self ):
    """ Check if JediHTTP server is running (up and serving). """
    try:
      return bool( self._GetResponse( '/healthy' ) )
    except:
      return False


  def _StopServer( self ):
    self._jedihttp_phandle.kill()
    self._jedihttp_phandle = None
    self._jedihttp_port = None

    if ( not self._keep_logfiles ):
      os.unlink( self._logfile_stdout )
      os.unlink( self._logfile_stderr )

    self._logger.info( 'Stopping JediHTTP' )


  def _StartServer( self, request_data ):
    self._ChoosePort()

    command = [ PYTHON_EXECUTABLE_PATH,
                PATH_TO_JEDIHTTP,
                '--port',
                str( self._jedihttp_port ) ]

    self._logfile_stdout = LOG_FILENAME_FORMAT.format(
        port = self._jedihttp_port, std = 'stdout' )
    self._logfile_stderr = LOG_FILENAME_FORMAT.format(
        port = self._jedihttp_port, std = 'stderr' )

    with open( self._logfile_stderr, 'w' ) as logerr:
      with open( self._logfile_stdout, 'w' ) as logout:
        self._jedihttp_phandle = utils.SafePopen( command,
                                                  stdout = logout,
                                                  stderr = logerr )
    self._logger.info( 'Starting JediHTTP server' )


  def _ChoosePort( self ):
    if not self._jedihttp_port:
      self._jedihttp_port = utils.GetUnusedLocalhostPort()
    self._logger.info( u'using port {0}'.format( self._jedihttp_port ) )


  def _GetResponse( self, handler, request_data = {} ):
    """ Handle comunication with server """
    target = urlparse.urljoin( self._ServerLocation(), handler )
    parameters = self._TranslateRequestForJediHTTP( request_data )
    response = requests.post( target, json = parameters )
    if response.status_code != requests.codes.ok:
      raise RuntimeError( response[ 'message' ] )
    return response.json()


  def _TranslateRequestForJediHTTP( self, request_data ):
    if not request_data:
      return {}

    path = request_data[ 'filepath' ]
    source = request_data[ 'file_data' ][ path ][ 'contents' ]
    line = request_data[ 'line_num' ]
    # JediHTTP as Jedi itself expects columns to start at 0, not 1
    col = request_data[ 'column_num' ] - 1

    return {
        'source': source,
        'line': line,
        'col': col,
        'path': path
    }


  def _ServerLocation( self ):
    return 'http://localhost:' + str( self._jedihttp_port )


  def _GetExtraData( self, completion ):
      location = {}
      if completion[ 'module_path' ]:
        location[ 'filepath' ] = ToUtf8IfNeeded( completion[ 'module_path' ] )
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
    return [ responses.BuildCompletionData(
                ToUtf8IfNeeded( completion[ 'name' ] ),
                ToUtf8IfNeeded( completion[ 'description' ] ),
                ToUtf8IfNeeded( completion[ 'docstring' ] ),
                extra_data = self._GetExtraData( completion ) )
             for completion in self._JediCompletions( request_data ) ]


  def _JediCompletions( self, request_data ):
    resp = self._GetResponse( '/completions', request_data )[ 'completions' ]
    return resp


  def OnFileReadyToParse( self, request_data ):
    if ( not self.ServerIsRunning() ):
      self._StartServer( request_data )


  def DefinedSubcommands( self ):
    # We don't want expose this sub-command because is not really needed for
    # the user but is useful in tests for tearing down the server
    subcommands = super( JediCompleter, self ).DefinedSubcommands()
    subcommands.remove( 'StopServer' )
    return subcommands


  def GetSubcommandsMap( self ):
    return {
      'GoToDefinition' : ( lambda self, request_data:
                           self._GoToDefinition( request_data ) ),
      'GoToDeclaration': ( lambda self, request_data:
                           self._GoToDeclaration( request_data ) ),
      'GoTo'           : ( lambda self, request_data:
                           self._GoTo( request_data ) ),
      'GetDoc'         : ( lambda self, request_data:
                           self._GetDoc( request_data ) ),
      'StopServer'     : ( lambda self, request_data:
                           self._StopServer() )
    }


  def _GoToDefinition( self, request_data ):
    try:
      return self._GetDefinitionsList( '/gotodefinition', request_data )
    except:
      raise RuntimeError( 'Can\'t jump do definition.' )


  def _GoToDeclaration( self, request_data ):
    try:
      return self._GetDefinitionsList( '/gotoassignment', request_data )
    except:
      raise RuntimeError( 'Can\'t jump do declaration.' )


  def _GoTo( self, request_data ):
    pass


  def _GetDoc( self, request_data ):
    pass


  def _GetDefinitionsList( self, handle, request_data ):
    try:
      response = self._GetResponse( handle, request_data )
      return self._BuildGoToResponse( response[ 'definitions' ] )
    except:
      raise RuntimeError( 'Cannot follow nothing. Put your cursor on a valid name.' )


  def _BuildGoToResponse( self, definition_list ):
   if len( definition_list ) == 1:
      definition = definition_list[ 0 ]
      if definition[ 'in_builtin_module' ]:
        if definition[ 'is_keyword' ]:
          raise RuntimeError( 'Cannot get the definition of Python keywords.' )
        else:
          raise RuntimeError( 'Builtin modules cannot be displayed.' )
      else:
        return responses.BuildGoToResponse( definition[ 'module_path' ],
                                            definition[ 'line' ],
                                            definition[ 'column' ] + 1 )
   else:
     # multiple definitions
     defs = []
     for definition in definition_list:
       if definition[ 'in_builtin_module' ]:
         defs.append( responses.BuildDescriptionOnlyGoToResponse(
                      'Builtin ' + definition[ 'description' ] ) )
       else:
         defs.append(
           responses.BuildGoToResponse( definition[ 'module_path' ],
                                        definition[ 'line' ],
                                        definition[ 'column' ] + 1,
                                        definition[ 'description' ] ) )
     return defs


  def _BuildDetailedInfoResponse( self, definition_list ):
    pass

