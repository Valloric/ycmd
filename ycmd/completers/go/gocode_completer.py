#!/usr/bin/env python
#
# Copyright (C) 2015 Google Inc.
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

import json
import logging
import os
import subprocess

from ycmd import responses
from ycmd import utils
from ycmd.completers.completer import Completer

GO_FILETYPES = set( [ 'go' ] )
BINARY_NOT_FOUND_MESSAGE = ( ' binary not found. Did you build it? ' +
                             'You can do so by running ' +
                             '"./install.py --gocode-completer".' )
COMPLETION_ERROR_MESSAGE = 'Gocode shell call failed.'
PARSE_ERROR_MESSAGE = 'Gocode returned invalid JSON response.'
NO_COMPLETIONS_MESSAGE = 'Gocode returned empty JSON response.'
GOCODE_PANIC_MESSAGE = ( 'Gocode panicked trying to find completions, ' +
                         'you likely have a syntax error.' )
PATH_TO_GOCODE_BINARY = os.path.join(
  os.path.abspath( os.path.dirname( __file__ ) ),
  '..', '..', '..', 'third_party', 'gocode',
  'gocode' + ( '.exe' if utils.OnWindows() else '' ) )
PATH_TO_GODEF_BINARY = os.path.join(
  os.path.abspath( os.path.dirname( __file__ ) ),
  '..', '..', '..', 'third_party', 'godef',
  'godef' + ( '.exe' if utils.OnWindows() else '' ) )

_logger = logging.getLogger( __name__ )


class GoCodeCompleter( Completer ):

  def __init__( self, user_options ):
    super( GoCodeCompleter, self ).__init__( user_options )
    self._popener = utils.SafePopen # Overridden in test.
    self._binary_code = self.FindGoCodeBinary( user_options )
    self._binary_def = self.FindGoDefBinary( user_options )

    if not self._binary_code:
      _logger.error( "Gocode" + BINARY_NOT_FOUND_MESSAGE )
      raise RuntimeError( "Gocode" + BINARY_NOT_FOUND_MESSAGE )

    _logger.info( 'Enabling go completion using %s binary', self._binary_code )

    if not self._binary_def:
      _logger.error( "Godef" + BINARY_NOT_FOUND_MESSAGE )
      raise RuntimeError( "Godef" + BINARY_NOT_FOUND_MESSAGE )

    _logger.info( 'Enabling go definitions using %s binary', self._binary_def )


  def SupportedFiletypes( self ):
    return GO_FILETYPES


  def ComputeCandidatesInner( self, request_data ):
    filename = request_data[ 'filepath' ]
    _logger.info( "gocode completion request %s" % filename )
    if not filename:
      return

    contents = utils.ToUtf8IfNeeded(
        request_data[ 'file_data' ][ filename ][ 'contents' ] )
    offset = _ComputeOffset( contents, request_data[ 'line_num' ],
                             request_data[ 'column_num' ] )

    stdoutdata = self._ExecuteGoCodeBinary( '-f=json', 'autocomplete',
                                            filename, str(offset),
                                            contents = contents )

    try:
      resultdata = json.loads( stdoutdata )
    except ValueError:
      _logger.error( PARSE_ERROR_MESSAGE )
      raise RuntimeError( PARSE_ERROR_MESSAGE )
    if len(resultdata) != 2:
      _logger.error( NO_COMPLETIONS_MESSAGE )
      raise RuntimeError( NO_COMPLETIONS_MESSAGE )
    for result in resultdata[1]:
      if result.get( 'class' ) == "PANIC":
        raise RuntimeError( GOCODE_PANIC_MESSAGE )

    return [ _ConvertCompletionData( x ) for x in resultdata[1] ]


  def GetSubcommandsMap( self ):
    return {
      'StartServer': ( lambda self, request_data, args: self._StartServer() ),
      'StopServer': ( lambda self, request_data, args: self._StopServer() ),
      'GoTo' : ( lambda self, request_data, args:
                 self._GoToDefinition( request_data ) ),
      'GoToDefinition' : ( lambda self, request_data, args:
                           self._GoToDefinition( request_data ) ),
      'GoToDeclaration' : ( lambda self, request_data, args:
                           self._GoToDefinition( request_data ) ),
    }


  def FindGoCodeBinary( self, user_options ):
    """ Find the path to the gocode binary.

    If 'gocode_binary_path' in the options is blank,
    use the version installed with YCM, if it exists,
    then the one on the path, if not.

    If the 'gocode_binary_path' is specified, use it
    as an absolute path.

    If the resolved binary exists, return the path,
    otherwise return None. """
    if user_options.get( 'gocode_binary_path' ):
      # The user has explicitly specified a path.
      if os.path.isfile( user_options[ 'gocode_binary_path' ] ):
        return user_options[ 'gocode_binary_path' ]
      else:
        return None
    # Try to use the bundled binary or one on the path.
    if os.path.isfile( PATH_TO_GOCODE_BINARY ):
      return PATH_TO_GOCODE_BINARY
    return utils.PathToFirstExistingExecutable( [ 'gocode' ] )


  def FindGoDefBinary( self, user_options ):
    """ Find the path to the godef binary.

    If 'godef_binary_path' in the options is blank,
    use the version installed with YCM, if it exists,
    then the one on the path, if not.

    If the 'godef_binary_path' is specified, use it
    as an absolute path.

    If the resolved binary exists, return the path,
    otherwise return None. """
    if user_options.get( 'godef_binary_path' ):
      # The user has explicitly specified a path.
      if os.path.isfile( user_options[ 'godef_binary_path' ] ):
        return user_options[ 'godef_binary_path' ]
      else:
        return None
    # Try to use the bundled binary or one on the path.
    if os.path.isfile( PATH_TO_GODEF_BINARY ):
      return PATH_TO_GODEF_BINARY
    return utils.PathToFirstExistingExecutable( [ 'godef' ] )


  def OnFileReadyToParse( self, request_data ):
    self._StartServer()


  def Shutdown( self ):
    self._StopServer()


  def _StartServer( self ):
    """ Start the GoCode server """
    self._ExecuteGoCodeBinary()


  def _StopServer( self ):
    """ Stop the GoCode server """
    _logger.info( 'Stopping GoCode server' )
    self._ExecuteGoCodeBinary( 'close' )


  def _ExecuteGoCodeBinary( self, *args, **kwargs ):
    """ Execute the GoCode binary with given arguments. Use the contents
    argument to send data to GoCode. Return the standard output. """
    proc = self._popener(
      [ self._binary_code ] + list(args), stdin = subprocess.PIPE,
      stdout = subprocess.PIPE, stderr = subprocess.PIPE )
    contents = kwargs[ 'contents' ] if 'contents' in kwargs else None
    stdoutdata, stderrdata = proc.communicate( contents )
    if proc.returncode:
      _logger.error( COMPLETION_ERROR_MESSAGE + " code %i stderr: %s",
                     proc.returncode, stderrdata)
      raise RuntimeError( COMPLETION_ERROR_MESSAGE )

    return stdoutdata


  def _ExecuteGoDefBinary( self, *args ):
    """ Execute the GoDef binary with given arguments. Use the contents
    argument to send data to GoDef. Return the standard output. """
    proc = self._popener(
      [ self._binary_def ] + list(args), stdin = subprocess.PIPE,
      stdout = subprocess.PIPE, stderr = subprocess.PIPE )
    stdoutdata, stderrdata = proc.communicate()
    if proc.returncode:
      _logger.error( COMPLETION_ERROR_MESSAGE + " code %i stderr: %s",
                     proc.returncode, stderrdata)
      raise RuntimeError( COMPLETION_ERROR_MESSAGE )

    return stdoutdata


  def _GoToDefinition( self, request_data ):
    try:
      filename = request_data[ 'filepath' ]
      _logger.info( "godef GoTo request %s" % filename )
      if not filename:
        return
      contents = utils.ToUtf8IfNeeded(
          request_data[ 'file_data' ][ filename ][ 'contents' ] )
      offset = _ComputeOffset( contents, request_data[ 'line_num' ],
                               request_data[ 'column_num' ] )
      stdout = self._ExecuteGoDefBinary( "-f=%s" % filename, '-json',
                                         "-o=%s" % offset )
      return self._ConstructGoToFromResponse( stdout )
    except Exception:
      raise RuntimeError( 'Can\'t jump to definition.' )


  def _ConstructGoToFromResponse( self, response_str):
    parsed = json.loads( response_str )
    if 'filename' in parsed:
      if 'column' in parsed:
        return responses.BuildGoToResponse( parsed[ 'filename' ],
                                            parsed[ 'line' ],
                                            parsed[ 'column' ] )
      else:
        return responses.BuildGoToResponse( parsed[ 'filename' ],
                                            1, 0 )
    else:
      raise RuntimeError( 'Can\'t jump to definition.' )




# Compute the byte offset in the file given the line and column.
# TODO(ekfriis): If this is slow, consider moving this to C++ ycm_core,
# perhaps in RequestWrap.
def _ComputeOffset( contents, line, col ):
  curline = 1
  curcol = 1
  for i, byte in enumerate( contents ):
    if curline == line and curcol == col:
      return i
    curcol += 1
    if byte == '\n':
      curline += 1
      curcol = 1
  _logger.error( 'GoCode completer - could not compute byte offset ' +
                 'corresponding to L%i C%i', line, col )
  return -1


def _ConvertCompletionData( completion_data ):
  return responses.BuildCompletionData(
    insertion_text = completion_data[ 'name' ],
    menu_text = completion_data[ 'name' ],
    extra_menu_info = completion_data[ 'type' ],
    kind = completion_data[ 'class' ],
    detailed_info = ' '.join( [
        completion_data[ 'name' ],
        completion_data[ 'type' ],
        completion_data[ 'class' ] ] ) )
