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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

from hamcrest import ( assert_that, calling, contains, contains_inanyorder,
                       equal_to, empty, raises )
from mock import patch
from nose.tools import ok_
import os.path
import sys

from ycmd.server_utils import ( AddNearestThirdPartyFoldersToSysPath,
                                CompatibleWithCurrentCore,
                                PathToNearestThirdPartyFolder )

DIR_OF_THIRD_PARTY = os.path.abspath(
  os.path.join( os.path.dirname( __file__ ), '..', '..', 'third_party' ) )
THIRD_PARTY_FOLDERS = (
  os.path.join( DIR_OF_THIRD_PARTY, 'argparse' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'bottle' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'frozendict' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'godef' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'gocode' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'JediHTTP' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'OmniSharpServer' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'racerd' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'requests' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'tern_runtime' ),
  os.path.join( DIR_OF_THIRD_PARTY, 'waitress' )
)


@patch( 'ycmd.server_utils._logger' )
def RunCompatibleWithCurrentCore( test, logger ):
  if 'import_error' in test:
    with patch( 'ycmd.server_utils.ImportCore',
                side_effect = ImportError( test[ 'import_error' ] ) ):
      code = CompatibleWithCurrentCore()
  else:
    code = CompatibleWithCurrentCore()

  assert_that( code, equal_to( test[ 'return_code' ] ) )

  if 'message' in test:
    assert_that( logger.method_calls[ 0 ][ 1 ][ 0 ],
                 equal_to( test[ 'message' ] ) )
  else:
    assert_that( logger.method_calls, empty() )


def CompatibleWithCurrentCore_Compatible_test():
  RunCompatibleWithCurrentCore( {
    'return_code': 0
  } )


def CompatibleWithCurrentCore_Unexpected_test():
  RunCompatibleWithCurrentCore( {
    'import_error': 'unexpected import error',
    'return_code': 1,
    'message': 'unexpected import error'
  } )


def CompatibleWithCurrentCore_Missing_test():
  import_errors = [
    # Raised by Python 2.
    'No module named ycm_core',
    # Raised by Python 3.
    "No module named 'ycm_core'"
  ]

  for error in import_errors:
    yield RunCompatibleWithCurrentCore, {
      'import_error': error,
      'return_code': 3,
      'message': 'ycm_core library not detected; you need to compile it.'
    }


def CompatibleWithCurrentCore_Python2_test():
  import_errors = [
    # Raised on Linux and OS X with Python 3.3 and 3.4.
    'dynamic module does not define init function (PyInit_ycm_core).',
    # Raised on Linux and OS X with Python 3.5.
    'dynamic module does not define module export function (PyInit_ycm_core).',
    # Raised on Windows.
    'Module use of python26.dll conflicts with this version of Python.',
    'Module use of python27.dll conflicts with this version of Python.'
  ]

  for error in import_errors:
    yield RunCompatibleWithCurrentCore, {
      'import_error': error,
      'return_code': 4,
      'message': 'ycm_core library compiled with Python 2 '
                 'but loaded with Python 3.'
    }


def CompatibleWithCurrentCore_Python3_test():
  import_errors = [
    # Raised on Linux and OS X.
    'dynamic module does not define init function (initycm_core).',
    # Raised on Windows.
    'Module use of python34.dll conflicts with this version of Python.',
    'Module use of python35.dll conflicts with this version of Python.'
  ]

  for error in import_errors:
    yield RunCompatibleWithCurrentCore, {
      'import_error': error,
      'return_code': 5,
      'message': 'ycm_core library compiled with Python 3 '
                 'but loaded with Python 2.'
    }


@patch( 'ycm_core.YcmCoreVersion', side_effect = AttributeError() )
def CompatibleWithCurrentCore_Outdated_NoYcmCoreVersionMethod_test( *args ):
  RunCompatibleWithCurrentCore( {
    'return_code': 6,
    'message': 'ycm_core library too old, PLEASE RECOMPILE.'
  } )


@patch( 'ycm_core.YcmCoreVersion', return_value = 10 )
@patch( 'ycmd.server_utils.ExpectedCoreVersion', return_value = 11 )
def CompatibleWithCurrentCore_Outdated_NoVersionMatch_test( *args ):
  RunCompatibleWithCurrentCore( {
    'return_code': 6,
    'message': 'ycm_core library too old, PLEASE RECOMPILE.'
  } )


def PathToNearestThirdPartyFolder_Success_test():
  ok_( PathToNearestThirdPartyFolder( os.path.abspath( __file__ ) ) )


def PathToNearestThirdPartyFolder_Failure_test():
  ok_( not PathToNearestThirdPartyFolder( os.path.expanduser( '~' ) ) )


def AddNearestThirdPartyFoldersToSysPath_Failure_test():
  assert_that(
    calling( AddNearestThirdPartyFoldersToSysPath ).with_args(
      os.path.expanduser( '~' ) ),
    raises( RuntimeError, '.*third_party folder.*' ) )


@patch( 'sys.path', [ '/some/path',
                      '/first/path/to/site-packages',
                      '/another/path',
                      '/second/path/to/site-packages' ] )
def AddNearestThirdPartyFoldersToSysPath_FutureBeforeSitePackages_test():
  AddNearestThirdPartyFoldersToSysPath( __file__ )
  assert_that( sys.path[ : len( THIRD_PARTY_FOLDERS ) ], contains_inanyorder(
    *THIRD_PARTY_FOLDERS
  ) )
  assert_that( sys.path[ len( THIRD_PARTY_FOLDERS ) : ], contains(
    '/some/path',
    os.path.join( DIR_OF_THIRD_PARTY, 'python-future', 'src' ),
    '/first/path/to/site-packages',
    '/another/path',
    '/second/path/to/site-packages',
  ) )


@patch( 'sys.path', [ '/some/path',
                      '/first/path/to/dist-packages',
                      '/another/path',
                      '/second/path/to/dist-packages' ] )
def AddNearestThirdPartyFoldersToSysPath_FutureBeforeDistPackages_test():
  AddNearestThirdPartyFoldersToSysPath( __file__ )
  assert_that( sys.path[ : len( THIRD_PARTY_FOLDERS ) ], contains_inanyorder(
    *THIRD_PARTY_FOLDERS
  ) )
  assert_that( sys.path[ len( THIRD_PARTY_FOLDERS ) : ], contains(
    '/some/path',
    os.path.join( DIR_OF_THIRD_PARTY, 'python-future', 'src' ),
    '/first/path/to/dist-packages',
    '/another/path',
    '/second/path/to/dist-packages',
  ) )


@patch( 'sys.path', [ '/some/path',
                      '/another/path' ] )
def AddNearestThirdPartyFoldersToSysPath_FutureLastIfNoPackages_test():
  AddNearestThirdPartyFoldersToSysPath( __file__ )
  assert_that( sys.path[ : len( THIRD_PARTY_FOLDERS ) ], contains_inanyorder(
    *THIRD_PARTY_FOLDERS
  ) )
  assert_that( sys.path[ len( THIRD_PARTY_FOLDERS ) : ], contains(
    '/some/path',
    '/another/path',
    os.path.join( DIR_OF_THIRD_PARTY, 'python-future', 'src' ),
  ) )
