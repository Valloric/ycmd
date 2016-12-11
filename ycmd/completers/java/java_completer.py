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
from builtins import *  # noqa
from future import standard_library
standard_library.install_aliases()

import logging
import os
import threading
import glob

from subprocess import PIPE

from ycmd import ( utils, responses )

from ycmd.completers.language_server import language_server_completer

_logger = logging.getLogger( __name__ )

LANGUAGE_SERVER_HOME = os.path.join( os.path.dirname( __file__ ),
                                     '..',
                                     '..',
                                     '..',
                                     'third_party',
                                     'eclipse.jdt.ls',
                                     'org.eclipse.jdt.ls.product',
                                     'target',
                                     'repository')

# TODO: Java 8 required (validate this)
PATH_TO_JAVA = utils.PathToFirstExistingExecutable( [ 'java' ] )

WORKSPACE_PATH = os.path.join( os.path.dirname( __file__ ),
                               '..',
                               '..',
                               '..',
                               'third_party',
                               'eclipse.jdt.ls-workspace' )


def ShouldEnableJavaCompleter():
  _logger.info( 'Looking for java lonaguage server' )
  if not PATH_TO_JAVA:
    _logger.warning( "Not enabling java completion: Couldn't find java" )
    return False

  if not os.path.exists( LANGUAGE_SERVER_HOME ):
    _logger.warning( 'Not using java completion: not installed' )
    return False

  # TODO: Check java version

  return True


def _PathToLauncherJar():
  # The file name changes between version of eclipse, so we use a glob as
  # recommended by the language server developers
  p = glob.glob(
    os.path.abspath(
      os.path.join(
        LANGUAGE_SERVER_HOME,
        'plugins',
        'org.eclipse.equinox.launcher_*.jar' ) ) )

  _logger.debug( 'Found launchers: {0}'.format( p ) )

  return p[ 0 ]


def _LauncherConfiguration():
  if utils.OnMac():
    config = 'config_mac'
  elif utils.OnWindows():
    config = 'config_win'
  else:
    config = 'config_linux'

  return os.path.abspath( os.path.join( LANGUAGE_SERVER_HOME, config ) )


class JavaCompleter( language_server_completer.LanguageServerCompleter ):
  def __init__( self, user_options ):
    super( JavaCompleter, self ).__init__( user_options )

    self._server_keep_logfiles = user_options[ 'server_keep_logfiles' ]

    # Used to ensure that starting/stopping of the server is synchronised
    self._server_state_mutex = threading.RLock()

    with self._server_state_mutex:
      self._server = None
      self._server_handle = None
      self._server_stderr = None
      self._server_stdout = None

      self._Reset()
      self._StartServer()


  def GetServer( self ):
    return self._server


  def SupportedFiletypes( self ):
    return [ 'java' ]


  def DebugInfo( self, request_data ):
    return responses.BuildDebugInfoResponse(
      name = "Java",
      servers = [
        responses.DebugInfoServer(
          name = "Java Language Server",
          handle = self._server_handle,
          executable = LANGUAGE_SERVER_HOME,
          logfiles = [ self._server_stdout, self._server_stderr ],
          port = [ self._server_stdout_port, self._server_stdin_port ] )
      ] )


  def Shutdown( self ):
    self._StopServer()


  def ServerIsHealthy( self, request_data = {} ):
    if not self._ServerIsRunning():
      return False

    return True


  def _Reset( self ):
    if self._server_handle:
      utils.CloseStandardStreams( self._server_handle )

    if not self._server_keep_logfiles:
      if self._server_stdout:
        utils.RemoveIfExists( self._server_stdout )
        self._server_stdout = None
      if self._server_stderr:
        utils.RemoveIfExists( self._server_stderr )
        self._server_stderr = None

    self._server_stdin_port = 0
    self._server_stdout_port = 0
    self._server_handle = None

    # TODO: close the sockets in the server
    self._server = None


  def _StartServer( self ):
    with self._server_state_mutex:
      _logger.info( 'Starting JDT Language Server...' )
      self._server_stdin_port = utils.GetUnusedLocalhostPort()
      self._server_stdout_port = utils.GetUnusedLocalhostPort()

      self._server = language_server_completer.TCPMultiStreamServer(
        self._server_stdin_port,
        self._server_stdout_port )

      self._server.start()

      env = os.environ.copy()
      env[ 'STDIN_PORT' ] = str( self._server_stdin_port )
      env[ 'STDOUT_PORT' ] = str( self._server_stdout_port )

      command = [
        PATH_TO_JAVA,
        '-Declipse.application=org.eclipse.jdt.ls.core.id1',
        '-Dosgi.bundles.defaultStartLevel=4',
        '-Declipse.product=org.eclipse.jdt.ls.core.product',
        '-Dlog.protocol=true',
        '-Dlog.level=ALL',
        '-noverify',
        '-Xmx1G',
        '-jar',
        _PathToLauncherJar(),
        '-configuration',
        _LauncherConfiguration(),
        '-data',
        os.path.abspath( WORKSPACE_PATH ),
      ]

      _logger.debug( 'Starting java-server with the following command: '
                     '{0}'.format( ' '.join( command ) ) )

      LOGFILE_FORMAT = 'java_language_server_{port}_{std}_'

      self._server_stdout = utils.CreateLogfile(
          LOGFILE_FORMAT.format( port = self._server_stdout_port,
                                 std = 'stdout' ) )

      self._server_stderr = utils.CreateLogfile(
          LOGFILE_FORMAT.format( port = self._server_stdin_port,
                                 std = 'stderr' ) )

      with utils.OpenForStdHandle( self._server_stdout ) as stdout:
        with utils.OpenForStdHandle( self._server_stderr ) as stderr:
          self._server_handle = utils.SafePopen( command,
                                                 stdin = PIPE,
                                                 stdout = stdout,
                                                 stderr = stderr,
                                                 env = env )

      if self._ServerIsRunning():
        _logger.info( 'JDT Language Server started, '
                      'with stdin {0}, stdout {1}'.format(
                        self._server_stdin_port,
                        self._server_stdout_port ) )
      else:
        _logger.warning( 'JDT Language Server failed to start' )
        return

      # Awaiting connection
      # spinlock
      # TODO: timeout
      self._server.TryServerConnection()

    # OK, so now we have to fire the Initialise request to the server:
    #
    # LS PROTOCOL - Initialise request
    #
    # The initialize request is sent as the first request from the client to
    # the server. If the server receives request or notification before the
    # initialize request it should act as follows:
    # - for a request the respond should be errored with code: -32001. The
    #   message can be picked by the server.
    # - notifications should be dropped.
    #
    # TODO/FIXME: This causes a hang on startup waiting for the
    # server. I suspect this is holding the server state mutex, and any
    # requests that come in (such as OnFileReadyToParse) just get blocked
    # waiting for this to happen. The fix is to have a proper state model, or
    # at least a simple one, rather than leaning on a lock (assuming that is
    # the actual problem)
    #
    self._WaitForInitiliase()


  def _StopServer( self ):
    with self._server_state_mutex:
      if self._ServerIsRunning():
        _logger.info( 'Stopping java server with PID {0}'.format(
                          self._server_handle.pid ) )
        self._server_handle.terminate()
        try:
          utils.WaitUntilProcessIsTerminated( self._server_handle,
                                              timeout = 5 )
          _logger.info( 'JDT Language server stopped' )
        except RuntimeError:
          _logger.exception( 'Error while stopping java server' )

      self._Reset()


  def GetSubcommandsMap( self ):
    return {
      'RestartServer': ( lambda self, request_data, args:
                            self._RestartServer() ),
    }


  def _RestartServer( self ):
    with self._server_state_mutex:
      self._StopServer()
      self._StartServer()


  def _ServerIsRunning( self ):
    return utils.ProcessIsRunning( self._server_handle )
