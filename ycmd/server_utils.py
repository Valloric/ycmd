# Copyright (C) 2013 Google Inc.
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
# No other imports from `future` because this module is loaded before we have
# put our submodules in sys.path

import io
import logging
import os
import re
import sys

CORE_MISSING_ERROR_REGEX = re.compile( "No module named '?ycm_core'?" )
CORE_PYTHON2_ERROR_REGEX = re.compile(
  'dynamic module does not define (?:init|module export) '
  'function \(PyInit_ycm_core\)|'
  'Module use of python2[0-9].dll conflicts with this version of Python\.$' )
CORE_PYTHON3_ERROR_REGEX = re.compile(
  'dynamic module does not define init function \(initycm_core\)|'
  'Module use of python3[0-9].dll conflicts with this version of Python\.$' )

CORE_MISSING_MESSAGE = 'ycm_core library not detected; you need to compile it.'
CORE_PYTHON2_MESSAGE = ( 'ycm_core library compiled with Python 2 '
                         'but loaded with Python 3.' )
CORE_PYTHON3_MESSAGE = ( 'ycm_core library compiled with Python 3 '
                         'but loaded with Python 2.' )
CORE_OUTDATED_MESSAGE = 'ycm_core library too old, PLEASE RECOMPILE.'

VERSION_FILENAME = 'CORE_VERSION'

DIR_OF_CURRENT_SCRIPT = os.path.dirname( os.path.abspath( __file__ ) )
DIR_PACKAGES_REGEX = re.compile( '(site|dist)-packages$' )

_logger = logging.getLogger( __name__ )


def ExpectedCoreVersion():
  filepath = os.path.join( DIR_OF_CURRENT_SCRIPT, '..', VERSION_FILENAME )
  with io.open( filepath, encoding = 'utf8' ) as f:
    return int( f.read() )


def ImportCore():
  """Imports and returns the ycm_core module. This function exists for easily
  mocking this import in tests."""
  import ycm_core as ycm_core
  return ycm_core


def CompatibleWithCurrentCore():
  """Checks if ycm_core library is compatible and returns with one of the
  following status codes:
     0: ycm_core is compatible;
     1: unexpected error;
     3: ycm_core is missing;
     4: ycm_core is compiled with Python 2 but loaded with Python 3;
     5: ycm_core is compiled with Python 3 but loaded with Python 2;
     6: ycm_core version is outdated.

  2 is not used as a status code because it has often a special meaning for Unix
  programs. See https://docs.python.org/2/library/sys.html#sys.exit"""
  try:
    ycm_core = ImportCore()
  except ImportError as error:
    message = str( error )
    if CORE_MISSING_ERROR_REGEX.match( message ):
      _logger.exception( CORE_MISSING_MESSAGE )
      return 3
    if CORE_PYTHON2_ERROR_REGEX.match( message ):
      _logger.exception( CORE_PYTHON2_MESSAGE )
      return 4
    if CORE_PYTHON3_ERROR_REGEX.match( message ):
      _logger.exception( CORE_PYTHON3_MESSAGE )
      return 5
    _logger.exception( message )
    return 1

  try:
    current_core_version = ycm_core.YcmCoreVersion()
  except AttributeError:
    _logger.exception( CORE_OUTDATED_MESSAGE )
    return 6

  if ExpectedCoreVersion() != current_core_version:
    _logger.error( CORE_OUTDATED_MESSAGE )
    return 6

  return 0


def SetUpPythonPath():
  sys.path.insert( 0, os.path.join( DIR_OF_CURRENT_SCRIPT, '..' ) )

  AddNearestThirdPartyFoldersToSysPath( __file__ )


def AncestorFolders( path ):
  folder = os.path.normpath( path )
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
    # library. Furthermore, we need to be sure that they are not overriden by
    # already installed packages (for example, the 'builtins' module from
    # 'pies2overrides' or a different version of 'python-future'). To work
    # around these issues, we place the python-future just before the first
    # path ending with 'site-packages' (or 'dist-packages' for Debian-like
    # distributions) so that its modules can be overridden by the standard
    # library but not by installed packages.
    if folder == 'python-future':
      folder = os.path.join( folder, 'src' )
      packages_indices = ( sys.path.index( path ) for path in sys.path
                           if DIR_PACKAGES_REGEX.search( path ) )
      sys.path.insert( next( packages_indices, len( sys.path ) ),
                       os.path.realpath( os.path.join( path_to_third_party,
                                                       folder ) ) )
      continue
    sys.path.insert( 0, os.path.realpath( os.path.join( path_to_third_party,
                                                        folder ) ) )
