# Copyright (C) 2015 ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from ycmd.completers.javascript.tern_completer import (
  ShouldEnableTernCompleter, TernCompleter )
from ycmd.completers.typescript.typescript_completer import (
  ShouldEnableTypeScriptCompleter, TypeScriptCompleter )


def GetCompleter( user_options ):
  if ( not user_options[ 'use_tern_completer' ] and
       ShouldEnableTypeScriptCompleter() ):
    return TypeScriptCompleter( user_options )
  if ShouldEnableTernCompleter():
    return TernCompleter( user_options )
  return None
