#!/usr/bin/env python
#
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

from hamcrest import assert_that, equal_to, has_length
from test_utils import BuildRequest
from .client_test import Client_test


class Shutdown_test( Client_test ):

  @Client_test.CaptureOutputFromServer
  def FromHandlerWithoutSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest( 'shutdown' )
    self._AssertResponse( response )

    self._AssertServerAndSubserversShutDown()


  @Client_test.CaptureOutputFromServer
  def FromHandlerWithSubserver_test( self ):
    self._Start()
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._AssertResponse( response )

    self._subservers = self._GetSubservers()
    assert_that( self._subservers, has_length( equal_to( 1 ) ) )

    response = self._PostRequest( 'shutdown' )
    self._AssertResponse( response )

    self._AssertServerAndSubserversShutDown()


  @Client_test.CaptureOutputFromServer
  def FromWatchdogWithoutSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()

    self._AssertServerAndSubserversShutDown()


  @Client_test.CaptureOutputFromServer
  def FromWatchdogWithSubserver_test( self ):
    self._Start( idle_suicide_seconds = 2, check_interval_seconds = 1 )
    self._WaitUntilReady()

    response = self._PostRequest(
      'run_completer_command',
      BuildRequest( command_arguments = [ 'StartServer' ],
                    filetype = 'javascript' )
    )
    self._AssertResponse( response )

    self._subservers = self._GetSubservers()
    assert_that( self._subservers, has_length( equal_to( 1 ) ) )

    self._AssertServerAndSubserversShutDown()
