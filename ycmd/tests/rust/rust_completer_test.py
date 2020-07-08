# Copyright (C) 2020 ycmd contributors
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

import os
from unittest.mock import patch
from hamcrest import assert_that, equal_to

from ycmd import user_options_store
from ycmd import utils
from ycmd.completers.rust.hook import GetCompleter


def GetCompleter_RAFound_test():
  assert_that( GetCompleter( user_options_store.GetAll() ) )


@patch( 'ycmd.completers.rust.rust_completer.RA_EXECUTABLE', 'does_not_exist' )
def GetCompleter_RANotFound_test( *args ):
  assert_that( not GetCompleter( user_options_store.GetAll() ) )


@patch( 'os.path.isfile', return_value = True )
@patch( 'os.access', return_value = True )
def GetCompleter_RAFromUserOption_test( *args ):
  user_options = user_options_store.GetAll().copy(
          rust_toolchain_root = 'rust-analyzer' )
  assert_that( GetCompleter( user_options )._rust_root,
               equal_to( 'rust-analyzer' ) )
  expected = utils.ExecutableName(
      os.path.join( 'rust-analyzer', 'bin', 'rust-analyzer' ) )
  assert_that( GetCompleter( user_options )._ra_path,
               equal_to( expected ) )
