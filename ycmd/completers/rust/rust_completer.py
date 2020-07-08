# Copyright (C) 2015-2020 ycmd contributors
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

import logging
import os
from subprocess import PIPE

from ycmd import responses, utils
from ycmd.completers.language_server import language_server_completer
from ycmd.utils import LOGGER, re


LOGFILE_FORMAT = 'ra_'
RA_BIN_DIR = os.path.abspath(
  os.path.join( os.path.dirname( __file__ ), '..', '..', '..', 'third_party',
                'rust-analyzer', 'bin' ) )
RUSTC_EXECUTABLE = utils.FindExecutable( os.path.join( RA_BIN_DIR, 'rustc' ) )
RA_EXECUTABLE = utils.FindExecutable( os.path.join(
    RA_BIN_DIR, 'rust-analyzer' ) )
RA_VERSION_REGEX = re.compile( r'^rust-analyzer (?P<version>.*)$' )


def _GetCommandOutput( command ):
  return utils.ToUnicode(
    utils.SafePopen( command,
                     stdin_windows = PIPE,
                     stdout = PIPE,
                     stderr = PIPE ).communicate()[ 0 ].rstrip() )


def _GetRAVersion( ra_path ):
  ra_version = _GetCommandOutput( [ ra_path, '--version' ] )
  match = RA_VERSION_REGEX.match( ra_version )
  if not match:
    LOGGER.error( 'Cannot parse Rust Language Server version: %s', ra_version )
    return None
  return match.group( 'version' )


def ShouldEnableRustCompleter( user_options ):
  if ( user_options[ 'rls_binary_path' ] and
       not user_options[ 'rustc_binary_path' ] ):
    LOGGER.error( 'Not using Rust completer: RUSTC not specified' )
    return False

  ra = utils.FindExecutableWithFallback( user_options[ 'rls_binary_path' ],
                                         RA_EXECUTABLE )
  if not ra:
    LOGGER.error( 'Not using Rust completer: no RA executable found at %s',
                  ra )
    return False
  LOGGER.info( 'Using Rust completer' )
  return True


class RustCompleter( language_server_completer.LanguageServerCompleter ):
  def __init__( self, user_options ):
    super().__init__( user_options )
    self._ra_path = utils.FindExecutableWithFallback(
        user_options[ 'rls_binary_path' ],
        RA_EXECUTABLE )
    self._rustc_path = utils.FindExecutableWithFallback(
        user_options[ 'rustc_binary_path' ],
        RUSTC_EXECUTABLE )


  def _Reset( self ):
    super()._Reset()
    self._server_progress = {}


  def GetServerName( self ):
    return 'Rust Language Server'


  def GetCommandLine( self ):
    return [ self._ra_path ]


  def GetServerEnvironment( self ):
    env = os.environ.copy()
    env[ 'RUSTC' ] = self._rustc_path
    if LOGGER.isEnabledFor( logging.DEBUG ):
      env[ 'RA_LOG' ] = 'rust_analyzer=trace'
    return env


  def GetProjectRootFiles( self ):
    # Without LSP workspaces support, RA relies on the rootUri to detect a
    # project.
    # TODO: add support for LSP workspaces to allow users to change project
    # without having to restart RA.
    return [ 'Cargo.toml' ]



  def SupportedFiletypes( self ):
    return [ 'rust' ]


  def GetTriggerCharacters( self, server_trigger_characters ):
    # The trigger characters supplied by RA ('.' and ':') are worse than ycmd's
    # own semantic triggers ('.' and '::') so we ignore them.
    return []


  def ExtraDebugItems( self, request_data ):
    project_state = ', '.join(
      set( self._server_progress.values() ) ).capitalize()
    return [
      responses.DebugInfoItem( 'Project State', project_state ),
      responses.DebugInfoItem( 'Version', _GetRAVersion( self._ra_path ) ),
      responses.DebugInfoItem( 'RUSTC', self._rustc_path )
    ]


  def HandleNotificationInPollThread( self, notification ):
    # TODO: the building status is currently displayed in the debug info. We
    # should notify the client about it through a special status/progress
    # message.
    if notification[ 'method' ] == 'window/progress':
      params = notification[ 'params' ]
      progress_id = params[ 'id' ]
      message = params[ 'title' ].lower()
      if not params[ 'done' ]:
        if params[ 'message' ]:
          message += ' ' + params[ 'message' ]
        if params[ 'percentage' ]:
          message += ' ' + params[ 'percentage' ]
      else:
        message += ' done'

      with self._server_info_mutex:
        self._server_progress[ progress_id ] = message

    super().HandleNotificationInPollThread( notification )


  def GetType( self, request_data ):
    try:
      hover_response = self.GetHoverResponse( request_data )[ 'value' ]
    except language_server_completer.NoHoverInfoException:
      raise RuntimeError( 'Unknown type.' )

    hover_response = hover_response.split( '\n___\n', 2 )[ 0 ]
    start = hover_response.rfind( '```rust\n' ) + len( '```rust\n' )
    end = hover_response.rfind( '\n```' )
    return responses.BuildDisplayMessageResponse( hover_response[ start:end ] )


  def GetDoc( self, request_data ):
    try:
      hover_response = self.GetHoverResponse( request_data )
    except language_server_completer.NoHoverInfoException:
      raise RuntimeError( 'No documentation available.' )

    lines = hover_response[ 'value' ].split( '\n' )
    documentation = '\n'.join(
      line for line in lines if line and not line.startswith( '```' ) ).strip()

    if not documentation:
      raise RuntimeError( 'No documentation available for current context.' )

    return responses.BuildDetailedInfoResponse( documentation )
