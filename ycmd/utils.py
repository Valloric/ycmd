# Copyright (C) 2011, 2012 Google Inc.
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

import tempfile
import os
import sys
import signal
import socket
import stat
import subprocess

from future.utils import PY2

# Creation flag to disable creating a console window on Windows. See
# https://msdn.microsoft.com/en-us/library/windows/desktop/ms684863.aspx
CREATE_NO_WINDOW = 0x08000000
# Executable extensions used on Windows
WIN_EXECUTABLE_EXTS = [ '.exe', '.bat', '.cmd' ]


def SanitizeQuery( query ):
  return query.strip()


# Python 3 complains on the common open(path).read() idiom because the file
# doesn't get closed. So, a helper func.
def ReadFile( filepath ):
  with open( filepath ) as f:
    return f.read()


# Given an object, returns a str object that's utf-8 encoded.
def ToUtf8IfNeeded( value ):
  # NOTE: the C++ interop layer specifically wants py2 'str' objects and
  # probably 'bytes' on py3. You likely want to wrap what this returns with
  # future.utils's native() if talking to C++.

  if isinstance( value, str ):
    return value.encode( 'utf8' )
  if isinstance( value, bytes ):
    return value
  return bytes( str( value ) )


def ToUnicodeIfNeeded( value ):
  if isinstance( value, str ):
    return value
  if isinstance( value, bytes ):
    # All incoming text should be utf8
    return str( value, 'utf8' )
  return str( value )


def ToBytes( value ):
  # This is tricky. On py2, the bytes type from builtins (from python-future) is
  # a subclass of str. So all of the following are true:
  #   isinstance(str(), bytes)
  #   isinstance(bytes(), str)
  # But they don't behave the same in one important aspect: iterating over a
  # bytes instance yields ints, while iterating over a (raw, py2) str yields
  # chars.
  if type( value ) == bytes:
    return value
  if isinstance( value, int ):
    value = str( value )
  return bytes( str( value ), encoding = 'utf-8' )


def PathToTempDir():
  tempdir = os.path.join( tempfile.gettempdir(), 'ycm_temp' )
  try:
    os.makedirs( tempdir )
    # Needed to support multiple users working on the same machine;
    # see issue 606.
    MakeFolderAccessibleToAll( tempdir )
  except OSError:
    # Folder already exists, skip folder creation.
    pass
  return tempdir


def MakeFolderAccessibleToAll( path_to_folder ):
  current_stat = os.stat( path_to_folder )
  # readable, writable and executable by everyone
  flags = ( current_stat.st_mode | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
            | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP )
  os.chmod( path_to_folder, flags )


def RunningInsideVim():
  try:
    import vim  # NOQA
    return True
  except ImportError:
    return False


def GetUnusedLocalhostPort():
  sock = socket.socket()
  # This tells the OS to give us any free port in the range [1024 - 65535]
  sock.bind( ( '', 0 ) )
  port = sock.getsockname()[ 1 ]
  sock.close()
  return port


def RemoveIfExists( filename ):
  try:
    os.remove( filename )
  except OSError:
    pass


def PathToFirstExistingExecutable( executable_name_list ):
  for executable_name in executable_name_list:
    path = FindExecutable( executable_name )
    if path:
      return path
  return None


# On Windows, distutils.spawn.find_executable only works for .exe files
# but .bat and .cmd files are also executables, so we use our own
# implementation.
def FindExecutable( executable ):
  paths = os.environ[ 'PATH' ].split( os.pathsep )
  base, extension = os.path.splitext( executable )

  if OnWindows() and extension.lower() not in WIN_EXECUTABLE_EXTS:
    extensions = WIN_EXECUTABLE_EXTS
  else:
    extensions = ['']

  for extension in extensions:
    executable_name = executable + extension
    if not os.path.isfile( executable_name ):
      for path in paths:
        executable_path = os.path.join(path, executable_name )
        if os.path.isfile( executable_path ):
          return executable_path
    else:
      return executable_name
  return None


def OnWindows():
  return sys.platform == 'win32'


def OnCygwin():
  return sys.platform == 'cygwin'


def OnMac():
  return sys.platform == 'darwin'


def OnTravis():
  return 'TRAVIS' in os.environ


def ProcessIsRunning( handle ):
  return handle is not None and handle.poll() is None


# From here: http://stackoverflow.com/a/8536476/1672783
def TerminateProcess( pid ):
  if OnWindows():
    import ctypes
    PROCESS_TERMINATE = 1
    handle = ctypes.windll.kernel32.OpenProcess( PROCESS_TERMINATE,
                                                 False,
                                                 pid )
    ctypes.windll.kernel32.TerminateProcess( handle, -1 )
    ctypes.windll.kernel32.CloseHandle( handle )
  else:
    os.kill( pid, signal.SIGTERM )


def AncestorFolders( path ):
  folder = os.path.abspath( path )
  while True:
    parent = os.path.dirname( folder )
    if parent == folder:
      break
    folder = parent
    yield folder


def PathToNearestThirdPartyFolder( path ):
  for folder in AncestorFolders( path ):
    path_to_third_party = os.path.join( folder, 'third_party' )
    if os.path.isdir( path_to_third_party ):
      return path_to_third_party
  return None


def AddNearestThirdPartyFoldersToSysPath( filepath ):
  path_to_third_party = PathToNearestThirdPartyFolder( filepath )
  if not path_to_third_party:
    raise RuntimeError(
        'No third_party folder found for: {0}'.format( filepath ) )

  # NOTE: Any hacks for loading modules that can't be imported without custom
  # logic need to be reproduced in run_tests.py as well.
  for folder in os.listdir( path_to_third_party ):
    # python-future needs special handling. Not only does it store the modules
    # under its 'src' folder, but SOME of its modules are only meant to be
    # accessible under py2, not py3. This is because these modules (like
    # `queue`) are implementations of modules present in the py3 standard
    # library. So to work around issues, we place the python-future last on
    # sys.path so that they can be overriden by the standard library.
    if folder == 'python-future':
      folder = os.path.join( folder, 'src' )
      sys.path.append( os.path.realpath( os.path.join( path_to_third_party,
                                                       folder ) ) )
      continue
    sys.path.insert( 0, os.path.realpath( os.path.join( path_to_third_party,
                                                        folder ) ) )


def ForceSemanticCompletion( request_data ):
  return ( 'force_semantic' in request_data and
           bool( request_data[ 'force_semantic' ] ) )


# A wrapper for subprocess.Popen that fixes quirks on Windows.
def SafePopen( args, **kwargs ):
  if OnWindows():
    # We need this to start the server otherwise bad things happen.
    # See issue #637.
    if kwargs.get( 'stdin_windows' ) is subprocess.PIPE:
      kwargs[ 'stdin' ] = subprocess.PIPE
    # Do not create a console window
    kwargs[ 'creationflags' ] = CREATE_NO_WINDOW
    # Python 2 fails to spawn a process from a command containing unicode
    # characters on Windows.  See https://bugs.python.org/issue19264 and
    # http://bugs.python.org/issue1759845.
    # Since paths are likely to contains such characters, we convert them to
    # short ones to obtain paths with only ascii characters.
    args = ConvertArgsToShortPath( args )

  kwargs.pop( 'stdin_windows', None )
  return subprocess.Popen( args, **kwargs )


# Convert paths in arguments command to short path ones
def ConvertArgsToShortPath( args ):
  def ConvertIfPath( arg ):
    if os.path.exists( arg ):
      return GetShortPathName( arg )
    return arg

  if isinstance( args, str ) or isinstance( args, bytes ):
    return ConvertIfPath( args )
  return [ ConvertIfPath( arg ) for arg in args ]


# Get the Windows short path name.
# Based on http://stackoverflow.com/a/23598461/200291
def GetShortPathName( path ):
  from ctypes import windll, wintypes, create_unicode_buffer

  # Set the GetShortPathNameW prototype
  _GetShortPathNameW = windll.kernel32.GetShortPathNameW
  _GetShortPathNameW.argtypes = [ wintypes.LPCWSTR,
                                  wintypes.LPWSTR,
                                  wintypes.DWORD]
  _GetShortPathNameW.restype = wintypes.DWORD

  output_buf_size = 0

  while True:
    output_buf = create_unicode_buffer( output_buf_size )
    needed = _GetShortPathNameW( path, output_buf, output_buf_size )
    if output_buf_size >= needed:
      return output_buf.value
    else:
      output_buf_size = needed

# Shim for imp.load_source so that it works on both Py2 & Py3. See upstream
# Python docs for info on what this does.
def LoadPythonSource( name, pathname ):
  if PY2:
    import imp
    return imp.load_source( name, pathname )
  else:
    import importlib
    return importlib.machinery.SourceFileLoader( name, pathname ).load_module()
