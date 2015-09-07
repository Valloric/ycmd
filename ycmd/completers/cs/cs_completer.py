#!/usr/bin/env python
#
# Copyright (C) 2011, 2012  Chiel ten Brinke <ctenbrinke@gmail.com>
#                           Google Inc.
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

from collections import defaultdict
import os
import fcntl
import time
from ycmd.completers.completer import Completer
from ycmd.utils import ForceSemanticCompletion
from ycmd import responses
from ycmd import utils
import json
import requests
import urlparse
import logging
import solutiondetection
from threading import (Thread, RLock)
from Queue import Queue, Empty
from ptyprocess import PtyProcessUnicode
import traceback
from subprocess import PIPE
import types

SERVER_NOT_FOUND_MSG = ( 'OmniSharp server binary not found at {0}. ' +
                         'Did you compile it? You can do so by running ' +
                         '"./install.py --omnisharp-completer".' )
INVALID_FILE_MESSAGE = 'File is invalid.'
NO_DIAGNOSTIC_MESSAGE = 'No diagnostic for current line!'
PATH_TO_LEGACY_OMNISHARP_BINARY = os.path.join(
  os.path.abspath( os.path.dirname( __file__ ) ),
  '..', '..', '..', 'third_party', 'OmniSharpServer',
  'OmniSharp', 'bin', 'Release', 'OmniSharp.exe' )
PATH_TO_ROSLYN_OMNISHARP_BINARY = os.path.join(
  os.path.abspath( os.path.dirname( __file__ ) ),
  '..', '..', '..', 'third_party', 'omnisharp-roslyn', 'scripts',
  (  'Omnisharp.cmd' if utils.OnWindows() or utils.OnCygwin() else 'Omnisharp' ) )

BENCHMARKING = False


# TODO: Handle this better than dummy classes
class CsharpDiagnostic:
  def __init__ ( self, ranges, location, location_extent, text, kind ):
    self.ranges_ = ranges
    self.location_ = location
    self.location_extent_ = location_extent
    self.text_ = text
    self.kind_ = kind


class CsharpFixIt:
  def __init__ ( self, location, chunks ):
    self.location = location
    self.chunks = chunks


class CsharpFixItChunk:
  def __init__ ( self, replacement_text, range ):
    self.replacement_text = replacement_text
    self.range = range


class CsharpDiagnosticRange:
  def __init__ ( self, start, end ):
    self.start_ = start
    self.end_ = end


class CsharpDiagnosticLocation:
  def __init__ ( self, line, column, filename ):
    self.line_number_ = line
    self.column_number_ = column
    self.filename_ = filename


class CsharpCompleter( Completer ):
  """
  A Completer that uses the Omnisharp server as completion engine.
  """
  subcommands = {
    'SetOmnisharpPath': ( lambda self, request_data, arguments:
        self._SetOmnisharpPath( request_data, arguments ) ),
    'UseLegacyOmnisharp': ( lambda self, request_data, arguments:
        self._SetOmnisharpPath( request_data, [ PATH_TO_LEGACY_OMNISHARP_BINARY, False ] ) ),
    'UseRoslynOmnisharp': ( lambda self, request_data, arguments:
        self._SetOmnisharpPath( request_data, [ PATH_TO_ROSLYN_OMNISHARP_BINARY, True ] ) ),
  }


  def __init__( self, user_options ):
    super( CsharpCompleter, self ).__init__( user_options )
    self._logger = logging.getLogger( __name__ )
    self._solution_for_file = {}
    self._completer_per_solution = {}
    self._diagnostic_store = None
    self._max_diagnostics_to_display = user_options[
      'max_diagnostics_to_display' ]
    self._omnisharp_path = PATH_TO_ROSLYN_OMNISHARP_BINARY
    self._use_stdio = True


  def Shutdown( self ):
    if ( self.user_options[ 'auto_stop_csharp_server' ] ):
      for solutioncompleter in self._completer_per_solution.values():
        solutioncompleter._StopServer()


  def SupportedFiletypes( self ):
    """ Just csharp """
    return [ 'cs' ]


  def _GetSolutionCompleter( self, request_data ):
    solution = self._GetSolutionFile( request_data[ "filepath" ] )
    if not solution in self._completer_per_solution:
      keep_logfiles = self.user_options[ 'server_keep_logfiles' ]
      if self._use_stdio:
        completer = StdioCsharpSolutionCompleter( self._omnisharp_path, solution, keep_logfiles )
      else:
        desired_omnisharp_port = self.user_options.get( 'csharp_server_port' )
        completer = HttpCsharpSolutionCompleter( self._omnisharp_path, solution, keep_logfiles, desired_omnisharp_port )
      self._completer_per_solution[ solution ] = completer

    return self._completer_per_solution[ solution ]


  def ShouldUseNowInner( self, request_data ):
    solutioncompleter = self._GetSolutionCompleter( request_data )
    return solutioncompleter.ShouldUseNowInner( request_data )


  def CompletionType( self, request_data ):
    return ForceSemanticCompletion( request_data )


  def ComputeCandidatesInner( self, request_data ):
    solutioncompleter = self._GetSolutionCompleter( request_data )
    completion_type = self.CompletionType( request_data )
    return [ responses.BuildCompletionData(
                completion[ 'CompletionText' ],
                completion[ 'DisplayText' ],
                completion[ 'Description' ],
                None,
                None,
                { "required_namespace_import" :
                   completion[ 'RequiredNamespaceImport' ] } )
             for completion
             in solutioncompleter._GetCompletions( request_data, 
                                                   completion_type ) ]


  def FilterAndSortCandidates( self, candidates, query ):
    result = super(CsharpCompleter, self).FilterAndSortCandidates( candidates,
                                                                   query )
    result.sort( _CompleteSorterByImport );
    return result


  def DefinedSubcommands( self ):
    return CsharpCompleter.subcommands.keys() + CsharpSolutionCompleter.subcommands.keys()


  def OnFileReadyToParse( self, request_data ):
    solutioncompleter = self._GetSolutionCompleter( request_data )

    if ( not solutioncompleter.ServerIsActive() and
         self.user_options[ 'auto_start_csharp_server' ] ):
      solutioncompleter._StartServer()
      return

    errors = solutioncompleter.CodeCheck( request_data )

    diagnostics = [ self._QuickFixToDiagnostic( x ) for x in
                    errors[ "QuickFixes" ] ]

    self._diagnostic_store = DiagnosticsToDiagStructure( diagnostics )

    return [ responses.BuildDiagnosticData( x ) for x in
             diagnostics[ : self._max_diagnostics_to_display ] ]


  def _QuickFixToDiagnostic( self, quick_fix ):
    filename = quick_fix[ "FileName" ]

    location = CsharpDiagnosticLocation( quick_fix[ "Line" ],
                                         quick_fix[ "Column" ], filename )
    location_range = CsharpDiagnosticRange( location, location )
    return CsharpDiagnostic( list(),
                             location,
                             location_range,
                             quick_fix[ "Text" ],
                             quick_fix[ "LogLevel" ].upper() )


  def GetDetailedDiagnostic( self, request_data ):
    current_line = request_data[ 'line_num' ]
    current_column = request_data[ 'column_num' ]
    current_file = request_data[ 'filepath' ]

    if not self._diagnostic_store:
      raise ValueError( NO_DIAGNOSTIC_MESSAGE )

    diagnostics = self._diagnostic_store[ current_file ][ current_line ]
    if not diagnostics:
      raise ValueError( NO_DIAGNOSTIC_MESSAGE )

    closest_diagnostic = None
    distance_to_closest_diagnostic = 999

    for diagnostic in diagnostics:
      distance = abs( current_column - diagnostic.location_.column_number_ )
      if distance < distance_to_closest_diagnostic:
        distance_to_closest_diagnostic = distance
        closest_diagnostic = diagnostic

    return responses.BuildDisplayMessageResponse(
      closest_diagnostic.text_ )


  def OnUserCommand( self, arguments, request_data ):
    if not arguments:
      raise ValueError( self.UserCommandsHelpMessage() )

    command = arguments[ 0 ]
    del arguments[ 0 ]
    if command in CsharpCompleter.subcommands:
      return CsharpCompleter.subcommands[ command ]( self, request_data, arguments )
    elif command in CsharpSolutionCompleter.subcommands:
      solutioncompleter = self._GetSolutionCompleter( request_data )
      return solutioncompleter.Subcommand( command, arguments, request_data )
    else:
      raise ValueError( self.UserCommandsHelpMessage() )


  def DebugInfo( self, request_data ):
    solutioncompleter = self._GetSolutionCompleter( request_data )
    if solutioncompleter.ServerIsRunning():
      return ( 'OmniSharp Server running at: {0}\n'
               'OmniSharp logfiles:\n{1}\n{2}' ).format(
                   solutioncompleter._ServerLocation(),
                   solutioncompleter._filename_stdout,
                   solutioncompleter._filename_stderr )
    else:
      return 'OmniSharp Server is not running'


  def ServerIsRunning( self, request_data = None ):
    """ Check if our OmniSharp server is running. """
    return self._CheckSingleOrAllActive( request_data,
                                         lambda i: i.ServerIsRunning() )


  def ServerIsReady( self, request_data = None ):
    """ Check if our OmniSharp server is ready (loaded solution file)."""
    return self._CheckSingleOrAllActive( request_data,
                                         lambda i: i.ServerIsReady() )


  def ServerTerminated( self, request_data = None ):
    """ Check if the server process has already terminated. """
    return self._CheckSingleOrAllActive( request_data,
                                         lambda i: i.ServerTerminated() )


  def _SetOmnisharpPath( self, request_data, arguments ):
    self._omnisharp_path = arguments[0]
    self._use_stdio = bool( arguments[1] )

    if not os.path.isfile( self._omnisharp_path ):
      raise RuntimeError(
           SERVER_NOT_FOUND_MSG.format( self._omnisharp_path ) )

    solution = self._GetSolutionFile( request_data[ "filepath" ] )
    if solution in self._completer_per_solution: 
      del self._completer_per_solution[ solution ]


  def _CheckSingleOrAllActive( self, request_data, action ):
    if request_data is not None:
      solutioncompleter = self._GetSolutionCompleter( request_data )
      return action( solutioncompleter )
    else:
      solutioncompleters = self._completer_per_solution.values()
      return all( action( completer )
        for completer in solutioncompleters if completer.ServerIsActive() )


  def _GetSolutionFile( self, filepath ):
    if not filepath in self._solution_for_file:
      # NOTE: detection could throw an exception if an extra_conf_store needs
      # to be confirmed
      path_to_solutionfile = solutiondetection.FindSolutionPath( filepath )
      if not path_to_solutionfile:
          raise RuntimeError( 'Autodetection of solution file failed. \n' )
      self._solution_for_file[ filepath ] = path_to_solutionfile

    return self._solution_for_file[ filepath ]


class CsharpSolutionCompleter( object ):
  subcommands = {
    'StartServer': ( lambda self, request_data, arguments: self._StartServer() ),
    'StopServer': ( lambda self, request_data, arguments: self._StopServer() ),
    'RestartServer': ( lambda self, request_data, arguments: self._RestartServer() ),
    'ReloadSolution': ( lambda self, request_data, arguments: self._ReloadSolution() ),
    'SolutionFile': ( lambda self, request_data, arguments: self._SolutionFile() ),
    'GoToDefinition': ( lambda self, request_data, arguments: self._GoToDefinition(
        request_data ) ),
    'GoToDeclaration': ( lambda self, request_data, arguments: self._GoToDefinition(
        request_data ) ),
    'GoTo': ( lambda self, request_data, arguments: self._GoToImplementation(
        request_data, True ) ),
    'GoToDefinitionElseDeclaration': ( lambda self, request_data, arguments:
        self._GoToDefinition( request_data ) ),
    'GoToImplementation': ( lambda self, request_data, arguments:
        self._GoToImplementation( request_data, False ) ),
    'GoToImplementationElseDeclaration': ( lambda self, request_data, arguments:
        self._GoToImplementation( request_data, True ) ),
    'GetType': ( lambda self, request_data, arguments: self._GetType(
        request_data ) ),
    'FixIt': ( lambda self, request_data, arguments: self._FixIt( request_data ) ),
    'ServerRunning': ( lambda self, request_data, arguments: self.ServerIsRunning() ),
    'ServerReady': ( lambda self, request_data, arguments: self.ServerIsReady() ),
    'ServerTerminated': ( lambda self, request_data, arguments: self.ServerTerminated() ),
    'ReadAllLines': ( lambda self, request_data, arguments: self._ReadAllLines() ),
  }


  def __init__( self, omnisharp_path, solution_path, keep_logfiles ):
    self._logger = logging.getLogger( __name__ )
    self._solution_path = solution_path
    self._keep_logfiles = keep_logfiles
    self._omnisharp_path = omnisharp_path
    self._filename_stderr = None
    self._filename_stdout = None
    self._omnisharp_phandle = None
    self._pending_request = 0;

    if not os.path.isfile( self._omnisharp_path ):
      raise RuntimeError(
           SERVER_NOT_FOUND_MSG.format( self._omnisharp_path ) )


  def ShouldUseNowInner( self, request_data ):
    return True


  def Subcommand( self, command, arguments, request_data ):
    command_lamba = CsharpSolutionCompleter.subcommands[ command ]
    return command_lamba( self, request_data, arguments )


  def DefinedSubcommands( self ):
    return CsharpSolutionCompleter.subcommands.keys()


  def CodeCheck( self, request_data ):
    filename = request_data[ 'filepath' ]
    if not filename:
      raise ValueError( INVALID_FILE_MESSAGE )

    return self._GetResponse( '/codecheck',
                              self._DefaultParameters( request_data ) )


  def _StartServer( self ):
    """ Start the OmniSharp server """
    raise RuntimeError( "Abstract method" )


  def _StopServer( self ):
    """ Stop the OmniSharp server """
    self._logger.info( 'Stopping OmniSharp server' )

    self._TryToStopServer()

    self._CleanupAfterServerStop()

    self._logger.info( 'Stopped OmniSharp server' )


  def _TryToStopServer( self ):
    for _ in range( 5 ):
      try:
        self._GetResponse( '/stopserver', timeout = .1 )
      except:
        pass
      for _ in range( 10 ):
        if self.ServerTerminated():
          return
        time.sleep( .1 )


  def _ForceStopServer( self ):
    # Kill it if it's still up
    if not self.ServerTerminated() and self._omnisharp_phandle is not None:
      self._logger.info( 'Killing OmniSharp server' )
      self._omnisharp_phandle.kill()


  def _CleanupAfterServerStop( self ):
    self._omnisharp_port = None
    self._omnisharp_phandle = None
    if ( not self._keep_logfiles ):
      if self._filename_stdout:
        try:
          os.unlink( self._filename_stdout );
        except:
          pass
      if self._filename_stderr:
        try:
          os.unlink( self._filename_stderr );
        except:
          pass


  def _RestartServer ( self ):
    """ Restarts the OmniSharp server """
    if self.ServerIsRunning():
      self._StopServer()
    return self._StartServer()


  def _ReloadSolution( self ):
    """ Reloads the solutions in the OmniSharp server """
    self._logger.info( 'Reloading Solution in OmniSharp server' )
    return self._GetResponse( '/reloadsolution' )


  def CompletionType( self, request_data ):
    return ForceSemanticCompletion( request_data )


  def _GetCompletions( self, request_data, completion_type ):
    """ Ask server for completions """
    parameters = self._DefaultParameters( request_data )
    parameters[ 'WantImportableTypes' ] = completion_type
    parameters[ 'ForceSemanticCompletion' ] = completion_type
    parameters[ 'WantDocumentationForEveryCompletionResult' ] = True
    completions = self._GetResponse( '/autocomplete', parameters )
    return completions if completions != None else []


  def _GoToDefinition( self, request_data ):
    """ Jump to definition of identifier under cursor """
    definition = self._GetResponse( '/gotodefinition',
                                    self._DefaultParameters( request_data ) )
    if definition[ 'FileName' ] != None:
      return responses.BuildGoToResponse( definition[ 'FileName' ],
                                          definition[ 'Line' ],
                                          definition[ 'Column' ] )
    else:
      raise RuntimeError( 'Can\'t jump to definition' )


  def _GoToImplementation( self, request_data, fallback_to_declaration ):
    """ Jump to implementation of identifier under cursor """
    implementation = self._GetResponse(
        '/findimplementations',
        self._DefaultParameters( request_data ) )

    if implementation[ 'QuickFixes' ]:
      if len( implementation[ 'QuickFixes' ] ) == 1:
        return responses.BuildGoToResponse(
            implementation[ 'QuickFixes' ][ 0 ][ 'FileName' ],
            implementation[ 'QuickFixes' ][ 0 ][ 'Line' ],
            implementation[ 'QuickFixes' ][ 0 ][ 'Column' ] )
      else:
        return [ responses.BuildGoToResponse( x[ 'FileName' ],
                                              x[ 'Line' ],
                                              x[ 'Column' ] )
                 for x in implementation[ 'QuickFixes' ] ]
    else:
      if ( fallback_to_declaration ):
        return self._GoToDefinition( request_data )
      elif implementation[ 'QuickFixes' ] == None:
        raise RuntimeError( 'Can\'t jump to implementation' )
      else:
        raise RuntimeError( 'No implementations found' )


  def _GetType( self, request_data ):
    request = self._DefaultParameters( request_data )
    request[ "IncludeDocumentation" ] = True

    result = self._GetResponse( '/typelookup', request )
    message = result[ "Type" ]
    if ( result[ "Documentation" ] ):
      message += "\n" + result[ "Documentation" ]

    return responses.BuildDisplayMessageResponse( message )


  def _FixIt( self, request_data ):
    request = self._DefaultParameters( request_data )

    result = self._GetResponse( '/fixcodeissue', request )
    replacement_text = result[ "Text" ]
    location = CsharpDiagnosticLocation( request_data['line_num'],
                                         request_data['column_num'],
                                         request_data['filepath'] )
    fixits = [ CsharpFixIt( location,
                            _BuildChunks( request_data, replacement_text ) ) ]

    return responses.BuildFixItResponse( fixits )


  def _DefaultParameters( self, request_data ):
    """ Some very common request parameters """
    parameters = {}
    parameters[ 'line' ] = request_data[ 'line_num' ]
    parameters[ 'column' ] = request_data[ 'column_num' ]
    filepath = request_data[ 'filepath' ]
    parameters[ 'buffer' ] = (
      request_data[ 'file_data' ][ filepath ][ 'contents' ] )
    parameters[ 'filename' ] = filepath
    return parameters


  def ServerTerminated( self ):
    """ Check if the server process has already terminated. """
    return ( self._omnisharp_phandle is not None and
             self._omnisharp_phandle.poll() is not None )


  def _SolutionFile( self ):
    """ Find out which solution file server was started with """
    return self._solution_path


  def _GetResponse( self, handler, parameters = {}, timeout = None ):
    """ Handle communication with server """
    raise RuntimeError("Abstract")


  def _ServerLocation( self ):
    raise RuntimeError("Abstract")


  def ServerIsActive( self ):
    """ Check if our OmniSharp server is active (started, not yet stopped)."""
    raise RuntimeError("Abstract")


  def ServerIsRunning( self ):
    """ Check if our OmniSharp server is running (up and serving)."""
    raise RuntimeError("Abstract")


  def ServerIsReady( self ):
    """ Check if our OmniSharp server is ready (loaded solution file)."""
    raise RuntimeError("Abstract")


class HttpCsharpSolutionCompleter( CsharpSolutionCompleter ):
  def __init__( self, omnisharp_path, solution_path, keep_logfiles, desired_omnisharp_port ):
    super( HttpCsharpSolutionCompleter, self ).__init__( omnisharp_path, solution_path, keep_logfiles )
    self._omnisharp_port = None
    self._omnisharp_phandle = None
    self._desired_omnisharp_port = desired_omnisharp_port;


  def _StartServer( self ):
    self._logger.info( 'startup' )

    self._logger.info(
        u'Loading solution file {0}'.format( self._solution_path ) )

    self._ChooseOmnisharpPort()

    command = [ self._omnisharp_path,
                '-p',
                str( self._omnisharp_port ),
                '-s',
                u'{0}'.format( self._solution_path ) ]

    if not utils.OnWindows() and not utils.OnCygwin():
      command.insert( 0, 'mono' )

    if utils.OnCygwin():
      command.extend( [ '--client-path-mode', 'Cygwin' ] )

    filename_format = os.path.join( utils.PathToTempDir(),
                                    u'omnisharp_{port}_{sln}_{std}.log' )

    solutionfile = os.path.basename( self._solution_path )
    self._filename_stdout = filename_format.format(
        port = self._omnisharp_port, sln = solutionfile, std = 'stdout' )
    self._filename_stderr = filename_format.format(
        port = self._omnisharp_port, sln = solutionfile, std = 'stderr' )

    with open( self._filename_stderr, 'w' ) as fstderr:
      with open( self._filename_stdout, 'w' ) as fstdout:
        self._omnisharp_phandle = utils.SafePopen(
            command, stdout = fstdout, stderr = fstderr )

    self._logger.info( 'Starting OmniSharp server' )


  def _GetResponse( self, handler, parameters = {}, timeout = None ):
    """ Handle communication with server """
    try:
      self._pending_request = self._pending_request + 1
      target = urlparse.urljoin( self._ServerLocation(), handler )
      response = requests.post( target, json = parameters, timeout = timeout )
      return response.json()
    finally:
      self._pending_request = (
        self._pending_request - 1 if self._pending_request > 0
        else 0 )


  def _CleanupAfterServerStop( self ):
    self._omnisharp_port = None
    super( HttpCsharpSolutionCompleter, self )._CleanupAfterServerStop()


  def _ServerLocation( self ):
    return 'http://localhost:' + str( self._omnisharp_port )


  def _ChooseOmnisharpPort( self ):
    if not self._omnisharp_port:
        if self._desired_omnisharp_port:
            self._omnisharp_port = int( self._desired_omnisharp_port )
        else:
            self._omnisharp_port = utils.GetUnusedLocalhostPort()
    self._logger.info( u'using port {0}'.format( self._omnisharp_port ) )


  def ServerIsActive( self ):
    """ Check if our OmniSharp server is active (started, not yet stopped)."""
    try:
      return bool( self._omnisharp_port )
    except:
      return False


  def ServerIsRunning( self ):
    """ Check if our OmniSharp server is running (up and serving)."""
    try:
      return bool( self._omnisharp_port and
                   self._GetResponse( '/checkalivestatus', timeout = 3 ) )
    except:
      return False


  def ServerIsReady( self ):
    """ Check if our OmniSharp server is ready (loaded solution file)."""
    try:
      return bool( self._omnisharp_port and
                   self._GetResponse( '/checkreadystatus', timeout = .2 ) )
    except:
      return False


  def ServerTerminated( self ):
    """ Check if the server process has already terminated. """
    return ( self._omnisharp_phandle is not None and
             self._omnisharp_phandle.poll() is not None )


class StdioCsharpSolutionCompleter( CsharpSolutionCompleter ):
  def __init__( self, omnisharp_path, solution_path, keep_logfiles ):
    super( StdioCsharpSolutionCompleter, self ).__init__( omnisharp_path, solution_path, keep_logfiles )
    self._stdio_in_queue = None
    self._stdio_out_queue = None
    self._stdio_seq = 0
    self._stdio_lock = None
    self._stdio_responses = {}
    self._stdio_aborted_seq = []
    if BENCHMARKING:
      self._stdio_last_write = 0


  def _StartServer( self ):
    self._logger.info( 'startup' )

    self._CleanupAfterServerStop()

    self._logger.info(
        u'Loading solution file {0}'.format( self._solution_path ) )

    command = [ self._omnisharp_path,
                '--stdio',
                '-s',
                u'{0}'.format( self._solution_path ) ]

    if utils.OnCygwin():
      command.extend( [ '--client-path-mode', 'Cygwin' ] )

    self._stdio_in_queue = Queue()
    self._stdio_out_queue = Queue()
    self._stdio_seq = 0
    self._stdio_lock = RLock()
    if BENCHMARKING:
      self._stdio_last_write = time.time()
    if not utils.OnWindows() and not utils.OnCygwin():
        phandle = utils.SafePopen( command, stdout = PIPE, stdin = PIPE )
        fd = phandle.stdin.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        def read( self, count ):
            return os.read( self.stdout.fileno(), count )
        def write( self, data ):
            return self.stdin.write( data )
        def terminate( self ):
            self.kill()
        def isalive( self ):
            return self.poll()
        for method in [ read, write, terminate, isalive ]:
            phandle.__dict__[ method.__name__ ] = types.MethodType( method, phandle )
        self._omnisharp_phandle = phandle
    else:
        phandle = PtyProcessUnicode.spawn( command, echo = False )
        self._omnisharp_phandle = phandle

    Thread( target = self._GenerateInLoop() ).start()
    Thread( target = self._GenerateOutLoop() ).start()

    self._logger.info( 'Starting OmniSharp server' )


  def _ProcessPacket( self, packet ):
    if 'Type' not in packet:
      self._logger.info( "Invalid packet: No Type\n" + str( packet ) )
    elif packet[ 'Type' ] == 'response':
      self._stdio_out_queue.put( packet );
    elif packet[ 'Type' ] == 'event': 
      if 'Event' not in packet:
        self._logger.info( "Invalid packet: No Event\n" + str( packet ) )
      elif packet[ 'Event' ] == 'log':
        try:
          log_message = packet[ "Body" ][ "Message" ]
        except (TypeError, KeyError) as e:
          self._logger.info( "Invalid log packet\n "+ str ( e ) + "\n\n" + str( packet ) )
        else:
          self._logger.info( "Omnisharp: " + log_message )
      elif packet[ 'Event' ] in [ 'MsBuildProjectDiagnostics', 'ProjectAdded', 'ProjectChanged', 'started' ]:
        pass
      else:
          self._logger.info( "Unknown event type: " + packet[ 'Event' ] + "\n\n" + str( packet ) )
    else:
        self._logger.info( "Unknown type: " + packet[ 'Type' ] + "\n\n" + str( packet ) )


  def _GenerateOutLoop( self ):
    def out_loop():
      try:
        data = ""
        while self._omnisharp_phandle is not None:
          if BENCHMARKING:
            last = time.time()
          data += self._omnisharp_phandle.read( 1024 * 1024 * 10 )
          if BENCHMARKING:
            self._logger.info( "Time Elapsed: {0} - {1} - {2}".format( time.time() - self._stdio_last_write, time.time() - last, len( data ) ))
          while "\n" in data:
            (line, data) = data.split("\n", 1)
            try:
              packet = json.loads( line )
            except ValueError:
              self._logger.error( "Omnisharp: " + line.rstrip() )
              continue

            self._ProcessPacket( packet )
      except Exception:
        self._logger.error( "Read error: " + traceback.format_exc() )
      finally:
        self._logger.error( 'Read abort!!!!!!!!!!!!!!!!!!!!!!!!!' )

    return out_loop


  def _GenerateInLoop( self ):
    def in_loop():
      try:
        while self._omnisharp_phandle is not None:
          try:
            data = self._stdio_in_queue.get( True, 1 )
          except Empty:
            continue
          self._omnisharp_phandle.write(data + "\n")
          if BENCHMARKING:
            self._stdio_last_write = time.time()
      except Exception:
        self._logger.error( "Write error: " + traceback.format_exc() )
      finally:
        self._logger.error( 'Write aborted!!!!!!!!!!!!!!!!!!!!!!!!!' )

    return in_loop


  def _CleanupAfterServerStop( self ):
    super( StdioCsharpSolutionCompleter, self )._CleanupAfterServerStop()
    self._stdio_out_queue = None
    self._stdio_in_queue = None
    self._stdio_seq = 0
    self._stdio_lock = None
    self._stdio_responses = {}
    self._stdio_aborted_seq = []


  def _ServerLocation( self ):
    return "STDIO"


  def _GetResponse( self, handler, parameters = {}, timeout = 10 ):
    """ Handle communication with server """
    if BENCHMARKING:
      start = time.time()

    self._stdio_lock.acquire( True )

    seq = self._stdio_seq + 1
    self._stdio_seq = seq

    try:
      parameters_json = json.dumps( parameters )
      request = { 'command': handler, 'seq': seq, 'arguments': parameters_json }
      request_json = json.dumps( request )

      self._stdio_in_queue.put( request_json )

      #self._logger.error( "Wrote for " + str( seq ) )

      self._ReadAllLines( seq, True, timeout )
            
      try:
        result = self._stdio_responses[ seq ]
        del self._stdio_responses[ seq ]
        return result
      except KeyError:
        return None
    except Exception:
      self._logger.error( "_GetResponse Error: " + traceback.format_exc() )
    finally:
      if BENCHMARKING:
        self._logger.info( "Elapsed time for {2} {0}: {1}".format( handler, time.time() - start, seq) )
      self._stdio_lock.release()


  def _ReadAllLines( self, seq = None, wait = False, timeout = None ):
    try:
      self._stdio_lock.acquire( True )
      self._pending_request = self._pending_request + 1
      while True:
        try:
          response = self._stdio_out_queue.get( wait, timeout )
        except Empty:
          response = None
        if response is None:
          self._stdio_aborted_seq.append( seq )
          return
        try:
          if 'Type' in response and response[ 'Type' ] == 'response':
            request_seq = response[ 'Request_seq' ]
            body =  response[ 'Body' ] if 'Body' in response else None
            self._stdio_responses[ request_seq ] = body

            #self._logger.error( "Read for " + str( request_seq ) )
              
            if seq is not None and request_seq == seq:
              return
            elif request_seq in self._stdio_aborted_seq:
              del self._stdio_responses[ request_seq ]
              self._stdio_aborted_seq.remove( request_seq )
        except Exception:
          self._logger.error( "_ReadAllLines Error: " + traceback.format_exc() )
    finally:
      self._pending_request = (
        self._pending_request - 1 if self._pending_request > 0
        else 0 )
      self._stdio_lock.release()


  def ServerIsActive( self ):
    """ Check if our OmniSharp server is active (started, not yet stopped)."""
    try:
      return bool( self._stdio_lock )
    except Exception:
      self._logger.info( "Active Error: " + traceback.format_exc() )
      return False


  def ServerIsRunning( self ):
    """ Check if our OmniSharp server is running (up and serving)."""
    try:
      return bool( self._stdio_lock and
                   self._GetResponse( '/checkalivestatus', timeout = 3 ) )
    except Exception:
      self._logger.info( "Running Error:" + traceback.format_exc() )
      return False


  def ServerIsReady( self ):
    """ Check if our OmniSharp server is ready (loaded solution file)."""
    try:
      return bool( self._stdio_lock and
                   self._GetResponse( '/checkreadystatus', timeout = .2 ) )
    except Exception:
      self._logger.info( "Ready error: " + traceback.format_exc() )
      return False


  def ServerTerminated( self ):
    """ Check if the server process has already terminated. """
    return ( self._omnisharp_phandle is not None and
             not self._omnisharp_phandle.isalive() )


  def _ForceStopServer( self ):
    # Kill it if it's still up
    if not self.ServerTerminated() and self._omnisharp_phandle is not None:
      self._logger.info( 'Killing OmniSharp server' )
      self._omnisharp_phandle.terminate()


def _CompleteSorterByImport( a, b ):
  return cmp( _CompleteIsFromImport( a ), _CompleteIsFromImport( b ) )


def _CompleteIsFromImport( candidate ):
  try:
    return candidate[ "extra_data" ][ "required_namespace_import" ] != None
  except ( KeyError, TypeError ):
    return False


def DiagnosticsToDiagStructure( diagnostics ):
  structure = defaultdict( lambda : defaultdict( list ) )
  for diagnostic in diagnostics:
    structure[ diagnostic.location_.filename_ ][
      diagnostic.location_.line_number_ ].append( diagnostic )
  return structure


def _BuildChunks( request_data, new_buffer ):
  filepath = request_data[ 'filepath' ]
  old_buffer = request_data[ 'file_data' ][ filepath ][ 'contents' ]
  new_buffer = _FixLineEndings( old_buffer, new_buffer )

  new_length = len( new_buffer )
  old_length = len( old_buffer )
  if new_length == old_length and new_buffer == old_buffer:
    return []
  min_length = min( new_length, old_length )
  start_index = 0
  end_index = min_length
  for i in range( 0, min_length - 1 ):
      if new_buffer[ i ] != old_buffer[ i ]:
          start_index = i
          break
  for i in range( 1, min_length ):
      if new_buffer[ new_length - i ] != old_buffer[ old_length - i ]:
          end_index = i - 1
          break
  # To handle duplicates, i.e aba => a
  if ( start_index + end_index > min_length ):
    start_index -= start_index + end_index - min_length

  replacement_text = new_buffer[ start_index : new_length - end_index ]

  ( start_line, start_column ) = _IndexToLineColumn( old_buffer, start_index )
  ( end_line, end_column ) = _IndexToLineColumn( old_buffer,
                                                 old_length - end_index )
  start = CsharpDiagnosticLocation( start_line, start_column, filepath )
  end = CsharpDiagnosticLocation( end_line, end_column, filepath )
  return [ CsharpFixItChunk( replacement_text,
                             CsharpDiagnosticRange( start, end ) ) ]


def _FixLineEndings( old_buffer, new_buffer ):
  new_windows = "\r\n" in new_buffer
  old_windows = "\r\n" in old_buffer
  if new_windows != old_windows:
    if new_windows:
      new_buffer = new_buffer.replace( "\r\n", "\n" )
      new_buffer = new_buffer.replace( "\r", "\n" )
    else:
      import re
      new_buffer = re.sub( "\r(?!\n)|(?<!\r)\n", "\r\n", new_buffer )
  return new_buffer


# Adapted from http://stackoverflow.com/a/24495900  
def _IndexToLineColumn( text, index ):
  """Get (line_number, col) of `index` in `string`."""
  lines = text.splitlines( True )
  curr_pos = 0
  for linenum, line in enumerate( lines ):
    if curr_pos + len( line ) > index:
      return linenum + 1, index - curr_pos + 1
    curr_pos += len( line )
  assert False
